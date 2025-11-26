"""
Dummy ticketing connector (mock implementation).
"""

import logging
from typing import Any

from app.core.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class DummyTicketingConnector(BaseConnector):
    """
    Mock ticketing system connector.
    Simulates ticket creation and updates.
    """

    def __init__(self):
        super().__init__("dummy_ticketing")
        self.tickets = {}  # In-memory ticket storage
        self.next_id = 1

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute ticketing operation."""
        if operation == "create_ticket":
            return await self._create_ticket(params)
        elif operation == "update_ticket":
            return await self._update_ticket(params)
        elif operation == "close_ticket":
            return await self._close_ticket(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _create_ticket(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create a new ticket."""
        queue = params.get("queue", "default")
        title = params.get("title")
        description = params.get("description", "")
        severity = params.get("severity", "medium")

        if not title:
            raise ValueError("Missing required parameter: title")

        ticket_id = f"TICKET-{self.next_id}"
        self.next_id += 1

        ticket = {
            "id": ticket_id,
            "queue": queue,
            "title": title,
            "description": description,
            "severity": severity,
            "status": "open",
        }

        self.tickets[ticket_id] = ticket

        logger.info(
            f"[TICKETING] Created ticket {ticket_id}: {title}",
            extra={"ticket_id": ticket_id, "queue": queue, "severity": severity},
        )

        return {
            "success": True,
            "action": "create_ticket",
            "ticket_id": ticket_id,
            "ticket": ticket,
            "message": f"Ticket {ticket_id} created successfully",
        }

    async def _update_ticket(self, params: dict[str, Any]) -> dict[str, Any]:
        """Update an existing ticket."""
        ticket_id = params.get("ticket_id")
        updates = params.get("updates", {})

        if not ticket_id:
            raise ValueError("Missing required parameter: ticket_id")

        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket not found: {ticket_id}")

        self.tickets[ticket_id].update(updates)

        logger.info(
            f"[TICKETING] Updated ticket {ticket_id}", extra={"ticket_id": ticket_id, "updates": updates}
        )

        return {
            "success": True,
            "action": "update_ticket",
            "ticket_id": ticket_id,
            "ticket": self.tickets[ticket_id],
            "message": f"Ticket {ticket_id} updated successfully",
        }

    async def _close_ticket(self, params: dict[str, Any]) -> dict[str, Any]:
        """Close a ticket."""
        ticket_id = params.get("ticket_id")

        if not ticket_id:
            raise ValueError("Missing required parameter: ticket_id")

        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket not found: {ticket_id}")

        self.tickets[ticket_id]["status"] = "closed"

        logger.info(f"[TICKETING] Closed ticket {ticket_id}", extra={"ticket_id": ticket_id})

        return {
            "success": True,
            "action": "close_ticket",
            "ticket_id": ticket_id,
            "message": f"Ticket {ticket_id} closed successfully",
        }

    def get_operations(self) -> list[str]:
        """Get supported operations."""
        return ["create_ticket", "update_ticket", "close_ticket"]
