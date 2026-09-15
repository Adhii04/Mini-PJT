"""
Nexus AI — Primary Application Entry Point
==========================================
Launches the FastAPI backend and serves the modular React dashboard.

Usage:
  python main.py
  uvicorn main:app --reload --port 8000
"""

import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
