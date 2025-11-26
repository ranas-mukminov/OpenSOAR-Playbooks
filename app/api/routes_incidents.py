"""
Incident management API routes.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.models import Incident
from app.core.schemas import (
    ErrorResponse,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
    SuccessResponse,
)
from app.db.session import get_session

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    incident_data: IncidentCreate, session: Session = Depends(get_session)
) -> Incident:
    """Create a new security incident."""
    incident = Incident(**incident_data.model_dump())
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
) -> IncidentListResponse:
    """List all incidents with pagination."""
    stmt = select(Incident).offset(skip).limit(limit).order_by(Incident.created_at.desc())
    incidents = session.exec(stmt).all()

    count_stmt = select(Incident)
    total = len(session.exec(count_stmt).all())

    return IncidentListResponse(incidents=list(incidents), total=total)


@router.get(
    "/{incident_id}", response_model=IncidentResponse, responses={404: {"model": ErrorResponse}}
)
async def get_incident(incident_id: int, session: Session = Depends(get_session)) -> Incident:
    """Get a specific incident by ID."""
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.patch(
    "/{incident_id}", response_model=IncidentResponse, responses={404: {"model": ErrorResponse}}
)
async def update_incident(
    incident_id: int, update_data: IncidentUpdate, session: Session = Depends(get_session)
) -> Incident:
    """Update an existing incident."""
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(incident, key, value)

    incident.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(incident)

    return incident


@router.delete(
    "/{incident_id}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_incident(
    incident_id: int, session: Session = Depends(get_session)
) -> SuccessResponse:
    """Delete an incident."""
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    session.delete(incident)
    session.commit()

    return SuccessResponse(message=f"Incident {incident_id} deleted successfully")
