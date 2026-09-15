"""
FastAPI Application Server Entrypoint
=====================================
Initializes FastAPI, configures CORS middleware, mounts static files and templates,
and registers all modular API route controllers.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from backend.routes import api_router

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("nexus_backend")

# Create FastAPI application
app = FastAPI(
    title="Nexus AI — Autonomous Attrition & Retention Framework",
    description="Production FastAPI Backend: Multi-Horizon Survival Analysis, ELV Economic Engine, SHAP-to-LLM Diagnostics, and 5-Agent Closed-Loop Retention System.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Directories
root_dir = os.path.dirname(os.path.dirname(__file__))
static_dirs = [
    os.path.join(root_dir, 'frontend', 'static'),
    os.path.join(root_dir, 'static')
]
for s_dir in static_dirs:
    if os.path.exists(s_dir):
        app.mount("/static", StaticFiles(directory=s_dir), name="static")
        break

# Register all modular API routes
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
def serve_dashboard():
    """Serves the Nexus Single-Page Application Dashboard."""
    template_candidates = [
        os.path.join(root_dir, 'frontend', 'templates', 'dashboard.html'),
        os.path.join(root_dir, 'templates', 'react_dashboard.html'),
        os.path.join(root_dir, 'templates', 'index.html'),
    ]
    for path in template_candidates:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    return "<h1>Nexus AI FastAPI Server is Running. Dashboard HTML not found.</h1>"


@app.get("/health", tags=["System Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "Nexus AI — FastAPI Backend",
        "version": "2.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
