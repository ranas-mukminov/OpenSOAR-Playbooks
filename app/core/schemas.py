"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.models import IncidentSeverity, IncidentStatus, PlaybookRunStatus

# Playbook Schemas


class PlaybookCreate(BaseModel):
    """Request schema for creating a playbook."""

    yaml_content: str = Field(..., description="YAML playbook definition")


class PlaybookResponse(BaseModel):
    """Response schema for playbook."""

    id: int
    name: str
    version: str
    description: str | None = None
    tags: list[str] = []
    author: str | None = None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaybookListResponse(BaseModel):
    """Response schema for playbook list."""

    playbooks: list[PlaybookResponse]
    total: int


# Incident Schemas


class IncidentCreate(BaseModel):
    """Request schema for creating an incident."""

    title: str = Field(..., min_length=1)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    owner: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    """Request schema for updating an incident."""

    title: str | None = None
    status: IncidentStatus | None = None
    severity: IncidentSeverity | None = None
    owner: str | None = None
    payload: dict[str, Any] | None = None
    tags: list[str] | None = None


class IncidentResponse(BaseModel):
    """Response schema for incident."""

    id: int
    title: str
    status: IncidentStatus
    severity: IncidentSeverity
    owner: str | None = None
    payload: dict[str, Any]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    """Response schema for incident list."""

    incidents: list[IncidentResponse]
    total: int


# Playbook Run Schemas


class PlaybookRunCreate(BaseModel):
    """Request schema for starting a playbook run."""

    incident_id: int | None = None
    event_id: int | None = None


class PlaybookRunResumeRequest(BaseModel):
    """Request schema for resuming a paused run."""

    decision: str = Field(..., pattern="^(approved|rejected)$")
    manual_input: dict[str, Any] | None = None


class PlaybookRunResponse(BaseModel):
    """Response schema for playbook run."""

    id: int
    playbook_id: int
    incident_id: int | None = None
    event_id: int | None = None
    status: PlaybookRunStatus
    current_step_id: str | None = None
    context: dict[str, Any]
    step_logs: list[dict[str, Any]]
    manual_task: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


class PlaybookRunListResponse(BaseModel):
    """Response schema for playbook run list."""

    runs: list[PlaybookRunResponse]
    total: int


# Event Schemas


class EventCreate(BaseModel):
    """Request schema for creating an event."""

    source: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    tags: list[str] = Field(default_factory=list)


class EventResponse(BaseModel):
    """Response schema for event."""

    id: int
    source: str
    timestamp: datetime
    payload: dict[str, Any]
    severity: IncidentSeverity
    tags: list[str]
    incident_id: int | None = None

    class Config:
        from_attributes = True


# Generic responses


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: str | None = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    message: str
    data: dict[str, Any] | None = None
