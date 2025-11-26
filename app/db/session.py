"""
Database session management and engine setup.
"""

from sqlmodel import Session, create_engine

from app.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
)


def get_session():
    """
    FastAPI dependency for database sessions.
    Yields a session and ensures proper cleanup.
    """
    with Session(engine) as session:
        yield session
