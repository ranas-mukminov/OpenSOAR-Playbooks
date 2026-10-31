"""
Execution context manager for playbook runs.
Maintains runtime state and provides template rendering.
"""

from typing import Any

from app.core.dsl import PlaybookDSL
from app.core.models import Event, Incident


class ExecutionContext:
    """
    Execution context for a playbook run.
    Stores incident/event data, variables, and step outputs.
    """

    def __init__(
        self,
        playbook_data: dict[str, Any],
        incident: Incident | None = None,
        event: Event | None = None,
    ):
        self.playbook_data = playbook_data
        self.incident = incident
        self.event = event
        self.dsl = PlaybookDSL()

        # Initialize context variables
        self.vars = playbook_data.get("vars", {}).copy()
        self.steps = {}  # Step outputs: {step_id: {output}}
        self.manual = {}  # Manual step input data

    def to_dict(self) -> dict[str, Any]:
        """Export context as dictionary for template rendering."""
        context = {"vars": self.vars, "steps": self.steps, "manual": self.manual}

        if self.incident:
            context["incident"] = {
                "id": self.incident.id,
                "title": self.incident.title,
                "status": self.incident.status,
                "severity": self.incident.severity,
                "owner": self.incident.owner,
                "payload": self.incident.payload,
                "tags": self.incident.tags,
                "created_at": (
                    self.incident.created_at.isoformat() if self.incident.created_at else None
                ),
            }

        if self.event:
            context["event"] = {
                "id": self.event.id,
                "source": self.event.source,
                "timestamp": self.event.timestamp.isoformat() if self.event.timestamp else None,
                "payload": self.event.payload,
                "severity": self.event.severity,
                "tags": self.event.tags,
            }

        return context

    def render_value(self, value: Any) -> Any:
        """Render a value with Jinja2 templates."""
        return self.dsl.render_value(value, self.to_dict())

    def set_step_output(self, step_id: str, output: dict[str, Any]) -> None:
        """Store step output for future reference."""
        self.steps[step_id] = {"output": output}

    def set_manual_input(self, manual_input: dict[str, Any]) -> None:
        """Store manual step input data."""
        self.manual.update(manual_input)

    def serialize(self) -> dict[str, Any]:
        """Serialize context for database storage."""
        return {"vars": self.vars, "steps": self.steps, "manual": self.manual}

    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
        playbook_data: dict[str, Any],
        incident: Incident | None = None,
        event: Event | None = None,
    ) -> "ExecutionContext":
        """Deserialize context from database."""
        ctx = cls(playbook_data, incident, event)
        ctx.vars = data.get("vars", {})
        ctx.steps = data.get("steps", {})
        ctx.manual = data.get("manual", {})
        return ctx
