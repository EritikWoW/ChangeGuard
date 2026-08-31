from datetime import datetime, timezone, timedelta
from collections import defaultdict
from app.services.store import store
from app.services.rule_engine import analyze_file, summarize
from app.services.config_store import config_store

BENCHMARK_CASES = [
    ("k8s-memory", "deployment.yaml", '@@\n-      memory: "512Mi"\n+      memory: "256Mi"', 'block'),
    ("k8s-privileged", "pod.yaml", '@@\n+    privileged: true', 'block'),
    ("k8s-root", "deployment.yml", '@@\n+      runAsUser: 0', 'block'),
    ("k8s-readiness", "deployment.yaml", '@@\n-    readinessProbe:\n-      httpGet:\n-        path: /health', 'block'),
    ("tf-public", "network.tf", '@@\n+ cidr_blocks = ["0.0.0.0/0"]\n+ ingress = true', 'block'),
    ("docker-secret", "Dockerfile", '@@\n+ ENV API_KEY=supersecret', 'block'),
    ("docker-root", "Dockerfile", '@@\n+ RUN apt-get update && apt-get install -y curl', 'warn'),
    ("safe-replicas", "deployment.yaml", '@@\n- replicas: 2\n+ replicas: 3', 'pass'),
    ("safe-label", "deployment.yaml", '@@\n+    app.kubernetes.io/version: v2', 'pass'),
    ("safe-doc", "README.md", '@@\n+ Deployment notes', 'pass'),
]

def _baseline(path, patch):
    low=(patch or '').lower()
    if 'privileged: true' in low or '0.0.0.0/0' in low or 'api_key=' in low or 'password=' in low:
        return 'block'
    return 'pass'

def run_benchmark():
    rows=[]; baseline_ok=0; cg_ok=0; dangerous=0; dangerous_cg=0; safe=0; safe_cg=0
    for name,path,patch,truth in BENCHMARK_CASES:
        b=_baseline(path,patch)
        findings=analyze_file(path,patch)
        d,_,_=summarize(findings); c=d.value
        baseline_ok += b==truth; cg_ok += c==truth
        is_danger=truth in {'block','warn'}
        if is_danger:
            dangerous+=1; dangerous_cg += c in {'block','warn'}
        else:
            safe+=1; safe_cg += c=='pass'
        rows.append({'case':name,'truth':truth,'baseline':b,'changeguard':c,'passed':c==truth})
    n=len(rows)
    baseline_score=round(100*baseline_ok/n)
    cg_score=round(100*cg_ok/n)
    result={
      'created_at':datetime.now(timezone.utc).isoformat(), 'cases':n,
      'overall_score':cg_score,'baseline_score':baseline_score,'improvement':cg_score-baseline_score,
      'metrics':[
        {'name':'Decision accuracy','baseline':baseline_score,'changeguard':cg_score,'unit':'%'},
        {'name':'Danger detection','baseline':round(100*sum(_baseline(p,pa) in {'block','warn'} for _,p,pa,t in BENCHMARK_CASES if t in {'block','warn'})/dangerous),'changeguard':round(100*dangerous_cg/dangerous),'unit':'%'},
        {'name':'Safe change accuracy','baseline':round(100*sum(_baseline(p,pa)=='pass' for _,p,pa,t in BENCHMARK_CASES if t=='pass')/safe),'changeguard':round(100*safe_cg/safe),'unit':'%'},
      ], 'results':rows
    }
    config_store.save_benchmark(result['created_at'],result); return result

def dashboard_data():
    items=store.list_full(500)
    now=datetime.now(timezone.utc); week=now-timedelta(days=7)
    week_items=[x for x in items if x.created_at>=week]
    counts={'block':0,'warn':0,'pass':0}
    for x in week_items: counts[x.decision.value]+=1
    claims=[c for a in items for c in a.claims]
    supported=sum(c.status=='supported' for c in claims)
    precision=round(100*supported/len(claims)) if claims else None
    trend=[]
    for i in range(6,-1,-1):
        day=(now-timedelta(days=i)).date(); trend.append({'day':day.strftime('%a'),'count':sum(a.created_at.date()==day for a in items)})
    return {'analyses_this_week':len(week_items),'blocked_changes':counts['block'],'safe_changes':counts['pass'],'warnings':counts['warn'],'evidence_precision':precision,'recent':[x.model_dump(mode='json') for x in items[:5]],'trend':trend}

def report_items():
    return [{'id':a.id,'repo':a.repo,'pull_request':a.pull_request,'title':a.title,'decision':a.decision.value,'confidence':a.confidence,'created_at':a.created_at.isoformat(),'summary':a.predicted_failure,'recommendation':a.recommendation} for a in store.list_full(100)]

def report_markdown(a):
    ev='\n'.join(f"- **{e.id}** {e.title}: {e.detail} ({e.location or e.source})" for e in a.evidence) or '- No blocking evidence.'
    return f"""# ChangeGuard Report\n\n## {a.repo} PR #{a.pull_request}: {a.title}\n\n**Decision:** {a.decision.value.upper()}  \n**Severity:** {a.severity.value.upper()}  \n**Confidence:** {a.confidence:.0%}  \n**Created:** {a.created_at.isoformat()}\n\n## Predicted failure\n{a.predicted_failure}\n\n{a.failure_detail}\n\n## Evidence\n{ev}\n\n## Recommendation\n{a.recommendation}\n\n## Reproduction\nRun ID: `{a.run_details.run_id if a.run_details else a.id}`\n"""
