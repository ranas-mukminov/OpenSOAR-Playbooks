"""
YAML playbook DSL parsing and validation.
"""

import re
from typing import Any

import yaml
from jinja2 import Environment, Template, TemplateSyntaxError


class PlaybookValidationError(Exception):
    """Raised when playbook validation fails."""

    pass


class PlaybookDSL:
    """
    Playbook DSL parser and validator.
    Loads YAML playbooks and validates their structure.
    """

    def __init__(self):
        self.jinja_env = Environment(autoescape=False)

    def parse(self, yaml_content: str) -> dict[str, Any]:
        """
        Parse YAML playbook content.

        Args:
            yaml_content: Raw YAML string

        Returns:
            Parsed playbook dictionary

        Raises:
            PlaybookValidationError: If parsing or validation fails
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise PlaybookValidationError(f"Invalid YAML: {e}")

        if not isinstance(data, dict):
            raise PlaybookValidationError("Playbook must be a YAML dictionary")

        # Validate structure
        self.validate(data)

        return data

    def validate(self, playbook: dict[str, Any]) -> None:
        """
        Validate playbook structure and semantics.

        Args:
            playbook: Parsed playbook dictionary

        Raises:
            PlaybookValidationError: If validation fails
        """
        # Required fields
        required = ["name", "version", "steps"]
        for field in required:
            if field not in playbook:
                raise PlaybookValidationError(f"Missing required field: {field}")

        # Validate name
        if not isinstance(playbook["name"], str) or not playbook["name"]:
            raise PlaybookValidationError("Playbook name must be a non-empty string")

        # Validate steps
        steps = playbook.get("steps", {})
        if not isinstance(steps, dict):
            raise PlaybookValidationError("Steps must be a dictionary")

        if not steps:
            raise PlaybookValidationError("Playbook must have at least one step")

        # Validate each step
        for step_id, step_data in steps.items():
            self._validate_step(step_id, step_data, steps)

        # Check for circular references
        self._check_circular_references(steps)

    def _validate_step(self, step_id: str, step: dict[str, Any], all_steps: dict) -> None:
        """Validate individual step structure."""
        if not isinstance(step, dict):
            raise PlaybookValidationError(f"Step '{step_id}' must be a dictionary")

        # Required: type
        if "type" not in step:
            raise PlaybookValidationError(f"Step '{step_id}' missing 'type' field")

        step_type = step["type"]
        valid_types = ["action", "condition", "manual", "wait"]
        if step_type not in valid_types:
            raise PlaybookValidationError(
                f"Step '{step_id}' has invalid type '{step_type}'. "
                f"Valid types: {valid_types}"
            )

        # Type-specific validation
        if step_type == "action":
            self._validate_action_step(step_id, step)
        elif step_type == "condition":
            self._validate_condition_step(step_id, step, all_steps)
        elif step_type == "manual":
            self._validate_manual_step(step_id, step, all_steps)
        elif step_type == "wait":
            self._validate_wait_step(step_id, step, all_steps)

    def _validate_action_step(self, step_id: str, step: dict[str, Any]) -> None:
        """Validate action step."""
        required = ["connector", "operation"]
        for field in required:
            if field not in step:
                raise PlaybookValidationError(
                    f"Action step '{step_id}' missing required field: {field}"
                )

        # Validate input parameters (if present)
        if "input" in step and not isinstance(step["input"], dict):
            raise PlaybookValidationError(
                f"Action step '{step_id}' input must be a dictionary"
            )

        # Validate Jinja2 templates in input
        if "input" in step:
            self._validate_templates(step["input"], step_id)

    def _validate_condition_step(
        self, step_id: str, step: dict[str, Any], all_steps: dict
    ) -> None:
        """Validate condition step."""
        if "expression" not in step:
            raise PlaybookValidationError(
                f"Condition step '{step_id}' missing 'expression' field"
            )

        # Validate expression is a Jinja2 template
        try:
            self.jinja_env.from_string(step["expression"])
        except TemplateSyntaxError as e:
            raise PlaybookValidationError(
                f"Condition step '{step_id}' has invalid expression: {e}"
            )

        # Validate branching
        for branch in ["on_true", "on_false"]:
            if branch not in step:
                raise PlaybookValidationError(
                    f"Condition step '{step_id}' missing '{branch}' field"
                )
            # Allow null for terminal steps
            if step[branch] is not None and step[branch] not in all_steps:
                raise PlaybookValidationError(
                    f"Condition step '{step_id}' references non-existent step: {step[branch]}"
                )

    def _validate_manual_step(
        self, step_id: str, step: dict[str, Any], all_steps: dict
    ) -> None:
        """Validate manual (approval) step."""
        if "prompt" not in step:
            raise PlaybookValidationError(f"Manual step '{step_id}' missing 'prompt' field")

        # Validate branching
        for branch in ["on_approved", "on_rejected"]:
            if branch not in step:
                raise PlaybookValidationError(
                    f"Manual step '{step_id}' missing '{branch}' field"
                )
            # Allow null for terminal steps
            if step[branch] is not None and step[branch] not in all_steps:
                raise PlaybookValidationError(
                    f"Manual step '{step_id}' references non-existent step: {step[branch]}"
                )

    def _validate_wait_step(self, step_id: str, step: dict[str, Any], all_steps: dict) -> None:
        """Validate wait step."""
        if "duration" not in step:
            raise PlaybookValidationError(f"Wait step '{step_id}' missing 'duration' field")

        if not isinstance(step["duration"], (int, float)) or step["duration"] < 0:
            raise PlaybookValidationError(
                f"Wait step '{step_id}' duration must be a non-negative number"
            )

    def _validate_templates(self, data: Any, step_id: str) -> None:
        """Recursively validate Jinja2 templates in data structure."""
        if isinstance(data, str):
            # Check if string contains Jinja2 template syntax
            if "{{" in data or "{%" in data:
                try:
                    self.jinja_env.from_string(data)
                except TemplateSyntaxError as e:
                    raise PlaybookValidationError(
                        f"Step '{step_id}' has invalid template syntax: {e}"
                    )
        elif isinstance(data, dict):
            for value in data.values():
                self._validate_templates(value, step_id)
        elif isinstance(data, list):
            for item in data:
                self._validate_templates(item, step_id)

    def _check_circular_references(self, steps: dict[str, Any]) -> None:
        """
        Check for circular references in step flow.

        Uses depth-first search to detect cycles.
        """

        def visit(step_id: str, visited: set, path: list):
            if step_id is None:
                return  # Terminal step

            if step_id in path:
                cycle = " -> ".join(path + [step_id])
                raise PlaybookValidationError(f"Circular reference detected: {cycle}")

            if step_id in visited:
                return  # Already checked this path

            visited.add(step_id)
            path.append(step_id)

            step = steps[step_id]
            step_type = step["type"]

            # Get next steps based on type
            next_steps = []
            if step_type == "action":
                next_steps = [step.get("next")]
            elif step_type == "condition":
                next_steps = [step.get("on_true"), step.get("on_false")]
            elif step_type == "manual":
                next_steps = [step.get("on_approved"), step.get("on_rejected")]
            elif step_type == "wait":
                next_steps = [step.get("next")]

            for next_step in next_steps:
                if next_step is not None:
                    visit(next_step, visited, path[:])

        # Start from each step (handles disconnected graphs)
        visited_global = set()
        for step_id in steps:
            if step_id not in visited_global:
                visit(step_id, visited_global, [])

    def render_template(self, template_str: str, context: dict[str, Any]) -> str:
        """
        Render a Jinja2 template string with context.

        Args:
            template_str: Template string
            context: Context dictionary

        Returns:
            Rendered string
        """
        template = self.jinja_env.from_string(str(template_str))
        return template.render(**context)

    def render_value(self, value: Any, context: dict[str, Any]) -> Any:
        """
        Recursively render templates in a value.

        Args:
            value: Value (may contain templates)
            context: Context dictionary

        Returns:
            Value with all templates rendered
        """
        if isinstance(value, str):
            if "{{" in value or "{%" in value:
                return self.render_template(value, context)
            return value
        elif isinstance(value, dict):
            return {k: self.render_value(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.render_value(item, context) for item in value]
        else:
            return value
