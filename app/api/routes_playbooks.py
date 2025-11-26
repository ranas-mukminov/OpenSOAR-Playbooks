"""
Playbook management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.dsl import PlaybookDSL, PlaybookValidationError
from app.core.models import Playbook
from app.core.schemas import (
    ErrorResponse,
    PlaybookCreate,
    PlaybookListResponse,
    PlaybookResponse,
    SuccessResponse,
)
from app.db.session import get_session

router = APIRouter(prefix="/playbooks", tags=["playbooks"])

dsl = PlaybookDSL()


@router.post(
    "",
    response_model=PlaybookResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_playbook(
    playbook_data: PlaybookCreate, session: Session = Depends(get_session)
) -> Playbook:
    """
    Upload and register a new playbook.

    Parses and validates the YAML content before storing.
    """
    try:
        # Parse and validate playbook
        parsed = dsl.parse(playbook_data.yaml_content)
    except PlaybookValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid playbook: {e}")

    # Check if playbook with same name exists
    stmt = select(Playbook).where(Playbook.name == parsed["name"])
    existing = session.exec(stmt).first()
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Playbook with name '{parsed['name']}' already exists"
        )

    # Create playbook
    playbook = Playbook(
        name=parsed["name"],
        version=parsed.get("version", "1.0.0"),
        description=parsed.get("description"),
        yaml_content=playbook_data.yaml_content,
        parsed_data=parsed,
        triggers=parsed.get("triggers", []),
        tags=parsed.get("tags", []),
        author=parsed.get("author"),
    )

    session.add(playbook)
    session.commit()
    session.refresh(playbook)

    return playbook


@router.get("", response_model=PlaybookListResponse)
async def list_playbooks(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
) -> PlaybookListResponse:
    """List all registered playbooks with pagination."""
    stmt = select(Playbook).offset(skip).limit(limit)
    playbooks = session.exec(stmt).all()

    count_stmt = select(Playbook)
    total = len(session.exec(count_stmt).all())

    return PlaybookListResponse(playbooks=list(playbooks), total=total)


@router.get("/{playbook_id}", response_model=PlaybookResponse, responses={404: {"model": ErrorResponse}})
async def get_playbook(playbook_id: int, session: Session = Depends(get_session)) -> Playbook:
    """Get a specific playbook by ID."""
    playbook = session.get(Playbook, playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    return playbook


@router.delete(
    "/{playbook_id}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_playbook(
    playbook_id: int, session: Session = Depends(get_session)
) -> SuccessResponse:
    """Delete a playbook."""
    playbook = session.get(Playbook, playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")

    session.delete(playbook)
    session.commit()

    return SuccessResponse(message=f"Playbook {playbook_id} deleted successfully")
