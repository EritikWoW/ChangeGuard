(() => {
  const $ = (s, r=document) => r.querySelector(s);
  const esc = (s='') => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const notify = (m) => { if (typeof toast === 'function') toast(m); };

  const footerVersion = $('.sidebar-footer .muted');
  if (footerVersion) footerVersion.textContent = 'v0.6.0';

  const benchmarkBtn = $('#runBenchmarkBtn');
  if (benchmarkBtn && !$('#runAgenticBenchmarkBtn')) {
    const actions = document.createElement('div');
    actions.className = 'hero-actions';
    benchmarkBtn.parentNode.replaceChild(actions, benchmarkBtn);
    benchmarkBtn.textContent = 'Run Smoke Benchmark';
    actions.appendChild(benchmarkBtn);

    const agentic = document.createElement('button');
    agentic.className = 'primary';
    agentic.id = 'runAgenticBenchmarkBtn';
    agentic.textContent = 'Run Agentic Benchmark';
    actions.appendChild(agentic);

    const exp = document.createElement('a');
    exp.className = 'secondary button-link';
    exp.href = '/api/hackathon/benchmarks/latest.md';
    exp.textContent = 'Export Report';
    actions.appendChild(exp);
  }

  const originalRenderBenchmark = window.renderBenchmark;
  window.renderBenchmark = function(b) {
    originalRenderBenchmark?.(b);
    if (!b || b.status === 'not_run') return;
    const root = $('#benchmarkContent');
    if (!root) return;
    const isAgentic = b.benchmark_type === 'single-prompt-vs-agentic';
    const ver = b.verification || {};
    const tok = b.token_usage || {};

    const meta = document.createElement('section');
    meta.className = 'card';
    meta.style.marginTop = '14px';
    meta.innerHTML = `
      <div class="card-head"><div><h3>${isAgentic ? 'Official Same-Model Agentic Evaluation' : 'Development Smoke Evaluation'}</h3><small>${esc(b.created_at || '')}</small></div><span class="pill ${isAgentic?'success':'info'}">${isAgentic?'SUBMISSION METRIC':'SMOKE'}</span></div>
      <div class="stats-grid" style="margin-top:14px">
        <div class="stat-card"><span>Challenging cases</span><b>${b.challenging_cases ?? 0}</b><small>of ${b.cases}</small></div>
        <div class="stat-card"><span>Supported AI claims</span><b>${ver.supported_ai_claims ?? 'N/A'}</b><small>verified against exact diff evidence</small></div>
        <div class="stat-card"><span>Rejected AI claims</span><b>${ver.rejected_ai_claims ?? 'N/A'}</b><small>excluded from final decision</small></div>
        <div class="stat-card"><span>Token usage</span><b>${tok.changeguard ?? 'N/A'}</b><small>baseline: ${tok.baseline ?? 'N/A'}</small></div>
      </div>`;
    root.appendChild(meta);

    if (Array.isArray(b.results)) {
      const cases = document.createElement('section');
      cases.className = 'card';
      cases.style.marginTop = '14px';
      cases.innerHTML = `<div class="card-head"><h3>Case-by-case Results</h3><span class="pill info">GROUND TRUTH</span></div>
        <div class="benchmark-table"><div class="tr head"><span>Case</span><span>Truth</span><span>Baseline</span><span>ChangeGuard</span></div>${b.results.map(r=>`<div class="tr"><span><b>${esc(r.case)}</b>${r.challenge?'<small style="display:block;color:var(--amber)">challenging</small>':''}</span><span>${esc(r.truth)}</span><span style="color:${r.baseline===r.truth?'var(--green)':'var(--red)'}">${esc(r.baseline)}</span><span style="color:${r.changeguard===r.truth?'var(--green)':'var(--red)'}">${esc(r.changeguard)}</span></div>`).join('')}</div>`;
      root.appendChild(cases);
    }
  };

  const agenticBtn = $('#runAgenticBenchmarkBtn');
  if (agenticBtn) agenticBtn.onclick = async () => {
    agenticBtn.disabled = true;
    agenticBtn.textContent = 'Running 15 cases...';
    try {
      const b = await api('/api/benchmarks/run-agentic', {method:'POST'});
      window.renderBenchmark(b);
      notify(`Agentic benchmark complete: ${b.baseline_score}% → ${b.overall_score}%`);
    } catch (e) {
      notify(e.message);
    } finally {
      agenticBtn.disabled = false;
      agenticBtn.textContent = 'Run Agentic Benchmark';
    }
  };

  const createReview = $('#createReviewBtn');
  if (createReview) createReview.onclick = async () => {
    const id = typeof currentAnalysisId !== 'undefined' ? currentAnalysisId : null;
    if (!id) return;
    if (!confirm('Post the current evidence-backed ChangeGuard report as a comment on this GitHub PR?')) return;
    createReview.disabled = true;
    createReview.textContent = 'Posting...';
    try {
      const result = await api(`/api/hackathon/github-review/${encodeURIComponent(id)}`, {method:'POST'});
      notify('GitHub review comment created');
      if (result.url) window.open(result.url, '_blank', 'noopener');
    } catch (e) {
      notify(e.message);
    } finally {
      createReview.disabled = false;
      createReview.textContent = 'Create GitHub Review';
    }
  };

  const trajHead = $('.trajectory-card .card-head');
  if (trajHead && !$('#exportTrajectoryBtn')) {
    const btn = document.createElement('button');
    btn.className = 'text-btn';
    btn.id = 'exportTrajectoryBtn';
    btn.textContent = 'Export trajectory';
    trajHead.appendChild(btn);
    btn.onclick = () => {
      const id = typeof currentAnalysisId !== 'undefined' ? currentAnalysisId : 'unknown';
      window.open(`/api/hackathon/analyses/${encodeURIComponent(id)}/trajectory.json`, '_blank');
    };
  }

  document.addEventListener('click', (e) => {
    const row = e.target.closest('.traj-row');
    if (!row || !$('#trajectory')?.contains(row)) return;
    const title = row.querySelector('b')?.textContent || 'Trajectory step';
    const summary = row.querySelector('small')?.textContent || '';
    if (typeof openDrawer === 'function') openDrawer({
      title,
      sub:'Representative agent trajectory',
      html:`<div class="detail-block"><b>Summary</b><small>${esc(summary)}</small></div><div class="detail-block"><b>Auditability</b><small>Export the complete trajectory JSON to inspect tool calls, claims, evidence links, status and run metadata.</small></div>`
    });
  });

  const benchmarkTitle = $('#benchmarksView .page-title p');
  if (benchmarkTitle) benchmarkTitle.textContent = 'Same-model baseline vs evidence-verified agentic workflow on 15 labeled cases.';
})();
