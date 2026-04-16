"""Shared pytest configuration."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path, override=False)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers",
        "requires_integration_secret: requires FAKE_NEWS_INTEGRATION_TEXT secret",
    )


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _skip_if_missing_integration_secret(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("requires_integration_secret"):
        if not os.getenv("FAKE_NEWS_INTEGRATION_TEXT"):
            pytest.skip("FAKE_NEWS_INTEGRATION_TEXT not set")
