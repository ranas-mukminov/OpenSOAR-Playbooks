"""
HTTP connector (mock implementation for v0.1).
"""

import logging
from typing import Any

from app.core.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class HttpConnector(BaseConnector):
    """
    Mock HTTP connector.
    In v0.1, logs requests instead of making real HTTP calls.
    """

    def __init__(self):
        super().__init__("http")

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute HTTP operation."""
        if operation == "request":
            return await self._request(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make an HTTP request (mocked)."""
        method = params.get("method", "GET").upper()
        url = params.get("url")
        headers = params.get("headers", {})
        body = params.get("body")

        if not url:
            raise ValueError("Missing required parameter: url")

        logger.info(
            f"[HTTP] {method} {url}",
            extra={"method": method, "url": url, "headers": headers, "body": body},
        )

        # Return mock response
        return {
            "success": True,
            "action": "request",
            "method": method,
            "url": url,
            "status_code": 200,
            "response": {"message": "Mock HTTP response"},
        }

    def get_operations(self) -> list[str]:
        """Get supported operations."""
        return ["request"]
