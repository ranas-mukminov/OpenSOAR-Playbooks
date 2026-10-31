"""
Playbook execution (runs) API routes.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.engine import PlaybookEngine, PlaybookEngineError
from app.core.models import PlaybookRun
from app.core.schemas import (
    ErrorResponse,
    PlaybookRunCreate,
    PlaybookRunListResponse,
    PlaybookRunResponse,
    PlaybookRunResumeRequest,
)
from app.db.session import get_session

router = APIRouter(prefix="/playbooks", tags=["execution"])


async def run_playbook_background(
    playbook_id: int,
    incident_id: int | None,
    event_id: int | None,
    session: Session,
):
    """Background task to run a playbook."""
    engine = PlaybookEngine(session)
    try:
        await engine.run_playbook(playbook_id, incident_id, event_id)
    except PlaybookEngineError:
        # Error is already logged and saved to run
        pass


@router.post(
    "/{playbook_id}/run",
    response_model=PlaybookRunResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def run_playbook(
    playbook_id: int,
    run_data: PlaybookRunCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> PlaybookRun:
    """
    Start a new playbook execution.

    The playbook will be executed asynchronously in the background.
    """
    engine = PlaybookEngine(session)

    try:
        run = await engine.run_playbook(playbook_id, run_data.incident_id, run_data.event_id)
    except PlaybookEngineError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return run


@router.get(
    "/{playbook_id}/runs",
    response_model=PlaybookRunListResponse,
    responses={404: {"model": ErrorResponse}},
)
async def list_playbook_runs(
    playbook_id: int, skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
) -> PlaybookRunListResponse:
    """List all runs for a specific playbook."""
    stmt = (
        select(PlaybookRun)
        .where(PlaybookRun.playbook_id == playbook_id)
        .offset(skip)
        .limit(limit)
        .order_by(PlaybookRun.created_at.desc())
    )
    runs = session.exec(stmt).all()

    count_stmt = select(PlaybookRun).where(PlaybookRun.playbook_id == playbook_id)
    total = len(session.exec(count_stmt).all())

    return PlaybookRunListResponse(runs=list(runs), total=total)


# Separate router for run management
runs_router = APIRouter(prefix="/runs", tags=["execution"])


@runs_router.get("", response_model=PlaybookRunListResponse)
async def list_all_runs(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
) -> PlaybookRunListResponse:
    """List all playbook runs across all playbooks."""
    stmt = select(PlaybookRun).offset(skip).limit(limit).order_by(PlaybookRun.created_at.desc())
    runs = session.exec(stmt).all()

    count_stmt = select(PlaybookRun)
    total = len(session.exec(count_stmt).all())

    return PlaybookRunListResponse(runs=list(runs), total=total)


@runs_router.get(
    "/{run_id}", response_model=PlaybookRunResponse, responses={404: {"model": ErrorResponse}}
)
async def get_run(run_id: int, session: Session = Depends(get_session)) -> PlaybookRun:
    """Get detailed information about a specific run."""
    run = session.get(PlaybookRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@runs_router.post(
    "/{run_id}/resume",
    response_model=PlaybookRunResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def resume_run(
    run_id: int,
    resume_data: PlaybookRunResumeRequest,
    session: Session = Depends(get_session),
) -> PlaybookRun:
    """
    Resume a paused playbook run (manual approval step).

    Requires a decision ('approved' or 'rejected') and optional manual input.
    """
    engine = PlaybookEngine(session)

    try:
        run = await engine.resume_run(run_id, resume_data.decision, resume_data.manual_input)
    except PlaybookEngineError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return run
