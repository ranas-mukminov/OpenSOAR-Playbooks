"""
Dummy identity connector (mock implementation).
"""

import logging
from typing import Any

from app.core.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class DummyIdentityConnector(BaseConnector):
    """
    Mock identity/user management connector.
    Simulates user account operations.
    """

    def __init__(self):
        super().__init__("dummy_identity")
        self.users = {
            "jdoe": {"username": "jdoe", "status": "active", "email": "jdoe@example.com"},
            "admin": {"username": "admin", "status": "active", "email": "admin@example.com"},
        }

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute identity operation."""
        if operation == "get_user_info":
            return await self._get_user_info(params)
        elif operation == "suspend_user":
            return await self._suspend_user(params)
        elif operation == "activate_user":
            return await self._activate_user(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _get_user_info(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get user information."""
        username = params.get("username")

        if not username:
            raise ValueError("Missing required parameter: username")

        user = self.users.get(username, {"username": username, "status": "unknown"})

        logger.info(f"[IDENTITY] Retrieved info for user {username}", extra={"username": username})

        return {"success": True, "action": "get_user_info", "user": user}

    async def _suspend_user(self, params: dict[str, Any]) -> dict[str, Any]:
        """Suspend a user account."""
        username = params.get("username")
        reason = params.get("reason", "Security incident")

        if not username:
            raise ValueError("Missing required parameter: username")

        if username in self.users:
            self.users[username]["status"] = "suspended"
        else:
            self.users[username] = {"username": username, "status": "suspended"}

        logger.warning(
            f"[IDENTITY] Suspended user {username}. Reason: {reason}",
            extra={"username": username, "reason": reason},
        )

        return {
            "success": True,
            "action": "suspend_user",
            "username": username,
            "message": f"User {username} suspended",
        }

    async def _activate_user(self, params: dict[str, Any]) -> dict[str, Any]:
        """Activate a user account."""
        username = params.get("username")

        if not username:
            raise ValueError("Missing required parameter: username")

        if username in self.users:
            self.users[username]["status"] = "active"
        else:
            self.users[username] = {"username": username, "status": "active"}

        logger.info(f"[IDENTITY] Activated user {username}", extra={"username": username})

        return {
            "success": True,
            "action": "activate_user",
            "username": username,
            "message": f"User {username} activated",
        }

    def get_operations(self) -> list[str]:
        """Get supported operations."""
        return ["get_user_info", "suspend_user", "activate_user"]
