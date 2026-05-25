"""Pytest fixtures for the TideGuard API tests."""

from __future__ import annotations

import os
import tempfile

_TMP_DB_DIR = tempfile.mkdtemp(prefix="tideguard_test_")
_DB_PATH = os.path.join(_TMP_DB_DIR, "test_tideguard.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_PATH}"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def app_instance():
    from tideguard_api.main import create_app

    app = create_app()
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture
async def client(app_instance):
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
