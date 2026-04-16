"""Compatibility entrypoint.

Use `uvicorn app.main:app` as the canonical startup command.
"""

from app.main import app

__all__ = ["app"]
