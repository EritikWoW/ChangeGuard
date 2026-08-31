from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

app.include_router(router)
app.include_router(hackathon_router)

# Assets are mounted separately so the SPA can reference CSS, JS and SVGs.
app.mount("/assets", StaticFiles(directory=settings.frontend_dir), name="assets")


@app.get("/", response_class=HTMLResponse)
async def frontend_index():
    """Serve the canonical UI plus the hackathon/submission enhancement layer."""
    html = (Path(settings.frontend_dir) / "index.html").read_text(encoding="utf-8")
    enhancement = '<script src="/assets/app-hackathon.js"></script>'
    if enhancement not in html:
        html = html.replace("</body>", enhancement + "\n</body>")
    return HTMLResponse(html)


# Keep the static catch-all last so /api/*, /assets/* and / win first.
app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
