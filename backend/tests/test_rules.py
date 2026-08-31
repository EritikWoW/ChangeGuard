from app.services.rule_engine import analyze_file, summarize
from app.models.schemas import Decision


def test_detects_k8s_memory_reduction():
    patch = '''@@ -1,3 +1,3 @@\n resources:\n   limits:\n-    memory: "512Mi"\n+    memory: "256Mi"'''
    findings = analyze_file('k8s/api/deployment.yaml', patch)
    assert any(f.rule_id == 'k8s-memory-reduction' for f in findings)
    decision, _, _ = summarize(findings)
    assert decision == Decision.BLOCK


def test_safe_readme_passes():
    findings = analyze_file('README.md', '@@ -1 +1 @@\n-old\n+new')
    decision, _, _ = summarize(findings)
    assert decision == Decision.PASS
