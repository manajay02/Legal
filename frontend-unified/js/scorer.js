/* ── Legal Argument Strength Scorer (FastAPI port 8000) ─────────── */

const Scorer = (() => {
  const API = () => CONFIG.SCORER_API;

  let pendingFile   = null;
  let uploadedDocId = null;

  /* ── Init ─────────────────────────────────────────────────────── */
  async function init() {
    setupCharCounter();
    setupSupportUpload();
    setupAnalyzeBtn();
    await checkHealth();
  }

  async function checkHealth() {
    const badge = document.getElementById('scorer-api-badge');
    try {
      const r = await fetch(`${API()}/api/v1/health`, { signal: AbortSignal.timeout(4000) });
      if (r.ok) {
        badge.className = 'api-status-badge online';
        badge.innerHTML = '<div class="pulse-dot online"></div><span>Online · port 8000</span>';
      } else throw new Error();
    } catch {
      badge.className = 'api-status-badge offline';
      badge.innerHTML = '<div class="pulse-dot offline"></div><span>Offline · start backend-nawanjana</span>';
    }
  }

  /* ── Character counter ────────────────────────────────────────── */
  function setupCharCounter() {
    const ta    = document.getElementById('scorer-text');
    const count = document.getElementById('scorer-char-count');
    ta.addEventListener('input', () => {
      const n = ta.value.length;
      count.textContent = n;
      count.style.color = n > CONFIG.SCORER_MAX_CHARS ? 'var(--red)' : n < CONFIG.SCORER_MIN_CHARS ? 'var(--text-3)' : 'var(--green-light)';
    });
  }

  /* ── Support document upload ──────────────────────────────────── */
  function setupSupportUpload() {
    const zone    = document.getElementById('support-upload-zone');
    const fileIn  = document.getElementById('support-file-input');
    const uploadBtn= document.getElementById('btn-upload-support');
    const listEl  = document.getElementById('support-docs-list');

    zone.addEventListener('click', () => fileIn.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('dragover');
      const f = e.dataTransfer.files[0];
      if (f) handleFileSelect(f);
    });
    fileIn.addEventListener('change', () => {
      if (fileIn.files[0]) handleFileSelect(fileIn.files[0]);
      fileIn.value = '';
    });

    uploadBtn.addEventListener('click', uploadSupportDoc);

    function handleFileSelect(f) {
      const ext = f.name.split('.').pop().toLowerCase();
      if (!['pdf','txt'].includes(ext)) { App.toast('Only PDF or TXT files supported.', 'error'); return; }
      if (f.size > CONFIG.SCORER_MAX_FILE)  { App.toast('File exceeds 10 MB limit.', 'error'); return; }
      pendingFile = f;
      uploadBtn.disabled = false;
      renderDocList();
    }

    async function uploadSupportDoc() {
      if (!pendingFile) return;
      uploadBtn.disabled = true;
      uploadBtn.innerHTML = '<span class="spinner"></span> Uploading…';
      try {
        const fd = new FormData(); fd.append('file', pendingFile);
        const r = await fetch(`${API()}/api/v1/documents/upload`, { method: 'POST', body: fd });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || d.error || 'Upload failed');
        uploadedDocId = d.doc_id || d.id || null;
        const name = pendingFile.name;
        pendingFile = null;
        App.toast('Document uploaded!', 'success');
        renderDocList({ name, docId: uploadedDocId, status: 'uploaded' });
      } catch (e) {
        App.toast(e.message, 'error');
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> Upload Document`;
      }
    }

    function renderDocList(docInfo) {
      listEl.innerHTML = '';
      // Pending file
      if (pendingFile) {
        listEl.innerHTML += `<div class="support-doc-item">
          <svg class="doc-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
          <span class="doc-name">${esc(pendingFile.name)}</span>
          <span class="doc-status pending">Pending</span>
          <button class="support-doc-remove" onclick="Scorer._clearPending()">✕</button>
        </div>`;
      }
      // Uploaded doc
      if (docInfo && docInfo.status === 'uploaded') {
        listEl.innerHTML += `<div class="support-doc-item">
          <svg class="doc-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
          <span class="doc-name">${esc(docInfo.name)}</span>
          <span class="doc-status uploaded">Uploaded</span>
        </div>`;
        uploadBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> Upload Document`;
        uploadBtn.disabled = true;
      }
    }
  }

  /* ── Analyze Argument ─────────────────────────────────────────── */
  function setupAnalyzeBtn() {
    const btn     = document.getElementById('btn-analyze-argument');
    const results = document.getElementById('scorer-results');

    btn.addEventListener('click', async () => {
      const text = document.getElementById('scorer-text').value.trim();
      if (text.length < CONFIG.SCORER_MIN_CHARS) {
        App.toast(`Argument must be at least ${CONFIG.SCORER_MIN_CHARS} characters.`, 'warning'); return;
      }
      if (text.length > CONFIG.SCORER_MAX_CHARS) {
        App.toast(`Argument exceeds ${CONFIG.SCORER_MAX_CHARS} characters.`, 'warning'); return;
      }
      if (pendingFile) {
        App.toast('Please upload the supporting document before analyzing.', 'warning'); return;
      }

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Analyzing…';
      results.style.display = 'none';

      try {
        const docIds = uploadedDocId ? [uploadedDocId] : [];
        const r = await fetch(`${API()}/api/v1/analyze_grounded`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ argument_text: text, doc_ids: docIds, stream: false })
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || d.error || 'Analysis failed');
        results.innerHTML = renderResults(d);
        results.style.display = '';
        App.toast('Argument analyzed!', 'success');
      } catch (e) {
        App.toast(e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Analyze Argument`;
      }
    });
  }

  /* ── Render response ──────────────────────────────────────────── */
  function renderResults(d) {
    // Try to extract score from various response shapes
    const score = d.overall_score ?? d.score ?? d.strength_score ?? d.argument_strength ?? null;
    const scoreNum = score !== null ? Math.round(Number(score)) : null;
    const label = d.overall_label || d.strength_label || d.label || (scoreNum !== null ? getScoreLabel(scoreNum) : 'N/A');
    const critique = d.critique || d.evaluation || d.summary || d.rationale || '';
    const strengths  = d.strengths  || d.strong_points || [];
    const weaknesses = d.weaknesses || d.weak_points   || [];
    const suggestions= d.suggestions || d.recommendations || [];
    const citations  = d.citations  || d.references || [];

    const ringClass = scoreNum !== null ? (scoreNum >= 70 ? 'high' : scoreNum >= 40 ? 'medium' : 'low') : 'medium';

    return `
    <div class="score-panel">
      ${scoreNum !== null ? `
      <div class="score-ring ${ringClass}">${scoreNum}</div>
      <div class="score-label">${esc(label)}</div>
      <div class="score-sub">Overall Argument Strength Score</div>` 
      : `<div class="score-label">${esc(label)}</div>`}
    </div>
    ${critique ? `
    <div class="argument-detail-section" style="padding:0 20px 14px;">
      <h4>Critique</h4>
      <div class="argument-quote">${esc(critique)}</div>
    </div>` : ''}
    ${strengths.length ? `
    <div class="argument-detail-section" style="padding:0 20px 14px;">
      <h4>Strengths</h4>
      ${strengths.map(s => `<div class="argument-quote" style="border-color:var(--green);">${esc(s)}</div>`).join('')}
    </div>` : ''}
    ${weaknesses.length ? `
    <div class="argument-detail-section" style="padding:0 20px 14px;">
      <h4>Weaknesses</h4>
      ${weaknesses.map(w => `<div class="argument-quote" style="border-color:var(--red);">${esc(w)}</div>`).join('')}
    </div>` : ''}
    ${suggestions.length ? `
    <div class="argument-detail-section" style="padding:0 20px 14px;">
      <h4>Suggestions</h4>
      <ul style="list-style:none;display:flex;flex-direction:column;gap:4px;">
        ${suggestions.map(s => `<li style="font-size:.82rem;color:var(--text-2);padding-left:12px;position:relative;">
          <span style="position:absolute;left:0;color:var(--gold-light);">›</span>${esc(s)}</li>`).join('')}
      </ul>
    </div>` : ''}
    ${citations.length ? `
    <div class="argument-detail-section" style="padding:0 20px 16px;">
      <h4>Citations &amp; References</h4>
      ${citations.map(c => `<div style="font-size:.78rem;color:var(--blue-light);margin-bottom:4px;">📎 ${esc(typeof c === 'string' ? c : JSON.stringify(c))}</div>`).join('')}
    </div>` : ''}
    `;
  }

  function getScoreLabel(n) {
    if (n >= 80) return 'Very Strong';
    if (n >= 60) return 'Strong';
    if (n >= 40) return 'Moderate';
    if (n >= 20) return 'Weak';
    return 'Very Weak';
  }

  function esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // Expose for inline handler
  function _clearPending() { pendingFile = null; document.getElementById('btn-upload-support').disabled = true; }

  return { init, checkHealth, _clearPending };
})();
