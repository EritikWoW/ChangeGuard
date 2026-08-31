import asyncio
from datetime import datetime, timezone
from time import perf_counter
from app.models.schemas import AnalysisResponse, Claim, Evidence, FileChange, Severity, TrajectoryStep, RunDetails
from app.services.github_service import GitHubService, parse_pr_url
from app.services.rule_engine import analyze_file, summarize_agentic, SEVERITY_WEIGHT
from app.services.store import store
from app.services.llm_service import analyze_with_llm
from app.services.config_store import config_store
from app.services.rule_engine import Finding


def _risk_categories(findings) -> dict[str, int]:
    scores = {"Reliability": 0, "Availability": 0, "Performance": 0, "Security": 0, "Cost": 0}
    for finding in findings:
        weight = {Severity.LOW: 20, Severity.MEDIUM: 45, Severity.HIGH: 75, Severity.CRITICAL: 95}[finding.severity]
        rid = finding.rule_id
        if rid.startswith(("docker-secret", "k8s-root", "k8s-privileged", "tf-public", "gha-")):
            scores["Security"] = max(scores["Security"], weight)
        if rid.startswith(("k8s-memory", "k8s-resources")):
            scores["Reliability"] = max(scores["Reliability"], weight)
            scores["Performance"] = max(scores["Performance"], min(100, weight + 5))
        if rid.startswith(("k8s-readiness", "k8s-memory", "k8s-resources")):
            scores["Availability"] = max(scores["Availability"], weight)
    return scores


async def analyze_github_pr(url: str) -> AnalysisResponse:
    started = perf_counter()
    ref = parse_pr_url(url)
    gh = GitHubService()
    try:
        pr_task = asyncio.create_task(gh.get_pull_request(ref))
        files_task = asyncio.create_task(gh.get_pull_files(ref))
        pr, raw_files = await asyncio.gather(pr_task, files_task)
    finally:
        await gh.close()

    deterministic_findings: list[Finding] = []
    file_models: list[FileChange] = []
    for raw in raw_files:
        findings = analyze_file(raw["filename"], raw.get("patch"))
        deterministic_findings.extend(findings)
        risk = max((f.severity for f in findings), key=lambda s: SEVERITY_WEIGHT[s], default=Severity.LOW)
        file_models.append(FileChange(
            path=raw["filename"], risk=risk, change_type=raw.get("status", "modified"),
            additions=raw.get("additions", 0), deletions=raw.get("deletions", 0), patch=raw.get("patch")
        ))

    llm_result = None
    llm_error = None
    try:
        llm_result = await analyze_with_llm(pr.get("title", ""), raw_files)
    except Exception as exc:
        llm_error = str(exc)

    # Exact quote matching establishes provenance. The final gate separately
    # decides whether that evidence is strong enough to change PASS/WARN/BLOCK.
    llm_verified: list[tuple[Finding, str]] = []
    llm_rejected = []
    if llm_result:
        by_path = {r.get("filename"): (r.get("patch") or "") for r in raw_files}
        for risk in llm_result.get("risks", []):
            path = risk.get("file", "")
            quote = risk.get("evidence_quote", "")
            sev_text = str(risk.get("severity", "medium")).lower()
            try: sev = Severity(sev_text)
            except Exception: sev = Severity.MEDIUM
            if quote and quote in by_path.get(path, ""):
                finding = Finding("llm-verified", sev, risk.get("title", "Agent risk"), risk.get("detail", ""), path, [quote], risk.get("recommendation", "Review before merge."))
                llm_verified.append((finding, quote))
            else:
                llm_rejected.append(risk)

    llm_findings = [finding for finding, _ in llm_verified]
    all_findings = deterministic_findings + llm_findings
    decision, severity, confidence = summarize_agentic(deterministic_findings, llm_findings)

    evidence: list[Evidence] = []
    claims: list[Claim] = []
    for i, finding in enumerate(all_findings, 1):
        ev_id = f"EV-{i:03d}"
        evidence.append(Evidence(
            id=ev_id, title=finding.title, source="GitHub diff", detail=finding.detail,
            location=finding.file, verified=True,
        ))
        if finding.rule_id == "llm-verified":
            reason = "Exact diff quote verified; decision impact is limited unless deterministic evidence corroborates it or severity requires human review."
        else:
            reason = f"Matched deterministic rule {finding.rule_id}"
        claims.append(Claim(
            id=f"CL-{i:03d}", text=finding.detail, status="supported", evidence_ids=[ev_id], reason=reason,
        ))

    for risk in llm_rejected:
        claims.append(Claim(id=f"CL-R{len(claims)+1:03d}", text=risk.get("detail") or risk.get("title") or "Unsupported LLM claim", status="rejected", evidence_ids=[], reason="Verifier could not match the claimed evidence quote to the referenced file patch."))

    if deterministic_findings:
        top = max(deterministic_findings + llm_findings, key=lambda f: SEVERITY_WEIGHT[f.severity])
        predicted_failure = top.title
        failure_detail = top.detail
        recommendation = top.recommendation
    elif decision.value == "warn" and llm_findings:
        top = max(llm_findings, key=lambda f: SEVERITY_WEIGHT[f.severity])
        predicted_failure = top.title
        failure_detail = top.detail
        recommendation = top.recommendation
    else:
        predicted_failure = "No blocking infrastructure failure predicted"
        failure_detail = "No deterministic safety rule matched strongly enough to change the merge gate. LLM-only low/medium hypotheses remain advisory even when their diff quote is verified."
        recommendation = "Proceed with normal review; inspect advisory agent findings if present."

    elapsed = perf_counter() - started
    analysis_id = f"gh-{ref.owner}-{ref.repo}-pr-{ref.number}-{int(datetime.now(timezone.utc).timestamp())}"
    analysis = AnalysisResponse(
        id=analysis_id,
        repo=f"{ref.owner}/{ref.repo}",
        pull_request=ref.number,
        title=pr.get("title", f"PR #{ref.number}"),
        branch_from=pr.get("head", {}).get("ref", "unknown"),
        branch_to=pr.get("base", {}).get("ref", "unknown"),
        decision=decision,
        severity=severity,
        confidence=confidence,
        predicted_failure=predicted_failure,
        failure_detail=failure_detail,
        recommendation=recommendation,
        analysis_time_seconds=round(elapsed, 3),
        model=(config_store.get_all().get("llm_model") if llm_result is not None else "deterministic-v0.5.0"),
        files=file_models,
        evidence=evidence,
        claims=claims,
        trajectory=[
            TrajectoryStep(order=1, agent="GitHub Collector", summary=f"Loaded PR metadata and {len(raw_files)} changed files.", status="done", tool_calls=["github.get_pull_request", "github.get_pull_files"]),
            TrajectoryStep(order=2, agent="Change Parser", summary="Normalized changed IaC/configuration files and patches.", status="done", tool_calls=["parse.patch"]),
            TrajectoryStep(order=3, agent="Risk Rules", summary=f"Evaluated deterministic safety rules and found {len(deterministic_findings)} candidate(s).", status="done", tool_calls=["rule_engine.analyze_file"]),
            TrajectoryStep(order=4, agent="Risk Agent", summary=(f"LLM produced {len(llm_result.get('risks', []))} risk candidate(s)." if llm_result is not None else (f"LLM unavailable: {llm_error}" if llm_error else "LLM not configured; deterministic mode.")), status=("done" if llm_result is not None else "skipped"), tool_calls=(["llm.chat.completions"] if llm_result is not None else [])),
            TrajectoryStep(order=5, agent="Verifier", summary=f"Verified provenance for {len(llm_verified)} LLM claim(s); rejected {len(llm_rejected)} unmatched claim(s). LLM-only low/medium findings remain advisory.", status="done", tool_calls=["evidence.verify_exact_quote", "decision.require_corroboration"]),
            TrajectoryStep(order=6, agent="Decision", summary=f"Final decision: {decision.value.upper()}.", status="done"),
        ],
        risk_categories=_risk_categories(all_findings),
        blast_radius=[],
        run_details=RunDetails(
            run_id=analysis_id, model=(config_store.get_all().get("llm_model") if llm_result is not None else "deterministic-v0.5.0"), tokens=((llm_result or {}).get("_usage", {}).get("tokens") if llm_result else None), estimated_cost_usd=None, retries=0
        ),
        created_at=datetime.now(timezone.utc),
        source_url=url,
    )
    store.save(analysis)
    return analysis
