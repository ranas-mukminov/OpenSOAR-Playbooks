# Connector Development Guide

Learn how to create custom connectors for OpenSOAR Playbooks.

---

## Overview

Connectors are the integration layer between OpenSOAR playbooks and external systems. Each connector implements a standard interface and provides operations that can be called from playbook steps.

---

## Connector Interface

All connectors must inherit from `BaseConnector` and implement:

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseConnector(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(
        self, 
        operation: str, 
        params: dict[str, Any], 
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a connector operation."""
        pass

    @abstractmethod
    def get_operations(self) -> list[str]:
        """List supported operations."""
        pass
```

---

## Creating a Custom Connector

### Example: Email Connector

```python
"""
Email connector for sending notifications.
"""

import logging
from typing import Any
from app.core.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class EmailConnector(BaseConnector):
    """Connector for email operations."""

    def __init__(self, smtp_server: str, smtp_port: int):
        super().__init__("email")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute email operation."""
        if operation == "send_email":
            return await self._send_email(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _send_email(self, params: dict[str, Any]) -> dict[str, Any]:
        """Send an email."""
        to = params.get("to")
        subject = params.get("subject")
        body = params.get("body")

        if not to or not subject:
            raise ValueError("Missing required parameters: to, subject")

        # TODO: Implement actual SMTP sending
        logger.info(
            f"[EMAIL] Sending email to {to}: {subject}",
            extra={"to": to, "subject": subject}
        )

        return {
            "success": True,
            "action": "send_email",
            "to": to,
            "subject": subject,
            "message_id": "mock-message-id"
        }

    def get_operations(self) -> list[str]:
        """Get supported operations."""
        return ["send_email"]
```

---

## Registering Connectors

Register your connector in `app/main.py`:

```python
from app.core.connectors.base import registry
from app.core.connectors.email import EmailConnector

# In the lifespan startup
registry.register(EmailConnector(smtp_server="localhost", smtp_port=587))
```

---

## Best Practices

1. **Parameter Validation**: Always validate required parameters
2. **Error Handling**: Return meaningful error messages
3. **Logging**: Log all operations with structured data
4. **Return Structure**: Always return `{"success": bool, "action": str, ...}`
5. **Async Operations**: Use `async def` for I/O operations
6. **Configuration**: Accept configuration in `__init__`, not hardcoded

---

## Testing Connectors

```python
import pytest
from app.core.connectors.email import EmailConnector


class TestEmailConnector:
    @pytest.mark.asyncio
    async def test_send_email(self):
        connector = EmailConnector("localhost", 587)
        
        result = await connector.execute(
            "send_email",
            {
                "to": "admin@example.com",
                "subject": "Test",
                "body": "Test email"
            },
            {}
        )
        
        assert result["success"] is True
        assert result["to"] == "admin@example.com"
```

---

## Advanced: Real HTTP Connector

For production use, implement real HTTP calls:

```python
import httpx
from typing import Any
from app.core.connectors.base import BaseConnector


class HttpConnector(BaseConnector):
    """Real HTTP connector using httpx."""

    def __init__(self, timeout: int = 30):
        super().__init__("http")
        self.timeout = timeout

    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        if operation == "request":
            return await self._request(params)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        method = params.get("method", "GET").upper()
        url = params.get("url")
        headers = params.get("headers", {})
        body = params.get("body")

        if not url:
            raise ValueError("Missing required parameter: url")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if method != "GET" else None
            )

        return {
            "success": response.is_success,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.headers.get("content-type") == "application/json" else response.text
        }

    def get_operations(self) -> list[str]:
        return ["request"]
```

---

## Security Considerations

1. **Never log secrets**: Filter API keys, passwords from logs
2. **Use environment variables**: Store credentials in `.env`, not code
3. **Validate inputs**: Sanitize all user-provided data
4. **Rate limiting**: Implement retry logic with backoff
5. **TLS/SSL**: Always use HTTPS for external APIs

---

## Next Steps

After creating a connector:
1. Write unit tests
2. Add to connector registry
3. Document operations in playbook examples
4. Submit PR with documentation updates
