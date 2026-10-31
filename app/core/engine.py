"""
Playbook execution engine.
Orchestrates playbook execution with step routing and state management.
"""

import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session

from app.core.connectors.base import registry
from app.core.context import ExecutionContext
from app.core.dsl import PlaybookDSL, PlaybookValidationError
from app.core.models import Event, Incident, Playbook, PlaybookRun, PlaybookRunStatus

logger = logging.getLogger(__name__)


class PlaybookEngineError(Exception):
    """Raised when playbook execution fails."""

    pass


class PlaybookEngine:
    """
    Playbook execution engine.
    Manages playbook execution lifecycle.
    """

    def __init__(self, session: Session):
        self.session = session
        self.dsl = PlaybookDSL()

    async def run_playbook(
        self,
        playbook_id: int,
        incident_id: int | None = None,
        event_id: int | None = None,
    ) -> PlaybookRun:
        """
        Start playbook execution.

        Args:
            playbook_id: Playbook to execute
            incident_id: Optional incident to run on
            event_id: Optional event to run on

        Returns:
            PlaybookRun instance

        Raises:
            PlaybookEngineError: If execution fails
        """
        # Load playbook
        playbook = self.session.get(Playbook, playbook_id)
        if not playbook:
            raise PlaybookEngineError(f"Playbook {playbook_id} not found")

        # Load incident/event
        incident = self.session.get(Incident, incident_id) if incident_id else None
        event = self.session.get(Event, event_id) if event_id else None

        # Parse playbook
        try:
            playbook_data = self.dsl.parse(playbook.yaml_content)
        except PlaybookValidationError as e:
            raise PlaybookEngineError(f"Invalid playbook: {e}") from e

        # Create execution context
        context = ExecutionContext(playbook_data, incident, event)

        # Create playbook run record
        run = PlaybookRun(
            playbook_id=playbook_id,
            incident_id=incident_id,
            event_id=event_id,
            status=PlaybookRunStatus.RUNNING,
            context=context.serialize(),
            step_logs=[],
            started_at=datetime.utcnow(),
        )

        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        logger.info(
            f"Started playbook run {run.id} for playbook '{playbook.name}'",
            extra={"run_id": run.id, "playbook_id": playbook_id, "incident_id": incident_id},
        )

        # Execute playbook
        try:
            await self._execute_from_step(
                run, playbook_data, context, get_first_step(playbook_data)
            )
        except Exception as e:
            logger.exception(f"Playbook run {run.id} failed", extra={"run_id": run.id})
            run.status = PlaybookRunStatus.FAILED
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.session.commit()
            raise PlaybookEngineError(f"Execution failed: {e}") from e

        return run

    async def resume_run(
        self, run_id: int, decision: str, manual_input: dict[str, Any] | None = None
    ) -> PlaybookRun:
        """
        Resume a paused playbook run (after manual approval).

        Args:
            run_id: Run to resume
            decision: "approved" or "rejected"
            manual_input: Optional user input data

        Returns:
            Updated PlaybookRun

        Raises:
            PlaybookEngineError: If resume fails
        """
        run = self.session.get(PlaybookRun, run_id)
        if not run:
            raise PlaybookEngineError(f"Run {run_id} not found")

        if run.status != PlaybookRunStatus.WAITING:
            raise PlaybookEngineError(f"Run {run_id} is not waiting (status: {run.status})")

        # Load playbook
        playbook = self.session.get(Playbook, run.playbook_id)
        playbook_data = self.dsl.parse(playbook.yaml_content)

        # Restore context
        incident = self.session.get(Incident, run.incident_id) if run.incident_id else None
        event = self.session.get(Event, run.event_id) if run.event_id else None
        context = ExecutionContext.deserialize(run.context, playbook_data, incident, event)

        # Store manual input
        if manual_input:
            context.set_manual_input(manual_input)

        # Determine next step based on decision
        manual_task = run.manual_task
        if not manual_task:
            raise PlaybookEngineError("No manual task found in run")

        step_id = manual_task["step_id"]
        step = playbook_data["steps"][step_id]

        if decision == "approved":
            next_step_id = step.get("on_approved")
        elif decision == "rejected":
            next_step_id = step.get("on_rejected")
        else:
            raise PlaybookEngineError(f"Invalid decision: {decision}")

        # Log decision
        self._log_step(run, step_id, {"decision": decision, "input": manual_input})

        # Update status and continue
        run.status = PlaybookRunStatus.RUNNING
        run.manual_task = None
        self.session.commit()

        logger.info(
            f"Resumed run {run_id} with decision '{decision}'",
            extra={"run_id": run_id, "decision": decision},
        )

        # Execute from next step
        try:
            await self._execute_from_step(run, playbook_data, context, next_step_id)
        except Exception as e:
            run.status = PlaybookRunStatus.FAILED
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.session.commit()
            raise PlaybookEngineError(f"Resume failed: {e}") from e

        return run

    async def _execute_from_step(
        self,
        run: PlaybookRun,
        playbook_data: dict[str, Any],
        context: ExecutionContext,
        step_id: str | None,
    ) -> None:
        """Execute playbook starting from a specific step."""
        current_step_id = step_id

        while current_step_id is not None:
            step = playbook_data["steps"].get(current_step_id)
            if not step:
                logger.error(
                    f"Step '{current_step_id}' not found", extra={"step_id": current_step_id}
                )
                break

            run.current_step_id = current_step_id
            run.context = context.serialize()
            self.session.commit()

            logger.debug(
                f"Executing step '{current_step_id}' (type: {step['type']})",
                extra={"run_id": run.id, "step_id": current_step_id, "type": step["type"]},
            )

            # Execute step based on type
            step_type = step["type"]

            if step_type == "action":
                current_step_id = await self._execute_action_step(
                    run, step, current_step_id, context
                )
            elif step_type == "condition":
                current_step_id = await self._execute_condition_step(
                    run, step, current_step_id, context
                )
            elif step_type == "manual":
                await self._execute_manual_step(run, step, current_step_id, context)
                return  # Pause execution
            elif step_type == "wait":
                current_step_id = await self._execute_wait_step(run, step, current_step_id, context)
            else:
                raise PlaybookEngineError(f"Unknown step type: {step_type}")

        # Execution completed
        run.status = PlaybookRunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        run.current_step_id = None
        self.session.commit()

        logger.info(f"Playbook run {run.id} completed successfully", extra={"run_id": run.id})

    async def _execute_action_step(
        self, run: PlaybookRun, step: dict[str, Any], step_id: str, context: ExecutionContext
    ) -> str | None:
        """Execute an action step."""
        connector_name = step["connector"]
        operation = step["operation"]
        input_params = step.get("input", {})

        # Render input parameters with context
        rendered_params = context.render_value(input_params)

        # Get connector
        try:
            connector = registry.get(connector_name)
        except ValueError:
            raise PlaybookEngineError(f"Connector not found: {connector_name}") from None

        # Execute operation
        try:
            result = await connector.execute(operation, rendered_params, context.to_dict())
        except Exception as e:
            logger.error(
                f"Connector execution failed: {e}",
                extra={"connector": connector_name, "operation": operation},
            )
            raise PlaybookEngineError(f"Connector '{connector_name}' failed: {e}") from e

        # Store output
        context.set_step_output(step_id, result)

        # Log execution
        self._log_step(
            run,
            step_id,
            {
                "type": "action",
                "connector": connector_name,
                "operation": operation,
                "params": rendered_params,
                "result": result,
            },
        )

        return step.get("next")

    async def _execute_condition_step(
        self, run: PlaybookRun, step: dict[str, Any], step_id: str, context: ExecutionContext
    ) -> str | None:
        """Execute a condition step."""
        expression = step["expression"]

        # Render and evaluate expression
        try:
            rendered = context.dsl.render_template(expression, context.to_dict())
            # Convert string result to boolean
            result = str(rendered).lower() in ("true", "1", "yes")
        except Exception as e:
            raise PlaybookEngineError(f"Condition evaluation failed: {e}") from e

        # Determine next step
        next_step_id = step["on_true"] if result else step["on_false"]

        # Log execution
        self._log_step(
            run,
            step_id,
            {"type": "condition", "expression": expression, "result": result, "next": next_step_id},
        )

        return next_step_id

    async def _execute_manual_step(
        self, run: PlaybookRun, step: dict[str, Any], step_id: str, context: ExecutionContext
    ) -> None:
        """Execute a manual approval step (pauses execution)."""
        prompt = step["prompt"]
        input_fields = step.get("input_fields", [])

        # Render prompt
        rendered_prompt = context.render_value(prompt)

        # Create manual task
        manual_task = {
            "step_id": step_id,
            "prompt": rendered_prompt,
            "input_fields": input_fields,
            "on_approved": step.get("on_approved"),
            "on_rejected": step.get("on_rejected"),
        }

        # Update run to waiting state
        run.status = PlaybookRunStatus.WAITING
        run.manual_task = manual_task
        run.context = context.serialize()
        self.session.commit()

        # Log step
        self._log_step(run, step_id, {"type": "manual", "prompt": rendered_prompt})

        logger.info(
            f"Playbook run {run.id} paused for manual approval",
            extra={"run_id": run.id, "step_id": step_id},
        )

    async def _execute_wait_step(
        self, run: PlaybookRun, step: dict[str, Any], step_id: str, context: ExecutionContext
    ) -> str | None:
        """Execute a wait step (simple delay)."""
        duration = step["duration"]

        # Log step
        self._log_step(run, step_id, {"type": "wait", "duration": duration})

        # Note: In v0.1, we don't actually wait. In production, this would schedule a delayed task.
        logger.info(
            f"Wait step (would wait {duration}s in production)",
            extra={"run_id": run.id, "step_id": step_id, "duration": duration},
        )

        return step.get("next")

    def _log_step(self, run: PlaybookRun, step_id: str, data: dict[str, Any]) -> None:
        """Add step execution log to run."""
        log_entry = {"step_id": step_id, "timestamp": datetime.utcnow().isoformat(), **data}

        run.step_logs.append(log_entry)
        self.session.commit()


def get_first_step(playbook_data: dict[str, Any]) -> str | None:
    """
    Determine the first step to execute.
    Returns the first step ID from the steps dictionary.
    """
    steps = playbook_data.get("steps", {})
    if steps:
        # Return first step in dictionary
        return next(iter(steps))
    return None
