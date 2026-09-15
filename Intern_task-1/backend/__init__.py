"""
Backend Package Initialization
==============================
Exposes the FastAPI application and state manager.
"""

from backend.server import app
from backend.state import state, reset_state, json_safe

__all__ = ['app', 'state', 'reset_state', 'json_safe']
