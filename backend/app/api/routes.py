import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.core.config import settings
from app.models.schemas import (
    AnalysisListItem,
    AnalysisResponse,
    CreateGithubAnalysisRequest,
    HealthResponse,
    RerunRequest,
    RerunResponse,
)
from app.services.analysis_service import analyze_github_pr
from app.services.benchmark_service import run_agentic_benchmark, run_smoke_benchmark
from app.services.config_store import config_store
from app.services.mock_analysis import get_demo_analysis
from app.services.store import store
from app.services.system_service import dashboard_data, report_items, report_markdown

router = APIRouter(prefix="/api")


class SettingsUpdate(BaseModel):
    github_token: str | None = None
    default_repository: str | None = None
    llm_provider: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    block_threshold: int | None = None
    require_evidence: bool | None = None
    reject_unsupported_blast_radius: bool | None = None
    trajectory_logging: bool | None = None


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)


@router.get("/settings")
async def get_settings():
    return config_store.public()


@router.put("/settings")
async def put_settings(payload: SettingsUpdate):
    values = {k: v for k, v in payload.model_dump().items() if v is not None}
    config_store.update(values)
    return config_store.public()


@router.post("/integrations/github/test")
async def test_github():
    cfg = config_store.get_all()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ChangeGuard/0.5"}
    if cfg.get("github_token"):
        headers["Authorization"] = f"Bearer {cfg['github_token']}"
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        response = await client.get(
            "https://api.github.com/user"
            if cfg.get("github_token")
            else "https://api.github.com/rate_limit"
        )
    if response.status_code >= 400:
        raise HTTPException(response.status_code, detail="GitHub connection failed")
    data = response.json()
    return {
        "ok": True,
        "authenticated": bool(cfg.get("github_token")),
        "login": data.get("login"),
        "remaining": (
            data.get("resources", {}).get("core", {}).get("remaining")
            if not cfg.get("github_token")
            else None
        ),
    }


@router.post("/integrations/llm/test")
async def test_llm():
    cfg = config_store.get_all()
    key = cfg.get("llm_api_key")
    base = (cfg.get("llm_base_url") or "").rstrip("/")
    if not key:
        raise HTTPException(400, detail="LLM API key is not configured")
    headers = {"Authorization": f"Bearer {key}"}
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        response = await client.get(base + "/models")
    if response.status_code >= 400:
        raise HTTPException(
            response.status_code,
            detail=f"LLM provider returned HTTP {response.status_code}",
        )
    return {
        "ok": True,
        "provider": cfg.get("llm_provider"),
        "model": cfg.get("llm_model"),
    }


@router.get("/dashboard")
async def dashboard():
    return dashboard_data()


@router.get("/reports")
async def reports():
    return report_items()


@router.get("/reports/{analysis_id}.md", response_class=PlainTextResponse)
async def report_md(analysis_id: str):
    analysis = store.get(analysis_id)
    if not analysis:
        raise HTTPException(404, detail="Analysis not found")
    return PlainTextResponse(
        report_markdown(analysis),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="changeguard-{analysis_id}.md"'
        },
    )


@router.get("/benchmarks/latest")
async def benchmark_latest():
    return config_store.latest_benchmark() or {"status": "not_run"}


@router.post("/benchmarks/run")
async def benchmark_run():
    """Zero-cost 15-case smoke benchmark used during development and CI."""
    return run_smoke_benchmark()


@router.post("/benchmarks/run-agentic")
async def benchmark_run_agentic():
    """Hackathon benchmark: same-model single prompt vs verified agentic workflow."""
    try:
        return await run_agentic_benchmark()
    except RuntimeError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, detail=f"LLM benchmark request failed: {exc}") from exc


@router.get("/analyses", response_model=list[AnalysisListItem])
async def list_analyses(limit: int = Query(50, ge=1, le=200)):
    return store.list(limit)


@router.post("/analyses/from-github", response_model=AnalysisResponse)
async def create_github_analysis(payload: CreateGithubAnalysisRequest):
    try:
        return await analyze_github_pr(payload.pr_url)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, detail=f"GitHub analysis failed: {exc}") from exc


@router.get("/analyses/demo", response_model=AnalysisResponse)
async def demo_analysis():
    return get_demo_analysis()


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def analysis_by_id(analysis_id: str):
    stored = store.get(analysis_id)
    if stored:
        return stored
    if analysis_id == "analysis-pr-184":
        return get_demo_analysis()
    raise HTTPException(404, detail="Analysis not found")


@router.post("/analyses/rerun", response_model=RerunResponse)
async def rerun_analysis(payload: RerunRequest):
    current = store.get(payload.analysis_id)
    if current and current.source_url:
        analysis = await analyze_github_pr(current.source_url)
    elif payload.analysis_id == "analysis-pr-184":
        analysis = get_demo_analysis()
    else:
        raise HTTPException(404, detail="Analysis not found")
    return RerunResponse(
        analysis=analysis,
        stages=[
            "Understand",
            "Collect Context",
            "Analyze Risks",
            "Verify Claims",
            "Final Decision",
        ],
    )
