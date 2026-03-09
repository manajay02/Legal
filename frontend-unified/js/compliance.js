/* ── Contract Compliance Auditor (FastAPI port 8002) ────────────── */

const Compliance = (() => {
  const API = () => CONFIG.COMPLIANCE_API;

  let compMode = 'file';   // 'file' | 'text'
  let lastResult = null;

  /* ── Clause reference data ─────────────────────────────────────── */
  const CLAUSE_TYPES = {
    'Service Contract': ['Scope of Work','Payment Terms','Delivery Schedule','Confidentiality','Termination Clause','Liability Limitation','Dispute Resolution','Governing Law'],
    'Employment Contract':['Job Description','Compensation','Working Hours','Leave Policy','Termination Notice','Non-Disclosure','Intellectual Property','Probation Period'],
    'Purchase Agreement': ['Goods Description','Purchase Price','Delivery Terms','Inspection Rights','Risk of Loss','Warranties','Return Policy','Force Majeure'],
    'Lease Agreement':   ['Premises Description','Rent Amount','Lease Duration','Security Deposit','Maintenance Responsibilities','Subletting Policy','Termination Conditions','Renewal Options'],
    'NDA':               ['Definition of Confidential Info','Obligations','Exclusions','Term','Return of Information','Remedies','Governing Law','Permitted Disclosures'],
  };

  /* ── Init ──────────────────────────────────────────────────────── */
  async function init() {
    setupTabs();
    setupModeToggle();
    setupFileUpload();
    setupAnalyzeText();
    renderMandatoryClauses();
    await checkHealth();
    await loadHistory();
  }

  async function checkHealth() {
    const badge = document.getElementById('compliance-api-badge');
    try {
      const r = await fetch(`${API()}/health`, { signal: AbortSignal.timeout(4000) });
      if (r.ok) {
        badge.className = 'api-status-badge online';
        badge.innerHTML = '<div class="pulse-dot online"></div><span>Online · port 8002</span>';
      } else throw new Error();
    } catch {
      badge.className = 'api-status-badge offline';
      badge.innerHTML = '<div class="pulse-dot offline"></div><span>Offline · start civil-compliance-auditor</span>';
    }
  }

  /* ── Tabs ──────────────────────────────────────────────────────── */
  const TAB_PANELS = { 'comp-upload':'comp-tab-upload', 'comp-results':'comp-tab-results', 'comp-history':'comp-tab-history', 'comp-clauses':'comp-tab-clauses' };

  function setupTabs() {
    document.querySelectorAll('#comp-tabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('#comp-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        Object.values(TAB_PANELS).forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });
        const panelId = TAB_PANELS[tab] || tab;
        const el = document.getElementById(panelId);
        if (el) el.style.display = '';
        if (tab === 'comp-history') loadHistory();
      });
    });
    // Show first tab
    Object.values(TAB_PANELS).slice(1).forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });
    const firstBtn = document.querySelector('#comp-tabs .tab-btn');
    if (firstBtn) firstBtn.classList.add('active');
  }

  /* ── Mode toggle (file / text) ─────────────────────────────────── */
  // HTML uses onclick="setCompMode('file'|'text')" — expose global function
  function setCompMode(mode) {
    compMode = mode;
    document.getElementById('comp-file-section').style.display = mode === 'file' ? '' : 'none';
    document.getElementById('comp-text-section').style.display = mode === 'text' ? '' : 'none';
    document.getElementById('comp-mode-file')?.classList.toggle('active', mode === 'file');
    document.getElementById('comp-mode-text')?.classList.toggle('active', mode === 'text');
  }
  // Expose so inline onclick works
  window.setCompMode = setCompMode;

  function setupModeToggle() {
    // Initial state already set by HTML (file section visible, text hidden)
    compMode = 'file';
  }

  /* ── File upload ───────────────────────────────────────────────── */
  function setupFileUpload() {
    const zone   = document.getElementById('comp-upload-zone');
    const fileIn = document.getElementById('comp-file-input');
    const btnFile= document.getElementById('btn-comp-upload');
    const btnText= document.getElementById('btn-comp-text');
    if (!zone || !fileIn) return;

    zone.addEventListener('click', () => fileIn.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('dragover');
      const f = e.dataTransfer.files[0];
      if (f) { zone._file = f; zone.querySelector('p').textContent = esc(f.name); }
    });
    fileIn.addEventListener('change', () => {
      if (fileIn.files[0]) {
        zone._file = fileIn.files[0];
        zone.querySelector('p').textContent = esc(fileIn.files[0].name);
      }
      fileIn.value = '';
    });

    btnFile?.addEventListener('click', async () => {
      if (!zone._file) { App.toast('Select a PDF file first.', 'warning'); return; }
      await analyzeFile(zone._file, btnFile);
    });
    btnText?.addEventListener('click', async () => {
      const text = document.getElementById('comp-text-input')?.value?.trim();
      if (!text) { App.toast('Enter contract text first.', 'warning'); return; }
      await analyzeText(text, btnText);
    });
  }

  /* ── Analyze text ──────────────────────────────────────────────── */
  function setupAnalyzeText() {
    // Text analysis triggered by shared btn-analyze-compliance via mode toggle above
  }

  /* ── PDF analysis ──────────────────────────────────────────────── */
  async function analyzeFile(file, btn) {
    if (!btn) return;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Analyzing…';
    try {
      const fd = new FormData(); fd.append('file', file);
      const r = await fetch(`${API()}/upload-pdf`, { method: 'POST', body: fd });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || d.error || 'Analysis failed');
      lastResult = d;
      renderComplianceResult(d);
      switchToResultsTab();
      App.toast('Compliance analysis complete!', 'success');
      await loadHistory();
    } catch (e) {
      App.toast(e.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> Analyze Compliance`;
    }
  }

  async function analyzeText(text, btn) {
    if (!btn) return;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Analyzing…';
    try {
      // Try /analyze-text endpoint; fall back to /upload-pdf with text blob
      let r = await fetch(`${API()}/analyze-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!r.ok && r.status === 404) {
        // Fallback: send as plain text file
        const blob = new Blob([text], { type: 'text/plain' });
        const fd = new FormData(); fd.append('file', blob, 'contract.txt');
        r = await fetch(`${API()}/upload-pdf`, { method: 'POST', body: fd });
      }
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || d.error || 'Analysis failed');
      lastResult = d;
      renderComplianceResult(d);
      switchToResultsTab();
      App.toast('Compliance analysis complete!', 'success');
      await loadHistory();
    } catch (e) {
      App.toast(e.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> Analyze Compliance`;
    }
  }

  function switchToResultsTab() {
    document.querySelector('#comp-tabs .tab-btn[data-tab="comp-results"]')?.click();
  }

  /* ── Render compliance result ──────────────────────────────────── */
  function renderComplianceResult(d) {
    const out = document.getElementById('comp-results-content');
    if (!out) return;

    const isContract  = d.is_contract ?? d.is_valid_contract ?? true;
    const overall    = d.compliance_status || d.overall_status || (isContract ? 'Reviewed' : 'Not a Contract');
    const score      = d.compliance_score  ?? d.score          ?? null;
    const present    = d.present_clauses   || d.clauses_present || [];
    const missing    = d.missing_clauses   || d.clauses_missing || [];
    const issues     = d.issues            || d.non_compliant_clauses || [];
    const summary    = d.summary           || d.review_summary  || '';
    const doctype    = d.document_type     || d.contract_type   || '';

    if (!isContract) {
      out.innerHTML = `<div class="compliance-warning">
        <div class="warning-icon">⚠️</div>
        <h3>Not a Contract</h3>
        <p>${esc(summary || 'The uploaded document does not appear to be a valid contract.')}</p>
      </div>`;
      return;
    }

    const scoreHtml = score !== null ? `
      <div class="score-ring ${score >= 80 ? 'high' : score >= 50 ? 'medium' : 'low'}">${Math.round(score)}</div>
      <div class="score-label">Compliance Score</div>` : '';

    out.innerHTML = `
      <div class="compliance-header">
        ${scoreHtml}
        <div class="compliance-meta">
          <div class="comp-status-badge ${overall.toLowerCase().replace(/\s/g,'-')}">${esc(overall)}</div>
          ${doctype ? `<div class="comp-type">${esc(doctype)}</div>` : ''}
          ${summary ? `<p class="comp-summary">${esc(summary)}</p>` : ''}
        </div>
      </div>
      ${present.length ? `
      <div class="clause-group">
        <h4 class="clause-group-title present">Present Clauses (${present.length})</h4>
        ${present.map(c => `<div class="clause-item present">
          <span class="clause-check">✓</span>
          <span class="clause-name">${esc(typeof c === 'string' ? c : c.name || c.clause || JSON.stringify(c))}</span>
          ${c.note ? `<span class="clause-note">${esc(c.note)}</span>` : ''}
        </div>`).join('')}
      </div>` : ''}
      ${missing.length ? `
      <div class="clause-group">
        <h4 class="clause-group-title missing">Missing Clauses (${missing.length})</h4>
        ${missing.map(c => `<div class="clause-item missing">
          <span class="clause-check">✗</span>
          <span class="clause-name">${esc(typeof c === 'string' ? c : c.name || c.clause || JSON.stringify(c))}</span>
          ${c.note ? `<span class="clause-note">${esc(c.note)}</span>` : ''}
        </div>`).join('')}
      </div>` : ''}
      ${issues.length ? `
      <div class="clause-group">
        <h4 class="clause-group-title issues">Issues Found (${issues.length})</h4>
        ${issues.map(i => `<div class="clause-item issue">
          <span class="clause-check">⚠</span>
          <span class="clause-name">${esc(typeof i === 'string' ? i : i.name || i.issue || JSON.stringify(i))}</span>
          ${i.description ? `<p class="clause-desc">${esc(i.description)}</p>` : ''}
        </div>`).join('')}
      </div>` : ''}
      ${!present.length && !missing.length && !issues.length ? '<div class="empty-state">No clause details returned by the API.</div>' : ''}`;
  }

  /* ── History ───────────────────────────────────────────────────── */
  async function loadHistory() {
    const list = document.getElementById('comp-history-list');
    if (!list) return;
    list.innerHTML = '<div class="placeholder-message"><span class="spinner-lg"></span></div>';
    try {
      const r = await fetch(`${API()}/history`);
      if (!r.ok) throw new Error();
      const data = await r.json();
      const items = Array.isArray(data) ? data : (data.history || data.items || []);
      if (!items.length) { list.innerHTML = '<div class="empty-state">No history yet.</div>'; return; }
      list.innerHTML = items.map(item => {
        const name  = item.filename || item.file_name || item.document || 'Document';
        const date  = item.created_at || item.analyzed_at || item.timestamp || '';
        const score = item.compliance_score ?? item.score ?? null;
        const status= item.compliance_status || item.status || '';
        return `<div class="history-item" onclick="Compliance.showHistoryItem(${esc(JSON.stringify(JSON.stringify(item)))})">
          <div class="history-icon">📋</div>
          <div class="history-info">
            <div class="history-name">${esc(name)}</div>
            <div class="history-meta">${date ? new Date(date).toLocaleString() : ''}${status ? ` · ${esc(status)}` : ''}</div>
          </div>
          ${score !== null ? `<div class="history-score ${score >= 80 ? 'high' : score >= 50 ? 'medium' : 'low'}">${Math.round(score)}</div>` : ''}
        </div>`;
      }).join('');
    } catch {
      list.innerHTML = '<div class="empty-state">History unavailable.</div>';
    }
  }

  function showHistoryItem(itemJson) {
    try {
      const d = typeof itemJson === 'string' ? JSON.parse(itemJson) : itemJson;
      renderComplianceResult(d);
      switchToResultsTab();
    } catch {}
  }

  /* ── Mandatory Clauses reference ───────────────────────────────── */
  function renderMandatoryClauses() {
    const grid = document.getElementById('contract-types-grid');
    const detail = document.getElementById('clause-detail-panel');
    if (!grid) return;

    grid.innerHTML = Object.keys(CLAUSE_TYPES).map(type => `
      <div class="contract-type-card" onclick="Compliance.showClauses('${esc(type)}')">
        <div class="contract-type-icon">📑</div>
        <div class="contract-type-name">${esc(type)}</div>
        <div class="contract-type-count">${CLAUSE_TYPES[type].length} clauses</div>
      </div>`).join('');

    if (detail) detail.style.display = 'none';
  }

  function showClauses(type) {
    const detail = document.getElementById('clause-detail-panel');
    if (!detail) return;
    const clauses = CLAUSE_TYPES[type] || [];
    detail.style.display = '';
    detail.innerHTML = `
      <h4 style="margin-bottom:12px;color:var(--text-1);">${esc(type)} — Mandatory Clauses</h4>
      <div style="display:flex;flex-wrap:wrap;gap:8px;">
        ${clauses.map((c,i) => `
          <div class="clause-ref-chip">
            <span class="clause-ref-num">${i+1}</span>
            <span>${esc(c)}</span>
          </div>`).join('')}
      </div>
      <button class="btn-link" style="margin-top:12px;" onclick="document.getElementById('clause-detail-panel').style.display='none'">Close ✕</button>`;
  }

  function esc(s) {
    return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  return { init, checkHealth, loadHistory, showHistoryItem, showClauses };
})();
