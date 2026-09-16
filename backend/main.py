"""Convenience ASGI entry point for local development.

Run from the backend directory with: ``uvicorn main:app --reload``.
"""

from app.main import app

