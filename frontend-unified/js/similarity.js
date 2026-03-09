/* ── Case Similarity Search Module (Flask backend port 5000) ────── */

const Similarity = (() => {
  const API = () => CONFIG.SEARCH_API;

  /* ── State ───────────────────────────────────────────────────── */
  let categories = {};      // { category: [subcategory, …] }
  let selectedCaseFile = null;
  let lastClassifyResult = null;

  /* ── Init ─────────────────────────────────────────────────────── */
  async function init() {
    await loadCategories();
    setupTabs();
    setupClassify();
    setupTextSearch();
    setupFileSearch();
  }

  async function loadCategories() {
    try {
      const r = await fetch(`${API()}/categories`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      categories = d.categories || {};
      populateCategorySelects();
    } catch {
      App.toast('Could not load categories from Search API. Is it running on port 5000?', 'warning');
    }
  }

  function populateCategorySelects() {
    const ids = ['sel-category-text', 'sel-category-file'];
    ids.forEach(id => {
      const sel = document.getElementById(id);
      if (!sel) return;
      sel.innerHTML = '<option value="">-- Any --</option>';
      Object.keys(categories).sort().forEach(cat => {
        const opt = document.createElement('option');
        opt.value = opt.textContent = cat;
        sel.appendChild(opt);
      });
    });
  }

  /* ── Tab switching ───────────────────────────────────────────── */
  function setupTabs() {
    document.querySelectorAll('#sim-tabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#sim-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.dataset.tab;
        document.getElementById('sim-tab-classify').style.display  = tab === 'classify' ? '' : 'none';
        document.getElementById('sim-tab-by-text').style.display   = tab === 'by-text'  ? '' : 'none';
        document.getElementById('sim-tab-by-file').style.display   = tab === 'by-file'  ? '' : 'none';
      });
    });
  }

  /* ── Classify tab ─────────────────────────────────────────────── */
  function setupClassify() {
    const zone    = document.getElementById('clf-upload-zone');
    const fileIn  = document.getElementById('clf-file');
    const nameEl  = document.getElementById('clf-file-name');
    const btnClf  = document.getElementById('btn-classify');
    const btnAdd  = document.getElementById('btn-add-case');
    const resPanel= document.getElementById('classify-result-panel');
    const resCont = document.getElementById('classify-result-content');

    zone.addEventListener('click', () => fileIn.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('dragover');
      const f = e.dataTransfer.files[0];
      if (f && f.name.toLowerCase().endsWith('.pdf')) setFile(f);
      else App.toast('Only PDF files are accepted.', 'error');
    });
    fileIn.addEventListener('change', () => {
      if (fileIn.files[0]) setFile(fileIn.files[0]);
    });

    function setFile(f) {
      fileIn._selectedFile = f;
      nameEl.textContent = `📄 ${f.name} (${formatBytes(f.size)})`;
      nameEl.style.display = 'flex';
    }

    btnClf.addEventListener('click', async () => {
      const file = fileIn._selectedFile;
      const text = document.getElementById('clf-text').value.trim();
      if (!file && !text) { App.toast('Provide a PDF or paste text.', 'warning'); return; }

      btnClf.disabled = true;
      btnClf.innerHTML = '<span class="spinner"></span> Classifying…';
      resPanel.style.display = 'none'; btnAdd.style.display = 'none';
      lastClassifyResult = null;

      try {
        let d;
        if (file) {
          const fd = new FormData(); fd.append('file', file);
          const r = await fetch(`${API()}/classify`, { method: 'POST', body: fd, credentials: 'include' });
          d = await r.json();
          if (!r.ok) throw new Error(d.error || 'Classification failed');
        } else {
          const r = await fetch(`${API()}/classify`, {
            method: 'POST', credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
          });
          d = await r.json();
          if (!r.ok) throw new Error(d.error || 'Classification failed');
        }
        lastClassifyResult = { ...d, _file: file, _text: text, _filename: file ? file.name : null };
        resCont.innerHTML = renderClassifyResult(d);
        resPanel.style.display = '';
        btnAdd.style.display = '';
        App.toast('Classification complete!', 'success');
      } catch (e) {
        App.toast(e.message, 'error');
      } finally {
        btnClf.disabled = false;
        btnClf.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg> Classify Document`;
      }
    });

    btnAdd.addEventListener('click', async () => {
      if (!lastClassifyResult) return;
      btnAdd.disabled = true;
      btnAdd.innerHTML = '<span class="spinner"></span> Saving…';
      try {
        let fd;
        if (lastClassifyResult._file) {
          fd = new FormData();
          fd.append('file', lastClassifyResult._file);
          if (lastClassifyResult._filename) fd.append('filename', lastClassifyResult._filename);
        }
        const opts = fd
          ? { method: 'POST', body: fd, credentials: 'include' }
          : { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: lastClassifyResult._text, filename: lastClassifyResult._filename || 'document.txt' }) };
        const r  = await fetch(`${API()}/add_case`, opts);
        const d  = await r.json();
        if (!r.ok) throw new Error(d.error || 'Save failed');
        App.toast('Case saved to database!', 'success');
        btnAdd.style.display = 'none';
        lastClassifyResult = null;
      } catch (e) {
        App.toast(e.message, 'error');
      } finally {
        btnAdd.disabled = false;
        btnAdd.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Save to Database`;
      }
    });
  }

  function renderClassifyResult(d) {
    const top5 = (d.subcategory_top5 || []).slice(0, 5);
    const catConf = d.category_confidence || {};
    const catPct = Object.values(catConf).map(v => v * 100);
    const maxCat = catPct.length ? Math.max(...catPct) : 0;

    return `<div class="classify-result-card">
      <div class="clf-row">
        <div class="clf-col">
          <div class="clf-label">Category</div>
          <div class="clf-value">${esc(d.category)}</div>
          <div class="clf-conf">${maxCat.toFixed(1)}% confidence</div>
        </div>
        <div class="clf-col">
          <div class="clf-label">Subcategory</div>
          <div class="clf-value">${esc(d.subcategory)}</div>
        </div>
      </div>
      ${top5.length ? `
      <div class="confidence-bars">
        <div class="clf-label" style="margin-bottom:8px;">Top Subcategory Matches</div>
        ${top5.map(([name, prob]) => {
          const pct = (prob * 100).toFixed(1);
          return `<div class="conf-row">
            <div class="conf-name" title="${esc(name)}">${esc(name)}</div>
            <div class="conf-bar"><div class="conf-bar-fill" style="width:${pct}%"></div></div>
            <div class="conf-pct">${pct}%</div>
          </div>`;
        }).join('')}
      </div>` : ''}
    </div>`;
  }

  /* ── Text Search tab ──────────────────────────────────────────── */
  function setupTextSearch() {
    const chk    = document.getElementById('chk-global-text');
    const catSel = document.getElementById('sel-category-text');
    const subSel = document.getElementById('sel-subcategory-text');
    const catWrap= document.getElementById('text-cat-wrap');
    const subWrap= document.getElementById('text-sub-wrap');
    const btn    = document.getElementById('btn-search-text');
    const results= document.getElementById('sim-text-results');

    chk.addEventListener('change', () => {
      catWrap.style.display = chk.checked ? 'none' : '';
      subWrap.style.display = chk.checked ? 'none' : '';
    });

    catSel.addEventListener('change', () => {
      const cat = catSel.value;
      subSel.innerHTML = '<option value="">-- Any --</option>';
      subSel.disabled = !cat;
      if (cat && categories[cat]) {
        categories[cat].sort().forEach(sub => {
          const opt = document.createElement('option');
          opt.value = opt.textContent = sub;
          subSel.appendChild(opt);
        });
      }
    });

    btn.addEventListener('click', async () => {
      const text = document.getElementById('txt-query').value.trim();
      if (!text) { App.toast('Enter a query text.', 'warning'); return; }
      const global_search = chk.checked;
      const category    = global_search ? null : (catSel.value || null);
      const subcategory = global_search ? null : (subSel.value || null);
      if (!global_search && (!category || !subcategory)) {
        App.toast('Select a category and subcategory, or enable Global Search.', 'warning'); return;
      }
      const top_n = parseInt(document.getElementById('sel-topn-text').value);

      btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Searching…';
      results.style.display = 'none';

      try {
        const r = await fetch(`${API()}/search`, {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, category, subcategory, global_search, top_n })
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || 'Search failed');
        results.innerHTML = renderSimilarityResults(d.results || []);
        results.style.display = '';
      } catch (e) {
        App.toast(e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg> Find Similar Cases`;
      }
    });
  }

  /* ── File/Category Browse tab ─────────────────────────────────── */
  function setupFileSearch() {
    const catSel  = document.getElementById('sel-category-file');
    const subSel  = document.getElementById('sel-subcategory-file');
    const casesCont= document.getElementById('file-cases-container');
    const casesWrap= document.getElementById('file-cases-list');
    const optsWrap = document.getElementById('file-search-options');
    const btn      = document.getElementById('btn-search-file');
    const results  = document.getElementById('sim-file-results');

    catSel.addEventListener('change', async () => {
      const cat = catSel.value;
      subSel.innerHTML = '<option value="">-- Select subcategory --</option>';
      subSel.disabled = !cat;
      casesWrap.style.display = 'none'; optsWrap.style.display = 'none';
      btn.disabled = true; selectedCaseFile = null;
      if (cat && categories[cat]) {
        subSel.disabled = false;
        categories[cat].sort().forEach(sub => {
          const opt = document.createElement('option');
          opt.value = opt.textContent = sub;
          subSel.appendChild(opt);
        });
      }
    });

    subSel.addEventListener('change', async () => {
      const cat = catSel.value; const sub = subSel.value;
      casesWrap.style.display = 'none'; optsWrap.style.display = 'none';
      btn.disabled = true; selectedCaseFile = null;
      if (!cat || !sub) return;
      try {
        const r = await fetch(`${API()}/filenames?category=${encodeURIComponent(cat)}&subcategory=${encodeURIComponent(sub)}`, { credentials: 'include' });
        const d = await r.json();
        const files = d.filenames || [];
        casesCont.innerHTML = files.length
          ? files.map(f => `<div class="case-item" data-filename="${esc(f)}">${esc(f)}</div>`).join('')
          : '<div style="color:var(--text-4);font-size:.8rem;">No cases found.</div>';
        casesWrap.style.display = '';
        casesCont.querySelectorAll('.case-item').forEach(el => {
          el.addEventListener('click', () => {
            casesCont.querySelectorAll('.case-item').forEach(x => x.classList.remove('selected'));
            el.classList.add('selected');
            selectedCaseFile = el.dataset.filename;
            optsWrap.style.display = '';
            btn.disabled = false;
          });
        });
      } catch { App.toast('Could not load case list.', 'error'); }
    });

    btn.addEventListener('click', async () => {
      if (!selectedCaseFile) return;
      const cat = catSel.value; const sub = subSel.value;
      const top_n = parseInt(document.getElementById('sel-topn-file').value);
      btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Searching…';
      results.style.display = 'none';
      try {
        const r = await fetch(`${API()}/search`, {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: selectedCaseFile, category: cat, subcategory: sub, global_search: false, top_n })
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || 'Search failed');
        results.innerHTML = renderSimilarityResults(d.results || []);
        results.style.display = '';
      } catch (e) {
        App.toast(e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg> Find Similar`;
      }
    });
  }

  /* ── Render helpers ───────────────────────────────────────────── */
  function renderSimilarityResults(results) {
    if (!results.length) return '<div class="empty-state"><p>No similar cases found.</p></div>';
    const header = `<div class="results-header"><span style="font-size:.9rem;font-weight:700;">Similar Cases</span>
      <span class="results-count">${results.length} result${results.length === 1 ? '' : 's'}</span></div>`;
    const items = results.map((r, i) => {
      const score = typeof r.score === 'number' ? r.score : (r.similarity_score || 0);
      const pct   = (score * 100).toFixed(1);
      const cls   = score >= 0.6 ? 'high' : score >= 0.3 ? 'med' : 'low';
      return `<div class="result-item">
        <div class="result-item-header">
          <div class="result-rank">${i + 1}</div>
          <div class="result-filename" title="${esc(r.filename)}">${esc(r.filename)}</div>
          <div class="result-score ${cls}">${pct}%</div>
        </div>
        <div class="result-meta">
          ${r.category ? `<span class="result-meta-tag">${esc(r.category)}</span>` : ''}
          ${r.subcategory ? `<span class="result-meta-tag">${esc(r.subcategory)}</span>` : ''}
        </div>
        ${r.snippet ? `<div class="result-snippet">${esc(r.snippet)}</div>` : ''}
        <button class="result-view-btn" onclick="window.open('${CONFIG.SEARCH_API.replace('/api','')+'/api/pdf/'}${encodeURIComponent(r.filename)}','_blank')">View document →</button>
      </div>`;
    }).join('');
    return header + items;
  }

  function esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function formatBytes(b) {
    if (b < 1024) return b + ' B';
    if (b < 1024*1024) return (b/1024).toFixed(1) + ' KB';
    return (b/(1024*1024)).toFixed(1) + ' MB';
  }

  return { init };
})();
