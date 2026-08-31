import json
from datetime import datetime, timezone
from pathlib import Path

from app.models.schemas import Severity
from app.services.baseline_service import review_case
from app.services.config_store import config_store
from app.services.llm_service import analyze_with_llm
from app.services.rule_engine import Finding, analyze_file, summarize


CASES_PATH = Path(__file__).resolve().parents[2] / "benchmark" / "cases.json"


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def _simple_baseline(path: str, patch: str) -> str:
    """Offline smoke baseline. The official benchmark uses review_case()."""
    low = (patch or "").lower()
    if "privileged: true" in low or "0.0.0.0/0" in low or "api_key=" in low:
        return "block"
    return "pass"


def _metrics(rows: list[dict]) -> list[dict]:
    n = len(rows) or 1
    baseline_accuracy = round(100 * sum(r["baseline"] == r["truth"] for r in rows) / n)
    final_accuracy = round(100 * sum(r["changeguard"] == r["truth"] for r in rows) / n)

    dangerous = [r for r in rows if r["truth"] in {"block", "warn"}]
    safe = [r for r in rows if r["truth"] == "pass"]

    def dangerous_detection(key: str) -> int:
        return round(100 * sum(r[key] in {"block", "warn"} for r in dangerous) / max(1, len(dangerous)))

    def safe_accuracy(key: str) -> int:
        return round(100 * sum(r[key] == "pass" for r in safe) / max(1, len(safe)))

    return [
        {"name": "Decision accuracy", "baseline": baseline_accuracy, "changeguard": final_accuracy, "unit": "%"},
        {"name": "Danger detection", "baseline": dangerous_detection("baseline"), "changeguard": dangerous_detection("changeguard"), "unit": "%"},
        {"name": "Safe change accuracy", "baseline": safe_accuracy("baseline"), "changeguard": safe_accuracy("changeguard"), "unit": "%"},
    ]


def _result_payload(rows: list[dict], benchmark_type: str, token_usage: dict | None = None) -> dict:
    metrics = _metrics(rows)
    overall = next(x for x in metrics if x["name"] == "Decision accuracy")
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_type": benchmark_type,
        "cases": len(rows),
        "challenging_cases": sum(bool(r.get("challenge")) for r in rows),
        "overall_score": overall["changeguard"],
        "baseline_score": overall["baseline"],
        "improvement": overall["changeguard"] - overall["baseline"],
        "metrics": metrics,
        "results": rows,
        "token_usage": token_usage or {},
    }
    config_store.save_benchmark(result["created_at"], result)
    return result


def run_smoke_benchmark() -> dict:
    """Zero-cost deterministic smoke benchmark for development/CI."""
    rows = []
    for case in load_cases():
        findings = analyze_file(case["path"], case["patch"])
        decision, _, _ = summarize(findings)
        rows.append(
            {
                "case": case["id"],
                "truth": case["truth"],
                "baseline": _simple_baseline(case["path"], case["patch"]),
                "changeguard": decision.value,
                "challenge": bool(case.get("challenge")),
            }
        )
    return _result_payload(rows, "development-smoke")


async def _agentic_final(case: dict) -> tuple[str, int, int, int]:
    findings = list(analyze_file(case["path"], case["patch"]))
    llm = await analyze_with_llm(case["title"], [{"filename": case["path"], "patch": case["patch"]}])
    supported = 0
    rejected = 0
    total_tokens = ((llm or {}).get("_usage") or {}).get("tokens") or 0

    if llm:
        for risk in llm.get("risks", []):
            quote = risk.get("evidence_quote", "")
            path = risk.get("file", "")
            severity_text = str(risk.get("severity", "medium")).lower()
            try:
                severity = Severity(severity_text)
            except Exception:
                severity = Severity.MEDIUM

            if path == case["path"] and quote and quote in case["patch"]:
                findings.append(
                    Finding(
                        "llm-verified",
                        severity,
                        risk.get("title", "Agent risk"),
                        risk.get("detail", ""),
                        path,
                        [quote],
                        risk.get("recommendation", "Review before merge."),
                    )
                )
                supported += 1
            else:
                rejected += 1

    decision, _, _ = summarize(findings)
    return decision.value, supported, rejected, total_tokens


async def run_agentic_benchmark() -> dict:
    """Official same-model benchmark: single-prompt baseline vs final verified workflow."""
    if not config_store.get_all().get("llm_api_key"):
        raise RuntimeError("Configure an LLM provider before running the agentic benchmark")

    rows = []
    baseline_tokens = 0
    final_tokens = 0
    supported_claims = 0
    rejected_claims = 0

    for case in load_cases():
        baseline = await review_case(case["title"], case["path"], case["patch"])
        baseline_tokens += baseline.get("tokens") or 0

        final_decision, supported, rejected, tokens = await _agentic_final(case)
        final_tokens += tokens
        supported_claims += supported
        rejected_claims += rejected

        rows.append(
            {
                "case": case["id"],
                "truth": case["truth"],
                "baseline": baseline["decision"],
                "changeguard": final_decision,
                "challenge": bool(case.get("challenge")),
                "baseline_reason": baseline.get("reason", ""),
                "verified_ai_claims": supported,
                "rejected_ai_claims": rejected,
            }
        )

    payload = _result_payload(
        rows,
        "single-prompt-vs-agentic",
        {"baseline": baseline_tokens, "changeguard": final_tokens},
    )
    payload["verification"] = {
        "supported_ai_claims": supported_claims,
        "rejected_ai_claims": rejected_claims,
    }
    # Save the enriched payload as the latest result as well.
    config_store.save_benchmark(payload["created_at"], payload)
    return payload
