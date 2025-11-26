"""
Dummy firewall connector (mock implementation).
"""

import logging
from typing import Any

from app.core.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class DummyFirewallConnector(BaseConnector):
    """
    Mock firewall connector for demonstrations.
    Logs actions instead of making real firewall changes.
    """

    def __init__(self):
        super().__init__("dummy_firewall")
        self.blocked_ips = set()  # In-memory tracking

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute firewall operation."""
        if operation == "block_ip":
            return await self._block_ip(params)
        elif operation == "unblock_ip":
            return await self._unblock_ip(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _block_ip(self, params: dict[str, Any]) -> dict[str, Any]:
        """Block an IP address."""
        ip = params.get("ip")
        duration = params.get("duration", 3600)
        reason = params.get("reason", "Security incident")

        if not ip:
            raise ValueError("Missing required parameter: ip")

        logger.info(
            f"[FIREWALL] Blocking IP {ip} for {duration}s. Reason: {reason}",
            extra={"ip": ip, "duration": duration, "reason": reason},
        )

        self.blocked_ips.add(ip)

        return {
            "success": True,
            "action": "block_ip",
            "ip": ip,
            "duration": duration,
            "message": f"IP {ip} blocked successfully",
        }

    async def _unblock_ip(self, params: dict[str, Any]) -> dict[str, Any]:
        """Unblock an IP address."""
        ip = params.get("ip")

        if not ip:
            raise ValueError("Missing required parameter: ip")

        logger.info(f"[FIREWALL] Unblocking IP {ip}", extra={"ip": ip})

        self.blocked_ips.discard(ip)

        return {"success": True, "action": "unblock_ip", "ip": ip, "message": f"IP {ip} unblocked"}

    def get_operations(self) -> list[str]:
        """Get supported operations."""
        return ["block_ip", "unblock_ip"]
