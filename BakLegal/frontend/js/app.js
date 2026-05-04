document.addEventListener("DOMContentLoaded", () => {

/* ── Config ───────────────────────────────────────────────────────────────── */
const API = "/similarity/api";

/* ── Sidebar navigation ───────────────────────────────────────────────────── */
const topbarCurrent = document.getElementById("topbar-current");
const navLabels = { similarity: "Similar Case Finder", compliance: "Compliance Checker", extractor: "Case Extractor", argument: "Argument Scorer" };

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", async () => {
    document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
    document.querySelectorAll(".component-panel").forEach(p => p.classList.remove("active"));
    item.classList.add("active");
    const panel = document.getElementById("panel-" + item.dataset.component);
    if (panel) panel.classList.add("active");
    if (topbarCurrent) topbarCurrent.textContent = navLabels[item.dataset.component] || item.querySelector(".nav-label").textContent;
    const comp = item.dataset.component;
    localStorage.setItem("lv_active_panel", comp);
    if (comp === "similarity")  loadCategories();
    if (comp === "compliance")  checkCmpBackend();
    if (comp === "extractor")   checkExtBackend();
    if (comp === "argument")    checkArgBackend();
  });
});

/* ── Restore last active panel on reload ─────────────────────────────────── */
(function restoreActivePanel() {
  const saved = localStorage.getItem("lv_active_panel");
  if (!saved || saved === "similarity") return; // default already active
  const navItem = document.querySelector(`.nav-item[data-component="${saved}"]`);
  if (navItem) navItem.click();
})();

/* ── DOM refs ─────────────────────────────────────────────────────────────── */
const selCategory   = document.getElementById("sel-category");
const selSubcategory= document.getElementById("sel-subcategory");
const selTopN       = document.getElementById("sel-topn");
const chkGlobal     = document.getElementById("chk-global");

const btnSearch     = document.getElementById("btn-search");
const btnClassify   = document.getElementById("btn-classify");
const searchOptions = document.getElementById("search-options");
const resultsPanel  = document.getElementById("results-panel");
const resultsList   = document.getElementById("results-list");
const resultsCount  = document.getElementById("results-count");
const classifyPanel = document.getElementById("classify-panel");
const classifyResult= document.getElementById("classify-result");
const clfFile       = document.getElementById("clf-file");
const clfText       = document.getElementById("clf-text");
const statsGrid     = document.getElementById("stats-grid");
const spinner       = document.getElementById("spinner");
const btnAddCase = document.getElementById("btn-add-case");

/* ── Utility ──────────────────────────────────────────────────────────────── */
function showSpinner(v) { if (spinner) spinner.style.display = v ? "flex" : "none"; }
function currentTab() { return document.querySelector(".tab.active").dataset.tab; }

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");

    const isClassify = tab.dataset.tab === "classify";
    if (btnSearch) btnSearch.style.display    = "none";
    if (btnClassify) btnClassify.style.display  = isClassify ? "inline-block" : "none";
    if (btnAddCase) btnAddCase.style.display   = isClassify ? "inline-block" : "none";
    if (searchOptions) searchOptions.style.display = isClassify ? "none"        : "flex";
  });
});

/* ── Load categories on page load ─────────────────────────────────────────── */
let categoriesData = {};

async function loadCategories() {
  try {
    const res  = await fetch(`${API}/categories`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    categoriesData = await res.json();
    clearBackendBanner("panel-similarity");
    selCategory.innerHTML = '<option value="">-- Select category --</option>';
    Object.keys(categoriesData).sort().forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat; opt.textContent = cat;
      selCategory.appendChild(opt);
    });
    renderStats(categoriesData);
  } catch (e) {
    console.error("Failed to load categories:", e);
    setBackendBanner("panel-similarity",
      " <strong>Similar Case Finder backend is offline.</strong> Run: <code>cd backend-M &amp;&amp; python app.py</code>",
      true);
    if (statsGrid) statsGrid.innerHTML = '<p style="color:var(--muted);text-align:center;padding:1rem;">Start backend-M to view dataset statistics.</p>';
    selCategory.innerHTML = '<option value=""> Backend offline</option>';
  }
}

/* ── Category → Subcategory cascade ──────────────────────────────────────── */
if (selCategory) {
  selCategory.addEventListener("change", () => {
    const cat = selCategory.value;
    if (selSubcategory) {
      selSubcategory.innerHTML = '<option value="">-- Select subcategory --</option>';
      selSubcategory.disabled  = !cat;
    }
    if (resultsPanel) resultsPanel.style.display = "none";
    if (!cat) return;
    (categoriesData[cat] || []).forEach(({ subcategory, count }) => {
      const opt = document.createElement("option");
      opt.value = subcategory;
      opt.textContent = `${subcategory} (${count})`;
      if (selSubcategory) selSubcategory.appendChild(opt);
    });
  });
}

/* ── Subcategory → Auto-show case list ───────────────────────────────────── */
if (selSubcategory) {
  selSubcategory.addEventListener("change", async () => {
    const cat = selCategory?.value;
    const sub = selSubcategory.value;
    if (resultsPanel) resultsPanel.style.display  = "none";
    if (classifyPanel) classifyPanel.style.display = "none";
    if (!sub) return;
    showSpinner(true);
    try {
      const res   = await fetch(`${API}/filenames?category=${encodeURIComponent(cat)}&subcategory=${encodeURIComponent(sub)}`);
      const files = await res.json();
      renderCaseList(files, cat, sub);
      if (resultsPanel) {
        resultsPanel.style.display = "block";
        resultsPanel.scrollIntoView({ behavior: "smooth" });
      }
    } catch {
      if (resultsList) resultsList.innerHTML = `<div class="error-msg"> Could not load cases. Is the backend running?</div>`;
      if (resultsPanel) resultsPanel.style.display = "block";
      Swal.fire({ icon: 'error', title: 'Connection Error', text: 'Could not load cases. Please ensure the server is running.', confirmButtonColor: '#1a3a5c' });
    } finally { showSpinner(false); }
  });
}

/* ── Classify Document ────────────────────────────────────────────────────── */
if (btnClassify) {
  btnClassify.addEventListener("click", async () => {
    const file = clfFile?.files[0];
    const text = clfText?.value.trim();

    if (!file && !text) {
      Swal.fire({ icon: 'warning', title: 'Missing Input', text: 'Please upload a PDF or paste document text.', confirmButtonColor: '#1a3a5c' });
      return;
    }

    showSpinner(true);
    if (classifyPanel) classifyPanel.style.display = "none";
    if (resultsPanel) resultsPanel.style.display  = "none";
    if (classifyResult) classifyResult.innerHTML    = "";

    try {
      let res;
      if (file) {
        const form = new FormData();
        form.append("file", file);
        res = await fetch(`${API}/classify`, { method: "POST", body: form });
      } else {
        res = await fetch(`${API}/classify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });
      }
      const data = await res.json();
      if (data.not_legal) {
        if (classifyResult) {
          classifyResult.innerHTML = `
            <div style="background:#fdecea;border:1.5px solid #f5c6cb;border-radius:10px;padding:1.25rem 1.5rem;">
              <div style="font-size:1.4rem;margin-bottom:.5rem;"> Not a Legal Document</div>
              <p style="color:#b71c1c;font-size:.95rem;margin-bottom:.5rem;">
                This does not appear to be a Sri Lankan legal document.
              </p>
              <p style="color:#7f1d1d;font-size:.85rem;">Please upload a valid Sri Lankan court judgment or case file.</p>
            </div>`;
        }
      } else if (data.error) {
        if (classifyResult) classifyResult.innerHTML = `<div class="error-msg"> ${data.error}</div>`;
      } else {
        renderClassifyResult(data);
      }
    } catch {
      if (classifyResult) classifyResult.innerHTML = `<div class="error-msg"> Could not reach the API. Is the backend running?</div>`;
      Swal.fire({ icon: 'error', title: 'Connection Error', text: 'Could not reach the API. Please ensure the server is running.', confirmButtonColor: '#1a3a5c' });
    } finally {
      if (classifyPanel) {
        classifyPanel.style.display = "block";
        classifyPanel.scrollIntoView({ behavior: "smooth" });
      }
      showSpinner(false);
    }
  });
}

/* ── Render similarity results ────────────────────────────────────────────── */
function renderResults(results) {
  resultsCount.textContent = results.length;
  if (!results.length) {
    resultsList.innerHTML = '<p style="color:var(--muted)">No similar cases found.</p>';
    return;
  }
  const maxScore = Math.max(...results.map(r => r.score), 0.01);
  resultsList.innerHTML = results.map((r, i) => `
    <div class="result-item">
      <div class="result-rank">${i + 1}</div>
      <div class="result-info">
        <div class="result-filename"> ${r.filename}</div>
        <div class="result-meta">${r.category} › ${r.subcategory}</div>
      </div>
      <div class="result-score">
        <div class="score-value">${(r.score * 100).toFixed(1)}%</div>
        <div class="score-bar-wrap">
          <div class="score-bar" style="width:${Math.round((r.score / maxScore) * 100)}%"></div>
        </div>
      </div>
    </div>
  `).join("");
}

/* ── Render case list (auto-show on subcategory select) ──────────────────── */
function renderCaseList(files, category, subcategory) {
  resultsCount.textContent = files.length;
  if (!files.length) {
    resultsList.innerHTML = '<p style="color:var(--muted)">No cases found in this subcategory.</p>';
    return;
  }
  resultsList.innerHTML = files.map((f, i) => `
    <div class="result-item">
      <div class="result-rank">${i + 1}</div>
      <div class="result-info">
        <div class="result-filename"> ${f}</div>
        <div class="result-meta">${category} › ${subcategory}</div>
      </div>
      <div class="result-score">
        <button class="btn-find-similar btn-secondary"
          style="font-size:.8rem;padding:.35rem .9rem;white-space:nowrap"
          data-filename="${f}" data-category="${category}" data-subcategory="${subcategory}">Find Similar</button>
      </div>
    </div>`).join("");

  resultsList.querySelectorAll(".btn-find-similar").forEach(btn => {
    btn.addEventListener("click", () =>
      findSimilarToFile(btn.dataset.filename, btn.dataset.category, btn.dataset.subcategory));
  });
}

/* ── Similarity search for a specific file ───────────────────────────────── */
async function findSimilarToFile(filename, category, subcategory) {
  const globalSearch = chkGlobal.checked;
  const topN = parseInt(selTopN.value, 10);
  const body = { filename, top_n: topN, global_search: globalSearch };
  if (!globalSearch) { body.category = category; body.subcategory = subcategory; }

  showSpinner(true);
  resultsCount.textContent = "";
  resultsList.innerHTML = "";

  try {
    const res = await fetch(`${API}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();

    let html = `<button class="btn-secondary" id="btn-back-list"
      style="margin-bottom:1rem;font-size:.85rem;">← Back to ${subcategory} cases</button>
      <p style="color:var(--muted);font-size:.9rem;margin-bottom:.75rem">Similar to: <strong>${filename}</strong></p>`;

    if (data.error) {
      html += `<div class="error-msg"> ${data.error}</div>`;
      resultsCount.textContent = 0;
    } else if (!data.results || !data.results.length) {
      html += `<p style="color:var(--muted)">No similar cases found.</p>`;
      resultsCount.textContent = 0;
    } else {
      const maxScore = Math.max(...data.results.map(r => r.score), 0.01);
      resultsCount.textContent = data.results.length;
      html += data.results.map((r, i) => `
        <div class="result-item">
          <div class="result-rank">${i + 1}</div>
          <div class="result-info">
            <div class="result-filename"> ${r.filename}</div>
            <div class="result-meta">${r.category} › ${r.subcategory}</div>
          </div>
          <div class="result-score">
            <div class="score-value">${(r.score * 100).toFixed(1)}%</div>
            <div class="score-bar-wrap">
              <div class="score-bar" style="width:${Math.round((r.score / maxScore) * 100)}%"></div>
            </div>
          </div>
        </div>`).join("");
    }

    resultsList.innerHTML = html;
    document.getElementById("btn-back-list").addEventListener("click", async () => {
      showSpinner(true);
      try {
        const r = await fetch(`${API}/filenames?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}`);
        const files = await r.json();
        renderCaseList(files, category, subcategory);
      } finally { showSpinner(false); }
    });
  } catch {
    resultsList.innerHTML = `<div class="error-msg"> Could not reach the API. Is the backend running?</div>`;
  } finally { showSpinner(false); }
}

/* ── Render classification result ─────────────────────────────────────────── */
function renderClassifyResult(data) {
  const legalPct = data.legal_confidence != null ? Math.round(data.legal_confidence * 100) : null;
  const confHtml = legalPct != null
    ? `<div style="margin-top:.75rem;padding:.5rem .9rem;background:#e8f5e9;border-radius:7px;font-size:.88rem;color:#2e7d32;display:inline-block;">
         Legal Document Confidence: <strong>${legalPct}%</strong>
       </div>`
    : "";
  classifyResult.innerHTML = `
    <div class="clf-prediction">
      <div>
        <div class="clf-label">Category</div>
        <div class="clf-value"> ${data.category}</div>
      </div>
      <div>
        <div class="clf-label">Subcategory</div>
        <div class="clf-value"> ${data.subcategory}</div>
      </div>
    </div>
    ${confHtml}`;
}

/* ── Subcategory descriptions ─────────────────────────────────────────────── */
const DESCRIPTIONS = {
  "Administrative"         : "Cases involving disputes between citizens and government authorities, including challenges to administrative decisions, public authority actions, and regulatory matters.",
  "Commercial"             : "Cases arising from business and trade disputes, including contracts, company law, banking, and commercial transactions between parties.",
  "Election"               : "Cases relating to electoral disputes, election petitions, validity of elections, and matters concerning the democratic process.",
  "Family Law"             : "Cases involving domestic relations such as divorce, maintenance, custody of children, and matrimonial property disputes.",
  "Labour"                 : "Cases concerning employment relationships, wrongful termination, workers' rights, trade union disputes, and labour regulations.",
  "Land Dispute"           : "Cases involving ownership, boundaries, possession, and rights over land and real property between private parties or with the state.",
  "Partition"              : "Cases where co-owners of property seek a division or sale of jointly held land or assets.",
  "Property"               : "Cases dealing with rights, ownership, transfer, and disputes over movable and immovable property.",
  "Restitutio Integrum"    : "Cases seeking restoration to the original position before an error or injustice occurred, typically filed when appeal periods have lapsed.",
  "Revision"               : "Cases where a higher court reviews the legality or regularity of proceedings of a lower court without a formal appeal.",
  "Attempted Murder"       : "Cases where the accused is charged with taking steps toward killing another person but the victim survives.",
  "Bail Application"       : "Applications made to the court by an accused person seeking release from custody pending trial.",
  "Bribery"                : "Cases involving corrupt offers, receipts, or solicitation of payments by or to public officials in exchange for favourable actions.",
  "Criminal Procedure"     : "Cases dealing with the rules and processes governing criminal investigations, trials, and administration of criminal justice.",
  "Drug Offences"          : "Cases involving the possession, trafficking, cultivation, or manufacture of controlled narcotic substances.",
  "Environmental Law"      : "Cases concerning violations of environmental regulations, illegal dumping, pollution, and destruction of natural resources.",
  "Forest Offence"         : "Cases involving illegal logging, encroachment into forest reserves, and unlawful extraction of timber or forest produce.",
  "Jurisdiction"           : "Cases raising questions about whether a particular court has the legal authority to hear and decide a matter.",
  "Kidnapping"             : "Cases involving the unlawful abduction or confinement of a person against their will.",
  "Money Laundering"       : "Cases involving the concealment or disguising of illegally obtained funds to make them appear legitimate.",
  "Murder"                 : "Cases where the accused is charged with the intentional and unlawful killing of another person.",
  "Procuration"            : "Cases involving the act of procuring or facilitating prostitution or sexual exploitation of another person.",
  "Public Property Offences": "Cases involving theft, damage, or misappropriation of property belonging to the state or public institutions.",
  "Rape"                   : "Cases involving non-consensual sexual intercourse committed by force, threat, or without the victim's consent.",
  "Revision"               : "Cases where a higher court reviews the legality or regularity of proceedings of a lower court without a formal appeal.",
  "Road Traffic Accident"  : "Cases arising from injuries, deaths, or damages caused by motor vehicle accidents on public roads.",
  "Robbery"                : "Cases involving theft accompanied by force or threat of force against the victim.",
  "Sexual Abuse"           : "Cases involving non-consensual sexual acts or exploitation, including offences against minors.",
};

/* ── Render stats ─────────────────────────────────────────────────────────── */
function renderStats(data) {
  statsGrid.innerHTML = "";
  Object.entries(data).sort().forEach(([cat, subcats]) => {
    subcats.forEach(({ subcategory, count }) => {
      const desc = DESCRIPTIONS[subcategory] || "Legal cases under this subcategory.";
      const card = document.createElement("div");
      card.className = "stat-card";
      card.innerHTML = `
        <div class="stat-cat">${cat}</div>
        <div class="stat-subcat">${subcategory}</div>
        <div class="stat-count">${count} case${count !== 1 ? "s" : ""}</div>
        <button class="btn-view-cases" data-cat="${cat}" data-sub="${subcategory}" title="View Cases">View</button>`;
      statsGrid.appendChild(card);
    });
  });

  // Event delegation for "View Cases" buttons
  statsGrid.addEventListener("click", e => {
    const btn = e.target.closest(".btn-view-cases");
    if (btn) openCaseModal(btn.dataset.cat, btn.dataset.sub);
  });
}

/* ── Modal ────────────────────────────────────────────────────────────────── */
async function openCaseModal(category, subcategory) {
  const desc = DESCRIPTIONS[subcategory] || "Legal cases under this subcategory.";

  // Build and inject modal
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div>
          <span class="modal-cat">${category}</span>
          <h2 class="modal-title">${subcategory}</h2>
        </div>
        <button class="modal-close" id="modal-close-btn"></button>
      </div>
      <div class="modal-desc">${desc}</div>
      <div class="modal-cases-wrap">
        <h3 class="modal-cases-title">Cases</h3>
        <div id="modal-cases-list"><p class="modal-loading">Loading...</p></div>
      </div>
    </div>`;
  document.body.appendChild(modal);

  // Close handlers
  modal.querySelector("#modal-close-btn").addEventListener("click", () => modal.remove());
  modal.addEventListener("click", e => { if (e.target === modal) modal.remove(); });
  document.addEventListener("keydown", function esc(e) {
    if (e.key === "Escape") { modal.remove(); document.removeEventListener("keydown", esc); }
  });

  // Fetch filenames
  try {
    const res   = await fetch(`${API}/filenames?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}`);
    const files = await res.json();
    const list  = modal.querySelector("#modal-cases-list");
    if (!files.length) {
      list.innerHTML = '<p class="modal-loading">No cases found.</p>';
    } else {
      list.innerHTML = files.map((f, i) => `
        <div class="modal-case-row">
          <span class="modal-case-num">${i + 1}</span>
          <span class="modal-case-name" style="cursor:pointer" data-filename="${f}"> ${f}</span>
        </div>`).join("");
      // Add click handler for each case name
      list.querySelectorAll('.modal-case-name').forEach(el => {
        el.addEventListener('click', () => {
          window.open(`${API}/pdf/${encodeURIComponent(el.dataset.filename)}`, '_blank');
        });
      });
    }
  } catch {
    modal.querySelector("#modal-cases-list").innerHTML = '<p class="modal-loading" style="color:#b71c1c">Failed to load cases.</p>';
  }
}

/* ── Add Case ─────────────────────────────────────────────────────────────── */
if (btnAddCase) {
  btnAddCase.addEventListener("click", async () => {
    const file = clfFile && clfFile.files[0];
    const text = clfText ? clfText.value.trim() : "";
    if (!file && !text) return;

    showSpinner(true);
    if (btnAddCase) btnAddCase.disabled = true;
    if (btnAddCase) btnAddCase.textContent = "Adding...";
    try {
      let res;
      if (file) {
        const fd = new FormData();
        fd.append("file", file);
        res = await fetch(`${API}/add_case`, { method: "POST", body: fd });
      } else {
        res = await fetch(`${API}/add_case`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });
      }
      const data = await res.json();
      if (data.success) {
        Swal.fire({ icon: 'success', title: 'Case Added', text: 'The document has been saved to the database.', timer: 2000, showConfirmButton: false });
        if (btnAddCase) btnAddCase.textContent = " Added!";
        if (btnAddCase) btnAddCase.style.background = "#2e7d32";
        if (clfFile) clfFile.value = "";
        if (clfText) clfText.value = "";
        loadCategories();
        setTimeout(() => {
          if (btnAddCase) btnAddCase.textContent = "Add Case to Database";
          if (btnAddCase) btnAddCase.style.background = "";
          if (btnAddCase) btnAddCase.disabled = false;
        }, 2000);
      } else if (data.duplicate) {
        if (btnAddCase) btnAddCase.textContent = "Duplicate";
        if (btnAddCase) btnAddCase.style.background = "#e65100";
        Swal.fire({ icon: 'warning', title: 'Duplicate Document', text: 'This document already exists in the database. Only unique documents can be added.', confirmButtonColor: '#1a3a5c' });
        setTimeout(() => {
          if (btnAddCase) btnAddCase.textContent = "Add Case to Database";
          if (btnAddCase) btnAddCase.style.background = "";
          if (btnAddCase) btnAddCase.disabled = false;
        }, 2000);
      } else {
        Swal.fire({ icon: 'error', title: 'Add Failed', text: 'Could not add the document to the database. Please try again.', confirmButtonColor: '#1a3a5c' });
        if (btnAddCase) btnAddCase.textContent = "Failed";
        if (btnAddCase) btnAddCase.style.background = "#b71c1c";
        setTimeout(() => {
          if (btnAddCase) btnAddCase.textContent = "Add Case to Database";
          if (btnAddCase) btnAddCase.style.background = "";
          if (btnAddCase) btnAddCase.disabled = false;
        }, 2000);
      }
    } catch {
      Swal.fire({ icon: 'error', title: 'Connection Error', text: 'Could not reach the API. Please ensure the server is running.', confirmButtonColor: '#1a3a5c' });
      if (btnAddCase) btnAddCase.textContent = " Error";
      if (btnAddCase) btnAddCase.style.background = "#b71c1c";
      setTimeout(() => {
        if (btnAddCase) btnAddCase.textContent = "Add Case to Database";
        if (btnAddCase) btnAddCase.style.background = "";
        if (btnAddCase) btnAddCase.disabled = false;
      }, 2000);
    } finally {
      showSpinner(false);
    }
  });
}

/* ── Backend connectivity helpers ───────────────────────────────────────── */
async function pingBackend(url) {
  try {
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), 3000);
    const res  = await fetch(url, { signal: ctrl.signal });
    clearTimeout(tid);
    return true;
  } catch { return false; }
}

function setBackendBanner(panelId, html, isError) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  let b = panel.querySelector(".backend-offline-banner");
  if (!b) {
    b = document.createElement("div");
    b.className = "backend-offline-banner";
    const insertBefore = panel.querySelector(".card, #compliance-card, #extractor-card") || panel.firstChild.nextSibling || panel.firstChild;
    panel.insertBefore(b, insertBefore);
  }
  b.style.cssText = `background:${isError?"#fdecea":"#e8f5e9"};color:${isError?"#b71c1c":"#2e7d32"};padding:.75rem 1.1rem;border-radius:8px;margin-bottom:1rem;font-size:.9rem;border:1px solid ${isError?"#f5c6c6":"#b2dfdb"};`;
  b.innerHTML = html;
}

function clearBackendBanner(panelId) {
  document.getElementById(panelId)?.querySelector(".backend-offline-banner")?.remove();
}

async function checkCmpBackend() {
  const ok = await pingBackend(`http://localhost:8000/compliance/`);
  if (!ok) {
    setBackendBanner("panel-compliance",
      " <strong>Compliance backend is offline.</strong> Run: <code>python server.py</code>",
      true);
  } else {
    clearBackendBanner("panel-compliance");
  }
}

async function checkExtBackend() {
  const ok = await pingBackend(`http://localhost:8000/extractor/`);
  if (!ok) {
    setBackendBanner("panel-extractor",
      " <strong>Case Extractor backend is offline.</strong> Run: <code>python server.py</code>",
      true);
  } else {
    clearBackendBanner("panel-extractor");
  }
}

/* ── Init ─────────────────────────────────────────────────────────────────── */
loadCategories();

/* ══════════════════════════════════════════════════════════════════════════
   COMPONENT 4 – Argument Strength Scorer  (FastAPI backend-N)
   ══════════════════════════════════════════════════════════════════════════ */

const ARG_API = "/argument/api/v1";

/* ── Backend check ───────────────────────────────────────────────────────── */
async function checkArgBackend() {
  const ok = await pingBackend(`${ARG_API}/health`);
  if (!ok) {
    setBackendBanner("panel-argument",
      " <strong>Argument Scorer backend is offline.</strong> Run: <code>python server.py</code>",
      true);
  } else {
    clearBackendBanner("panel-argument");
  }
}

/* ── Status helper ───────────────────────────────────────────────────────── */
function argStatus(html, type = "info") {
  const el = document.getElementById("arg-status");
  const bg = { info: "#e3f2fd", success: "#e8f5e9", error: "#fdecea", warn: "#fff8e1" };
  const fg = { info: "#1a3a5c", success: "#2e7d32", error: "#b71c1c", warn: "#795900" };
  el.innerHTML = `<div style="padding:.75rem 1rem;border-radius:8px;background:${bg[type]};color:${fg[type]};font-size:.9rem;">${html}</div>`;
}

/* ── Text / Document mismatch detail panel ───────────────────────────────── */
function argShowMismatchDetails(detail) {
  const el  = document.getElementById("arg-status");
  const md  = detail.mismatch_details || {};
  const overlapWords       = md.overlap_words        ?? "—";
  const overlapPct         = md.overlap_ratio_pct    ?? "—";
  const argWords           = md.argument_word_count  ?? "—";
  const docWords           = md.document_word_count  ?? "—";
  const reqWords           = md.required_overlap_words      ?? 5;
  const reqPct             = md.required_overlap_ratio_pct  ?? 10;
  const topArgWords        = (md.top_argument_words  || []).join(", ") || "—";
  const topDocWords        = (md.top_document_words  || []).join(", ") || "—";

  // Visual overlap bar (capped at 100%)
  const barPct = Math.min(100, typeof overlapPct === "number" ? overlapPct : 0);
  const barColor = barPct >= reqPct ? "#2e7d32" : "#b71c1c";

  el.innerHTML = `
    <div style="border:1px solid #f5c6c6;border-radius:10px;background:#fff8f8;padding:1rem 1.2rem;color:#1a1a1a;font-size:.9rem;">
      <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.75rem;">
        <span style="font-size:1.2rem;">⚠️</span>
        <strong style="color:#b71c1c;font-size:1rem;">Text &amp; Document Do Not Match</strong>
      </div>
      <p style="margin:0 0 .9rem;color:#555;">${detail.message}</p>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:.6rem .5rem;margin-bottom:.9rem;">
        <div style="background:#fff;border:1px solid #e0e0e0;border-radius:7px;padding:.55rem .8rem;">
          <div style="font-size:.75rem;color:#888;margin-bottom:.2rem;text-transform:uppercase;letter-spacing:.04em;">Overlapping Words</div>
          <div style="font-size:1.2rem;font-weight:700;color:${barColor};">${overlapWords}</div>
          <div style="font-size:.78rem;color:#888;">Required ≥ ${reqWords}</div>
        </div>
        <div style="background:#fff;border:1px solid #e0e0e0;border-radius:7px;padding:.55rem .8rem;">
          <div style="font-size:.75rem;color:#888;margin-bottom:.2rem;text-transform:uppercase;letter-spacing:.04em;">Overlap Ratio</div>
          <div style="font-size:1.2rem;font-weight:700;color:${barColor};">${overlapPct}%</div>
          <div style="font-size:.78rem;color:#888;">Required ≥ ${reqPct}%</div>
        </div>
        <div style="background:#fff;border:1px solid #e0e0e0;border-radius:7px;padding:.55rem .8rem;">
          <div style="font-size:.75rem;color:#888;margin-bottom:.2rem;text-transform:uppercase;letter-spacing:.04em;">Argument Words</div>
          <div style="font-size:1.15rem;font-weight:600;color:#333;">${argWords}</div>
          <div style="font-size:.78rem;color:#888;">unique content words</div>
        </div>
        <div style="background:#fff;border:1px solid #e0e0e0;border-radius:7px;padding:.55rem .8rem;">
          <div style="font-size:.75rem;color:#888;margin-bottom:.2rem;text-transform:uppercase;letter-spacing:.04em;">Document Words</div>
          <div style="font-size:1.15rem;font-weight:600;color:#333;">${docWords}</div>
          <div style="font-size:.78rem;color:#888;">unique content words</div>
        </div>
      </div>

      <!-- Overlap bar -->
      <div style="margin-bottom:.9rem;">
        <div style="font-size:.78rem;color:#777;margin-bottom:.3rem;">Overlap level</div>
        <div style="background:#e0e0e0;border-radius:4px;height:8px;overflow:hidden;">
          <div style="width:${barPct}%;height:100%;background:${barColor};border-radius:4px;transition:width .4s ease;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:.72rem;color:#aaa;margin-top:.2rem;">
          <span>0%</span><span style="color:${barColor};font-weight:600;">${overlapPct}%</span><span>100%</span>
        </div>
      </div>

      <div style="background:#fff;border:1px solid #e0e0e0;border-radius:7px;padding:.6rem .8rem;margin-bottom:.5rem;">
        <div style="font-size:.78rem;color:#888;margin-bottom:.3rem;font-weight:600;">Words only in your argument (not in document):</div>
        <div style="color:#555;font-size:.85rem;word-break:break-all;">${topArgWords}</div>
      </div>
      <div style="background:#fff;border:1px solid #e0e0e0;border-radius:7px;padding:.6rem .8rem;">
        <div style="font-size:.78rem;color:#888;margin-bottom:.3rem;font-weight:600;">Words only in the document (not in argument):</div>
        <div style="color:#555;font-size:.85rem;word-break:break-all;">${topDocWords}</div>
      </div>

      <p style="margin:.85rem 0 0;font-size:.82rem;color:#777;">
        💡 <strong>Tip:</strong> Make sure your argument text is based on or refers to the content of the uploaded document, or upload a document that corresponds to your argument.
      </p>
    </div>`;
}


function animateGauge(score) {
  const circle = document.getElementById("arg-gauge-circle");
  const numEl  = document.getElementById("arg-score-num");
  const target = 314 - (score / 100) * 314;

  // Color based on score
  let color = "#b71c1c"; // red
  if (score >= 80) color = "#2e7d32";      // green
  else if (score >= 60) color = "#1565c0"; // blue
  else if (score >= 40) color = "#ef6c00"; // orange

  circle.style.stroke = color;
  circle.style.transition = "stroke-dashoffset 1.2s ease-out";
  circle.setAttribute("stroke-dashoffset", target);

  // Animate number
  let cur = 0;
  const step = Math.max(1, Math.ceil(score / 40));
  const iv = setInterval(() => {
    cur = Math.min(cur + step, score);
    numEl.textContent = cur;
    if (cur >= score) clearInterval(iv);
  }, 25);
}

/* ── Render results ──────────────────────────────────────────────────────── */
function renderArgResults(data) {
  // Score + badge
  animateGauge(data.overall_score);

  const badge = document.getElementById("arg-strength-badge");
  badge.textContent = data.strength_label;
  badge.className = "arg-strength-badge badge-" + data.strength_label.toLowerCase().replace(/\s+/g, "-");

  // Category breakdown
  const bdEl = document.getElementById("arg-breakdown");
  bdEl.innerHTML = data.breakdown.map(c => {
    const pct = (c.points / c.weight) * 100;
    let barColor = "#b71c1c";
    if (pct >= 80) barColor = "#2e7d32";
    else if (pct >= 60) barColor = "#1565c0";
    else if (pct >= 40) barColor = "#ef6c00";

    const strengthsHtml = (c.strengths && c.strengths.length)
      ? `<div class="arg-cat-list arg-cat-strengths"><strong>Strengths:</strong><ul>${c.strengths.map(s => `<li>${s}</li>`).join("")}</ul></div>` : "";
    const gapsHtml = (c.gaps && c.gaps.length)
      ? `<div class="arg-cat-list arg-cat-gaps"><strong>Gaps:</strong><ul>${c.gaps.map(g => `<li>${g}</li>`).join("")}</ul></div>` : "";

    // Document Support Detected
    const supports = c.support_detected || [];
    const ratioLabel = c.support_ratio_label || null;
    const ratioPct = c.support_ratio_percent;
    let supportHtml = "";
    if (supports.length || ratioLabel != null) {
      const ratioBadge = ratioLabel
        ? `<span class="arg-support-badge arg-support-${ratioLabel.toLowerCase()}">${ratioLabel}${ratioPct != null ? ` (${ratioPct}%)` : ""}</span>`
        : "";
      const claimsInfo = (c.total_claims != null && c.supported_claims != null)
        ? `<span class="arg-support-claims">${c.supported_claims}/${c.total_claims} claims supported</span>`
        : "";
      const bulletList = supports.length
        ? `<ul class="arg-support-list">${supports.map(s => `<li>${s}</li>`).join("")}</ul>`
        : `<p class="arg-support-none">No document references detected</p>`;
      supportHtml = `
        <div class="arg-cat-support">
          <div class="arg-support-header">
            <strong> Document Support Detected</strong>
            ${ratioBadge}${claimsInfo}
          </div>
          ${bulletList}
        </div>`;
    } else {
      supportHtml = `
        <div class="arg-cat-support">
          <div class="arg-support-header">
            <strong> Document Support Detected</strong>
          </div>
          <p class="arg-support-none">No document references detected</p>
        </div>`;
    }

    return `
      <div class="arg-cat-card">
        <div class="arg-cat-header" onclick="this.parentElement.classList.toggle('expanded')">
          <span class="arg-cat-expand-icon">&#9654;</span>
          <span class="arg-cat-name">${c.category}</span>
          <span class="arg-cat-score">${c.points}/${c.weight}</span>
        </div>
        <div class="arg-cat-bar-track">
          <div class="arg-cat-bar-fill" style="width:${pct}%;background:${barColor}"></div>
        </div>
        <div class="arg-cat-details">
          <div class="arg-cat-rationale">${c.rationale || ""}</div>
          ${strengthsHtml}${gapsHtml}${supportHtml}
        </div>
      </div>`;
  }).join("");

  // Areas Need Attention — categories scoring below 60%
  const weakCats = data.breakdown.filter(c => (c.points / c.weight) * 100 < 60);
  const attCard = document.getElementById("arg-attention-card");
  const attEl   = document.getElementById("arg-attention");
  if (weakCats.length) {
    attCard.style.display = "block";
    attEl.innerHTML = weakCats.map(c => {
      const pct = Math.round((c.points / c.weight) * 100);
      const gapList = (c.gaps && c.gaps.length)
        ? `<ul class="arg-att-gaps">${c.gaps.map(g => `<li>${g}</li>`).join("")}</ul>`
        : "";
      const unrefs = (c.not_referenced && c.not_referenced.length)
        ? `<div class="arg-att-unrefs"><strong>Unsupported claims:</strong><ul>${c.not_referenced.map(u => `<li>${u}</li>`).join("")}</ul></div>`
        : "";
      return `
        <div class="arg-att-item">
          <div class="arg-att-header">
            <span class="arg-att-icon"></span>
            <span class="arg-att-name">${c.category}</span>
            <span class="arg-att-score" style="color:${pct < 40 ? '#b71c1c' : '#ef6c00'}">${pct}%</span>
          </div>
          <div class="arg-att-rationale">${c.rationale || ""}</div>
          ${gapList}${unrefs}
        </div>`;
    }).join("");
  } else {
    attCard.style.display = "none";
  }

  // Feedback
  const fbEl = document.getElementById("arg-feedback-list");
  fbEl.innerHTML = data.feedback.map(f => `<li>${f}</li>`).join("");

  // Evidence items (grounded analysis)
  const evidenceCard = document.getElementById("arg-evidence-card");
  const evidenceEl   = document.getElementById("arg-evidence");
  if (data.evidence && data.evidence.length) {
    evidenceCard.style.display = "block";
    evidenceEl.innerHTML = data.evidence.map(ev => `
      <div class="arg-evidence-item">
        <div class="arg-ev-header">
          <span class="arg-ev-title">${ev.title || ev.source || "Evidence"}</span>
          <span class="arg-ev-score">${Math.round((ev.score || 0) * 100)}% match</span>
        </div>
        <div class="arg-ev-excerpt">${ev.excerpt || ""}</div>
        <div class="arg-ev-meta">
          ${ev.page_estimate ? `<span>Page ~${ev.page_estimate}</span>` : ""}
          ${ev.para_estimate ? `<span>¶ ${ev.para_estimate}</span>` : ""}
          ${ev.section_estimate ? `<span>§ ${ev.section_estimate}</span>` : ""}
        </div>
      </div>
    `).join("");
  } else {
    evidenceCard.style.display = "none";
  }

  // Warning
  if (data.warning) {
    argStatus(" " + data.warning, "warn");
  }

  document.getElementById("arg-results").style.display = "block";
}

/* ── Analyze button ──────────────────────────────────────────────────────── */

/* ── Supporting document upload state ────────────────────────────────────── */
let argSupportDocId = null;
let argSupportFileName = null;

/* ── Character counter ───────────────────────────────────────────────────── */
document.getElementById("arg-text").addEventListener("input", () => {
  document.getElementById("arg-char-count").textContent =
    document.getElementById("arg-text").value.length;
});

/* ── Drag-drop zone ──────────────────────────────────────────────────────── */
(function initArgDropZone() {
  const zone  = document.getElementById("arg-drop-zone");
  const input = document.getElementById("arg-support-file");

  zone.addEventListener("click", () => input.click());
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault(); zone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; handleSupportUpload(input.files[0]); }
  });
  input.addEventListener("change", () => { if (input.files[0]) handleSupportUpload(input.files[0]); });
})();

async function handleSupportUpload(file) {
  const statusEl = document.getElementById("arg-support-status");
  const allowed = ["application/pdf", "text/plain"];
  if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|txt)$/i)) {
    statusEl.innerHTML = `<div class="arg-upload-msg error">❌ Only PDF or TXT files are supported.</div>`;
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    statusEl.innerHTML = `<div class="arg-upload-msg error">❌ File too large (max 10 MB).</div>`;
    return;
  }

  statusEl.innerHTML = `<div class="arg-upload-msg info">Uploading <strong>${file.name}</strong>…</div>`;

  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${ARG_API}/documents/upload`, { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const errorMsg = err.detail || `Upload failed (${res.status})`;
      
      // Check if it's a validation error
      if (res.status === 400) {
        statusEl.innerHTML = `<div class="arg-upload-msg error">❌ ${errorMsg}</div>`;
      } else {
        statusEl.innerHTML = `<div class="arg-upload-msg error">Upload error: ${errorMsg}</div>`;
      }
      argSupportDocId = null;
      return;
    }
    const data = await res.json();
    argSupportDocId   = data.doc_id;
    argSupportFileName = data.filename;
    statusEl.innerHTML = `<div class="arg-upload-msg success">
       ✓ <strong>${data.filename}</strong> uploaded (${(data.text_length / 1000).toFixed(1)}k chars)
      <button type="button" class="arg-remove-doc" id="btn-arg-remove-doc">&times;</button>
    </div>`;
    document.getElementById("btn-arg-remove-doc").addEventListener("click", () => {
      argSupportDocId = null; argSupportFileName = null;
      statusEl.innerHTML = "";
      document.getElementById("arg-support-file").value = "";
    });
  } catch (e) {
    statusEl.innerHTML = `<div class="arg-upload-msg error">❌ Upload error: ${e.message}</div>`;
    argSupportDocId = null;
  }
}

/* ── Analyze click ───────────────────────────────────────────────────────── */
document.getElementById("btn-arg-analyze").addEventListener("click", async () => {
  const text     = document.getElementById("arg-text").value.trim();
  const caseType = "civil"; // default case type

  if (!text) {
    Swal.fire({ icon: 'warning', title: 'Missing Input', text: 'Please enter your legal argument text before analyzing.', confirmButtonColor: '#1a3a5c' });
    return;
  }
  if (text.length < 50) {
    Swal.fire({ icon: 'warning', title: 'Text Too Short', text: 'Argument text must be at least 50 characters. Please provide more detail.', confirmButtonColor: '#1a3a5c' });
    return;
  }

  // Reset
  document.getElementById("arg-results").style.display = "none";
  document.getElementById("arg-status").innerHTML = "";
  document.getElementById("arg-spinner").style.display = "block";
  document.getElementById("btn-arg-analyze").disabled = true;

  try {
    let res;
    if (argSupportDocId) {
      // Grounded analysis with supporting document
      res = await fetch(`${ARG_API}/analyze_grounded`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          jurisdiction: "sri_lanka",
          case_type: caseType,
          doc_ids: [argSupportDocId],
          include_case_corpus: false,
          fast_mode: false
        })
      });
    } else {
      // Basic text-only analysis
      res = await fetch(`${ARG_API}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, jurisdiction: "sri_lanka", case_type: caseType })
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = err.detail;

      // Structured mismatch error — show detail panel, no score
      if (res.status === 400 && detail && typeof detail === "object" && detail.type === "text_document_mismatch") {
        argShowMismatchDetails(detail);
      } else {
        const errorMsg = (typeof detail === "string" ? detail : (detail && detail.message) || `Server error ${res.status}`);
        Swal.fire({ icon: 'error', title: 'Analysis Error', text: errorMsg, confirmButtonColor: '#1a3a5c' });
        argStatus("❌ " + errorMsg, "error");
      }
      return;
    }

    const data = await res.json();
    renderArgResults(data);
    Swal.fire({ icon: 'success', title: 'Analysis Complete', text: argSupportDocId ? 'Argument scored with supporting document.' : 'Argument scored successfully.', timer: 2000, showConfirmButton: false });
    argStatus("✓ Analysis complete." + (argSupportDocId ? " (grounded with supporting document)" : ""), "success");
  } catch (e) {
    Swal.fire({ icon: 'error', title: 'Connection Error', text: e.message, confirmButtonColor: '#1a3a5c' });
    argStatus("Error: " + e.message, "error");
  } finally {
    document.getElementById("arg-spinner").style.display = "none";
    document.getElementById("btn-arg-analyze").disabled = false;
  }
});

/* ══════════════════════════════════════════════════════════════════════════
   COMPONENT 2 – Civil Case Extractor  (FastAPI backend-P on port 8002)
   ══════════════════════════════════════════════════════════════════════════ */

const EXT_API = "/extractor/api/v1";

/* ── Tab switching for extractor ─────────────────────────────────────────── */
document.querySelectorAll("#ext-tabs .tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#ext-tabs .tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll("#panel-extractor .tab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    const target = document.getElementById(tab.dataset.etab);
    if (target) target.classList.add("active");
    if (tab.dataset.etab === "ext-documents") extLoadDocuments();
  });
});

/* ── Spinner helpers ─────────────────────────────────────────────────────── */
function extShowSpinner(msg = "Processing…") {
  document.getElementById("ext-spinner").style.display = "block";
  document.getElementById("ext-spinner-msg").textContent = msg;
}
function extHideSpinner() {
  document.getElementById("ext-spinner").style.display = "none";
}

/* ── Status message helper ───────────────────────────────────────────────── */
function extStatus(el, html, type = "info") {
  const colors = { info: "#1a3a5c", success: "#2e7d32", error: "#b71c1c", warn: "#795900" };
  el.innerHTML = `<div style="padding:.75rem 1rem;border-radius:8px;background:${type==='error'?'#fdecea':type==='success'?'#e8f5e9':'#e3f2fd'};color:${colors[type]};font-size:.9rem;">${html}</div>`;
}

/* ── Drag-drop zone for extractor ────────────────────────────────────────── */
(function initExtDropZone() {
  const zone   = document.getElementById("ext-drop-zone");
  const input  = document.getElementById("ext-file");
  const inner  = document.getElementById("ext-drop-inner");
  const prev   = document.getElementById("ext-file-preview");
  const nameEl = document.getElementById("ext-file-name");
  const sizeEl = document.getElementById("ext-file-size");
  const rmBtn  = document.getElementById("ext-file-remove");
  if (!zone) return;

  function showExtFilePreview(file) {
    nameEl.textContent = file.name;
    sizeEl.textContent = (file.size / 1024).toFixed(1) + " KB";
    inner.style.display = "none";
    prev.style.display = "flex";
  }

  zone.addEventListener("click", () => input.click());
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault(); zone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; showExtFilePreview(input.files[0]); }
  });
  input.addEventListener("change", () => { if (input.files[0]) showExtFilePreview(input.files[0]); });

  rmBtn?.addEventListener("click", e => {
    e.stopPropagation();
    input.value = "";
    inner.style.display = "";
    prev.style.display = "none";
  });
})();

/* ── Poll document until COMPLETED or FAILED ─────────────────────────────── */
async function extPollDocument(docId, statusEl) {
  const MAX_POLLS = 60; // up to 3 minutes
  const INTERVAL  = 3000;
  let polls = 0;
  return new Promise((resolve, reject) => {
    const poll = async () => {
      polls++;
      if (polls > MAX_POLLS) {
        reject(new Error("Processing timed out. Check the Documents tab for the latest status."));
        return;
      }
      try {
        const res = await fetch(`${EXT_API}/documents/${docId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const doc = await res.json();
        const status = (doc.status || "").toLowerCase();
        const elapsed = (polls * INTERVAL / 1000).toFixed(0);
        if (status === "completed") {
          resolve(doc);
        } else if (status === "failed") {
          reject(new Error(doc.error || "Extraction failed on the server."));
        } else {
          extStatus(statusEl,
            ` AI is processing your document… <span style="color:var(--muted);font-size:.82rem">(${elapsed}s — checking again in 3s)</span>`,
            "info");
          setTimeout(poll, INTERVAL);
        }
      } catch (e) { reject(e); }
    };
    setTimeout(poll, INTERVAL);
  });
}

/* ── Upload & Process ────────────────────────────────────────────────────── */
document.getElementById("btn-ext-upload")?.addEventListener("click", async () => {
  const fileInput = document.getElementById("ext-file");
  const statusEl  = document.getElementById("ext-upload-status");
  statusEl.innerHTML = "";

  if (!fileInput.files.length) {
    Swal.fire({ icon: 'warning', title: 'No File Selected', text: 'Please select or drag a PDF file first.', confirmButtonColor: '#1a3a5c' });
    return;
  }
  const file = fileInput.files[0];
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    Swal.fire({ icon: 'warning', title: 'Invalid File Type', text: 'Only PDF files are supported. Please select a .pdf file.', confirmButtonColor: '#1a3a5c' });
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    Swal.fire({ icon: 'warning', title: 'File Too Large', text: 'File exceeds the 50 MB limit. Please use a smaller file.', confirmButtonColor: '#1a3a5c' });
    return;
  }

  const btn = document.getElementById("btn-ext-upload");
  btn.disabled = true;
  extShowSpinner("Uploading PDF…");
  extStatus(statusEl, " Uploading…", "info");

  try {
    // Step 1: Upload
    const formData = new FormData();
    formData.append("file", file);
    const upRes = await fetch(`${EXT_API}/upload`, { method: "POST", body: formData });
    if (!upRes.ok) {
      const err = await upRes.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed (${upRes.status})`);
    }
    const upData = await upRes.json();
    const docId  = upData.document_id;
    extStatus(statusEl,
      ` Uploaded — ID: <code>${docId}</code><br> Starting AI extraction…`,
      "success");

    // Step 2: Trigger processing
    const procRes = await fetch(`${EXT_API}/process/${docId}`, { method: "POST" });
    if (!procRes.ok) {
      const err = await procRes.json().catch(() => ({}));
      throw new Error(err.detail || `Processing failed (${procRes.status})`);
    }
    extShowSpinner("AI is extracting metadata, sections, citations…");
    extStatus(statusEl,
      ` AI is processing your document… <span style="color:var(--muted);font-size:.82rem">(checking every 3s)</span>`,
      "info");

    // Step 3: Poll until extraction completes
    await extPollDocument(docId, statusEl);

    extStatus(statusEl,
      ` <strong>Extraction complete!</strong><br> Document ID: <code>${docId}</code>`,
      "success");
    Swal.fire({ icon: 'success', title: 'Extraction Complete', text: 'Document metadata, sections and citations have been extracted.', timer: 2500, showConfirmButton: false });

    // Auto-show output
    extShowOutputForDoc(docId);
  } catch (e) {
    Swal.fire({ icon: 'error', title: 'Extraction Failed', text: e.message, confirmButtonColor: '#1a3a5c' });
    extStatus(statusEl, ` Error: ${e.message}`, "error");
  } finally {
    extHideSpinner();
    btn.disabled = false;
  }
});

/* ── Load document list ──────────────────────────────────────────────────── */
async function extLoadDocuments() {
  const listEl = document.getElementById("ext-doc-list");
  document.getElementById("ext-doc-detail").style.display = "none";
  listEl.innerHTML = "<p style='color:var(--muted)'>Loading…</p>";
  extShowSpinner("Fetching documents…");
  try {
    const res  = await fetch(`${EXT_API}/documents`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const docs = data.documents || data;
    if (!docs.length) {
      listEl.innerHTML = "<p style='color:var(--muted)'>No documents yet. Upload a PDF first.</p>";
      return;
    }

    const statusColor = s => s === "completed" ? "#2e7d32" : s === "processing" ? "#3949ab" : s === "failed" ? "#b71c1c" : "#1a3a5c";
    const statusBg    = s => s === "completed" ? "#e8f5e9"  : s === "processing" ? "#e8eaf6"  : s === "failed" ? "#fdecea"  : "#e3f2fd";
    const statusIcon  = s => s === "completed" ? "&#10003;" : s === "processing" ? "&#9679;"  : s === "failed" ? "&#10007;" : "&#8226;";
    const borderColor = s => s === "completed" ? "#2e7d32"  : s === "processing" ? "#3949ab"  : s === "failed" ? "#b71c1c"  : "#1a3a5c";

    listEl.innerHTML = `<div class="ext-doc-grid">${docs.map(d => {
      const st = (d.status || "").toLowerCase();
      return `
      <div class="ext-doc-card" data-doc-id="${d.document_id}" style="border-left:4px solid ${borderColor(st)}">
        <div class="ext-doc-card-header">
          <span class="ext-doc-card-icon">&#128196;</span>
          <span class="ext-doc-card-badge" style="background:${statusBg(st)};color:${statusColor(st)}">${statusIcon(st)} ${d.status || "unknown"}</span>
        </div>
        <div class="ext-doc-card-title" title="${d.filename || d.document_id}">${d.filename || d.document_id}</div>
        <div class="ext-doc-card-meta">
          ${d.case_number  ? `<div class="ext-doc-meta-row"><span class="ext-doc-meta-lbl">Case No</span><span>${d.case_number}</span></div>` : ""}
          ${d.court        ? `<div class="ext-doc-meta-row"><span class="ext-doc-meta-lbl">Court</span><span>${d.court}</span></div>` : ""}
          ${d.date         ? `<div class="ext-doc-meta-row"><span class="ext-doc-meta-lbl">Date</span><span>${d.date}</span></div>` : ""}
          ${d.parties_count  ? `<div class="ext-doc-meta-row"><span class="ext-doc-meta-lbl">Parties</span><span>${d.parties_count}</span></div>` : ""}
          ${d.sections_count ? `<div class="ext-doc-meta-row"><span class="ext-doc-meta-lbl">Sections</span><span>${d.sections_count}</span></div>` : ""}
        </div>
        <div class="ext-doc-card-footer">
          <button class="ext-doc-view-btn" data-doc-id="${d.document_id}">View Details &#8594;</button>
        </div>
      </div>`;
    }).join("")}</div>`;

    // View button + card click
    listEl.querySelectorAll(".ext-doc-view-btn").forEach(btn => {
      btn.addEventListener("click", e => { e.stopPropagation(); extViewDocument(btn.dataset.docId); });
    });
    listEl.querySelectorAll(".ext-doc-card[data-doc-id]").forEach(card => {
      card.addEventListener("click", () => extViewDocument(card.dataset.docId));
    });
  } catch (e) {
    listEl.innerHTML = `<p style='color:#b71c1c'>Error loading documents: ${e.message}</p>`;
    Swal.fire({ icon: 'error', title: 'Load Failed', text: 'Could not load the document list. ' + e.message, confirmButtonColor: '#1a3a5c' });
  } finally {
    extHideSpinner();
  }
}

document.getElementById("btn-ext-refresh")?.addEventListener("click", extLoadDocuments);

/* ══════════════════════════════════════════════════════════════════════════
   BULK UPLOAD
   ══════════════════════════════════════════════════════════════════════════ */
(function initExtBulk() {
  const bulkDrop      = document.getElementById("ext-bulk-drop");
  const bulkInput     = document.getElementById("ext-bulk-input");
  const fileListEl    = document.getElementById("ext-bulk-file-list");
  const progressEl    = document.getElementById("ext-bulk-progress");
  const btnStart      = document.getElementById("btn-ext-bulk-start");
  const btnClear      = document.getElementById("btn-ext-bulk-clear");
  if (!bulkDrop) return;

  let bulkFiles = []; // { file, rowId }

  /* ── Drag-drop zone ───────────────────────────────────────────────────── */
  bulkDrop.addEventListener("click", () => bulkInput.click());
  bulkDrop.addEventListener("dragover",  e => { e.preventDefault(); bulkDrop.classList.add("drag-over"); });
  bulkDrop.addEventListener("dragleave", () => bulkDrop.classList.remove("drag-over"));
  bulkDrop.addEventListener("drop", e => {
    e.preventDefault(); bulkDrop.classList.remove("drag-over");
    addFiles(Array.from(e.dataTransfer.files));
  });
  bulkInput.addEventListener("change", function () {
    addFiles(Array.from(this.files));
    this.value = "";
  });

  /* ── Add files to queue ───────────────────────────────────────────────── */
  function addFiles(newFiles) {
    const valid = newFiles.filter(f => {
      if (!f.name.toLowerCase().endsWith(".pdf")) return false;
      if (f.size > 50 * 1024 * 1024) return false;
      // avoid exact duplicates
      return !bulkFiles.some(b => b.file.name === f.name && b.file.size === f.size);
    });
    valid.forEach(f => bulkFiles.push({ file: f, rowId: "br_" + Date.now() + "_" + Math.random().toString(36).slice(2) }));
    renderQueue();
  }

  /* ── Render queue rows ────────────────────────────────────────────────── */
  function renderQueue() {
    if (!bulkFiles.length) {
      fileListEl.innerHTML = "";
      btnStart.disabled = true;
      return;
    }
    fileListEl.innerHTML = bulkFiles.map(b => `
      <div class="ext-bulk-file-row" id="${b.rowId}">
        <span class="ext-bulk-file-icon">&#128196;</span>
        <span class="ext-bulk-file-name" title="${b.file.name}">${b.file.name}</span>
        <span class="ext-bulk-file-size">${(b.file.size / 1024).toFixed(1)} KB</span>
        <span class="ext-bulk-file-status queued" id="${b.rowId}_st">Queued</span>
        <button class="ext-bulk-remove" data-row="${b.rowId}" title="Remove">&#10005;</button>
      </div>
    `).join("");

    // Remove buttons
    fileListEl.querySelectorAll(".ext-bulk-remove").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        bulkFiles = bulkFiles.filter(b => b.rowId !== btn.dataset.row);
        renderQueue();
      });
    });
    btnStart.disabled = false;
  }

  /* ── Clear all ────────────────────────────────────────────────────────── */
  btnClear?.addEventListener("click", () => {
    bulkFiles = [];
    renderQueue();
    progressEl.innerHTML = "";
  });

  /* ── Progress UI helpers ──────────────────────────────────────────────── */
  let historyCards = []; // accumulates result cards

  function renderProgress(done, failed, total) {
    const pct = total ? Math.round((done + failed) / total * 100) : 0;
    const existing = document.getElementById("ext-bulk-prog-wrap");
    const html = `
      <div class="ext-bulk-progress-wrap" id="ext-bulk-prog-wrap">
        <div class="ext-bulk-progress-header">
          <span>Bulk Extraction Progress</span>
          <span>${done + failed} / ${total} (${pct}%)</span>
        </div>
        <div class="ext-bulk-bar-track"><div class="ext-bulk-bar-fill" style="width:${pct}%"></div></div>
        <div class="ext-bulk-counters">
          <div>Completed: <span class="c-done">${done}</span></div>
          <div>Failed: <span class="c-err">${failed}</span></div>
          <div>Remaining: <span class="c-left">${Math.max(0, total - done - failed)}</span></div>
        </div>
        <div class="ext-bulk-history-grid" id="ext-bulk-hist-grid">${historyCards.join("")}</div>
      </div>`;
    if (existing) {
      existing.outerHTML = html;
    } else {
      progressEl.innerHTML = html;
    }
  }

  function setRowStatus(rowId, label, cls) {
    const st = document.getElementById(rowId + "_st");
    if (!st) return;
    st.textContent = label;
    st.className = "ext-bulk-file-status " + cls;
  }

  function appendHistCard(b, docId, doc, errMsg) {
    const ok = !!docId && !errMsg;
    const badgeCls = ok ? "done" : "error";
    const cardCls  = ok ? "status-done" : "status-error";
    const meta = ok ? [
      doc.case_number ? `<div>&#9654; Case No: <strong>${doc.case_number}</strong></div>` : "",
      doc.court  ? `<div>&#9654; Court: ${doc.court}</div>` : "",
      doc.date   ? `<div>&#9654; Date: ${doc.date}</div>` : "",
      doc.parties_count  ? `<div>&#9654; Parties: ${doc.parties_count}</div>` : "",
      doc.sections_count ? `<div>&#9654; Sections: ${doc.sections_count}</div>` : "",
    ].filter(Boolean).join("") : `<div style="color:#b71c1c">&#9888; ${errMsg}</div>`;

    historyCards.push(`
      <div class="ext-bulk-hist-card ${cardCls}" ${ok ? `data-bulk-doc="${docId}"` : ""}>
        <div class="ext-bulk-hist-title" title="${b.file.name}">${b.file.name}</div>
        <div class="ext-bulk-hist-meta">${meta || '<span style="color:var(--muted)">No metadata extracted</span>'}</div>
        <div class="ext-bulk-hist-footer">
          <span class="ext-bulk-hist-badge ${badgeCls}">${ok ? "&#10003; Completed" : "&#10007; Failed"}</span>
          ${ok ? `<button class="ext-bulk-hist-view" data-bulk-view="${docId}">View Details</button>` : ""}
        </div>
      </div>
    `);
  }

  /* ── Process a single file ────────────────────────────────────────────── */
  async function processBulkFile(b, doneRef, failedRef, total) {
    setRowStatus(b.rowId, "Uploading…", "uploading");
    let docId = null;
    try {
      // Upload
      const fd = new FormData();
      fd.append("file", b.file);
      const upRes = await fetch(`${EXT_API}/upload`, { method: "POST", body: fd });
      if (!upRes.ok) {
        const err = await upRes.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed (${upRes.status})`);
      }
      const upData = await upRes.json();
      docId = upData.document_id;

      // Trigger processing
      setRowStatus(b.rowId, "Processing…", "processing");
      const procRes = await fetch(`${EXT_API}/process/${docId}`, { method: "POST" });
      if (!procRes.ok) {
        const err = await procRes.json().catch(() => ({}));
        throw new Error(err.detail || `Process trigger failed (${procRes.status})`);
      }

      // Poll
      const dummyEl = document.createElement("div");
      const doc = await extPollDocument(docId, dummyEl);

      setRowStatus(b.rowId, "Done", "done");
      doneRef.v++;
      appendHistCard(b, docId, doc, null);
    } catch (e) {
      setRowStatus(b.rowId, "Error", "error");
      failedRef.v++;
      appendHistCard(b, docId, null, e.message);
    }
    renderProgress(doneRef.v, failedRef.v, total);

    // Attach view listeners on newly rendered cards
    document.querySelectorAll("[data-bulk-view]").forEach(btn => {
      if (!btn._bulkViewBound) {
        btn._bulkViewBound = true;
        btn.addEventListener("click", e => {
          e.stopPropagation();
          extViewDocument(btn.dataset.bulkView);
        });
      }
    });
    document.querySelectorAll("[data-bulk-doc]").forEach(card => {
      if (!card._bulkCardBound) {
        card._bulkCardBound = true;
        card.addEventListener("click", () => extViewDocument(card.dataset.bulkDoc));
      }
    });
  }

  /* ── Start bulk extraction ────────────────────────────────────────────── */
  btnStart?.addEventListener("click", async () => {
    if (!bulkFiles.length) {
      Swal.fire({ icon: "warning", title: "No Files Selected", text: "Add at least one PDF before starting.", confirmButtonColor: "#1a3a5c" });
      return;
    }
    const total = bulkFiles.length;
    const doneRef   = { v: 0 };
    const failedRef = { v: 0 };
    historyCards = [];

    btnStart.disabled = true;
    btnClear.disabled = true;
    bulkDrop.style.pointerEvents = "none";
    bulkDrop.style.opacity = "0.55";

    renderProgress(0, 0, total);

    for (const b of bulkFiles) {
      await processBulkFile(b, doneRef, failedRef, total);
    }

    btnStart.disabled = false;
    btnClear.disabled = false;
    bulkDrop.style.pointerEvents = "";
    bulkDrop.style.opacity = "";

    Swal.fire({
      icon: doneRef.v === total ? "success" : (failedRef.v === total ? "error" : "info"),
      title: "Bulk Extraction Complete",
      html: `<strong>${doneRef.v}</strong> succeeded &nbsp;&bull;&nbsp; <strong>${failedRef.v}</strong> failed out of <strong>${total}</strong> file${total !== 1 ? "s" : ""}.`,
      confirmButtonColor: "#1a3a5c",
      timer: 4000,
      timerProgressBar: true
    });
  });
})();


document.querySelectorAll("#ext-out-tabs .ext-otab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#ext-out-tabs .ext-otab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".ext-otab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    const target = document.getElementById(tab.dataset.otab);
    if (target) target.classList.add("active");
  });
});

/* ── Populate document dropdown ──────────────────────────────────────────── */
async function extPopulateOutputDropdown() {
  const sel = document.getElementById("ext-output-doc");
  try {
    const res  = await fetch(`${EXT_API}/documents`);
    if (!res.ok) return;
    const data = await res.json();
    const docs = data.documents || data;
    sel.innerHTML = docs.map(d => {
      const label = d.filename || d.document_id;
      const caseNo = d.case_number ? ` (${d.case_number})` : "";
      return `<option value="${d.document_id}">${label}${caseNo}</option>`;
    }).join("");
  } catch (_) {
    sel.innerHTML = `<option value="">No documents</option>`;
  }
}

/* ── View document & show output ─────────────────────────────────────────── */
async function extViewDocument(docId) {
  extShowSpinner("Loading case details…");
  const outputEl = document.getElementById("ext-output");

  try {
    const res = await fetch(`${EXT_API}/documents/${docId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const doc = await res.json();

    // Store full doc for JSON export
    window._extCurrentDoc = doc;

    const meta = doc.metadata || {};
    const secs = doc.sections || [];
    const out  = doc.outcome  || {};
    const ins  = doc.insights || {};
    const cits = doc.citations|| [];
    const tl   = doc.timeline || [];
    const conf = doc.confidence_scores || {};

    // Show output section
    outputEl.style.display = "block";

    // Populate dropdown and select current doc
    await extPopulateOutputDropdown();
    const sel = document.getElementById("ext-output-doc");
    sel.value = docId;

    // ── Status badges ────────────────────────────────────
    const statusBar    = document.getElementById("ext-status-bar");
    const statusLabel  = document.getElementById("ext-status-label");
    const badgesEl     = document.getElementById("ext-status-badges");
    statusBar.style.display = "flex";

    const badges = [];
    if (out.classification)       badges.push(`Outcome`);
    if (tl.length)                badges.push(`Timeline (${tl.length} events)`);
    if (cits.length)              badges.push(`Citations (${cits.length})`);
    if (ins.key_legal_issues?.length || ins.doctrines?.length) badges.push(`Insights`);
    if (secs.length)              badges.push(`Sections (${secs.length})`);

    const totalFields = 5;
    const extracted = badges.length;
    if (extracted >= totalFields) {
      statusLabel.innerHTML = " <strong>All fields extracted</strong>";
    } else {
      statusLabel.innerHTML = ` <strong>${extracted}/${totalFields} fields extracted</strong>`;
    }
    badgesEl.innerHTML = badges.map(b =>
      `<span class="ext-badge-pill"> ${b}</span>`
    ).join("");

    // ── TAB: Metadata ────────────────────────────────────
    document.getElementById("eot-metadata").innerHTML = `
      <h3 class="ext-section-title"> Case Information</h3>
      <div class="ext-info-grid">
        ${extInfoCard("CASE NUMBER", meta.case_number)}
        ${extInfoCard("COURT", meta.court)}
        ${extInfoCard("DATE", meta.date)}
        ${extInfoCard("YEAR", meta.year)}
        ${extInfoCard("CASE TYPE", meta.case_type)}
      </div>
      ${meta.judges?.length ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Judges</h3>
      <div class="ext-info-grid">${meta.judges.map(j => extInfoCard("JUDGE", j)).join("")}</div>` : ""}
      ${meta.parties?.length ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Parties</h3>
      <div class="ext-info-grid">${meta.parties.map((p, i) => extInfoCard(i === 0 ? "PETITIONER/PLAINTIFF" : "RESPONDENT/DEFENDANT", p)).join("")}</div>` : ""}
      ${meta.petitioners?.length ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Petitioners</h3>
      <div class="ext-tag-list">${meta.petitioners.map(p => `<span class="ext-tag">${p}</span>`).join("")}</div>` : ""}
      ${meta.respondents?.length ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Respondents</h3>
      <div class="ext-tag-list">${meta.respondents.map(r => `<span class="ext-tag">${r}</span>`).join("")}</div>` : ""}
      ${meta.legal_provisions?.length ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Legal Provisions</h3>
      <div class="ext-tag-list">${meta.legal_provisions.map(l => `<span class="ext-tag">${l}</span>`).join("")}</div>` : ""}
    `;

    // ── TAB: Outcome ─────────────────────────────────────
    const outcomeClass = (out.classification || "").toLowerCase();
    const outColor = outcomeClass.includes("allowed") && !outcomeClass.includes("partially") ? "#2e7d32"
                   : outcomeClass.includes("dismiss") ? "#b71c1c" : "#ef6c00";
    document.getElementById("eot-outcome").innerHTML = out.classification ? `
      <div class="ext-outcome-card" style="border-left:4px solid ${outColor}">
        <div class="ext-outcome-badge" style="background:${outColor}">${out.classification}</div>
        ${out.confidence != null ? `<p style="margin-top:.5rem;font-size:.88rem;color:var(--muted)">Confidence: <strong>${out.confidence}%</strong></p>` : ""}
        ${out.explanation ? `<p style="margin-top:.6rem;font-size:.9rem;line-height:1.6">${out.explanation}</p>` : ""}
      </div>
    ` : `<p class="ext-empty">No outcome data available.</p>`;

    // ── TAB: Sections ────────────────────────────────────
    const userNotes = doc.user_notes || {};
    document.getElementById("eot-sections").innerHTML = secs.length ? `
      <h3 class="ext-section-title"> Sections (${secs.length})</h3>
      ${secs.map((s, i) => {
        const secId = `sec-${i + 1}`;
        const hasNote = userNotes[secId] && userNotes[secId].trim();
        return `
        <details class="ext-section-block">
          <summary>
            <span class="ext-sec-num">${s.section_number || (i + 1)}</span>
            <span class="ext-sec-title">${s.title || "Untitled"}</span>
            ${hasNote ? `<span class="ext-sec-note-badge" title="Has note"></span>` : ""}
            ${s.page_start ? `<span class="ext-sec-page">p.${s.page_start}</span>` : ""}
          </summary>
          <div class="ext-sec-body">${(s.content || s.text || "No content").replace(/\n/g, "<br>")}</div>
          ${s.clauses?.length ? `<div class="ext-clauses"><strong>Clauses:</strong><ul>${s.clauses.map(cl => `<li><strong>${cl.clause_number || ""}:</strong> ${cl.text || ""}</li>`).join("")}</ul></div>` : ""}
        </details>
      `}).join("")}
    ` : `<p class="ext-empty">No sections extracted.</p>`;

    // ── TAB: Timeline ────────────────────────────────────
    document.getElementById("eot-timeline").innerHTML = tl.length ? `
      <h3 class="ext-section-title"> Timeline (${tl.length} events)</h3>
      <div class="ext-timeline">
        ${tl.map(ev => `
          <div class="ext-tl-item">
            <div class="ext-tl-dot"></div>
            <div class="ext-tl-content">
              <div class="ext-tl-date">${ev.date || "Unknown"}</div>
              <div class="ext-tl-name">${ev.event_name || ""}</div>
              ${ev.description ? `<div class="ext-tl-desc">${ev.description}</div>` : ""}
              ${ev.event_type ? `<span class="ext-tl-type">${ev.event_type}</span>` : ""}
            </div>
          </div>
        `).join("")}
      </div>
    ` : `<p class="ext-empty">No timeline events extracted.</p>`;

    // ── TAB: Citations ───────────────────────────────────
    document.getElementById("eot-citations").innerHTML = cits.length ? `
      <h3 class="ext-section-title"> Citations (${cits.length})</h3>
      <div class="ext-cit-list">
        ${cits.map(c => {
          if (typeof c === "string") return `<div class="ext-cit-card"><p>${c}</p></div>`;
          return `<div class="ext-cit-card">
            ${c.case_name ? `<div class="ext-cit-name">${c.case_name}</div>` : ""}
            <div class="ext-cit-meta">
              ${c.year ? `<span>Year: ${c.year}</span>` : ""}
              ${c.source ? `<span>Source: ${c.source}</span>` : ""}
              ${c.usage ? `<span class="ext-cit-usage">${c.usage}</span>` : ""}
            </div>
          </div>`;
        }).join("")}
      </div>
    ` : `<p class="ext-empty">No citations extracted.</p>`;

    // ── TAB: Insights ────────────────────────────────────
    const hasInsights = ins.key_legal_issues?.length || ins.doctrines?.length || ins.reliefs_requested || ins.risk_level;
    document.getElementById("eot-insights").innerHTML = hasInsights ? `
      ${ins.key_legal_issues?.length ? `
      <h3 class="ext-section-title"> Key Legal Issues</h3>
      <div class="ext-tag-list">${ins.key_legal_issues.map(i => `<span class="ext-tag">${i}</span>`).join("")}</div>` : ""}
      ${ins.doctrines?.length ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Legal Doctrines</h3>
      <div class="ext-tag-list">${ins.doctrines.map(d => `<span class="ext-tag">${d}</span>`).join("")}</div>` : ""}
      ${ins.reliefs_requested ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Reliefs Requested</h3>
      <p style="font-size:.9rem;line-height:1.6">${ins.reliefs_requested}</p>` : ""}
      ${ins.reliefs_granted ? `
      <h3 class="ext-section-title" style="margin-top:1.25rem"> Reliefs Granted</h3>
      <p style="font-size:.9rem;line-height:1.6">${ins.reliefs_granted}</p>` : ""}
      ${ins.risk_level ? `
      <div class="ext-info-grid" style="margin-top:1.25rem">
        ${extInfoCard("RISK LEVEL", ins.risk_level)}
        ${extInfoCard("STATE INVOLVEMENT", ins.state_involvement ? "Yes" : "No")}
        ${ins.state_involvement_level ? extInfoCard("INVOLVEMENT LEVEL", ins.state_involvement_level) : ""}
      </div>` : ""}
    ` : `<p class="ext-empty">No insights extracted.</p>`;

    // ── TAB: Notes ───────────────────────────────────────
    const notesHtml = secs.length ? `
      <h3 class="ext-section-title"> Notes by Section</h3>
      <p style="font-size:.88rem;color:var(--muted);margin-bottom:1rem;">Add notes for each section. Notes are saved automatically.</p>
      ${secs.map((s, i) => {
        const secId = `sec-${i + 1}`;
        const noteText = userNotes[secId] || "";
        return `
        <div class="ext-note-block">
          <div class="ext-note-header">
            <span class="ext-sec-num">${s.section_number || (i + 1)}</span>
            <span class="ext-sec-title">${s.title || "Untitled"}</span>
          </div>
          <textarea class="ext-note-textarea" data-section-id="${secId}" data-doc-id="${doc.document_id}" placeholder="Add notes for this section...">${noteText}</textarea>
        </div>
      `}).join("")}
    ` : `<p class="ext-empty">No sections available for notes.</p>`;
    document.getElementById("eot-notes").innerHTML = notesHtml;

    // Attach save handlers to all note textareas
    document.querySelectorAll(".ext-note-textarea").forEach(textarea => {
      let saveTimeout;
      textarea.addEventListener("input", () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(async () => {
          const docId = textarea.dataset.docId;
          const sectionId = textarea.dataset.sectionId;
          const noteText = textarea.value;
          try {
            const allNotes = {};
            document.querySelectorAll(".ext-note-textarea").forEach(ta => {
              if (ta.value.trim()) {
                allNotes[ta.dataset.sectionId] = ta.value;
              }
            });
            await fetch(`${EXT_API}/documents/${docId}/notes`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ notes: allNotes })
            });
            textarea.style.borderColor = "#2e7d32";
            setTimeout(() => { textarea.style.borderColor = ""; }, 1000);
          } catch (e) {
            console.error("Failed to save note:", e);
            textarea.style.borderColor = "#b71c1c";
          }
        }, 800);
      });
    });

    // ── TAB: Confidence ──────────────────────────────────
    const hasConf = conf.outcome != null || conf.sections != null || conf.citations != null || conf.insights != null;
    document.getElementById("eot-confidence").innerHTML = hasConf ? `
      <h3 class="ext-section-title"> Confidence Scores</h3>
      <div class="ext-conf-grid">
        ${extConfBar("Outcome", conf.outcome)}
        ${extConfBar("Sections", conf.sections)}
        ${extConfBar("Citations", conf.citations)}
        ${extConfBar("Insights", conf.insights)}
      </div>
    ` : `<p class="ext-empty">No confidence scores available.</p>`;

    // ── TAB: Raw Text ────────────────────────────────────
    document.getElementById("eot-rawtext").innerHTML = doc.raw_text
      ? `<pre class="ext-raw-text">${doc.raw_text}</pre>`
      : `<p class="ext-empty">Raw text not available.</p>`;

    // ── TAB: JSON Export ─────────────────────────────────
    document.getElementById("eot-json").innerHTML = `
      <div style="display:flex;justify-content:flex-end;margin-bottom:.75rem">
        <button class="btn-secondary" id="btn-ext-copy-json" style="font-size:.82rem">Copy JSON</button>
        <button class="btn-secondary" id="btn-ext-download-json" style="font-size:.82rem;margin-left:.5rem">Download</button>
      </div>
      <pre class="ext-raw-text" style="max-height:500px">${JSON.stringify(doc, null, 2)}</pre>
    `;
    document.getElementById("btn-ext-copy-json")?.addEventListener("click", () => {
      navigator.clipboard.writeText(JSON.stringify(doc, null, 2));
      document.getElementById("btn-ext-copy-json").textContent = "Copied!";
      setTimeout(() => document.getElementById("btn-ext-copy-json").textContent = "Copy JSON", 1500);
    });
    document.getElementById("btn-ext-download-json")?.addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(doc, null, 2)], { type: "application/json" });
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
      a.download = `${meta.case_number || docId}.json`; a.click();
    });

    // Reset to Metadata tab
    document.querySelectorAll("#ext-out-tabs .ext-otab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".ext-otab-content").forEach(c => c.classList.remove("active"));
    document.querySelector("[data-otab='eot-metadata']").classList.add("active");
    document.getElementById("eot-metadata").classList.add("active");

    outputEl.scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    document.getElementById("eot-metadata").innerHTML = `<p style='color:#b71c1c'> ${e.message}</p>`;
    outputEl.style.display = "block";
  } finally {
    extHideSpinner();
  }
}

/* ── Helper: info card ───────────────────────────────────────────────────── */
function extInfoCard(label, value) {
  if (!value && value !== 0) return "";
  return `<div class="ext-info-card"><div class="ext-info-label">${label}</div><div class="ext-info-value">${value}</div></div>`;
}

/* ── Helper: confidence bar ──────────────────────────────────────────────── */
function extConfBar(label, score) {
  if (score == null) return "";
  const color = score >= 80 ? "#2e7d32" : score >= 50 ? "#1565c0" : score >= 30 ? "#ef6c00" : "#b71c1c";
  return `<div class="ext-conf-item">
    <div class="ext-conf-label">${label}</div>
    <div class="ext-conf-track"><div class="ext-conf-fill" style="width:${score}%;background:${color}"></div></div>
    <div class="ext-conf-pct" style="color:${color}">${score}%</div>
  </div>`;
}

/* ── View Output button & after-upload trigger ───────────────────────────── */
document.getElementById("btn-ext-view-output")?.addEventListener("click", () => {
  const docId = document.getElementById("ext-output-doc").value;
  if (docId) extViewDocument(docId);
});

/* ── After upload success → show output ──────────────────────────────────── */
function extShowOutputForDoc(docId) {
  document.getElementById("ext-output").style.display = "block";
  extViewDocument(docId);
}

/* ── Search ──────────────────────────────────────────────────────────────── */
document.getElementById("btn-ext-search")?.addEventListener("click", async () => {
  const query   = document.getElementById("ext-search-input").value.trim();
  const outcome = document.getElementById("ext-search-outcome").value;
  const yrFrom  = document.getElementById("ext-search-year-from").value;
  const yrTo    = document.getElementById("ext-search-year-to").value;
  const k       = parseInt(document.getElementById("ext-search-k").value);
  const resultsEl = document.getElementById("ext-search-results");

  if (!query) { Swal.fire({ icon: 'warning', title: 'Empty Search', text: 'Please enter a search query before searching.', confirmButtonColor: '#1a3a5c' }); return; }

  extShowSpinner("Searching…");
  resultsEl.innerHTML = "";

  try {
    const body = {
      query,
      k,
      filters: {
        ...(outcome  ? { outcome }              : {}),
        ...(yrFrom   ? { year_from: +yrFrom }   : {}),
        ...(yrTo     ? { year_to:   +yrTo }     : {}),
      }
    };
    const res  = await fetch(`${EXT_API}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const hits = data.results || [];

    if (!hits.length) {
      extStatus(resultsEl, "No matching cases found.", "info");
      return;
    }

    resultsEl.innerHTML = hits.map((h, i) => `
      <div class="result-card" style="padding:1rem;margin-bottom:.75rem;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:.5rem">
          <strong>${i+1}. ${h.filename || h.document_id}</strong>
          <span style="font-size:.8rem;white-space:nowrap;color:var(--muted)">Score: ${(h.final_score||0).toFixed(1)}%</span>
        </div>
        ${h.case_number ? `<div style="font-size:.82rem;color:var(--muted)">${h.case_number}</div>` : ""}
        ${h.court ? `<div style="font-size:.82rem;color:var(--muted)"> ${h.court} ${h.year?`(${h.year})`:""}</div>` : ""}
        ${h.outcome ? `<div style="font-size:.82rem"><strong>Outcome:</strong> ${h.outcome}</div>` : ""}
        ${h.risk_level ? `<div style="font-size:.82rem"><strong>Risk:</strong> ${h.risk_level}</div>` : ""}
        ${h.key_legal_issues?.length ? `<div style="font-size:.82rem;margin-top:.3rem"><strong>Issues:</strong> ${h.key_legal_issues.join(", ")}</div>` : ""}
        ${h.reasoning_summary ? `<div style="font-size:.82rem;margin-top:.3rem;color:var(--muted)">${h.reasoning_summary.slice(0,200)}…</div>` : ""}
      </div>
    `).join("");
  } catch (e) {
    Swal.fire({ icon: 'error', title: 'Search Failed', text: e.message, confirmButtonColor: '#1a3a5c' });
    extStatus(resultsEl, ` Search error: ${e.message}`, "error");
  } finally {
    extHideSpinner();
  }
});

/* ══════════════════════════════════════════════════════════════════════════
   COMPONENT 3 – Civil Compliance Checker  (FastAPI backend-C on port 8001)
   ══════════════════════════════════════════════════════════════════════════ */

const CMP_API = "/compliance";

/* ── Tab switching for compliance ───────────────────────────────────────── */
document.querySelectorAll("#cmp-tabs .tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#cmp-tabs .tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll("#panel-compliance .tab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    const target = document.getElementById(tab.dataset.ctab);
    if (target) target.classList.add("active");
    if (tab.dataset.ctab === "cmp-history") cmpLoadHistory();
  });
});

/* ── Input tab switching (Upload File / Paste Text) ──────────────────────── */
document.getElementById("cmp-itab-file")?.addEventListener("click", () => {
  document.getElementById("cmp-itab-file").classList.add("active");
  document.getElementById("cmp-itab-text").classList.remove("active");
  document.getElementById("cmp-panel-file").classList.add("active");
  document.getElementById("cmp-panel-text").classList.remove("active");
});
document.getElementById("cmp-itab-text")?.addEventListener("click", () => {
  document.getElementById("cmp-itab-text").classList.add("active");
  document.getElementById("cmp-itab-file").classList.remove("active");
  document.getElementById("cmp-panel-text").classList.add("active");
  document.getElementById("cmp-panel-file").classList.remove("active");
});

/* ── Drag-drop zone ──────────────────────────────────────────────────────── */
(function initCmpDropZone() {
  const zone   = document.getElementById("cmp-drop-zone");
  const input  = document.getElementById("cmp-pdf");
  const inner  = document.getElementById("cmp-drop-inner");
  const prev   = document.getElementById("cmp-file-preview");
  const nameEl = document.getElementById("cmp-file-name");
  const sizeEl = document.getElementById("cmp-file-size");
  const rmBtn  = document.getElementById("cmp-file-remove");
  if (!zone) return;

  zone.addEventListener("click", () => input.click());
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault(); zone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; showFilePreview(input.files[0]); }
  });
  input.addEventListener("change", () => { if (input.files[0]) showFilePreview(input.files[0]); });

  function showFilePreview(file) {
    nameEl.textContent = file.name;
    sizeEl.textContent = (file.size / 1024).toFixed(1) + " KB";
    inner.style.display = "none";
    prev.style.display = "flex";
  }
  rmBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    input.value = "";
    inner.style.display = "";
    prev.style.display = "none";
  });
})();

/* ── Spinner helpers ─────────────────────────────────────────────────────── */
function cmpShowSpinner(msg = "Checking compliance…") {
  document.getElementById("cmp-spinner").style.display = "block";
  document.getElementById("cmp-spinner-msg").textContent = msg;
}
function cmpHideSpinner() { document.getElementById("cmp-spinner").style.display = "none"; }

function cmpStatus(el, html, type = "info") {
  const bg = { info: "#e3f2fd", success: "#e8f5e9", error: "#fdecea", warn: "#fff8e1" };
  const fg = { info: "#1a3a5c", success: "#2e7d32", error: "#b71c1c", warn: "#795900" };
  el.innerHTML = `<div style="padding:.75rem 1rem;border-radius:8px;background:${bg[type]};color:${fg[type]};font-size:.9rem;">${html}</div>`;
}

/* ── Run Compliance Check ────────────────────────────────────────────────── */
document.getElementById("btn-cmp-check")?.addEventListener("click", async () => {
  // Detect which input tab is active — ignore the other input to avoid stale state
  const isTextMode = document.getElementById("cmp-itab-text")?.classList.contains("active");
  const pdfFile  = isTextMode ? null : document.getElementById("cmp-pdf").files[0];
  const text     = document.getElementById("cmp-text").value.trim();
  const statusEl = document.getElementById("cmp-check-status");

  // Helper: show inline validation message and scroll to it
  function cmpValidationMsg(title, body) {
    statusEl.innerHTML = `
      <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:1rem 1.2rem;">
        <div style="font-weight:700;font-size:1rem;color:#b91c1c;margin-bottom:.35rem">${title}</div>
        <div style="font-size:.88rem;color:#7f1d1d;line-height:1.6">${body}</div>
      </div>`;
    statusEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  if (!pdfFile && !text) {
    cmpValidationMsg(
      'No Document Provided',
      'Please upload a PDF, TXT or DOCX file, or paste your contract text before analyzing.'
    );
    return;
  }

  // File-type validation
  if (pdfFile && !pdfFile.name.toLowerCase().match(/\.(pdf|txt|docx)$/)) {
    cmpValidationMsg(
      'Invalid File Type',
      'Only <strong>PDF</strong>, <strong>TXT</strong> and <strong>DOCX</strong> files are supported. Please upload a valid file.'
    );
    return;
  }

  // Text content validation — pre-screen before sending to server
  if (!pdfFile && text) {
    const lower = text.toLowerCase();

    // Strong rejection: clearly a court judgment
    const judgmentSignals = [
      'plaintiff', 'defendant', 'appellant', 'respondent', 'petitioner',
      'court of appeal', 'supreme court', 'high court', 'district court',
      'magistrate court', 'labour tribunal',
      'held that', 'court held', 'judgment', 'judgement', 'case no',
      'counsel for', 'learned counsel', 'cross-examination',
      'remanded', 'acquitted', 'convicted', 'appeal is dismissed', 'appeal is allowed',
      'habeas corpus', 'certiorari', 'mandamus',
      'in the matter of', 'ratio decidendi'
    ];
    const judgmentHits = judgmentSignals.filter(k => lower.includes(k));
    if (judgmentHits.length >= 3) {
      cmpValidationMsg(
        'This is not a valid document',
        'This does not appear to be a contract or agreement document — it looks like a <strong>court judgment or case law</strong>.<br>Please upload a valid contract or agreement document.'
      );
      return;
    }

    // Weak rejection: not enough contract signals
    const contractSignals = [
      'agreement', 'this agreement', 'contract', 'this contract', 'deed',
      'party', 'parties', 'whereas', 'hereby agrees', 'now therefore',
      'employer', 'employee', 'landlord', 'tenant', 'lessor', 'lessee',
      'borrower', 'lender', 'hereinafter', 'in witness whereof',
      'salary', 'rent', 'deposit', 'termination', 'notice period',
      'either party', 'both parties', 'signed by', 'executed on',
      'epf', 'etf', 'gratuity', 'annual leave', 'probationary',
      'confidentiality', 'non-disclosure', 'governing law',
      'arbitration', 'dispute resolution', 'force majeure'
    ];
    const contractHits = contractSignals.filter(k => lower.includes(k));
    if (contractHits.length < 3) {
      cmpValidationMsg(
        'This is not a valid document',
        'This does not appear to be a contract or agreement document.<br>Please upload a valid contract or agreement document.'
      );
      return;
    }
  }

  cmpShowSpinner("Running compliance analysis…");
  cmpStatus(statusEl, " Analysing document…", "info");

  try {
    let res;
    if (pdfFile) {
      if (pdfFile.name.toLowerCase().endsWith('.txt')) {
        // Read TXT file client-side and send to /check endpoint
        const txtContent = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = e => resolve(e.target.result);
          reader.onerror = () => reject(new Error('Failed to read file'));
          reader.readAsText(pdfFile);
        });
        res = await fetch(`${CMP_API}/check`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contract_text: txtContent })
        });
      } else {
        const fd = new FormData();
        fd.append('file', pdfFile);
        res = await fetch(`${CMP_API}/upload-pdf`, { method: 'POST', body: fd });
      }
    } else {
      res = await fetch(`${CMP_API}/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract_text: text })
      });
    }
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      // HTTP 400 = document type rejection from the gate
      if (res.status === 400 && errBody.detail && errBody.detail.valid === false) {
        cmpValidationMsg('This is not a valid document', 'This does not appear to be a contract or agreement document.<br>Please upload a valid contract or agreement document.');
        cmpHideSpinner();
        return;
      }
      throw new Error(errBody.detail || `Server error (${res.status})`);
    }
    const data = await res.json();

    // Legacy fallback: valid:false in 200 response
    if (data.valid === false) {
      cmpValidationMsg('This is not a valid document', 'This does not appear to be a contract or agreement document.<br>Please upload a valid contract or agreement document.');
      cmpHideSpinner();
      return;
    }

    // Block zero-score documents before rendering
    const _clauses = data.clauses || [];
    const _entail  = _clauses.filter(c => c.prediction === "entailment");
    const _score   = (_entail.length / Math.max(_clauses.length, 1)) * 100;
    if (_score === 0) {
      cmpStatus(statusEl,
        `<div style="display:flex;align-items:flex-start;gap:.75rem">`
        + `<span style="font-size:1.5rem;line-height:1">&#9888;</span>`
        + `<div><strong style="font-size:1rem">Invalid Document &mdash; Zero Compliance Score</strong><br>`
        + `<span style="font-size:.88rem;opacity:.85">This document scored 0% compliance. It does not contain any recognisable legal clauses for this contract type and cannot be analysed.</span>`
        + `</div></div>`,
        "error");
      cmpHideSpinner();
      return;
    }

    statusEl.innerHTML = "";
    cmpRenderResultPage(data);
    Swal.fire({ icon: 'success', title: 'Compliance Analysis Complete', text: 'Your document has been analyzed against Sri Lankan civil law.', timer: 2500, showConfirmButton: false });
  } catch (e) {
    Swal.fire({ icon: 'error', title: 'Analysis Failed', text: e.message, confirmButtonColor: '#1a3a5c' });
    cmpStatus(statusEl, ` Error: ${e.message}`, "error");
  } finally {
    cmpHideSpinner();
  }
});

/* ── Render full results page ────────────────────────────────────────────── */
function cmpRenderResultPage(data) {
  const clauses       = data.clauses || [];
  const entailment    = clauses.filter(c => c.prediction === "entailment");
  const contradiction = clauses.filter(c => c.prediction === "contradiction");

  // Calculate real legal compliance score based on actual clause analysis
  const score = (entailment.length / Math.max(clauses.length, 1)) * 100;

  const present = data.present_mandatory || [];
  const missing = data.missing_mandatory || [];
  const docType       = data.document_type || data.domain || "Legal Document";
  const dtLabel       = docType.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) + " Contract";

  // Hide upload card, show results
  document.getElementById("compliance-card").style.display = "none";
  const resultsEl = document.getElementById("cmp-results");
  resultsEl.style.display = "block";

  // Hero badge & score
  document.getElementById("cmp-hero-badge").textContent = dtLabel;
  const pctEl = document.getElementById("cmp-hero-pct");
  pctEl.textContent = score.toFixed(1) + "%";
  const circle = document.getElementById("cmp-score-circle");
  const offset = 314 - (score / 100) * 314;
  const sColor = score >= 70 ? "#4ade80" : score >= 40 ? "#fbbf24" : "#f87171";
  if (circle) {
    circle.style.stroke = sColor;
    circle.style.transition = "stroke-dashoffset 1.2s ease-out";
    setTimeout(() => circle.setAttribute("stroke-dashoffset", offset), 50);
  }

  // Summary cards — event delegation handles clicks (functions not in global scope)
  const summaryGrid = document.getElementById("cmp-summary-grid");
  summaryGrid.innerHTML = `
    <div class="cmp-sum-card cmp-sum-total cmp-sum-clickable" data-clause-page="total">
      <div class="cmp-sum-num">${clauses.length}</div>
      <div class="cmp-sum-label">Total Clauses</div>
      <div class="cmp-sum-view-link">View all →</div>
    </div>
    <div class="cmp-sum-card cmp-sum-compliant cmp-sum-clickable" data-clause-page="compliant">
      <div class="cmp-sum-num">${entailment.length}</div>
      <div class="cmp-sum-label">Compliant</div>
      <div class="cmp-sum-pct">${((entailment.length / Math.max(clauses.length, 1)) * 100).toFixed(1)}%</div>
      <div class="cmp-sum-view-link" style="color:#2e7d32">View →</div>
    </div>
    <div class="cmp-sum-card cmp-sum-violation cmp-sum-clickable" data-clause-page="noncompliant">
      <div class="cmp-sum-num" style="color:#b71c1c">${contradiction.length}</div>
      <div class="cmp-sum-label">Non-Compliant</div>
      <div class="cmp-sum-pct" style="color:#b71c1c">${((contradiction.length / Math.max(clauses.length, 1)) * 100).toFixed(1)}%</div>
      <div class="cmp-sum-view-link" style="color:#b71c1c">View →</div>
    </div>
    <div class="cmp-sum-card cmp-sum-missing cmp-sum-clickable" data-clause-page="missing">
      <div class="cmp-sum-num" style="color:#e65100">${missing.length}</div>
      <div class="cmp-sum-label">Missing Clauses</div>
      <div class="cmp-sum-view-link" style="color:#e65100">View →</div>
    </div>
  `;
  summaryGrid.querySelectorAll("[data-clause-page]").forEach(card => {
    card.addEventListener("click", () => cmpShowClausePage(card.dataset.clausePage));
  });

  // Mandatory + Acts row
  const actionRow = document.getElementById("cmp-action-row");
  actionRow.innerHTML = `
    <div class="cmp-action-card" data-action="missing">
      <div class="cmp-action-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1a3a5c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/><polyline points="9 9 10 9"/></svg>
      </div>
      <div class="cmp-action-info">
        <strong>Mandatory Clauses</strong>
        <p>View required clauses and missing items</p>
      </div>
      <div class="cmp-action-badges">
        <span class="cmp-act-badge green">${present.length} Present</span>
        <span class="cmp-act-badge red">${missing.length} Missing</span>
      </div>
      <span class="cmp-action-arrow">→</span>
    </div>
    <div class="cmp-action-card" data-action="acts">
      <div class="cmp-action-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1a3a5c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      </div>
      <div class="cmp-action-info">
        <strong>Download Acts</strong>
        <p>Access official Sri Lankan legislation PDFs</p>
      </div>
      <span class="cmp-action-arrow">→</span>
    </div>
  `;
  actionRow.querySelectorAll("[data-action]").forEach(card => {
    card.addEventListener("click", () => {
      if (card.dataset.action === "missing") cmpShowClausePage("missing");
      else cmpGoToActsLibrary();
    });
  });

  // Store data for sub-pages and download report
  window._cmpClauses = clauses;
  window._cmpPresent = present;
  window._cmpMissing = missing;
  window._cmpData = data;

  // Ensure main page visible, detail page hidden
  document.getElementById("cmp-main-page").style.display = "block";
  document.getElementById("cmp-detail-page").style.display = "none";
}

/* ── Filter clauses ──────────────────────────────────────────────────────── */
function cmpFilterClauses(type) {
  document.querySelectorAll(".cmp-cfilt").forEach(b => b.classList.remove("active"));
  const btn = document.querySelector(`.cmp-cfilt[data-cfilt="${type}"]`);
  if (btn) btn.classList.add("active");
  const clauses = window._cmpClauses || [];
  const filtered = type === "all" ? clauses : clauses.filter(c => c.prediction === type);
  cmpRenderClauses(filtered);
}

/* ── Render clause cards ─────────────────────────────────────────────────── */
function cmpRenderClauses(clauses) {
  const listEl = document.getElementById("cmp-clause-list");
  listEl.innerHTML = clauses.map((c, i) => {
    const isViolation = c.prediction === "contradiction";
    const borderColor = isViolation ? "#f87171" : "#4ade80";
    const badgeClass  = isViolation ? "cmp-cl-badge-violation" : "cmp-cl-badge-entailment";
    const badgeText   = isViolation ? "CONTRADICTION" : "ENTAILMENT";
    const statusDot   = isViolation ? "" : "";
    const statusText  = isViolation ? "ILLEGAL" : "LEGAL";
    const confPct     = c.confidence || 0;
    const confColor   = isViolation ? "#ef6c00" : "#2e7d32";  // Orange for contradiction, Green for entailment
    const recBg       = isViolation ? "#fff3cd" : "#e8f5e9";
    const provBg      = isViolation ? "#ffe8cc" : "#e8f5e9";

    return `
    <div class="cmp-clause-card" style="border-left:4px solid ${borderColor}">
      <div class="cmp-cl-header">
        <span class="cmp-cl-num">#${i + 1}</span>
        <span class="cmp-cl-badge ${badgeClass}">● ${badgeText}</span>
        <span class="cmp-cl-expand" onclick="this.closest('.cmp-clause-card').classList.toggle('expanded')">▾</span>
      </div>
      <div class="cmp-cl-preview">
        <div class="cmp-cl-clause-text">"${(c.clause || "").replace(/"/g, '&quot;')}"</div>
      </div>
      <div class="cmp-cl-details">
        <div class="cmp-cl-meta-row">
          <div class="cmp-cl-meta-item">
            <span class="cmp-cl-meta-label">LAW REFERENCE</span>
            <span class="cmp-cl-meta-value">${c.law_reference || "—"}</span>
          </div>
          <div class="cmp-cl-meta-item">
            <span class="cmp-cl-meta-label">STATUS</span>
            <span class="cmp-cl-meta-value">${statusText}</span>
          </div>
        </div>

        <div class="cmp-cl-conf-row">
          <span class="cmp-cl-field-label">CONFIDENCE SCORE</span>
          <div class="cmp-cl-conf-track">
            <div class="cmp-cl-conf-fill" style="width:${confPct}%;background:${confColor}"></div>
            <span class="cmp-cl-conf-pct">${confPct.toFixed(1)}%</span>
          </div>
        </div>

        ${c.matched_rule ? `
        <div class="cmp-cl-provision" style="background:${provBg}">
          <span class="cmp-cl-field-label"> APPLICABLE LAW PROVISION</span>
          <p>${c.matched_rule}</p>
        </div>` : ""}

        ${c.recommendation ? `
        <div class="cmp-cl-recommendation" style="background:${recBg}">
          <span class="cmp-cl-field-label"> ANALYSIS &amp; RECOMMENDATION</span>
          <p>${c.recommendation}</p>
        </div>` : ""}
      </div>
    </div>`;
  }).join("");
}

/* ── Render mandatory clauses grid (present + missing) ───────────────────── */
function cmpRenderMandatory(present, missing) {
  // Present
  document.getElementById("cmp-present-count").textContent = `${present.length} Found`;
  document.getElementById("cmp-present-grid").innerHTML = present.map(c => `
    <div class="cmp-mand-card cmp-mand-present">
      <div class="cmp-mand-card-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      </div>
      <div class="cmp-mand-card-body">
        <div class="cmp-mand-card-title">${c.clause || c.id}</div>
        <div class="cmp-mand-card-desc">${c.legal_basis || ''}</div>
      </div>
    </div>
  `).join("") || '<p style="color:var(--muted);font-size:.88rem;padding:.5rem 0">No present mandatory clauses detected.</p>';

  // Missing
  document.getElementById("cmp-missing-count").textContent = `${missing.length} Missing`;
  document.getElementById("cmp-missing-grid").innerHTML = missing.map(c => `
    <div class="cmp-mand-card cmp-mand-missing">
      <div class="cmp-mand-card-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
      </div>
      <div class="cmp-mand-card-body">
        <div class="cmp-mand-card-title">${c.clause || c.id}</div>
        <div class="cmp-mand-card-desc">${c.legal_basis || c.rule || ''}</div>
      </div>
    </div>
  `).join("") || '<p style="color:var(--muted);font-size:.88rem;padding:.5rem 0">No missing mandatory clauses — great!</p>';
}

/* ── Back to upload ──────────────────────────────────────────────────────── */
function cmpBackToUpload(targetTab) {
  document.getElementById("cmp-results").style.display = "none";
  document.getElementById("cmp-main-page").style.display = "block";
  document.getElementById("cmp-detail-page").style.display = "none";
  document.getElementById("compliance-card").style.display = "";
  // Always switch to the requested tab (default: Check Document)
  const tabId = targetTab || "cmp-check";
  const tabBtn = document.querySelector(`[data-ctab="${tabId}"]`);
  if (tabBtn) tabBtn.click();
}
document.getElementById("btn-cmp-back-summary")?.addEventListener("click", cmpShowMainPage);
document.getElementById("btn-cmp-new")?.addEventListener("click", () => cmpBackToUpload("cmp-check"));
document.getElementById("btn-cmp-new2")?.addEventListener("click", () => cmpBackToUpload("cmp-check"));

/* ── Detail page tab bar — navigate back and switch tab ──────────────────── */
document.querySelectorAll("#cmp-detail-tabs .tab").forEach(btn => {
  btn.addEventListener("click", () => cmpBackToUpload(btn.dataset.dtab));
});

function cmpGoToActsLibrary() {
  document.getElementById("cmp-results").style.display = "none";
  document.getElementById("compliance-card").style.display = "";
  document.querySelector('[data-ctab="cmp-acts"]')?.click();
  // Show the Back to Summary button since we came from results
  const backBtn = document.getElementById("btn-acts-back-summary");
  if (backBtn) backBtn.style.display = "";
}

/* ── Acts Library → Back to Summary ────────────────────────────────────── */
document.getElementById("btn-acts-back-summary")?.addEventListener("click", () => {
  if (!window._cmpData) return;
  document.getElementById("compliance-card").style.display = "none";
  document.getElementById("cmp-results").style.display = "block";
  document.getElementById("cmp-main-page").style.display = "block";
  document.getElementById("cmp-detail-page").style.display = "none";
  // Hide the button again
  const backBtn = document.getElementById("btn-acts-back-summary");
  if (backBtn) backBtn.style.display = "none";
  window.scrollTo({ top: 0, behavior: "smooth" });
});

/* ── Show clause detail sub-page ─────────────────────────────────────────── */
function cmpShowClausePage(type) {
  const clauses      = window._cmpClauses || [];
  const present      = window._cmpPresent || [];
  const missing      = window._cmpMissing || [];
  const entailment   = clauses.filter(c => c.prediction === "entailment");
  const contradiction = clauses.filter(c => c.prediction === "contradiction");

  document.getElementById("cmp-main-page").style.display = "none";
  document.getElementById("cmp-detail-page").style.display = "block";

  // ── Build mini summary strip ──────────────────────────────────────────
  const strip = document.getElementById("cmp-detail-summary-strip");
  if (strip) {
    const total = clauses.length;
    const eLen  = entailment.length;
    const cLen  = contradiction.length;
    const mLen  = missing.length;
    const maxC  = Math.max(total, 1);
    strip.innerHTML = `
      <div class="cmp-sum-card cmp-sum-total cmp-sum-clickable${type === 'total' ? ' cmp-sum-active' : ''}" data-dpage="total">
        <div class="cmp-sum-num">${total}</div>
        <div class="cmp-sum-label">Total Clauses</div>
        <div class="cmp-sum-view-link">${type === 'total' ? 'Viewing →' : 'View all →'}</div>
      </div>
      <div class="cmp-sum-card cmp-sum-compliant cmp-sum-clickable${type === 'compliant' ? ' cmp-sum-active' : ''}" data-dpage="compliant">
        <div class="cmp-sum-num">${eLen}</div>
        <div class="cmp-sum-label">Compliant</div>
        <div class="cmp-sum-pct" style="color:#2e7d32">${((eLen / maxC) * 100).toFixed(1)}%</div>
        <div class="cmp-sum-view-link" style="color:#2e7d32">${type === 'compliant' ? 'Viewing →' : 'View →'}</div>
      </div>
      <div class="cmp-sum-card cmp-sum-violation cmp-sum-clickable${type === 'noncompliant' ? ' cmp-sum-active' : ''}" data-dpage="noncompliant">
        <div class="cmp-sum-num" style="color:#b71c1c">${cLen}</div>
        <div class="cmp-sum-label">Non-Compliant</div>
        <div class="cmp-sum-pct" style="color:#b71c1c">${((cLen / maxC) * 100).toFixed(1)}%</div>
        <div class="cmp-sum-view-link" style="color:#b71c1c">${type === 'noncompliant' ? 'Viewing →' : 'View →'}</div>
      </div>
      <div class="cmp-sum-card cmp-sum-missing cmp-sum-clickable${type === 'missing' ? ' cmp-sum-active' : ''}" data-dpage="missing">
        <div class="cmp-sum-num" style="color:#e65100">${mLen}</div>
        <div class="cmp-sum-label">Missing Clauses</div>
        <div class="cmp-sum-view-link" style="color:#e65100">${type === 'missing' ? 'Viewing →' : 'View →'}</div>
      </div>
    `;
    strip.querySelectorAll("[data-dpage]").forEach(card => {
      if (!card.classList.contains("cmp-sum-active")) {
        card.addEventListener("click", () => cmpShowClausePage(card.dataset.dpage));
      }
    });
  }
  // ─────────────────────────────────────────────────────────────────────

  const clauseSection    = document.getElementById("cmp-detail-clause-section");
  const mandatorySection = document.getElementById("cmp-mandatory-section");
  const titleEl          = document.getElementById("cmp-detail-title");

  if (type === "missing") {
    clauseSection.style.display    = "none";
    mandatorySection.style.display = "block";
    cmpRenderMandatory(present, missing);
  } else {
    clauseSection.style.display    = "block";
    mandatorySection.style.display = "none";
    let filtered, title;
    if (type === "compliant") {
      filtered = entailment;
      title    = ` Compliant Clauses (${entailment.length})`;
    } else if (type === "noncompliant") {
      filtered = contradiction;
      title    = ` Non-Compliant Clauses (${contradiction.length})`;
    } else {
      filtered = clauses;
      title    = ` All Clauses (${clauses.length})`;
    }
    titleEl.textContent = title;
    cmpRenderClauses(filtered);
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ── Back to main summary page ───────────────────────────────────────────── */
function cmpShowMainPage() {
  document.getElementById("cmp-detail-page").style.display = "none";
  document.getElementById("cmp-main-page").style.display  = "block";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ── Download report dropdown toggle ────────────────────────────────────── */
document.getElementById("btn-cmp-download")?.addEventListener("click", (e) => {
  e.stopPropagation();
  const menu = document.getElementById("cmp-download-menu");
  if (!menu) return;
  menu.style.display = menu.style.display === "none" ? "block" : "none";
});
document.addEventListener("click", () => {
  const menu = document.getElementById("cmp-download-menu");
  if (menu) menu.style.display = "none";
});
document.getElementById("btn-cmp-dl-pdf")?.addEventListener("click", () => cmpGenerateReport("pdf"));
document.getElementById("btn-cmp-dl-txt")?.addEventListener("click", () => cmpGenerateReport("txt"));

async function cmpGenerateReport(format) {
  const data = window._cmpData;
  if (!data) return;
  const btn = document.getElementById("btn-cmp-download");
  const menu = document.getElementById("cmp-download-menu");
  if (menu) menu.style.display = "none";
  btn.disabled = true; btn.textContent = format === "pdf" ? "⏳ Generating PDF…" : "⏳ Generating TXT…";

  const clauses = data.clauses || [];
  const present = data.present_mandatory || [];
  const missing = data.missing_mandatory || [];
  const score = (present.length + missing.length) > 0
    ? Math.round(present.length / (present.length + missing.length) * 100) : 0;

  // ── TXT: build text file and download, then return early
  if (format === "txt") {
    const total = clauses.length;
    const lines = [
      "COMPLIANCE ANALYSIS REPORT",
      "Generated by LexVision — " + new Date().toLocaleString(),
      "=====================================================",
      "",
      `Compliance Score: ${score}%`,
      `Total Clauses: ${total}`,
      `Compliant: ${clauses.filter(c => c.prediction === 'entailment').length}`,
      `Violations: ${clauses.filter(c => c.prediction === 'contradiction').length}`,
      `Missing Mandatory Clauses: ${missing.length}`,
      "",
      "=====================================================",
      "DETAILED CLAUSE ANALYSIS",
      "=====================================================",
      "",
      ...clauses.map((c, i) => [
        `Clause ${i + 1}: ${c.prediction === 'entailment' ? 'COMPLIANT' : 'VIOLATION'}`,
        `Text: ${c.clause || ''}`,
        c.law_reference ? `Law Reference: ${c.law_reference}` : null,
        c.recommendation ? `Recommendation: ${c.recommendation}` : null,
        `Confidence: ${c.confidence || 0}%`,
        ""
      ].filter(Boolean).join("\n")),
      "=====================================================",
      "PRESENT MANDATORY CLAUSES",
      "=====================================================",
      "",
      ...present.map(p => `✓ ${p.clause || ''}${p.legal_basis ? ' — ' + p.legal_basis : ''}`),
      "",
      "=====================================================",
      "MISSING MANDATORY CLAUSES",
      "=====================================================",
      "",
      ...missing.map(m => `✗ ${m.clause || ''}${m.legal_basis ? ' — ' + m.legal_basis : ''}`)
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `compliance_report_${data.analysis_id || "report"}.txt`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    btn.disabled = false; btn.textContent = "Download Report ▾";
    return;
  }

  // ── PDF: build HTML report
  const total = clauses.length;
  const compliant = clauses.filter(c => c.prediction === 'entailment').length;
  const violations = clauses.filter(c => c.prediction === 'contradiction').length;

  /* Build a clean, simple HTML report from the data (avoids SVG/canvas issues) */

  const reportHTML = `
    <div style="font-family:Arial,Helvetica,sans-serif;color:#1a1a2e;padding:20px;max-width:780px;margin:0 auto">
      <div style="text-align:center;padding:30px 20px;background:#0d47a1;color:#fff;border-radius:12px;margin-bottom:24px">
        <h1 style="margin:0 0 6px;font-size:22px">Compliance Analysis Report</h1>
        <p style="margin:0;opacity:.85;font-size:12px">Generated by LexVision &mdash; ${new Date().toLocaleDateString()}</p>
        <div style="margin-top:16px;font-size:38px;font-weight:700">${score}%</div>
        <div style="font-size:12px;opacity:.8">Compliance Score</div>
      </div>
      <table style="width:100%;border-collapse:separate;border-spacing:10px 0;margin-bottom:22px"><tr>
        <td style="background:#f8f9fa;border:1px solid #e5e7eb;border-radius:10px;padding:14px;text-align:center;width:25%">
          <div style="font-size:22px;font-weight:700;color:#0d47a1">${total}</div>
          <div style="font-size:11px;color:#666">Total Clauses</div>
        </td>
        <td style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px;text-align:center;width:25%">
          <div style="font-size:22px;font-weight:700;color:#16a34a">${compliant}</div>
          <div style="font-size:11px;color:#666">Compliant</div>
        </td>
        <td style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:14px;text-align:center;width:25%">
          <div style="font-size:22px;font-weight:700;color:#dc2626">${violations}</div>
          <div style="font-size:11px;color:#666">Violations</div>
        </td>
        <td style="background:#fefce8;border:1px solid #fde68a;border-radius:10px;padding:14px;text-align:center;width:25%">
          <div style="font-size:22px;font-weight:700;color:#d97706">${missing.length}</div>
          <div style="font-size:11px;color:#666">Missing</div>
        </td>
      </tr></table>

      <h2 style="font-size:15px;border-bottom:2px solid #0d47a1;padding-bottom:6px;margin:22px 0 14px">Detailed Clause Analysis</h2>
      ${clauses.map((c, i) => {
        const isComp = c.prediction === 'entailment';
        const bg = isComp ? '#f0fdf4' : '#fef2f2';
        const border = isComp ? '#bbf7d0' : '#fecaca';
        const badge = isComp ? 'Compliant' : 'Violation';
        const badgeColor = isComp ? '#16a34a' : '#dc2626';
        return `
        <div style="background:${bg};border:1px solid ${border};border-radius:10px;padding:12px 14px;margin-bottom:10px">
          <div style="margin-bottom:6px">
            <strong style="font-size:12px;color:#0d47a1">Clause ${i + 1}</strong>
            <span style="font-size:10px;font-weight:600;color:${badgeColor};background:${isComp ? '#dcfce7' : '#fee2e2'};padding:2px 8px;border-radius:99px;margin-left:8px">${badge}</span>
          </div>
          <p style="font-size:11px;color:#374151;margin:0 0 6px;line-height:1.5">${(c.clause || '').replace(/</g,'&lt;')}</p>
          ${c.violated_act ? `<div style="font-size:10px;color:#555"><b>Act:</b> ${c.violated_act}</div>` : ''}
          ${c.section ? `<div style="font-size:10px;color:#555"><b>Section:</b> ${c.section}</div>` : ''}
          ${c.recommendation ? `<div style="font-size:10px;color:#0d47a1;margin-top:4px"><b>Recommendation:</b> ${c.recommendation}</div>` : ''}
          <div style="font-size:10px;color:#999;margin-top:3px">Confidence: ${c.confidence || 0}%</div>
        </div>`;
      }).join('')}

      ${present.length ? `
        <h2 style="font-size:15px;border-bottom:2px solid #16a34a;padding-bottom:6px;margin:22px 0 14px">Present Mandatory Clauses (${present.length})</h2>
        ${present.map(p => `
          <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 12px;margin-bottom:8px">
            <div style="font-size:11px;font-weight:600;color:#166534">${(p.clause || '').replace(/</g,'&lt;')}</div>
            ${p.legal_basis ? `<div style="font-size:10px;color:#555;margin-top:3px">${p.legal_basis}</div>` : ''}
          </div>
        `).join('')}
      ` : ''}

      ${missing.length ? `
        <h2 style="font-size:15px;border-bottom:2px solid #d97706;padding-bottom:6px;margin:22px 0 14px">Missing Mandatory Clauses (${missing.length})</h2>
        ${missing.map(m => `
          <div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:10px 12px;margin-bottom:8px">
            <div style="font-size:11px;font-weight:600;color:#92400e">${(m.clause || '').replace(/</g,'&lt;')}</div>
            ${m.legal_basis ? `<div style="font-size:10px;color:#555;margin-top:3px">${m.legal_basis}</div>` : ''}
          </div>
        `).join('')}
      ` : ''}

      <div style="text-align:center;margin-top:28px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:10px;color:#999">
        Generated by LexVision Legal AI System &mdash; ${new Date().toLocaleString()}
      </div>
    </div>`;

  /* Render into a hidden off-screen container */
  const container = document.createElement('div');
  container.innerHTML = reportHTML;
  container.style.cssText = 'position:fixed;left:-9999px;top:0;width:800px;background:#fff;z-index:-1';
  document.body.appendChild(container);

  try {
    if (typeof html2pdf !== 'undefined') {
      await html2pdf().set({
        margin: [8, 8, 8, 8],
        filename: `compliance_report_${data.analysis_id || 'report'}.pdf`,
        image: { type: 'jpeg', quality: 0.95 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff', logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      }).from(container.firstElementChild).save();
    } else {
      /* Fallback: open printable report in new window */
      const w = window.open('', '_blank');
      w.document.write('<!DOCTYPE html><html><head><title>Compliance Report</title></head><body style="margin:0;padding:0">' + reportHTML + '</body></html>');
      w.document.close(); w.focus(); w.print();
    }
  } catch (e) {
    console.error('PDF generation error:', e);
    /* Fallback to print dialog */
    try {
      const w = window.open('', '_blank');
      w.document.write('<!DOCTYPE html><html><head><title>Compliance Report</title></head><body style="margin:0;padding:0">' + reportHTML + '</body></html>');
      w.document.close(); w.focus(); w.print();
    } catch (_) { Swal.fire({ icon: 'error', title: 'PDF Failed', text: 'Could not generate PDF. Please try again.', confirmButtonColor: '#1a3a5c' }); }
  } finally {
    document.body.removeChild(container);
    btn.disabled = false; btn.textContent = 'Download Report ▾';
  }
}

/* ── Load history ────────────────────────────────────────────────────────── */
async function cmpLoadHistory() {
  const listEl = document.getElementById("cmp-history-list");
  listEl.innerHTML = "<p style='color:var(--muted)'>Loading…</p>";
  cmpShowSpinner("Fetching history…");
  try {
    const res  = await fetch(`${CMP_API}/history?limit=50`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const items = data.analyses || [];
    if (!items.length) {
      listEl.innerHTML = "<p style='color:var(--muted)'>No previous analyses found.</p>";
      return;
    }
    listEl.innerHTML = items.map(a => {
      const sc = (a.compliance_score || 0);
      const scColor = sc >= 80 ? "#2e7d32" : sc >= 50 ? "#e65100" : "#b71c1c";
      const aid = a.id || a._id || "";
      return `
      <div class="cmp-hist-item" data-id="${aid}" style="border:1px solid var(--border);border-radius:10px;padding:.9rem 1rem;margin-bottom:.7rem;transition:box-shadow .2s">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.4rem">
          <div style="flex:1;min-width:0">
            <strong style="font-size:.93rem">${a.filename || "Unnamed"}</strong>
          </div>
          <div style="display:flex;align-items:center;gap:.6rem;flex-shrink:0">
            <span style="font-size:.82rem;font-weight:700;color:#fff;background:${scColor};padding:.2rem .6rem;border-radius:99px">${sc.toFixed(0)}%</span>
            <button data-cmp-action="view" data-cmp-id="${aid}" style="padding:.35rem;border:1px solid var(--primary);color:var(--primary);background:transparent;border-radius:6px;cursor:pointer;line-height:1;width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center" title="View full report">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button data-cmp-action="delete" data-cmp-id="${aid}" style="padding:.35rem;border:1px solid #b71c1c;color:#b71c1c;background:transparent;border-radius:6px;cursor:pointer;line-height:1;width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center" title="Delete this analysis">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            </button>
          </div>
        </div>
        <div id="cmp-hist-detail-${aid}" style="display:none;margin-top:.8rem;border-top:1px solid var(--border);padding-top:.8rem"></div>
      </div>`;
    }).join("");
    // Attach click handlers via event delegation (works inside DOMContentLoaded scope)
    listEl.querySelectorAll("[data-cmp-action='view']").forEach(btn => {
      btn.addEventListener("click", () => cmpViewHistory(btn.dataset.cmpId));
    });
    listEl.querySelectorAll("[data-cmp-action='delete']").forEach(btn => {
      btn.addEventListener("click", () => cmpDeleteHistory(btn.dataset.cmpId));
    });
  } catch (e) {
    listEl.innerHTML = `<p style='color:#b71c1c'>Error loading history: ${e.message}</p>`;
    Swal.fire({ icon: 'error', title: 'Load Failed', text: 'Could not load history. ' + e.message, confirmButtonColor: '#1a3a5c' });
  } finally {
    cmpHideSpinner();
  }
}

async function cmpViewHistory(id) {
  const detailEl = document.getElementById(`cmp-hist-detail-${id}`);
  if (!detailEl) return;
  if (detailEl.style.display !== "none") { detailEl.style.display = "none"; return; }
  detailEl.innerHTML = "<p style='color:var(--muted);font-size:.85rem'>Loading details…</p>";
  detailEl.style.display = "block";
  try {
    const res = await fetch(`${CMP_API}/history/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    // Render into full results page
    cmpRenderResultPage(data);
  } catch (e) {
    detailEl.innerHTML = `<p style='color:#b71c1c;font-size:.85rem'>Error: ${e.message}</p>`;
    Swal.fire({ icon: 'error', title: 'Load Failed', text: e.message, confirmButtonColor: '#1a3a5c' });
  }
}

async function cmpDeleteHistory(id) {
  const result = await Swal.fire({
    title: 'Delete Analysis?',
    text: 'This action cannot be undone.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#b71c1c',
    cancelButtonColor: '#6b7280',
    confirmButtonText: 'Yes, delete it',
    cancelButtonText: 'Cancel'
  });
  if (!result.isConfirmed) return;
  try {
    const res = await fetch(`${CMP_API}/history/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    // Remove the card from DOM
    const card = document.querySelector(`.cmp-hist-item[data-id="${id}"]`);
    if (card) card.remove();
    // If no items left show empty message
    const listEl = document.getElementById("cmp-history-list");
    if (!listEl.querySelector(".cmp-hist-item")) {
      listEl.innerHTML = "<p style='color:var(--muted)'>No previous analyses found.</p>";
    }
    Swal.fire({ icon: 'success', title: 'Deleted', text: 'Analysis has been removed.', timer: 1500, showConfirmButton: false });
  } catch (e) {
    Swal.fire({ icon: 'error', title: 'Delete Failed', text: e.message, confirmButtonColor: '#1a3a5c' });
  }
}

document.getElementById("btn-cmp-refresh")?.addEventListener("click", cmpLoadHistory);

/* ── Load Acts Library ───────────────────────────────────────────────────── */
/* ── Acts Library — auto-load, search & category filter ─────────────────── */
(function initActsLibrary() {
    // 10 Domains Supported
  const ACT_CATEGORIES = {
    // 1. Employment Law Domain - ALL employment related acts
    employment: ['Industrial Disputes', 'Industrial-Disputes-Act-Consolidated-2024',
      'Shop and Office', 'Shop-and-Office-Employees-Consolidated-2024',
      'Termination of Employment', 'Termination-of-Employment-of-Workmen-Consolidated-2024',
      'Maternity Benefits', 'Maternity-Benefits-Consolidated-2024',
      'Payment Of Gratuity', 'Employees Provident', 'Employees-Provident-Fund-Consolidated-2024',
      'Employees Trust', 'Employees-Trust-Fund-Act-Consolidated-2024',
      'EMPLOYMENT OF WOMEN', 'Minimum Wages', 'Wages Boards'],
    
    // 2. Consumer Protection Domain
    consumer: ['Consumer Affairs Authority', 'Consumer Credit', 'UNFAIR CONTRACT', 'UNFAIR_CONTRACT_TERMS_ACT', 'Money Lending'],
    
    // 3. Rental Domain
    rental: ['Rent', 'Rental', 'Registration of Documents', 'Registration-of-Documents-Consolidated-2024'],
    
    // 4. Finance Leasing Domain
    finance_leasing: ['Finance Leasing', 'Finance-Leasing', 'Hire Purchase', 'Hire-Purchase', 'Lease'],
    
    // 5. Partnership Domain
    partnership: ['Partnership', 'Partnership-Ordinance', 'Partner', 'Joint Venture'],
    
    // 6. General Domain
    general: ['Prevention of Frauds', 'Prevention-of-Frauds-Consolidated-2024', 'Contracts', 'Fraud'],
    
    // 7. Property & Land Sale Domain
    property_sale: ['SALE OF GOODS', 'Sale of Goods', 'Registration of Documents', 'Registration-of-Documents-Consolidated-2024',
      'Prevention of Frauds', 'Prevention-of-Frauds-Consolidated-2024'],
    
    // 8. Electronic Domain
    electronic: ['Electronic Transactions', 'Electronic-Transactions-Consolidated-2024', 'Digital', 'E-commerce', 'E-signature'],
    
    // 9. Microfinance Domain
    microfinance: ['Microfinance', 'Microcredit', 'Small Loans', 'Money Lending'],
    
    // 10. Pawn Domain
    pawn: ['PAWNBROKERS', 'Pawn', 'Pledge', 'Pawning']
  };

  function categorize(filename) {
    const upper = filename.toUpperCase();
    for (const [cat, keywords] of Object.entries(ACT_CATEGORIES)) {
      if (keywords.some(k => upper.includes(k.toUpperCase()))) return cat;
    }
    return 'general';
  }
  const catLabels = {
    all: 'All Acts',
    employment: 'Employment Law',
    consumer: 'Consumer Protection',
    rental: 'Rental',
    finance_leasing: 'Finance & Leasing',
    partnership: 'Partnership',
    general: 'General',
    property_sale: 'Property & Sale',
    electronic: 'Electronic',
    microfinance: 'Microfinance',
    pawn: 'Pawn'
  };

  let allActs = [];
  let loaded = false;

  async function loadActs() {
    if (loaded) return;
    const listEl = document.getElementById('cmp-acts-list');
    listEl.innerHTML = '<p style="color:var(--muted)">Loading acts…</p>';
    try {
      const res = await fetch(`${CMP_API}/acts/list`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      allActs = (data.acts || []).map(f => ({ filename: f, category: categorize(f) }));
      loaded = true;
      renderActs(allActs);
    } catch (e) {
      listEl.innerHTML = `<p style='color:#b71c1c'>Error loading acts: ${e.message}</p>`;
      Swal.fire({ icon: 'error', title: 'Load Failed', text: 'Could not load the Acts library. ' + e.message, confirmButtonColor: '#1a3a5c' });
    }
  }

  function renderActs(acts) {
    const countEl = document.getElementById('acts-count');
    const listEl = document.getElementById('cmp-acts-list');
    countEl.innerHTML = `<strong>${acts.length}</strong> Acts Available`;
    if (!acts.length) { listEl.innerHTML = '<p style="color:var(--muted)">No acts match your search.</p>'; return; }
    
   
    listEl.innerHTML = acts.map(a => {
      const displayName = a.filename.replace(/\.pdf$/i, '').replace(/-/g, ' ');
      const catLabel = catLabels[a.category] || 'General Law';
      return `
      <div class="acts-card">
        <div class="acts-card-top">
          <span class="acts-card-cat acts-cat-${a.category}">${catLabel}</span>
        </div>
        <div class="acts-card-title">${displayName}</div>
        <div class="acts-card-type">PDF Document</div>
        <a href="${CMP_API}/acts/download/${encodeURIComponent(a.filename)}" target="_blank" class="acts-card-btn">Download PDF</a>
      </div>`;
    }).join('');
  }

  function filterActs() {
    const search = (document.getElementById('acts-search')?.value || '').toLowerCase();
    const cat = document.querySelector('.acts-cat.active')?.dataset.cat || 'all';
    let filtered = allActs;
    if (cat !== 'all') filtered = filtered.filter(a => a.category === cat);
    if (search) filtered = filtered.filter(a => a.filename.toLowerCase().includes(search));
    renderActs(filtered);
  }

  // Category filter buttons
  document.querySelectorAll('.acts-cat').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.acts-cat').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterActs();
    });
  });

  // Search
  document.getElementById('acts-search')?.addEventListener('input', filterActs);

  // Auto-load when Acts tab is clicked
  const actsTab = document.querySelector('[data-ctab="cmp-acts"]');
  if (actsTab) actsTab.addEventListener('click', loadActs);
})();

}); // End of DOMContentLoaded
