"""
Pytest configuration and fixtures.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.connectors import dummy_firewall, dummy_identity, dummy_reputation, dummy_slack, dummy_ticketing, http
from app.core.connectors.base import ConnectorRegistry


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="connector_registry")
def connector_registry_fixture():
    """Create a connector registry with all connectors."""
    registry = ConnectorRegistry()
    registry._connectors.clear()  # Clear existing connectors

    registry.register(dummy_firewall.DummyFirewallConnector())
    registry.register(dummy_ticketing.DummyTicketingConnector())
    registry.register(dummy_identity.DummyIdentityConnector())
    registry.register(dummy_slack.DummySlackConnector())
    registry.register(dummy_reputation.DummyReputationConnector())
    registry.register(http.HttpConnector())

    return registry


@pytest.fixture(name="sample_playbook_yaml")
def sample_playbook_yaml_fixture():
    """Sample valid playbook YAML."""
    return """
name: test_playbook
version: 1.0.0
description: Test playbook

steps:
  step1:
    type: action
    connector: dummy_firewall
    operation: block_ip
    input:
      ip: "192.0.2.1"
    next: step2

  step2:
    type: action
    connector: dummy_ticketing
    operation: create_ticket
    input:
      title: "Test ticket"
    next: null
"""
