"""
Tests for DSL parser and validator.
"""

import pytest

from app.core.dsl import PlaybookDSL, PlaybookValidationError


class TestPlaybookDSL:
    """Test playbook DSL parsing and validation."""

    def test_parse_valid_playbook(self, sample_playbook_yaml):
        """Test parsing a valid playbook."""
        dsl = PlaybookDSL()
        result = dsl.parse(sample_playbook_yaml)

        assert result["name"] == "test_playbook"
        assert result["version"] == "1.0.0"
        assert "steps" in result
        assert len(result["steps"]) == 2

    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML."""
        dsl = PlaybookDSL()
        invalid_yaml = "name: test\ninvalid yaml: [unclosed"

        with pytest.raises(PlaybookValidationError, match="Invalid YAML"):
            dsl.parse(invalid_yaml)

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        dsl = PlaybookDSL()

        # Missing 'name'
        yaml1 = "version: 1.0.0\nsteps: {}"
        with pytest.raises(PlaybookValidationError, match="Missing required field: name"):
            dsl.parse(yaml1)

        # Missing 'steps'
        yaml2 = "name: test\nversion: 1.0.0"
        with pytest.raises(PlaybookValidationError, match="Missing required field: steps"):
            dsl.parse(yaml2)

    def test_empty_steps(self):
        """Test validation fails with empty steps."""
        dsl = PlaybookDSL()
        yaml_content = "name: test\nversion: 1.0.0\nsteps: {}"

        with pytest.raises(PlaybookValidationError, match="must have at least one step"):
            dsl.parse(yaml_content)

    def test_invalid_step_type(self):
        """Test validation fails with invalid step type."""
        dsl = PlaybookDSL()
        yaml_content = """
name: test
version: 1.0.0
steps:
  step1:
    type: invalid_type
"""
        with pytest.raises(PlaybookValidationError, match="invalid type"):
            dsl.parse(yaml_content)

    def test_action_step_missing_connector(self):
        """Test action step validation requires connector."""
        dsl = PlaybookDSL()
        yaml_content = """
name: test
version: 1.0.0
steps:
  step1:
    type: action
    operation: test_op
"""
        with pytest.raises(PlaybookValidationError, match="missing required field: connector"):
            dsl.parse(yaml_content)

    def test_condition_step_validation(self):
        """Test condition step validation."""
        dsl = PlaybookDSL()

        # Valid condition
        yaml_valid = """
name: test
version: 1.0.0
steps:
  step1:
    type: condition
    expression: "{{ true }}"
    on_true: step2
    on_false: null
  step2:
    type: action
    connector: test
    operation: test
    next: null
"""
        result = dsl.parse(yaml_valid)
        assert result["steps"]["step1"]["type"] == "condition"

    def test_manual_step_validation(self):
        """Test manual step validation."""
        dsl = PlaybookDSL()
        yaml_content = """
name: test
version: 1.0.0
steps:
  step1:
    type: manual
    prompt: "Approve action?"
    on_approved: null
    on_rejected: null
"""
        result = dsl.parse(yaml_content)
        assert result["steps"]["step1"]["prompt"] == "Approve action?"

    def test_circular_reference_detection(self):
        """Test circular reference detection."""
        dsl = PlaybookDSL()
        yaml_content = """
name: test
version: 1.0.0
steps:
  step1:
    type: action
    connector: test
    operation: test
    next: step2
  step2:
    type: action
    connector: test
    operation: test
    next: step1
"""
        with pytest.raises(PlaybookValidationError, match="Circular reference"):
            dsl.parse(yaml_content)

    def test_template_rendering(self):
        """Test Jinja2 template rendering."""
        dsl = PlaybookDSL()
        context = {"incident": {"id": 123, "severity": "high"}, "vars": {"name": "test"}}

        result = dsl.render_template("Incident {{ incident.id }} is {{ incident.severity }}", context)
        assert result == "Incident 123 is high"

    def test_render_value_with_dict(self):
        """Test rendering values in nested structures."""
        dsl = PlaybookDSL()
        context = {"incident": {"ip": "192.0.2.1"}}

        data = {"static": "value", "dynamic": "IP: {{ incident.ip }}", "nested": {"ip": "{{ incident.ip }}"}}

        result = dsl.render_value(data, context)
        assert result["static"] == "value"
        assert result["dynamic"] == "IP: 192.0.2.1"
        assert result["nested"]["ip"] == "192.0.2.1"
