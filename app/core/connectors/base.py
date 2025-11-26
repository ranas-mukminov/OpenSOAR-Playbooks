"""
Connector framework for external system integrations.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """
    Abstract base class for all connectors.
    Connectors integrate with external systems (firewalls, ticketing, email, etc.)
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(
        self, operation: str, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a connector operation.

        Args:
            operation: Operation name (e.g., "block_ip", "create_ticket")
            params: Operation parameters
            context: Execution context (incident, event, vars)

        Returns:
            Operation result dictionary

        Raises:
            ValueError: If operation is not supported
        """
        pass

    @abstractmethod
    def get_operations(self) -> list[str]:
        """
        Get list of supported operations.

        Returns:
            List of operation names
        """
        pass


class ConnectorRegistry:
    """
    Singleton registry for connectors.
    Manages connector registration and lookup.
    """

    _instance = None
    _connectors: dict[str, BaseConnector] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, connector: BaseConnector) -> None:
        """Register a connector."""
        self._connectors[connector.name] = connector

    def get(self, name: str) -> BaseConnector:
        """Get connector by name."""
        if name not in self._connectors:
            raise ValueError(f"Connector '{name}' not found")
        return self._connectors[name]

    def list_connectors(self) -> list[str]:
        """List all registered connector names."""
        return list(self._connectors.keys())


# Global registry instance
registry = ConnectorRegistry()
