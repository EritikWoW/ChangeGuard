from dataclasses import dataclass, field
from pathlib import PurePosixPath
from app.models.schemas import Decision, Severity


@dataclass
class Finding:
    rule_id: str
    severity: Severity
    title: str
    detail: str
    file: str
    evidence: list[str] = field(default_factory=list)
    recommendation: str = "Review this infrastructure change before merge."


SEVERITY_WEIGHT = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def _added_lines(patch: str | None) -> list[str]:
    if not patch:
        return []
    return [line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")]


def _removed_lines(patch: str | None) -> list[str]:
    if not patch:
        return []
    return [line[1:] for line in patch.splitlines() if line.startswith("-") and not line.startswith("---")]


def analyze_file(path: str, patch: str | None) -> list[Finding]:
    name = PurePosixPath(path).name.lower()
    full = "\n".join(_added_lines(patch))
    removed = "\n".join(_removed_lines(patch))
    low = full.lower()
    removed_low = removed.lower()
    findings: list[Finding] = []

    if name in {"dockerfile", "containerfile"}:
        if "user root" in low or ("user " not in low and any(x in low for x in ["apt-get", "apk add", "yum install"])):
            findings.append(Finding(
                "docker-root", Severity.MEDIUM, "Container may run as root",
                "The Dockerfile change does not establish a non-root runtime user or explicitly selects root.", path,
                ["Dockerfile runtime user"], "Use a dedicated non-root USER for the final image stage."
            ))
        if any(token in low for token in ["password=", "api_key=", "apikey=", "secret=", "token="]):
            findings.append(Finding(
                "docker-secret", Severity.CRITICAL, "Possible secret embedded in image",
                "A newly added Dockerfile line appears to contain secret-like material.", path,
                ["Added Dockerfile line contains a secret-like assignment"], "Remove the value and use a runtime secret store."
            ))

    if path.endswith((".yaml", ".yml")):
        if "privileged: true" in low:
            findings.append(Finding(
                "k8s-privileged", Severity.CRITICAL, "Privileged container enabled",
                "The change enables privileged container execution.", path,
                ["privileged: true"], "Avoid privileged mode or require an explicit security exception."
            ))
        if "runasuser: 0" in low or "runasnonroot: false" in low:
            findings.append(Finding(
                "k8s-root", Severity.HIGH, "Workload may run as root",
                "The security context permits UID 0/root execution.", path,
                ["Kubernetes securityContext changed"], "Require runAsNonRoot and a non-zero UID."
            ))
        if "resources:" in removed_low and "resources:" not in low:
            findings.append(Finding(
                "k8s-resources-removed", Severity.HIGH, "Resource controls removed",
                "The patch appears to remove Kubernetes resource configuration.", path,
                ["resources section removed"], "Keep explicit requests and limits or document why they are safe to remove."
            ))
        # Detect suspicious memory limit reductions using common units.
        import re
        before = re.findall(r"memory:\s*[\"']?(\d+)(Mi|Gi)", removed, re.I)
        after = re.findall(r"memory:\s*[\"']?(\d+)(Mi|Gi)", full, re.I)
        if before and after:
            def mib(v): return int(v[0]) * (1024 if v[1].lower() == "gi" else 1)
            old, new = mib(before[-1]), mib(after[-1])
            if new < old:
                ratio = new / old if old else 1
                sev = Severity.HIGH if ratio <= .5 else Severity.MEDIUM
                findings.append(Finding(
                    "k8s-memory-reduction", sev, "Container memory limit reduced",
                    f"Memory limit decreases from {old}Mi to {new}Mi ({(1-ratio)*100:.0f}% reduction). This can increase OOMKill risk if runtime usage is unchanged.", path,
                    [f"memory limit {old}Mi -> {new}Mi"], "Validate against production p95/max memory before merging."
                ))
        if "readinessprobe:" in removed_low and "readinessprobe:" not in low:
            findings.append(Finding(
                "k8s-readiness-removed", Severity.HIGH, "Readiness probe removed",
                "The patch appears to remove the workload readiness probe.", path,
                ["readinessProbe removed"], "Restore readiness checks or document an equivalent health gate."
            ))

    if path.endswith((".tf", ".tfvars")):
        if "0.0.0.0/0" in full and any(x in low for x in ["cidr", "ingress", "source_ranges", "security_group"]):
            findings.append(Finding(
                "tf-public-ingress", Severity.CRITICAL, "Public network exposure introduced",
                "The Terraform diff adds a 0.0.0.0/0 network source in an access-related context.", path,
                ["0.0.0.0/0 added"], "Restrict ingress to the smallest required CIDR range."
            ))
        if "public_access" in low and "true" in low:
            findings.append(Finding(
                "tf-public-access", Severity.HIGH, "Public access enabled",
                "The Terraform change appears to enable a public-access setting.", path,
                ["public_access=true added"], "Keep the resource private unless public exposure is explicitly required."
            ))

    if ".github/workflows/" in path and path.endswith((".yml", ".yaml")):
        if "pull_request_target:" in low and "checkout" in low:
            findings.append(Finding(
                "gha-pr-target", Severity.HIGH, "Sensitive pull_request_target workflow",
                "pull_request_target can expose repository secrets to unsafe workflow logic when combined with untrusted checkout patterns.", path,
                ["pull_request_target added"], "Use pull_request where possible and avoid executing untrusted PR code with privileged tokens."
            ))

    return findings


def summarize(findings: list[Finding]) -> tuple[Decision, Severity, float]:
    if not findings:
        return Decision.PASS, Severity.LOW, 0.88
    highest = max((f.severity for f in findings), key=lambda s: SEVERITY_WEIGHT[s])
    if highest in {Severity.CRITICAL, Severity.HIGH}:
        return Decision.BLOCK, highest, min(0.98, 0.83 + 0.03 * len(findings))
    return Decision.WARN, highest, min(0.94, 0.72 + 0.04 * len(findings))


def summarize_agentic(
    deterministic_findings: list[Finding],
    verified_llm_findings: list[Finding],
) -> tuple[Decision, Severity, float]:
    """Gate policy for the agentic reviewer.

    Deterministic evidence is allowed to make blocking decisions. An exact LLM
    evidence quote proves provenance, but by itself it does not prove that a
    benign change is hazardous. Therefore low/medium LLM-only findings remain
    advisory, while high/critical LLM-only findings escalate to WARN for human
    review rather than autonomously blocking a change.
    """
    if deterministic_findings:
        return summarize(deterministic_findings + verified_llm_findings)
    if not verified_llm_findings:
        return Decision.PASS, Severity.LOW, 0.88

    highest = max((f.severity for f in verified_llm_findings), key=lambda s: SEVERITY_WEIGHT[s])
    if highest in {Severity.CRITICAL, Severity.HIGH}:
        return Decision.WARN, highest, min(0.86, 0.68 + 0.03 * len(verified_llm_findings))

    # Exact evidence location is retained in the report, but an uncorroborated
    # low/medium hypothesis does not change the merge gate.
    return Decision.PASS, Severity.LOW, 0.78
