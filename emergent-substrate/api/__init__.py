"""
API Module - FastAPI REST Endpoints
10 REST endpoints + lifespan bootstrapper
"""

from .main import app, lifespan

__all__ = ["app", "lifespan"]
