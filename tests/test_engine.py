"""
Tests for playbook execution engine.
"""

import pytest

from app.core.engine import PlaybookEngine, get_first_step
from app.core.models import Incident, IncidentSeverity, Playbook, PlaybookRunStatus


class TestPlaybookEngine:
    """Test playbook execution engine."""

    @pytest.mark.asyncio
    async def test_simple_linear_execution(self, session, connector_registry):
        """Test executing a simple linear playbook."""
        playbook_yaml = """
name: simple_test
version: 1.0.0
steps:
  step1:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "Test ticket"
    next: step2
  step2:
    type: action
    connector: dummy_firewall
    operation: block_ip
    input:
      ip: "192.0.2.1"
    next: null
"""

        # Create playbook
        playbook = Playbook(
            name="simple_test",
            version="1.0.0",
            yaml_content=playbook_yaml,
            parsed_data={},
        )
        session.add(playbook)
        session.commit()
        session.refresh(playbook)

        # Run playbook
        engine = PlaybookEngine(session)
        run = await engine.run_playbook(playbook.id)

        # Verify execution
        assert run.status == PlaybookRunStatus.COMPLETED
        assert len(run.step_logs) == 2
        assert run.step_logs[0]["step_id"] == "step1"
        assert run.step_logs[1]["step_id"] == "step2"

    @pytest.mark.asyncio
    async def test_condition_branching(self, session, connector_registry):
        """Test playbook with conditional branching."""
        playbook_yaml = """
name: condition_test
version: 1.0.0
vars:
  threshold: 50
steps:
  check:
    type: condition
    expression: "{{ vars.threshold > 40 }}"
    on_true: step_high
    on_false: step_low
  step_high:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "High threshold"
    next: null
  step_low:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "Low threshold"
    next: null
"""

        playbook = Playbook(
            name="condition_test", version="1.0.0", yaml_content=playbook_yaml, parsed_data={}
        )
        session.add(playbook)
        session.commit()
        session.refresh(playbook)

        engine = PlaybookEngine(session)
        run = await engine.run_playbook(playbook.id)

        assert run.status == PlaybookRunStatus.COMPLETED
        # Should have taken the true branch (step_high)
        assert any(log["step_id"] == "step_high" for log in run.step_logs)
        assert not any(log["step_id"] == "step_low" for log in run.step_logs)

    @pytest.mark.asyncio
    async def test_manual_step_pause(self, session, connector_registry):
        """Test playbook pauses on manual approval step."""
        playbook_yaml = """
name: manual_test
version: 1.0.0
steps:
  step1:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "Before approval"
    next: approval
  approval:
    type: manual
    prompt: "Continue execution?"
    on_approved: step2
    on_rejected: null
  step2:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "After approval"
    next: null
"""

        playbook = Playbook(
            name="manual_test", version="1.0.0", yaml_content=playbook_yaml, parsed_data={}
        )
        session.add(playbook)
        session.commit()
        session.refresh(playbook)

        engine = PlaybookEngine(session)
        run = await engine.run_playbook(playbook.id)

        # Should be waiting for approval
        assert run.status == PlaybookRunStatus.WAITING
        assert run.manual_task is not None
        assert run.manual_task["step_id"] == "approval"
        assert "Continue execution?" in run.manual_task["prompt"]

    @pytest.mark.asyncio
    async def test_resume_run_approved(self, session, connector_registry):
        """Test resuming a paused run with approval."""
        playbook_yaml = """
name: resume_test
version: 1.0.0
steps:
  approval:
    type: manual
    prompt: "Approve?"
    on_approved: step_approved
    on_rejected: step_rejected
  step_approved:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "Approved"
    next: null
  step_rejected:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "Rejected"
    next: null
"""

        playbook = Playbook(
            name="resume_test", version="1.0.0", yaml_content=playbook_yaml, parsed_data={}
        )
        session.add(playbook)
        session.commit()
        session.refresh(playbook)

        engine = PlaybookEngine(session)

        # Start run (will pause)
        run = await engine.run_playbook(playbook.id)
        assert run.status == PlaybookRunStatus.WAITING

        # Resume with approval
        run = await engine.resume_run(run.id, "approved", {"justification": "Looks good"})

        # Should complete and execute approved path
        assert run.status == PlaybookRunStatus.COMPLETED
        assert any(log["step_id"] == "step_approved" for log in run.step_logs)
        assert not any(log["step_id"] == "step_rejected" for log in run.step_logs)

    @pytest.mark.asyncio
    async def test_context_rendering(self, session, connector_registry):
        """Test template rendering with incident context."""
        playbook_yaml = """
name: context_test
version: 1.0.0
steps:
  step1:
    type: action
    connector: dummy_firewall
    operation: block_ip
    input:
      ip: "{{ incident.payload.src_ip }}"
      reason: "Incident {{ incident.id }} - {{ incident.severity }}"
    next: null
"""

        playbook = Playbook(
            name="context_test", version="1.0.0", yaml_content=playbook_yaml, parsed_data={}
        )
        session.add(playbook)
        session.commit()
        session.refresh(playbook)

        # Create incident with payload
        incident = Incident(
            title="Test incident",
            severity=IncidentSeverity.HIGH,
            payload={"src_ip": "192.0.2.99"},
        )
        session.add(incident)
        session.commit()
        session.refresh(incident)

        # Run playbook on incident
        engine = PlaybookEngine(session)
        run = await engine.run_playbook(playbook.id, incident_id=incident.id)

        assert run.status == PlaybookRunStatus.COMPLETED
        # Check that template was rendered
        step_log = run.step_logs[0]
        assert step_log["params"]["ip"] == "192.0.2.99"
        assert str(incident.id) in step_log["params"]["reason"]


def test_get_first_step():
    """Test getting the first step from playbook."""
    playbook_data = {"steps": {"step1": {}, "step2": {}}}
    first = get_first_step(playbook_data)
    assert first == "step1"
