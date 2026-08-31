from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.api.hackathon_routes import router as hackathon_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes are registered before static/frontend mounts.
app.include_router(router)
app.include_router(hackathon_router)

# The frontend references CSS, JS and SVG files through /assets/*.
# Mount the frontend directory at /assets first so these URLs resolve to
# styles.css, app.js and changeguard-svg-icons/* inside the frontend root.
app.mount("/assets", StaticFiles(directory=settings.frontend_dir), name="assets")

# Serve index.html and any root-level frontend files from /.
# Keep this catch-all mount last so /api/* and /assets/* win first.
app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
