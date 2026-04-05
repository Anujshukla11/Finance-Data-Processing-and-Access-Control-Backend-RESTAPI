"""
Test configuration - ensures the database is initialized before any tests run.

The FastAPI `on_event("startup")` hook does NOT fire when using TestClient,
so we call initialize_db() manually here as a session-scoped fixture.
"""
import pytest
from app.database.setup import initialize_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize the database once before the entire test session."""
    initialize_db()
    yield
