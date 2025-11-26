"""
Dummy reputation lookup connector (mock implementation).
"""

import hashlib
import logging
from typing import Any

from app.core.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class DummyReputationConnector(BaseConnector):
    """
    Mock IP/URL reputation lookup connector.
    Returns fake reputation scores based on hash.
    """

    def __init__(self):
        super().__init__("dummy_reputation")

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute reputation operation."""
        if operation == "lookup_ip":
            return await self._lookup_ip(params)
        elif operation == "lookup_urls":
            return await self._lookup_urls(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _lookup_ip(self, params: dict[str, Any]) -> dict[str, Any]:
        """Look up IP reputation."""
        ip = params.get("ip")

        if not ip:
            raise ValueError("Missing required parameter: ip")

        # Generate fake score based on IP hash
        score = int(hashlib.md5(ip.encode()).hexdigest()[:2], 16) % 100

        category = "unknown"
        if score < 30:
            category = "malicious"
        elif score < 60:
            category = "suspicious"
        else:
            category = "clean"

        logger.info(
            f"[REPUTATION] IP {ip} score: {score} ({category})",
            extra={"ip": ip, "score": score, "category": category},
        )

        return {
            "success": True,
            "action": "lookup_ip",
            "ip": ip,
            "score": score,
            "category": category,
            "details": {"source": "mock_reputation_db"},
        }

    async def _lookup_urls(self, params: dict[str, Any]) -> dict[str, Any]:
        """Look up URL reputations."""
        urls = params.get("urls", [])

        if not isinstance(urls, list):
            raise ValueError("Parameter 'urls' must be a list")

        results = []
        malicious_count = 0

        for url in urls:
            # Generate fake score
            score = int(hashlib.md5(url.encode()).hexdigest()[:2], 16) % 100
            is_malicious = score < 30

            if is_malicious:
                malicious_count += 1

            results.append({"url": url, "score": score, "malicious": is_malicious})

        logger.info(
            f"[REPUTATION] Checked {len(urls)} URLs, {malicious_count} malicious",
            extra={"url_count": len(urls), "malicious_count": malicious_count},
        )

        return {
            "success": True,
            "action": "lookup_urls",
            "results": results,
            "malicious_count": malicious_count,
            "total_checked": len(urls),
        }

    def get_operations(self) -> list[str]:
        """Get supported operations."""
        return ["lookup_ip", "lookup_urls"]
