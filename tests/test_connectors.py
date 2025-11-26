"""
Tests for connector framework.
"""

import pytest

from app.core.connectors.base import ConnectorRegistry
from app.core.connectors.dummy_firewall import DummyFirewallConnector
from app.core.connectors.dummy_ticketing import DummyTicketingConnector


class TestConnectors:
    """Test connector framework."""

    @pytest.mark.asyncio
    async def test_firewall_connector(self):
        """Test dummy firewall connector."""
        connector = DummyFirewallConnector()

        # Test block_ip
        result = await connector.execute(
            "block_ip", {"ip": "192.0.2.1", "duration": 3600, "reason": "Test"}, {}
        )

        assert result["success"] is True
        assert result["ip"] == "192.0.2.1"
        assert "192.0.2.1" in connector.blocked_ips

        # Test unblock_ip
        result = await connector.execute("unblock_ip", {"ip": "192.0.2.1"}, {})
        assert result["success"] is True
        assert "192.0.2.1" not in connector.blocked_ips

    @pytest.mark.asyncio
    async def test_ticketing_connector(self):
        """Test dummy ticketing connector."""
        connector = DummyTicketingConnector()

        # Test create_ticket
        result = await connector.execute(
            "create_ticket",
            {"title": "Test ticket", "description": "Test desc", "severity": "high"},
            {},
        )

        assert result["success"] is True
        assert result["ticket_id"].startswith("TICKET-")
        ticket_id = result["ticket_id"]

        # Test update_ticket
        result = await connector.execute(
            "update_ticket", {"ticket_id": ticket_id, "updates": {"status": "in_progress"}}, {}
        )
        assert result["success"] is True
        assert connector.tickets[ticket_id]["status"] == "in_progress"

        # Test close_ticket
        result = await connector.execute("close_ticket", {"ticket_id": ticket_id}, {})
        assert result["success"] is True
        assert connector.tickets[ticket_id]["status"] == "closed"

    @pytest.mark.asyncio
    async def test_connector_operations_list(self):
        """Test connector returns list of operations."""
        connector = DummyFirewallConnector()
        operations = connector.get_operations()

        assert "block_ip" in operations
        assert "unblock_ip" in operations

    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test connector raises error for invalid operation."""
        connector = DummyFirewallConnector()

        with pytest.raises(ValueError, match="Unsupported operation"):
            await connector.execute("invalid_operation", {}, {})

    @pytest.mark.asyncio
    async def test_missing_parameters(self):
        """Test connector validates required parameters."""
        connector = DummyFirewallConnector()

        with pytest.raises(ValueError, match="Missing required parameter"):
            await connector.execute("block_ip", {}, {})


class TestConnectorRegistry:
    """Test connector registry."""

    def test_register_and_get_connector(self):
        """Test registering and retrieving connectors."""
        registry = ConnectorRegistry()
        registry._connectors.clear()

        connector = DummyFirewallConnector()
        registry.register(connector)

        retrieved = registry.get("dummy_firewall")
        assert retrieved.name == "dummy_firewall"

    def test_get_nonexistent_connector(self):
        """Test getting non-existent connector raises error."""
        registry = ConnectorRegistry()
        registry._connectors.clear()

        with pytest.raises(ValueError, match="Connector .* not found"):
            registry.get("nonexistent")

    def test_list_connectors(self):
        """Test listing all registered connectors."""
        registry = ConnectorRegistry()
        registry._connectors.clear()

        registry.register(DummyFirewallConnector())
        registry.register(DummyTicketingConnector())

        connectors = registry.list_connectors()
        assert "dummy_firewall" in connectors
        assert "dummy_ticketing" in connectors
