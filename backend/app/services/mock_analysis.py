from datetime import datetime, timezone
from app.models.schemas import (
    AnalysisResponse, Claim, Decision, Evidence, FileChange,
    Severity, TrajectoryStep,
)


def get_demo_analysis() -> AnalysisResponse:
    return AnalysisResponse(
        id="analysis-pr-184",
        repo="EritikWoW/changeguard-demo",
        pull_request=184,
        title="Reduce memory limit for checkout-api",
        branch_from="feature/reduce-memory",
        branch_to="main",
        decision=Decision.BLOCK,
        severity=Severity.HIGH,
        confidence=0.93,
        predicted_failure="OOMKilled (Out Of Memory)",
        failure_detail="The container is likely to be killed due to insufficient memory.",
        recommendation="Do not merge this change. Increase the memory limit to at least 600Mi, then rerun verification.",
        analysis_time_seconds=18.4,
        model="gpt-5.6",
        files=[
            FileChange(path="k8s/checkout-api/deployment.yaml", risk=Severity.HIGH),
            FileChange(path="helm/checkout-api/values.yaml", risk=Severity.MEDIUM),
            FileChange(path="docs/README.md", risk=Severity.LOW),
        ],
        evidence=[
            Evidence(id="EV-001", title="deployment.yaml", source="repository", detail="Memory limit changed 512Mi -> 256Mi", location="L25"),
            Evidence(id="EV-002", title="Current p95 memory", source="metrics:7d", detail="412Mi"),
            Evidence(id="EV-003", title="Max observed memory", source="metrics:7d", detail="487Mi"),
        ],
        claims=[
            Claim(id="CL-001", text="The new limit is below p95 memory usage.", status="supported", evidence_ids=["EV-001", "EV-002"]),
            Claim(id="CL-002", text="The new limit is below observed peak memory usage.", status="supported", evidence_ids=["EV-001", "EV-003"]),
            Claim(id="CL-003", text="The deployment is likely to be OOMKilled.", status="supported", evidence_ids=["EV-001", "EV-002", "EV-003"]),
            Claim(id="CL-004", text="This change may affect PostgreSQL.", status="rejected", reason="No evidence of a direct dependency."),
        ],
        trajectory=[
            TrajectoryStep(order=1, agent="Change Analyzer", summary="Detected a memory limit reduction in checkout-api.", status="done"),
            TrajectoryStep(order=2, agent="Evidence Collector", summary="Loaded runtime memory evidence and dependency context.", status="done", tool_calls=["read_repository_file", "get_runtime_metrics"]),
            TrajectoryStep(order=3, agent="Risk Analyzer", summary="Generated OOMKilled as the primary failure hypothesis.", status="done"),
            TrajectoryStep(order=4, agent="Verifier", summary="Rejected one unsupported PostgreSQL blast-radius claim.", status="1_rejected"),
            TrajectoryStep(order=5, agent="Decision", summary="3 supported claims -> BLOCK.", status="block"),
        ],
        created_at=datetime.now(timezone.utc),
    )
