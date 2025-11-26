"""
Dummy Slack connector (mock implementation).
"""

import logging
from typing import Any

from app.core.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class DummySlackConnector(BaseConnector):
    """
    Mock Slack messaging connector.
    Logs messages instead of sending to real Slack.
    """

    def __init__(self):
        super().__init__("dummy_slack")
        self.messages = []  # In-memory message log

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute Slack operation."""
        if operation == "send_message":
            return await self._send_message(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _send_message(self, params: dict[str, Any]) -> dict[str, Any]:
        """Send a message to Slack channel."""
        channel = params.get("channel", "#general")
        message = params.get("message")

        if not message:
            raise ValueError("Missing required parameter: message")

        message_data = {"channel": channel, "message": message, "timestamp": "mock-ts"}

        self.messages.append(message_data)

        logger.info(
            f"[SLACK] Sent message to {channel}: {message[:50]}...",
            extra={"channel": channel, "message": message},
        )

        return {
            "success": True,
            "action": "send_message",
            "channel": channel,
            "message_ts": "mock-ts",
            "message": f"Message sent to {channel}",
        }

    def get_operations(self) -> list[str]:
        """Get supported operations."""
        return ["send_message"]
