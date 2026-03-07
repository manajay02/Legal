/* ── Config ───────────────────────────────────────────────────────────────── */
const API = "http://localhost:5000/api";

/* ── Sidebar navigation ───────────────────────────────────────────────────── */
const topbarCurrent = document.getElementById("topbar-current");
const navLabels = { similarity: "Similarity Search", extractor: "Case Extractor", summarizer: "Case Summarizer", component3: "Component 3", component4: "Component 4" };

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
    document.querySelectorAll(".component-panel").forEach(p => p.classList.remove("active"));
    item.classList.add("active");
    const panel = document.getElementById("panel-" + item.dataset.component);
    if (panel) panel.classList.add("active");
    if (topbarCurrent) topbarCurrent.textContent = navLabels[item.dataset.component] || item.querySelector(".nav-label").textContent;
  });
});

/* ── DOM refs ─────────────────────────────────────────────────────────────── */
const selCategory   = document.getElementById("sel-category");
const selSubcategory= document.getElementById("sel-subcategory");
const selFilename   = document.getElementById("sel-filename");
const selTopN       = document.getElementById("sel-topn");
const chkGlobal     = document.getElementById("chk-global");
const txtQuery      = document.getElementById("txt-query");
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
function showSpinner(v) { spinner.style.display = v ? "flex" : "none"; }
function currentTab() { return document.querySelector(".tab.active").dataset.tab; }

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");

    const isClassify = tab.dataset.tab === "classify";
    btnSearch.style.display    = isClassify ? "none"         : "inline-block";
    btnClassify.style.display  = isClassify ? "inline-block" : "none";
    btnAddCase.style.display   = isClassify ? "inline-block" : "none";
    searchOptions.style.display = isClassify ? "none"        : "flex";
  });
});

/* ── Load categories on page load ─────────────────────────────────────────── */
let categoriesData = {};

async function loadCategories() {
  try {
    const res  = await fetch(`${API}/categories`);
    categoriesData = await res.json();
    selCategory.innerHTML = '<option value="">-- Select category --</option>';
    Object.keys(categoriesData).sort().forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat; opt.textContent = cat;
      selCategory.appendChild(opt);
    });
    renderStats(categoriesData);
  } catch (e) {
    console.error("Failed to load categories:", e);
  }
}

/* ── Category → Subcategory cascade ──────────────────────────────────────── */
selCategory.addEventListener("change", () => {
  const cat = selCategory.value;
  selSubcategory.innerHTML = '<option value="">-- Select subcategory --</option>';
  selFilename.innerHTML    = '<option value="">-- Select file --</option>';
  selSubcategory.disabled  = !cat;
  selFilename.disabled     = true;
  if (!cat) return;
  (categoriesData[cat] || []).forEach(({ subcategory, count }) => {
    const opt = document.createElement("option");
    opt.value = subcategory;
    opt.textContent = `${subcategory} (${count})`;
    selSubcategory.appendChild(opt);
  });
});

/* ── Subcategory → Filename cascade ──────────────────────────────────────── */
selSubcategory.addEventListener("change", async () => {
  const cat = selCategory.value;
  const sub = selSubcategory.value;
  selFilename.innerHTML = '<option value="">-- Select file --</option>';
  selFilename.disabled  = !sub;
  if (!sub) return;
  showSpinner(true);
  try {
    const res   = await fetch(`${API}/filenames?category=${encodeURIComponent(cat)}&subcategory=${encodeURIComponent(sub)}`);
    const files = await res.json();
    files.forEach(f => {
      const opt = document.createElement("option");
      opt.value = f; opt.textContent = f;
      selFilename.appendChild(opt);
    });
  } finally { showSpinner(false); }
});

/* ── Similarity Search ────────────────────────────────────────────────────── */
btnSearch.addEventListener("click", async () => {
  const tab         = currentTab();
  const globalSearch= chkGlobal.checked;
  const topN        = parseInt(selTopN.value, 10);
  const body        = { top_n: topN, global_search: globalSearch };

  if (tab === "by-file") {
    const filename = selFilename.value;
    if (!filename) { alert("Please select a case file."); return; }
    body.filename = filename;
    if (!globalSearch) {
      body.category    = selCategory.value;
      body.subcategory = selSubcategory.value;
    }
  } else {
    const text = txtQuery.value.trim();
    if (!text) { alert("Please enter a query text."); return; }
    body.text = text;
  }

  showSpinner(true);
  classifyPanel.style.display = "none";
  resultsPanel.style.display  = "none";
  resultsList.innerHTML = "";

  try {
    const res  = await fetch(`${API}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    resultsList.innerHTML = data.error
      ? `<div class="error-msg">⚠️ ${data.error}</div>`
      : "";
    if (!data.error) renderResults(data.results);
  } catch {
    resultsList.innerHTML = `<div class="error-msg">⚠️ Could not reach the API. Is the backend running?</div>`;
  } finally {
    resultsPanel.style.display = "block";
    resultsPanel.scrollIntoView({ behavior: "smooth" });
    showSpinner(false);
  }
});

/* ── Classify Document ────────────────────────────────────────────────────── */
btnClassify.addEventListener("click", async () => {
  const file = clfFile.files[0];
  const text = clfText.value.trim();

  if (!file && !text) {
    alert("Please upload a PDF or paste document text.");
    return;
  }

  showSpinner(true);
  classifyPanel.style.display = "none";
  resultsPanel.style.display  = "none";
  classifyResult.innerHTML    = "";

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
    if (data.error) {
      classifyResult.innerHTML = `<div class="error-msg">⚠️ ${data.error}</div>`;
    } else {
      renderClassifyResult(data);
    }
  } catch {
    classifyResult.innerHTML = `<div class="error-msg">⚠️ Could not reach the API. Is the backend running?</div>`;
  } finally {
    classifyPanel.style.display = "block";
    classifyPanel.scrollIntoView({ behavior: "smooth" });
    showSpinner(false);
  }
});

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
        <div class="result-filename">📄 ${r.filename}</div>
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

/* ── Render classification result ─────────────────────────────────────────── */
function renderClassifyResult(data) {
  classifyResult.innerHTML = `
    <div class="clf-prediction">
      <div>
        <div class="clf-label">Category</div>
        <div class="clf-value">⚖️ ${data.category}</div>
      </div>
      <div>
        <div class="clf-label">Subcategory</div>
        <div class="clf-value">📁 ${data.subcategory}</div>
      </div>
    </div>`;
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
        <button class="btn-view-cases" data-cat="${cat}" data-sub="${subcategory}">View Cases</button>`;
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
        <button class="modal-close" id="modal-close-btn">✕</button>
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
          <span class="modal-case-name" style="cursor:pointer" data-filename="${f}">📄 ${f}</span>
        </div>`).join("");
      // Add click handler for each case name
      list.querySelectorAll('.modal-case-name').forEach(el => {
        el.addEventListener('click', () => {
          window.open(`http://localhost:5000/api/pdf/${encodeURIComponent(el.dataset.filename)}`, '_blank');
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
    btnAddCase.disabled = true;
    btnAddCase.textContent = "Adding...";
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
        btnAddCase.textContent = "✔ Added!";
        btnAddCase.style.background = "#2e7d32";
        if (clfFile) clfFile.value = "";
        if (clfText) clfText.value = "";
        loadCategories();
        setTimeout(() => {
          btnAddCase.textContent = "Add Case to Database";
          btnAddCase.style.background = "";
          btnAddCase.disabled = false;
        }, 2000);
      } else {
        btnAddCase.textContent = "✘ Failed";
        btnAddCase.style.background = "#b71c1c";
        setTimeout(() => {
          btnAddCase.textContent = "Add Case to Database";
          btnAddCase.style.background = "";
          btnAddCase.disabled = false;
        }, 2000);
      }
    } catch {
      btnAddCase.textContent = "✘ Error";
      btnAddCase.style.background = "#b71c1c";
      setTimeout(() => {
        btnAddCase.textContent = "Add Case to Database";
        btnAddCase.style.background = "";
        btnAddCase.disabled = false;
      }, 2000);
    } finally {
      showSpinner(false);
    }
  });
}

/* ── Init ─────────────────────────────────────────────────────────────────── */
loadCategories();

/* ══════════════════════════════════════════════════════════════════════════
   COMPONENT 2 – Civil Case Extractor  (FastAPI on port 8000)
   ══════════════════════════════════════════════════════════════════════════ */

const EXT_API = "http://localhost:8000/api/v1";

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

/* ── Upload & Process ────────────────────────────────────────────────────── */
document.getElementById("btn-ext-upload")?.addEventListener("click", async () => {
  const fileInput = document.getElementById("ext-file");
  const statusEl  = document.getElementById("ext-upload-status");
  statusEl.innerHTML = "";

  if (!fileInput.files.length) {
    extStatus(statusEl, "⚠️ Please select a PDF file first.", "warn");
    return;
  }
  const file = fileInput.files[0];
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    extStatus(statusEl, "⚠️ Only PDF files are supported.", "warn");
    return;
  }

  extShowSpinner("Uploading PDF…");
  extStatus(statusEl, "⏳ Uploading…", "info");

  try {
    // Step 1: Upload
    const formData = new FormData();
    formData.append("file", file);
    const upRes  = await fetch(`${EXT_API}/upload`, { method: "POST", body: formData });
    if (!upRes.ok) {
      const err = await upRes.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed (${upRes.status})`);
    }
    const upData = await upRes.json();
    const docId  = upData.document_id;
    extStatus(statusEl, `✅ Uploaded — ID: <code>${docId}</code><br>⏳ Sending to AI for extraction…`, "success");
    extShowSpinner("AI is extracting metadata, sections, citations…");

    // Step 2: Process
    const procRes  = await fetch(`${EXT_API}/process/${docId}`, { method: "POST" });
    if (!procRes.ok) {
      const err = await procRes.json().catch(() => ({}));
      throw new Error(err.detail || `Processing failed (${procRes.status})`);
    }
    const procData = await procRes.json();

    extStatus(statusEl,
      `✅ <strong>Extraction complete!</strong><br>` +
      `📄 Document ID: <code>${docId}</code><br>` +
      `📋 Status: <strong>${procData.status || "processing"}</strong><br>` +
      `<em>Switch to the <strong>Documents</strong> tab to view full results.</em>`,
      "success");
  } catch (e) {
    extStatus(statusEl, `❌ Error: ${e.message}`, "error");
  } finally {
    extHideSpinner();
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
    listEl.innerHTML = docs.map(d => `
      <div class="result-card" data-doc-id="${d.document_id}" style="cursor:pointer;padding:1rem;margin-bottom:.75rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <strong>${d.filename || d.document_id}</strong>
            ${d.case_number ? `<span style="margin-left:.5rem;font-size:.8rem;color:var(--muted)">${d.case_number}</span>` : ""}
          </div>
          <span class="badge" style="background:${d.status==='completed'?'#2e7d32':d.status==='processing'?'#795900':'#1a3a5c'};color:#fff;padding:.2rem .65rem;border-radius:99px;font-size:.75rem">${d.status}</span>
        </div>
        ${d.court  ? `<div style="font-size:.82rem;color:var(--muted);margin-top:.25rem">🏛 ${d.court}</div>` : ""}
        ${d.date   ? `<div style="font-size:.82rem;color:var(--muted);">📅 ${d.date}</div>` : ""}
        ${d.parties_count  ? `<div style="font-size:.82rem;color:var(--muted);">👥 ${d.parties_count} parties</div>` : ""}
        ${d.sections_count ? `<div style="font-size:.82rem;color:var(--muted);">📑 ${d.sections_count} sections</div>` : ""}
      </div>
    `).join("");

    // Click to expand
    listEl.querySelectorAll(".result-card[data-doc-id]").forEach(card => {
      card.addEventListener("click", () => extViewDocument(card.dataset.docId));
    });
  } catch (e) {
    listEl.innerHTML = `<p style='color:#b71c1c'>Error loading documents: ${e.message}</p>`;
  } finally {
    extHideSpinner();
  }
}

document.getElementById("btn-ext-refresh")?.addEventListener("click", extLoadDocuments);

/* ── View document detail ────────────────────────────────────────────────── */
async function extViewDocument(docId) {
  extShowSpinner("Loading case details…");
  const detailEl  = document.getElementById("ext-doc-detail");
  const contentEl = document.getElementById("ext-detail-content");
  document.getElementById("ext-detail-id").textContent = docId;
  contentEl.innerHTML = "";
  detailEl.style.display = "block";
  detailEl.scrollIntoView({ behavior: "smooth" });

  try {
    const res  = await fetch(`${EXT_API}/documents/${docId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const doc  = await res.json();

    const meta = doc.metadata || {};
    const secs = doc.sections || [];
    const out  = doc.outcome  || {};
    const ins  = doc.insights || [];
    const cits = doc.citations|| [];

    contentEl.innerHTML = `
      <!-- Metadata card -->
      <div style="background:#f4f6f9;border-radius:8px;padding:1rem;margin-bottom:1rem;">
        <h4 style="margin-bottom:.5rem;color:var(--primary)">📋 Case Metadata</h4>
        ${meta.case_number ? `<p><strong>Case No.:</strong> ${meta.case_number}</p>` : ""}
        ${meta.court       ? `<p><strong>Court:</strong> ${meta.court}</p>` : ""}
        ${meta.date        ? `<p><strong>Date:</strong> ${meta.date}</p>` : ""}
        ${meta.case_type   ? `<p><strong>Type:</strong> ${meta.case_type}</p>` : ""}
        ${meta.judges?.length ? `<p><strong>Judges:</strong> ${meta.judges.join(", ")}</p>` : ""}
        ${meta.parties?.length ? `<p><strong>Parties:</strong> ${meta.parties.join(" v. ")}</p>` : ""}
      </div>

      <!-- Outcome -->
      ${out.decision ? `
      <div style="background:#e8f5e9;border-radius:8px;padding:1rem;margin-bottom:1rem;">
        <h4 style="margin-bottom:.5rem;color:#2e7d32">⚖️ Outcome</h4>
        <p><strong>Decision:</strong> ${out.decision}</p>
        ${out.risk_level ? `<p><strong>Risk Level:</strong> ${out.risk_level}</p>` : ""}
        ${out.explanation ? `<p style="font-size:.88rem;margin-top:.35rem">${out.explanation}</p>` : ""}
      </div>` : ""}

      <!-- Sections -->
      ${secs.length ? `
      <div style="margin-bottom:1rem;">
        <h4 style="margin-bottom:.5rem;color:var(--primary)">📑 Sections (${secs.length})</h4>
        ${secs.map(s => `
          <details style="border:1px solid var(--border);border-radius:8px;padding:.6rem .85rem;margin-bottom:.4rem;">
            <summary style="cursor:pointer;font-weight:600">${s.title || "Section"}</summary>
            <p style="font-size:.85rem;margin-top:.5rem;white-space:pre-wrap">${(s.content || s.text || "").slice(0,500)}${(s.content || s.text||"").length>500?"…":""}</p>
          </details>
        `).join("")}
      </div>` : ""}

      <!-- Citations -->
      ${cits.length ? `
      <div style="margin-bottom:1rem;">
        <h4 style="margin-bottom:.5rem;color:var(--primary)">📚 Citations (${cits.length})</h4>
        <ul style="font-size:.85rem;padding-left:1.2rem">${cits.map(c => `<li>${typeof c==="string"?c:c.text||JSON.stringify(c)}</li>`).join("")}</ul>
      </div>` : ""}

      <!-- Insights -->
      ${ins.length ? `
      <div>
        <h4 style="margin-bottom:.5rem;color:var(--primary)">💡 Legal Insights</h4>
        <ul style="font-size:.85rem;padding-left:1.2rem">${ins.map(i => `<li>${typeof i==="string"?i:i.insight||i.text||JSON.stringify(i)}</li>`).join("")}</ul>
      </div>` : ""}
    `;
  } catch (e) {
    contentEl.innerHTML = `<p style='color:#b71c1c'>❌ ${e.message}</p>`;
  } finally {
    extHideSpinner();
  }
}

/* ── Search ──────────────────────────────────────────────────────────────── */
document.getElementById("btn-ext-search")?.addEventListener("click", async () => {
  const query   = document.getElementById("ext-search-input").value.trim();
  const outcome = document.getElementById("ext-search-outcome").value;
  const yrFrom  = document.getElementById("ext-search-year-from").value;
  const yrTo    = document.getElementById("ext-search-year-to").value;
  const k       = parseInt(document.getElementById("ext-search-k").value);
  const resultsEl = document.getElementById("ext-search-results");

  if (!query) { extStatus(resultsEl, "⚠️ Please enter a search query.", "warn"); return; }

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
        ${h.court ? `<div style="font-size:.82rem;color:var(--muted)">🏛 ${h.court} ${h.year?`(${h.year})`:""}</div>` : ""}
        ${h.outcome ? `<div style="font-size:.82rem"><strong>Outcome:</strong> ${h.outcome}</div>` : ""}
        ${h.risk_level ? `<div style="font-size:.82rem"><strong>Risk:</strong> ${h.risk_level}</div>` : ""}
        ${h.key_legal_issues?.length ? `<div style="font-size:.82rem;margin-top:.3rem"><strong>Issues:</strong> ${h.key_legal_issues.join(", ")}</div>` : ""}
        ${h.reasoning_summary ? `<div style="font-size:.82rem;margin-top:.3rem;color:var(--muted)">${h.reasoning_summary.slice(0,200)}…</div>` : ""}
      </div>
    `).join("");
  } catch (e) {
    extStatus(resultsEl, `❌ Search error: ${e.message}`, "error");
  } finally {
    extHideSpinner();
  }
});
