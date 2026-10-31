"""
Main FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
from sqlmodel import SQLModel

from app.api import routes_incidents, routes_playbooks, routes_runs
from app.config import settings
from app.core.connectors import (
    dummy_firewall,
    dummy_identity,
    dummy_reputation,
    dummy_slack,
    dummy_ticketing,
    http,
)
from app.core.connectors.base import registry
from app.db.session import engine

# Configure logging
logger = logging.getLogger()

if settings.log_format == "json":
    log_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
else:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

logger.setLevel(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting OpenSOAR Playbooks API", extra={"version": settings.app_version})

    # Create database tables
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created/verified")

    # Register connectors
    registry.register(dummy_firewall.DummyFirewallConnector())
    registry.register(dummy_ticketing.DummyTicketingConnector())
    registry.register(dummy_identity.DummyIdentityConnector())
    registry.register(dummy_slack.DummySlackConnector())
    registry.register(dummy_reputation.DummyReputationConnector())
    registry.register(http.HttpConnector())

    logger.info(
        f"Registered {len(registry.list_connectors())} connectors",
        extra={"connectors": registry.list_connectors()},
    )

    yield

    # Shutdown
    logger.info("Shutting down OpenSOAR Playbooks API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Open-source SOAR playbook engine for incident response automation",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple API key authentication dependency
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key from header."""
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key


# Register routers
app.include_router(routes_playbooks.router, dependencies=[Depends(verify_api_key)])
app.include_router(routes_incidents.router, dependencies=[Depends(verify_api_key)])
app.include_router(routes_runs.router, dependencies=[Depends(verify_api_key)])
app.include_router(routes_runs.runs_router, dependencies=[Depends(verify_api_key)])


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
        "connectors": registry.list_connectors(),
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
