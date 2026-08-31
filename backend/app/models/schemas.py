from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


class Decision(StrEnum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Evidence(BaseModel):
    id: str
    title: str
    source: str
    detail: str
    location: str | None = None
    verified: bool = True


class Claim(BaseModel):
    id: str
    text: str
    status: Literal["supported", "rejected", "insufficient"]
    evidence_ids: list[str] = Field(default_factory=list)
    reason: str | None = None


class FileChange(BaseModel):
    path: str
    risk: Severity
    change_type: str = "modified"
    additions: int = 0
    deletions: int = 0
    patch: str | None = None


class RunDetails(BaseModel):
    run_id: str
    model: str
    tokens: int | None = None
    estimated_cost_usd: float | None = None
    retries: int = 0


class TrajectoryStep(BaseModel):
    order: int
    agent: str
    summary: str
    status: str
    tool_calls: list[str] = Field(default_factory=list)
    duration_ms: int | None = None


class AnalysisResponse(BaseModel):
    id: str
    repo: str
    pull_request: int
    title: str
    branch_from: str
    branch_to: str
    decision: Decision
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    predicted_failure: str
    failure_detail: str
    recommendation: str
    analysis_time_seconds: float
    model: str
    files: list[FileChange]
    evidence: list[Evidence]
    claims: list[Claim]
    trajectory: list[TrajectoryStep]
    risk_categories: dict[str, int] = Field(default_factory=dict)
    blast_radius: list[str] = Field(default_factory=list)
    run_details: RunDetails | None = None
    created_at: datetime
    source_url: str | None = None


class CreateGithubAnalysisRequest(BaseModel):
    pr_url: str
    include_repository_context: bool = True


class RerunRequest(BaseModel):
    analysis_id: str


class RerunResponse(BaseModel):
    analysis: AnalysisResponse
    stages: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class AnalysisListItem(BaseModel):
    id: str
    repo: str
    pull_request: int
    title: str
    decision: Decision
    severity: Severity
    confidence: float
    created_at: datetime
