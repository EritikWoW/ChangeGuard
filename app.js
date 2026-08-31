const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => [...r.querySelectorAll(s)];
const toast = (msg) => { const el=$('#toast'); el.textContent=msg; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2600); };
let currentAnalysisId = 'analysis-pr-184';

const views = {
  analysis:{el:'#analysisView', crumb:'Analysis / PR #184'},
  dashboard:{el:'#dashboardView', crumb:'Dashboard'},
  analyses:{el:'#analysesView', crumb:'Analyses'},
  benchmarks:{el:'#benchmarksView', crumb:'Benchmarks'},
  reports:{el:'#reportsView', crumb:'Reports'},
  settings:{el:'#settingsView', crumb:'Settings'}
};
function showView(name){
  $$('.view-section').forEach(v=>v.classList.add('hidden'));
  $(views[name].el).classList.remove('hidden');
  $$('.nav-item').forEach(x=>x.classList.toggle('active',x.dataset.view===name));
  const parts=views[name].crumb.split(' / ');
  $('#breadcrumbs').innerHTML=parts.length>1?`<span>${parts[0]}</span><b>/</b><strong>${parts[1]}</strong>`:`<strong>${parts[0]}</strong>`;
  window.scrollTo({top:0,behavior:'smooth'});
}
$$('.nav-item').forEach(btn=>btn.onclick=()=>btn.dataset.view==='analysis'?openNewAnalysis():showView(btn.dataset.view));
$$('[data-go]').forEach(btn=>btn.onclick=()=>btn.dataset.go==='analysis'?openNewAnalysis():showView(btn.dataset.go));
$$('[data-open-analysis]').forEach(btn=>btn.onclick=()=>showView('analysis'));

function openNewAnalysis(){ $('#newAnalysisModal').classList.add('open'); }
$$('.modal-close').forEach(b=>b.onclick=()=>$('#newAnalysisModal').classList.remove('open'));

function escapeHtml(s=''){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function pillClass(sev){return sev==='critical'||sev==='high'?'danger':sev==='medium'?'warn':'success';}
function decisionSymbol(d){return d==='block'?'⊖':d==='warn'?'△':'✓';}
function decisionText(d){return d==='block'?'BLOCK':d==='warn'?'WARN':'PASS';}

function renderPatch(patch){
  if(!patch) return '<div><span class="ln">—</span><code>Patch unavailable from GitHub API for this file.</code></div>';
  return patch.split('\n').slice(0,120).map((line,i)=>{
    let cls=''; if(line.startsWith('+')&&!line.startsWith('+++')) cls='added'; else if(line.startsWith('-')&&!line.startsWith('---')) cls='removed';
    return `<div class="${cls}"><span class="ln">${i+1}</span><code>${escapeHtml(line)}</code></div>`;
  }).join('');
}

function renderVerification(a){
  const claims=a.claims||[];
  const counts={supported:0,rejected:0,insufficient:0};
  claims.forEach(c=>counts[c.status]=(counts[c.status]||0)+1);
  const total=claims.length;
  const pct=(n)=>total?Math.round(n*100/total):0;
  const rejected=claims.filter(c=>c.status==='rejected');
  $('#verificationContent').innerHTML=`
    <div class="verify-grid">
      <div class="donut verify" style="${total?`background:conic-gradient(var(--green) 0 ${pct(counts.supported)}%,var(--red) ${pct(counts.supported)}% ${pct(counts.supported+counts.rejected)}%,#748296 ${pct(counts.supported+counts.rejected)}% 100%)`:'background:#26364b'}"><div><b>${total}</b><small>Total Claims</small></div></div>
      <div class="legend">
        <span><i class="dot green"></i>Supported <b>${counts.supported} (${pct(counts.supported)}%)</b></span>
        <span><i class="dot red"></i>Rejected <b>${counts.rejected} (${pct(counts.rejected)}%)</b></span>
        <span><i class="dot gray"></i>Insufficient <b>${counts.insufficient} (${pct(counts.insufficient)}%)</b></span>
      </div>
    </div>
    ${rejected.length?rejected.map(c=>`<div class="rejected"><span class="pill danger">REJECTED</span><b>${escapeHtml(c.text)}</b><small>${escapeHtml(c.reason||'Rejected by verifier.')}</small></div>`).join(''):'<div class="detail-block"><b>No rejected claims</b><small>'+ (total?'All current claims are supported by submitted evidence.':'No claims were generated because no deterministic safety finding matched this PR.') +'</small></div>'}`;
}

function renderFinalDecision(a){
  const box=$('#finalDecisionBox');
  box.className=`final-decision ${a.decision}`;
  const title=a.decision==='block'?'BLOCK MERGE':a.decision==='warn'?'REVIEW REQUIRED':'PASS — NO BLOCKING RISK';
  const desc=a.decision==='block'?'Verified evidence indicates a blocking infrastructure risk.':a.decision==='warn'?'Potential risk detected; human review is recommended.':'No configured blocking infrastructure risk was verified.';
  box.querySelector('strong').textContent=title;
  box.querySelector('span').textContent=desc;
  const pill=$('#finalConfidencePill');
  pill.className=`pill ${a.decision==='block'?'danger':a.decision==='warn'?'warn':'success'}`;
  pill.textContent=`${Math.round(a.confidence*100)}% CONFIDENCE`;
}

function renderRiskCategories(a){
  const values=a.risk_categories||{};
  const order=['Reliability','Availability','Performance','Security','Cost'];
  const root=$('.area-risk');
  root.innerHTML='<h3>Risk Categories</h3>'+order.map(name=>{const value=Number(values[name]||0); const tone=value>=70?'danger':value>=35?'warn':'success'; return `<div class="risk-metric"><div><span>${name}</span><b>${value}/100</b></div><div class="risk-track"><i class="${tone}" style="width:${Math.max(1,value)}%"></i></div></div>`}).join('');
}

function renderBlastRadius(a){
  const items=a.blast_radius||[];
  const badge=$('#blastBadge');
  if(!items.length){
    badge.className='pill info'; badge.textContent='NOT INFERRED';
    $('#blastSubtitle').textContent='Requires repository/dependency context';
    $('#blastGraph').innerHTML='<div class="detail-block"><b>No dependency path inferred</b><small>This deterministic run only evaluates changed files and diff evidence. No service dependency claim is made.</small></div>';
    return;
  }
  badge.className='pill danger'; badge.textContent=`${items.length} SERVICES`;
  $('#blastSubtitle').textContent='Dependency path inferred from repository context';
  $('#blastGraph').innerHTML=items.map((x,i)=>`${i?'<div class="edge">→</div>':''}<div class="node ${i===0?'danger-node':''}">${escapeHtml(x)}<small>${i===0?'changed':'affected'}</small></div>`).join('');
}

function renderRunDetails(a){
  const rd=a.run_details||{};
  const rows=[['Model',rd.model||a.model||'—'],['Run ID',rd.run_id||a.id||'—'],['Tokens',rd.tokens==null?'N/A':Number(rd.tokens).toLocaleString()],['Estimated cost',rd.estimated_cost_usd==null?'N/A':`$${Number(rd.estimated_cost_usd).toFixed(4)}`],['Retries',rd.retries??0]];
  $('#runDetailsList').innerHTML=rows.map(([k,v])=>`<div><dt>${k}</dt><dd>${escapeHtml(v)}</dd></div>`).join('');
}

function renderAnalysis(a){
  currentAnalysisId=a.id;
  views.analysis.crumb=`Analysis / PR #${a.pull_request}`;
  $('#breadcrumbs').innerHTML=`<span>Analysis</span><b>/</b><strong>PR #${a.pull_request}</strong>`;
  $('#analysisTitle').textContent=`PR #${a.pull_request}: ${a.title}`;
  $('#analysisMeta').innerHTML=`${escapeHtml(a.repo)}/${escapeHtml(a.branch_from)} <span>→</span> ${escapeHtml(a.branch_to)} · analyzed now`;
  $('#confidenceVal').textContent=Math.round(a.confidence*100)+'%';
  $('#filesChangedVal').textContent=a.files.length;
  $('#analysisTimeVal').textContent=a.analysis_time_seconds.toFixed(2)+'s';
  $('#predictedFailure').textContent=a.predicted_failure;
  $('#failureDetail').textContent=a.failure_detail;
  $('#whyRisky').textContent=a.failure_detail;
  $('#recommendationText').textContent=a.recommendation;
  renderVerification(a);
  renderFinalDecision(a);
  renderRiskCategories(a);
  renderBlastRadius(a);
  renderRunDetails(a);

  const verdict=$('#summaryVerdict');
  verdict.className=`verdict ${a.decision}`;
  verdict.querySelector('.verdict-title').textContent=`${decisionSymbol(a.decision)} ${decisionText(a.decision)}`;
  verdict.querySelector('small').textContent=a.decision==='block'?'Verified blocking risk detected':a.decision==='warn'?'Review recommended':'No blocking risk detected';
  const riskPill=verdict.closest('.summary-card').querySelector('.kv .pill');
  riskPill.className=`pill ${pillClass(a.severity)}`; riskPill.textContent=a.severity.toUpperCase();

  $('#filesHeading').textContent=`Files Changed (${a.files.length})`;
  $('#filesList').innerHTML=a.files.slice(0,8).map((f,idx)=>{
    const parts=f.path.split('/'); const name=parts.pop(); const dir=parts.join('/') || '/';
    return `<div class="file-row ${idx===0?'selected':''}" data-file-index="${idx}"><div><b>${escapeHtml(name)}</b><small>${escapeHtml(dir)}</small></div><span class="pill ${pillClass(f.risk)}">${f.risk.toUpperCase()}</span></div>`;
  }).join('');
  $$('#filesList .file-row').forEach(row=>row.onclick=()=>{const f=a.files[Number(row.dataset.fileIndex)]; if(!f)return; $$('#filesList .file-row').forEach(x=>x.classList.remove('selected')); row.classList.add('selected'); $('#diffCard .card-head small').textContent=f.path; $('#diffView').innerHTML=renderPatch(f.patch); $('#diffCard').scrollIntoView({behavior:'smooth',block:'center'});});

  $('#evidenceHeading').textContent=`Evidence (${a.evidence.length})`;
  $('#evidenceList').innerHTML=a.evidence.length ? a.evidence.map(ev=>`<button class="evidence-row" data-evidence-id="${escapeHtml(ev.id)}"><span class="check"><svg class="ui-icon sm"><use href="/assets/changeguard-svg-icons/sprite.svg#evidence"></use></svg></span><div><b><em>${escapeHtml(ev.id)}</em> ${escapeHtml(ev.title)}</b><small>${escapeHtml(ev.source)} · ${escapeHtml(ev.detail)}</small></div><span class="muted">${escapeHtml(ev.location||'')}</span></button>`).join('') : '<div class="detail-block"><b>No blocking evidence</b><small>No deterministic safety rule matched this pull request.</small></div>';
  $$('#evidenceList .evidence-row').forEach(btn=>btn.onclick=()=>{const ev=a.evidence.find(e=>e.id===btn.dataset.evidenceId); if(!ev)return; const idx=a.files.findIndex(f=>f.path===ev.location); if(idx>=0){const row=$(`#filesList .file-row[data-file-index="${idx}"]`); row?.click();}});

  const first=a.files.find(f=>f.patch)||a.files[0];
  if(first){
    $('#diffCard .card-head small').textContent=first.path;
    $('#diffView').innerHTML=renderPatch(first.patch);
  }

  const traj=$('#trajectory');
  traj.innerHTML=a.trajectory.map(t=>`<button class="traj-row"><span class="traj-num">${String(t.order).padStart(2,'0')}</span><div><b>${escapeHtml(t.agent)}</b><small>${escapeHtml(t.summary)}</small></div><span class="pill ${t.status.includes('reject')||t.status.includes('fail')?'danger':t.status.includes('retry')?'warn':'success'}">${escapeHtml(t.status)}</span></button>`).join('');
  $('.trajectory-card .card-head small').textContent=`Execution path · ${a.trajectory.length} stages · ${a.analysis_time_seconds.toFixed(2)}s`;
  showView('analysis');
}

$('#startAnalysisBtn').onclick=async()=>{
  const url=$('#prUrlInput').value.trim();
  if(!url){toast('Enter a GitHub PR URL');return;}
  const btn=$('#startAnalysisBtn');
  btn.disabled=true; btn.textContent='Analyzing GitHub PR...';
  try{
    const r=await fetch('/api/analyses/from-github',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pr_url:url,include_repository_context:true})});
    const payload=await r.json();
    if(!r.ok) throw new Error(payload.detail||`HTTP ${r.status}`);
    $('#newAnalysisModal').classList.remove('open');
    renderAnalysis(payload);
    toast(`Analysis complete: ${decisionText(payload.decision)}`);
  }catch(e){toast(e.message);}
  finally{btn.disabled=false;btn.textContent='Start Analysis';}
};

$('#compactToggle').onclick=()=>{document.body.classList.toggle('compact');toast(document.body.classList.contains('compact')?'Compact density enabled':'Comfortable density enabled');};
$('#shareBtn').onclick=()=>navigator.clipboard?.writeText(location.href).then(()=>toast('Share link copied')).catch(()=>toast('Share link ready'));
$('#githubBtn').onclick=()=>toast('Public PRs work now. Set CHANGEGUARD_GITHUB_TOKEN for private repos / higher limits.');
$('#createReviewBtn').onclick=()=>toast('GitHub write-back is the next backend milestone');
$('#runBenchmarkBtn').onclick=()=>toast('Benchmark runner will use fixed test cases');

const trajectory=$('#trajectory');
$('#trajectoryToggle').onclick=(e)=>{trajectory.classList.toggle('collapsed');e.currentTarget.textContent=trajectory.classList.contains('collapsed')?'Expand':'Collapse';};

function openDrawer(d){$('#drawerTitle').textContent=d.title;$('#drawerSubtitle').textContent=d.sub||'';$('#drawerBody').innerHTML=d.html||'';$('#drawer').classList.add('open');}
$('#drawerClose').onclick=()=>$('#drawer').classList.remove('open');
$('#drawer').onclick=(e)=>{if(e.target.id==='drawer')$('#drawer').classList.remove('open');};
$$('[data-action="report"]').forEach(b=>b.onclick=()=>showView('reports'));
$$('[data-action="evidence"]').forEach(b=>b.onclick=()=>$('.area-evidence').scrollIntoView({behavior:'smooth',block:'center'}));

const stepper=$('#stepper');
$('#rerunBtn').onclick=async(e)=>{
 const btn=e.currentTarget;btn.disabled=true;btn.innerHTML='<svg class="ui-icon"><use href="/assets/changeguard-svg-icons/sprite.svg#rerun"></use></svg> Running...';
 const steps=$$('.step',stepper);steps.forEach(s=>s.className='step');
 try{
   const request=fetch('/api/analyses/rerun',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({analysis_id:currentAnalysisId})});
   for(let i=0;i<steps.length;i++){steps[i].classList.add('active');await new Promise(r=>setTimeout(r,180));steps[i].classList.remove('active');steps[i].classList.add('done');}
   const response=await request; const payload=await response.json(); if(!response.ok)throw new Error(payload.detail||`HTTP ${response.status}`);
   renderAnalysis(payload.analysis); toast('Analysis rerun complete');
 }catch(err){toast('Backend: '+err.message);}finally{steps.at(-1).classList.add('active');btn.disabled=false;btn.innerHTML='<svg class="ui-icon"><use href="/assets/changeguard-svg-icons/sprite.svg#rerun"></use></svg> Re-run Analysis';}
};

(async()=>{try{const r=await fetch('/api/health');if(!r.ok)throw new Error();const data=await r.json();$('.online').innerHTML='<i></i> Backend connected';console.info('ChangeGuard backend',data);}catch(e){$('.online').innerHTML='<i style="background:#e4b044"></i> Backend unavailable';}})();

// ---- Live application pages (v0.5) ----
let analysesCache=[];
const relTime=(iso)=>{const d=new Date(iso),sec=Math.max(0,(Date.now()-d)/1000);if(sec<60)return 'now';if(sec<3600)return `${Math.floor(sec/60)}m ago`;if(sec<86400)return `${Math.floor(sec/3600)}h ago`;return `${Math.floor(sec/86400)}d ago`;};
async function api(url,opts={}){const r=await fetch(url,opts);let data;try{data=await r.json()}catch{data=await r.text()}if(!r.ok)throw new Error(data?.detail||`HTTP ${r.status}`);return data;}

async function loadDashboard(){
  const d=await api('/api/dashboard');
  const stat=(t,v,s)=>`<div class="stat-card"><span>${t}</span><b>${v}</b><small>${s}</small></div>`;
  $('#dashboardStats').innerHTML=stat('Analyses this week',d.analyses_this_week,'saved runs')+stat('Blocked changes',d.blocked_changes,'verified decisions')+stat('Safe changes',d.safe_changes,`${d.warnings} warning(s)`)+stat('Evidence precision',d.evidence_precision==null?'N/A':d.evidence_precision+'%','from stored claims');
  $('#dashboardRecent').innerHTML=d.recent.length?d.recent.map(a=>`<button data-id="${a.id}"><span class="status-dot ${a.decision==='block'?'danger-bg':a.decision==='warn'?'warn-bg':'success-bg'}"></span><div><b>PR #${a.pull_request} · ${escapeHtml(a.repo)}</b><small>${escapeHtml(a.title)}</small></div><span class="pill ${a.decision==='block'?'danger':a.decision==='warn'?'warn':'success'}">${a.decision.toUpperCase()}</span></button>`).join(''):'<div class="detail-block"><b>No analyses yet</b><small>Analyze a GitHub PR to populate the dashboard.</small></div>';
  $$('#dashboardRecent [data-id]').forEach(b=>b.onclick=()=>openStoredAnalysis(b.dataset.id));
  const max=Math.max(1,...d.trend.map(x=>x.count)); $('#dashboardTrend').innerHTML=d.trend.map(x=>`<i style="height:${Math.max(5,Math.round(x.count/max*100))}%" title="${x.count} analyses"></i>`).join(''); $('#dashboardTrendLabels').innerHTML=d.trend.map(x=>`<span>${x.day}</span>`).join('');
}

async function openStoredAnalysis(id){const a=await api('/api/analyses/'+encodeURIComponent(id));renderAnalysis(a);}
async function loadAnalyses(){analysesCache=await api('/api/analyses?limit=200');renderAnalysesTable();}
function renderAnalysesTable(){
  const q=($('#analysisSearch')?.value||'').toLowerCase();const f=$('#analysisFilters .filter.active')?.dataset.filter||'all';
  const rows=analysesCache.filter(a=>(f==='all'||a.decision===f)&&(`${a.repo} ${a.title} ${a.pull_request}`.toLowerCase().includes(q)));
  $('#analysisTable').innerHTML=`<div class="tr head"><span>Analysis</span><span>Repository</span><span>Decision</span><span>Confidence</span><span>Time</span></div>`+(rows.length?rows.map(a=>`<button class="tr" data-id="${a.id}"><span><b>PR #${a.pull_request}</b><small>${escapeHtml(a.title)}</small></span><span>${escapeHtml(a.repo)}</span><span><i class="pill ${a.decision==='block'?'danger':a.decision==='warn'?'warn':'success'}">${a.decision.toUpperCase()}</i></span><span>${Math.round(a.confidence*100)}%</span><span>${relTime(a.created_at)}</span></button>`).join(''):'<div class="detail-block"><b>No matching analyses</b></div>');
  $$('#analysisTable [data-id]').forEach(b=>b.onclick=()=>openStoredAnalysis(b.dataset.id));
}
$('#analysisSearch')?.addEventListener('input',renderAnalysesTable); $$('#analysisFilters .filter').forEach(b=>b.onclick=()=>{$$('#analysisFilters .filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');renderAnalysesTable();});

async function loadReports(){const rows=await api('/api/reports');$('#reportsGrid').innerHTML=rows.length?rows.map(r=>`<article class="card report-card"><div class="report-top"><span class="pill ${r.decision==='block'?'danger':r.decision==='warn'?'warn':'success'}">${r.decision.toUpperCase()}</span><small>${relTime(r.created_at)}</small></div><h3>PR #${r.pull_request} · ${escapeHtml(r.repo)}</h3><p>${escapeHtml(r.summary)}</p><div class="report-actions"><button class="secondary" data-open="${r.id}">Open</button><a class="primary button-link" href="/api/reports/${encodeURIComponent(r.id)}.md">Export Markdown</a></div></article>`).join(''):'<section class="card"><div class="detail-block"><b>No reports yet</b><small>Reports are generated from saved analyses.</small></div></section>';
  $$('#reportsGrid [data-open]').forEach(b=>b.onclick=()=>openStoredAnalysis(b.dataset.open));
}

function renderBenchmark(b){if(!b||b.status==='not_run'){$('#benchmarkContent').innerHTML='<section class="card"><div class="detail-block"><b>Benchmark has not been run</b><small>Click Run Benchmark to execute the bundled test cases.</small></div></section>';return;} $('#benchmarkContent').innerHTML=`<div class="benchmark-hero"><section class="card score-card"><span>Overall score</span><b>${b.overall_score}%</b><small>ChangeGuard deterministic workflow</small></section><section class="card score-card baseline"><span>Baseline score</span><b>${b.baseline_score}%</b><small>Simple pattern baseline</small></section><section class="card score-card gain"><span>Measured improvement</span><b>${b.improvement>=0?'+':''}${b.improvement}</b><small>percentage points</small></section></div><section class="card"><div class="card-head"><h3>Evaluation Results</h3><span class="pill info">${b.cases} CASES</span></div><div class="benchmark-table"><div class="tr head"><span>Metric</span><span>Baseline</span><span>ChangeGuard</span><span>Change</span></div>${b.metrics.map(m=>`<div class="tr"><span>${m.name}</span><span>${m.baseline}${m.unit}</span><span>${m.changeguard}${m.unit}</span><b>${m.changeguard-m.baseline>=0?'+':''}${m.changeguard-m.baseline}${m.unit}</b></div>`).join('')}</div></section>`;}
async function loadBenchmark(){renderBenchmark(await api('/api/benchmarks/latest'));}
$('#runBenchmarkBtn').onclick=async()=>{const b=$('#runBenchmarkBtn');b.disabled=true;b.textContent='Running...';try{renderBenchmark(await api('/api/benchmarks/run',{method:'POST'}));toast('Benchmark complete');}catch(e){toast(e.message)}finally{b.disabled=false;b.textContent='Run Benchmark'}};

let settingsCache={};
async function loadSettings(){settingsCache=await api('/api/settings');$('#githubStatusText').textContent=settingsCache.github_configured?`Token configured (${settingsCache.github_token_masked})`:'Public GitHub API only — no token';$('#defaultRepoText').textContent=settingsCache.default_repository||'Not set';$('#llmStatusText').textContent=settingsCache.llm_configured?`${settingsCache.llm_provider} · ${settingsCache.llm_model} · ${settingsCache.llm_api_key_masked}`:'Not configured';$('#blockThreshold').value=settingsCache.block_threshold;$('#blockThresholdText').textContent=settingsCache.block_threshold+'% confidence';$('#requireEvidence').checked=settingsCache.require_evidence;$('#rejectBlast').checked=settingsCache.reject_unsupported_blast_radius;}
$('#blockThreshold')?.addEventListener('input',e=>$('#blockThresholdText').textContent=e.target.value+'% confidence');
$('#savePolicyBtn').onclick=async()=>{try{await api('/api/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({block_threshold:Number($('#blockThreshold').value),require_evidence:$('#requireEvidence').checked,reject_unsupported_blast_radius:$('#rejectBlast').checked})});toast('Policy saved')}catch(e){toast(e.message)}};
$('#githubConnectBtn').onclick=()=>openDrawer({title:'GitHub Integration',sub:'Token is stored locally in ChangeGuard SQLite.',html:`<label class="field"><span>Personal access token</span><input id="ghTokenField" type="password" placeholder="github_pat_..." value=""></label><p class="muted">Leave empty to keep the current token. Public PR analysis works without a token; private repositories require one.</p><div class="modal-actions"><button class="secondary" id="ghTestBtn">Test current connection</button><button class="primary" id="ghSaveBtn">Save</button></div>`});
$('#llmConfigureBtn').onclick=()=>openDrawer({title:'LLM Provider',sub:'OpenAI-compatible API configuration.',html:`<label class="field"><span>Base URL</span><input id="llmBaseField" value="${escapeHtml(settingsCache.llm_base_url||'https://api.openai.com/v1')}"></label><label class="field"><span>Model</span><input id="llmModelField" value="${escapeHtml(settingsCache.llm_model||'gpt-5.6')}"></label><label class="field"><span>API key</span><input id="llmKeyField" type="password" placeholder="sk-... (leave blank to keep current)"></label><div class="modal-actions"><button class="secondary" id="llmTestBtn">Test current connection</button><button class="primary" id="llmSaveBtn">Save</button></div>`});
$('#defaultRepoBtn').onclick=async()=>{const v=prompt('Default repository (owner/repo):',settingsCache.default_repository||'');if(v!==null){await api('/api/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({default_repository:v})});await loadSettings();toast('Default repository saved')}};
document.addEventListener('click',async e=>{if(e.target.id==='ghSaveBtn'){const t=$('#ghTokenField').value;const body=t?{github_token:t}:{};await api('/api/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});await loadSettings();toast('GitHub settings saved');$('#drawer').classList.remove('open')}if(e.target.id==='ghTestBtn'){try{const r=await api('/api/integrations/github/test',{method:'POST'});toast(r.authenticated?`GitHub connected as ${r.login}`:`GitHub public API connected · ${r.remaining} requests remaining`)}catch(err){toast(err.message)}}if(e.target.id==='llmSaveBtn'){const body={llm_base_url:$('#llmBaseField').value,llm_model:$('#llmModelField').value};if($('#llmKeyField').value)body.llm_api_key=$('#llmKeyField').value;await api('/api/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});await loadSettings();toast('LLM settings saved');$('#drawer').classList.remove('open')}if(e.target.id==='llmTestBtn'){try{const r=await api('/api/integrations/llm/test',{method:'POST'});toast(`LLM connection OK · ${r.model}`)}catch(err){toast(err.message)}}});

$('#githubBtn').onclick=()=>{showView('settings');loadSettings();};
$('#exportAllReportsBtn').onclick=async()=>{const rows=await api('/api/reports');const blob=new Blob([JSON.stringify(rows,null,2)],{type:'application/json'});const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download='changeguard-reports-index.json';a.click();URL.revokeObjectURL(u);};

const originalShowView=showView;
showView=function(name){originalShowView(name); if(name==='dashboard')loadDashboard().catch(e=>toast(e.message)); if(name==='analyses')loadAnalyses().catch(e=>toast(e.message)); if(name==='benchmarks')loadBenchmark().catch(e=>toast(e.message)); if(name==='reports')loadReports().catch(e=>toast(e.message)); if(name==='settings')loadSettings().catch(e=>toast(e.message));};
