from app.services.rule_engine import Finding, analyze_file, summarize, summarize_agentic
from app.models.schemas import Decision, Severity


def test_detects_k8s_memory_reduction():
    patch = '''@@ -1,3 +1,3 @@\n resources:\n   limits:\n-    memory: "512Mi"\n+    memory: "256Mi"'''
    findings = analyze_file('k8s/api/deployment.yaml', patch)
    assert any(f.rule_id == 'k8s-memory-reduction' for f in findings)
    decision, _, _ = summarize(findings)
    assert decision == Decision.BLOCK


def test_detects_readiness_probe_removal_case_insensitively():
    patch = '''@@\n-      readinessProbe:\n-        httpGet:\n-          path: /health\n-          port: 8080'''
    findings = analyze_file('k8s/api/deployment.yaml', patch)
    assert any(f.rule_id == 'k8s-readiness-removed' for f in findings)
    decision, _, _ = summarize(findings)
    assert decision == Decision.BLOCK


def test_safe_readme_passes():
    findings = analyze_file('README.md', '@@ -1 +1 @@\n-old\n+new')
    decision, _, _ = summarize(findings)
    assert decision == Decision.PASS


def test_llm_only_medium_finding_is_advisory():
    llm_finding = Finding(
        'llm-verified',
        Severity.MEDIUM,
        'Small timeout increase',
        'A small timeout increase might delay failures.',
        'nginx.conf',
        ['proxy_read_timeout 35s;'],
    )
    decision, severity, _ = summarize_agentic([], [llm_finding])
    assert decision == Decision.PASS
    assert severity == Severity.LOW


def test_llm_only_high_finding_requires_human_review_not_block():
    llm_finding = Finding(
        'llm-verified',
        Severity.HIGH,
        'Novel high-risk change',
        'The agent found a high-risk pattern without deterministic corroboration.',
        'custom.conf',
        ['dangerous_setting=true'],
    )
    decision, severity, _ = summarize_agentic([], [llm_finding])
    assert decision == Decision.WARN
    assert severity == Severity.HIGH
