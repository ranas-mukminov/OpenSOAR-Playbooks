"""
SQLModel ORM models for OpenSOAR Playbooks domain entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


# Enums
class IncidentStatus(str, Enum):  # noqa: UP042
    """Incident lifecycle statuses."""

    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    CONTAINED = "contained"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):  # noqa: UP042
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlaybookRunStatus(str, Enum):  # noqa: UP042
    """Playbook execution statuses."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"  # Paused on manual step
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Domain Models


class Event(SQLModel, table=True):
    """
    Raw security event from external sources (SIEM, EDR, logs).
    Immutable record of security-relevant activity.
    """

    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    source: str = Field(index=True)  # e.g., "siem", "edr", "firewall"
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    payload: dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM, index=True)
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    incident_id: int | None = Field(default=None, foreign_key="incidents.id")
    incident: Optional["Incident"] = Relationship(back_populates="events")


class Incident(SQLModel, table=True):
    """
    Aggregation of related events requiring response.
    Primary target for playbook execution.
    """

    __tablename__ = "incidents"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    status: IncidentStatus = Field(default=IncidentStatus.NEW, index=True)
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM, index=True)
    owner: str | None = Field(default=None, index=True)
    payload: dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    events: list[Event] = Relationship(back_populates="incident")
    playbook_runs: list["PlaybookRun"] = Relationship(back_populates="incident")


class Playbook(SQLModel, table=True):
    """
    YAML-defined workflow specification.
    Versioned automation workflows with triggers and steps.
    """

    __tablename__ = "playbooks"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    version: str = Field(default="1.0.0")
    description: str | None = None
    yaml_content: str  # Full YAML definition
    parsed_data: dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Parsed structure
    triggers: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    author: str | None = None
    enabled: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    playbook_runs: list["PlaybookRun"] = Relationship(back_populates="playbook")


class PlaybookRun(SQLModel, table=True):
    """
    Single execution instance of a playbook.
    Tracks execution state, progress, and results.
    """

    __tablename__ = "playbook_runs"

    id: int | None = Field(default=None, primary_key=True)
    playbook_id: int = Field(foreign_key="playbooks.id", index=True)
    incident_id: int | None = Field(default=None, foreign_key="incidents.id", index=True)
    event_id: int | None = Field(default=None, foreign_key="events.id", index=True)
    status: PlaybookRunStatus = Field(default=PlaybookRunStatus.PENDING, index=True)

    # Execution context and state
    current_step_id: str | None = None  # Current step being executed
    context: dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Variables, step outputs
    step_logs: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSON))  # Execution log

    # Manual step data (for pause/resume)
    manual_task: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Error tracking
    error_message: str | None = None

    # Relationships
    playbook: Playbook = Relationship(back_populates="playbook_runs")
    incident: Incident | None = Relationship(back_populates="playbook_runs")
    event: Event | None = Relationship(back_populates=None)
