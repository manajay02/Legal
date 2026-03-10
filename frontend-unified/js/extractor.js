/* ── Civil Document Extractor (FastAPI port 8001) ───────────────── */

const Extractor = (() => {
  const API = () => CONFIG.EXTRACTOR_API;

  let documents = [];
  let currentTab = 'ext-tab-upload';

  /* ── Init ─────────────────────────────────────────────────────── */
  async function init() {
    setupTabs();
    // Single-button handles both single and batch based on active mode
    const extBtn = document.getElementById('btn-ext-upload');
    if (extBtn) {
      extBtn.addEventListener('click', () => {
        const batchActive = document.querySelector('#ext-mode-toggle .mode-btn[data-mode="batch"]')?.classList.contains('active');
        const zone = document.getElementById(batchActive ? 'ext-batch-zone' : 'ext-upload-zone');
        if (!zone?._files?.length) { App.toast('Select a file first.', 'warning'); return; }
        if (batchActive) uploadBatch(zone._files); else uploadSingle(zone._files);
      });
    }
    setupUploadZone('ext-upload-zone', 'ext-file-input', null, null, false);
    setupUploadZone('ext-batch-zone',  'ext-batch-input',  null, null, true);
    setupSearch();
    await checkHealth();
    await loadStats();
    // Wire refresh button
    document.getElementById('btn-refresh-docs')?.addEventListener('click', loadDocuments);
    await loadDocuments();
  }

  async function checkHealth() {
    const badge = document.getElementById('extractor-api-badge');
    try {
      const r = await fetch(`${API()}/health`, { signal: AbortSignal.timeout(4000) });
      if (r.ok) {
        const data = await r.json();
        const status = data.status || 'unknown';
        // Accept both 'healthy' and 'degraded' as functional
        if (status === 'healthy' || status === 'degraded') {
          badge.className = 'api-status-badge online';
          badge.innerHTML = `<div class="pulse-dot online"></div><span>Online · port 8001${status === 'degraded' ? ' (limited)' : ''}</span>`;
        } else {
          throw new Error('unhealthy');
        }
      } else throw new Error();
    } catch {
      badge.className = 'api-status-badge offline';
      badge.innerHTML = '<div class="pulse-dot offline"></div><span>Offline · start backend-paramitha</span>';
    }
  }

  /* ── Stats ────────────────────────────────────────────────────── */
  async function loadStats() {
    try {
      const r = await fetch(`${API()}/api/v1/documents`);
      if (!r.ok) return;
      const docs = await r.json();
      const list = Array.isArray(docs) ? docs : (docs.documents || docs.items || []);
      documents = list;
      document.getElementById('ext-total-docs').textContent = list.length;
      document.getElementById('ext-completed').textContent  = list.filter(d => (d.status||'').toLowerCase() === 'completed').length;
      document.getElementById('ext-processing').textContent = list.filter(d => (d.status||'').toLowerCase() === 'processing').length;
    } catch {}
  }

  /* ── Tabs ─────────────────────────────────────────────────────── */
  function setupTabs() {
    document.querySelectorAll('#ext-tabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('#ext-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('#ext-tab-upload, #ext-tab-documents, #ext-tab-search').forEach(t => t.style.display = 'none');
        const el = document.getElementById(tab);
        if (el) el.style.display = '';
        currentTab = tab;
        if (tab === 'ext-tab-documents') loadDocuments();
        if (tab === 'ext-tab-search') document.getElementById('ext-search-input')?.focus();
      });
    });
    // Show first tab
    document.querySelectorAll('#ext-tab-documents, #ext-tab-search').forEach(t => t.style.display = 'none');
    const firstBtn = document.querySelector('#ext-tabs .tab-btn');
    if (firstBtn) firstBtn.classList.add('active');
  }

  /* ── Upload zone setup ────────────────────────────────────────── */
  function setupUploadZone(zoneId, inputId, _btnId, _handler, multiple) {
    const zone   = document.getElementById(zoneId);
    const fileIn = document.getElementById(inputId);
    if (!zone || !fileIn) return;

    if (multiple) fileIn.multiple = true;

    zone.addEventListener('click', () => fileIn.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('dragover');
      const files = multiple ? [...e.dataTransfer.files] : [e.dataTransfer.files[0]].filter(Boolean);
      if (files.length) displaySelected(zone, files, multiple);
      zone._files = files;
    });
    fileIn.addEventListener('change', () => {
      const files = [...fileIn.files];
      if (!files.length) return;
      displaySelected(zone, files, multiple);
      zone._files = files;
      fileIn.value = '';
    });
  }

  function displaySelected(zone, files, multiple) {
    const names = files.map(f => esc(f.name)).join(', ');
    zone.querySelector('p').textContent = multiple
      ? `${files.length} file(s): ${names}`
      : names;
  }

  /* ── Single upload ────────────────────────────────────────────── */
  async function uploadSingle(files) {
    const file = files[0];
    const btn  = document.getElementById('btn-ext-upload');
    const result = document.getElementById('ext-upload-result');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Uploading…';
    result.innerHTML = '<div class="placeholder-message">Uploading document…</div>';
    result.style.display = '';

    try {
      // Step 1: Upload the file
      const fd = new FormData(); fd.append('file', file);
      const uploadResp = await fetch(`${API()}/api/v1/upload`, { method: 'POST', body: fd });
      const uploadData = await uploadResp.json();
      if (!uploadResp.ok) throw new Error(uploadData.detail || uploadData.error || 'Upload failed');
      
      const docId = uploadData.document_id;
      result.innerHTML = '<div class="placeholder-message">Extracting data (this may take a minute)…</div>';
      btn.innerHTML = '<span class="spinner"></span> Extracting…';
      
      // Step 2: Call process endpoint to extract data
      const processResp = await fetch(`${API()}/api/v1/process/${encodeURIComponent(docId)}`, { method: 'POST' });
      const processData = await processResp.json();
      if (!processResp.ok) throw new Error(processData.detail || processData.error || 'Processing failed');
      
      // Step 3: Fetch the processed document to get full results
      const docResp = await fetch(`${API()}/api/v1/documents/${encodeURIComponent(docId)}`);
      const docData = await docResp.json();
      
      result.innerHTML = renderDocResult(docData);
      document.getElementById('ext-upload-zone')._files = [];
      document.getElementById('ext-upload-zone').querySelector('p').textContent = 'Drag & drop a PDF/TXT, or click to browse';
      App.toast('Document processed!', 'success');
      await loadStats();
    } catch (e) {
      result.innerHTML = `<div class="empty-state error">${esc(e.message)}</div>`;
      App.toast(e.message, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/></svg> Upload &amp; Extract`;
      }
    }
  }

  /* ── Batch upload ─────────────────────────────────────────────── */
  async function uploadBatch(files) {
    const btn = document.getElementById('btn-ext-upload');
    const out = (() => {
      let el = document.getElementById('ext-batch-results');
      if (!el) { el = document.createElement('div'); el.id = 'ext-batch-results'; document.getElementById('ext-tab-upload')?.appendChild(el); }
      return el;
    })();
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Uploading ${files.length} files…`;
    out.innerHTML = '';
    out.style.display = '';

    const results = [];
    for (const file of files) {
      out.innerHTML += `<div class="batch-row" id="batch-${esc(file.name.replace(/\W/g,'_'))}">
        <span class="batch-filename">${esc(file.name)}</span>
        <span class="batch-status pending">Uploading…</span></div>`;
      try {
        // Step 1: Upload
        const fd = new FormData(); fd.append('file', file);
        const uploadResp = await fetch(`${API()}/api/v1/upload`, { method: 'POST', body: fd });
        const uploadData = await uploadResp.json();
        if (!uploadResp.ok) throw new Error(uploadData.detail || 'Upload failed');
        
        const docId = uploadData.document_id;
        // Update status to processing
        const row = document.getElementById(`batch-${file.name.replace(/\W/g,'_')}`);
        if (row) row.querySelector('.batch-status').textContent = 'Processing…';
        
        // Step 2: Process
        const processResp = await fetch(`${API()}/api/v1/process/${encodeURIComponent(docId)}`, { method: 'POST' });
        const processData = await processResp.json();
        if (!processResp.ok) throw new Error(processData.detail || 'Processing failed');
        
        results.push({ name: file.name, ok: true, data: processData });
      } catch (e) {
        results.push({ name: file.name, ok: false, error: e.message });
      }
    }

    // Re-render results
    out.innerHTML = results.map(res => `<div class="batch-row">
      <span class="batch-filename">${esc(res.name)}</span>
      <span class="batch-status ${res.ok ? 'uploaded' : 'error'}">${res.ok ? 'Done' : esc(res.error)}</span>
    </div>`).join('');

    const ok = results.filter(r => r.ok).length;
    App.toast(`Batch complete: ${ok}/${files.length} processed.`, ok === files.length ? 'success' : 'warning');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/></svg> Upload &amp; Extract`;
    }
    document.getElementById('ext-batch-zone')._files = [];
    document.getElementById('ext-batch-zone').querySelector('p').textContent = 'Drag & drop multiple PDFs, or click to browse';
    await loadStats();
  }

  /* ── Documents list ──────────────────────────────────────────── */
  async function loadDocuments() {
    const list = document.getElementById('ext-docs-list');
    if (!list) return;
    list.innerHTML = '<div class="placeholder-message"><span class="spinner-lg"></span></div>';
    try {
      const r = await fetch(`${API()}/api/v1/documents`);
      const data = await r.json();
      documents = Array.isArray(data) ? data : (data.documents || data.items || []);
      renderDocList(documents, list);
    } catch {
      list.innerHTML = '<div class="empty-state">Unable to reach extractor backend.</div>';
    }
  }

  function renderDocList(docs, el) {
    if (!docs.length) { el.innerHTML = '<div class="empty-state">No documents extracted yet.</div>'; return; }
    el.innerHTML = docs.map(doc => {
      const status = (doc.status || 'unknown').toLowerCase();
      const name   = doc.filename || doc.name || doc.file_name || 'Document';
      const id     = doc.id || doc._id || doc.doc_id || '';
      const date   = doc.created_at || doc.uploaded_at || doc.timestamp || '';
      const isClickable = status === 'completed';
      return `<div class="doc-list-item ${isClickable ? 'clickable' : ''}" data-id="${esc(id)}" ${isClickable ? `onclick="Extractor.viewDoc('${esc(id)}')"` : ''}>
        <div class="doc-list-icon">${status === 'completed' ? '✅' : status === 'processing' ? '⏳' : '📄'}</div>
        <div class="doc-list-info">
          <div class="doc-list-name">${esc(name)}</div>
          <div class="doc-list-meta">${date ? `Uploaded: ${new Date(date).toLocaleString()}` : ''} ${id ? `· ID: ${esc(id.slice(0,8))}...` : ''}</div>
        </div>
        <span class="doc-status-chip ${status}">${esc(status)}</span>
        ${isClickable ? `<span class="doc-view-hint">Click to view details →</span>` : ''}
      </div>`;
    }).join('');
  }

  async function viewDoc(id) {
    if (!id) return;
    
    // Show loading state in detail panel
    const detailPanel = document.getElementById('ext-doc-detail');
    if (detailPanel) {
      detailPanel.innerHTML = `<div class="placeholder-message"><span class="spinner-lg"></span> Loading document details...</div>`;
      detailPanel.style.display = '';
      detailPanel.scrollIntoView({ behavior: 'smooth' });
    }
    
    try {
      const r = await fetch(`${API()}/api/v1/documents/${encodeURIComponent(id)}`);
      const d = await r.json();
      
      // Show in document detail panel (in Documents tab)
      if (detailPanel) {
        detailPanel.innerHTML = `
          <div class="detail-header">
            <h3>📄 Document Details</h3>
            <button class="btn-secondary btn-sm" onclick="document.getElementById('ext-doc-detail').style.display='none'">✕ Close</button>
          </div>
          ${renderDocResult(d)}
        `;
        detailPanel.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (e) {
      if (detailPanel) {
        detailPanel.innerHTML = `<div class="empty-state error">Could not load document details: ${esc(e.message)}</div>`;
      }
      App.toast('Could not load document details.', 'error');
    }
  }

  function renderDocResult(d) {
    // Extract metadata (API returns nested structure)
    const meta     = d.metadata || {};
    const title    = meta.case_number || d.title || d.case_title || d.filename || 'Extracted Document';
    const court    = meta.court || d.court || d.court_name || '';
    const date     = meta.date || d.judgment_date || d.date || '';
    const caseType = meta.case_type || d.case_type || '';
    const year     = meta.year || '';
    const parties  = meta.parties || d.parties || d.involved_parties || [];
    const judges   = meta.judges || d.judges || [];
    const petitioners = meta.petitioners || [];
    const respondents = meta.respondents || [];
    const legalProvisions = meta.legal_provisions || d.legal_refs || d.legal_references || d.citations || [];
    
    // Extract sections from API response
    const sections = d.sections || [];
    
    // Build metadata section
    let metaHtml = '';
    if (court) metaHtml += `<div class="ext-field"><span class="ext-label">Court</span><span class="ext-value">${esc(court)}</span></div>`;
    if (date) metaHtml += `<div class="ext-field"><span class="ext-label">Date</span><span class="ext-value">${esc(date)}</span></div>`;
    if (caseType) metaHtml += `<div class="ext-field"><span class="ext-label">Case Type</span><span class="ext-value">${esc(caseType)}</span></div>`;
    if (year) metaHtml += `<div class="ext-field"><span class="ext-label">Year</span><span class="ext-value">${esc(year)}</span></div>`;
    if (parties.length) metaHtml += `<div class="ext-field"><span class="ext-label">Parties</span><span class="ext-value">${esc(Array.isArray(parties) ? parties.join(' vs ') : parties)}</span></div>`;
    if (judges.length) metaHtml += `<div class="ext-field"><span class="ext-label">Judges</span><span class="ext-value">${esc(Array.isArray(judges) ? judges.join(', ') : judges)}</span></div>`;
    if (petitioners.length) metaHtml += `<div class="ext-field"><span class="ext-label">Petitioners</span><span class="ext-value">${esc(Array.isArray(petitioners) ? petitioners.join(', ') : petitioners)}</span></div>`;
    if (respondents.length) metaHtml += `<div class="ext-field"><span class="ext-label">Respondents</span><span class="ext-value">${esc(Array.isArray(respondents) ? respondents.join(', ') : respondents)}</span></div>`;
    
    // Build legal provisions section
    let provisionsHtml = '';
    if (legalProvisions.length) {
      provisionsHtml = `<div class="ext-section"><h4>📜 Legal Provisions</h4><ul>${legalProvisions.map(r => `<li>${esc(typeof r === 'string' ? r : JSON.stringify(r))}</li>`).join('')}</ul></div>`;
    }
    
    // Build sections HTML
    let sectionsHtml = '';
    if (sections.length) {
      sectionsHtml = sections.map(s => {
        const sTitle = s.title || `Section ${s.order_index || ''}`;
        const sText = s.text || s.content || '';
        if (!sText) return '';
        return `<div class="ext-section">
          <h4>${esc(sTitle)}</h4>
          <p>${esc(sText)}</p>
        </div>`;
      }).filter(Boolean).join('');
    }
    
    // Check for timeline, citations, insights, outcome
    let extrasHtml = '';
    if (d.timeline && d.timeline.length) {
      extrasHtml += `<div class="ext-section"><h4>📅 Timeline</h4><ul>${d.timeline.map(t => `<li><strong>${esc(t.date || t.year || '')}</strong>: ${esc(t.event || t.description || '')}</li>`).join('')}</ul></div>`;
    }
    if (d.citations && d.citations.length) {
      extrasHtml += `<div class="ext-section"><h4>📖 Citations</h4><ul>${d.citations.map(c => `<li>${esc(typeof c === 'string' ? c : c.citation || JSON.stringify(c))}</li>`).join('')}</ul></div>`;
    }
    if (d.insights) {
      extrasHtml += `<div class="ext-section"><h4>💡 Insights</h4><p>${esc(typeof d.insights === 'string' ? d.insights : JSON.stringify(d.insights))}</p></div>`;
    }
    if (d.outcome) {
      extrasHtml += `<div class="ext-section"><h4>⚖️ Outcome</h4><p>${esc(typeof d.outcome === 'string' ? d.outcome : JSON.stringify(d.outcome))}</p></div>`;
    }
    
    // Status badge
    const status = d.status || 'unknown';
    const statusClass = status === 'completed' ? 'completed' : status === 'processing' ? 'processing' : 'unknown';
    const statusBadge = `<span class="doc-status-chip ${statusClass}">${esc(status)}</span>`;
    
    const hasContent = metaHtml || provisionsHtml || sectionsHtml || extrasHtml;

    return `<div class="ext-result-card">
      <div class="ext-result-header">
        <div class="ext-result-title">${esc(title)}</div>
        ${statusBadge}
      </div>
      ${metaHtml ? `<div class="ext-metadata">${metaHtml}</div>` : ''}
      ${provisionsHtml}
      ${sectionsHtml}
      ${extrasHtml}
      ${!hasContent ? '<div class="empty-state">No structured data extracted.</div>' : ''}
    </div>`;
  }

  /* ── Search ───────────────────────────────────────────────────── */
  function setupSearch() {
    const inp = document.getElementById('ext-search-input');
    const btn = document.getElementById('btn-ext-search');
    const out = document.getElementById('ext-search-results');
    if (!inp || !btn) return;

    btn.addEventListener('click', searchDocs);
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') searchDocs(); });

    async function searchDocs() {
      const q = inp.value.trim();
      if (!q) { App.toast('Enter a search term.', 'warning'); return; }
      btn.disabled = true; btn.textContent = 'Searching…';
      out.innerHTML = '<div class="placeholder-message"><span class="spinner-lg"></span></div>';
      try {
        const r = await fetch(`${API()}/api/v1/documents?query=${encodeURIComponent(q)}`);
        const data = await r.json();
        const results = Array.isArray(data) ? data : (data.documents || data.items || []);
        const filtered = results.filter(doc => {
          const text = JSON.stringify(doc).toLowerCase();
          return text.includes(q.toLowerCase());
        });
        renderDocList(filtered, out);
      } catch {
        out.innerHTML = '<div class="empty-state">Search failed — backend may be offline.</div>';
      } finally {
        btn.disabled = false; btn.textContent = 'Search';
      }
    }
  }

  function esc(s) {
    return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  return { init, checkHealth, loadDocuments, viewDoc };
})();
