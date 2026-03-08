/* ── Config ───────────────────────────────────────────────────────────────── */
const API = "http://localhost:5000/api";

/* ── Auth check & user display ───────────────────────────────────────────── */
(async function checkAuth() {
  try {
    const res = await fetch(`${API}/auth/me`, { credentials: "include" });
    const data = await res.json();
    if (!data.authenticated) { window.location.href = "/login.html"; return; }
    const nameEl   = document.getElementById("user-name");
    const avatarEl = document.getElementById("user-avatar");
    if (nameEl) nameEl.textContent = data.user.name;
    if (avatarEl) avatarEl.textContent = data.user.name.charAt(0);
  } catch {
    window.location.href = "/login.html";
  }
})();

/* Logout */
document.getElementById("btn-logout")?.addEventListener("click", async () => {
  await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
  window.location.href = "/login.html";
});

/* ── Toast notifications ──────────────────────────────────────────────────── */
function showToast(message, type = "info", duration = 4000) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  const icons = { success: "✔", error: "✘", warning: "⚠", info: "ℹ" };
  toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span class="toast-msg">${message}</span>`;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("toast-show"));
  setTimeout(() => {
    toast.classList.remove("toast-show");
    toast.addEventListener("transitionend", () => toast.remove());
  }, duration);
}

/* ── Sidebar navigation ───────────────────────────────────────────────────── */
const topbarCurrent = document.getElementById("topbar-current");
const navLabels = { similarity: "Similarity Search", compliance: "Civil Compliance", about: "About Us", help: "Help & User Guide" };

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
const filteredCasesList = document.getElementById("filtered-cases-list");
const filteredCasesContainer = document.getElementById("filtered-cases-container");
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
const statsGrid     = document.getElementById("category-cards-grid");
const categoryCardsPanel = document.getElementById("category-cards-panel");
const spinner       = document.getElementById("spinner");
const btnAddCase = document.getElementById("btn-add-case");

/* ── Utility ──────────────────────────────────────────────────────────────── */
function showSpinner(v) { spinner.style.display = v ? "flex" : "none"; }
function currentTab() { return document.querySelector(".tab.active").dataset.tab; }

let selectedFilename = null;  // tracks clicked case in the filtered list

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");

    const isClassify = tab.dataset.tab === "classify";
    const isByFile    = tab.dataset.tab === "by-file";
    btnSearch.style.display    = isClassify ? "none"         : "inline-block";
    btnClassify.style.display  = isClassify ? "inline-block" : "none";
    btnAddCase.style.display   = isClassify ? "inline-block" : "none";
    searchOptions.style.display = isClassify ? "none"        : "flex";
  });
});

/* Set initial button state for Classify tab (which is now the default) */
btnSearch.style.display    = "none";
btnClassify.style.display  = "inline-block";
btnAddCase.style.display   = "inline-block";
searchOptions.style.display = "none";

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
  selSubcategory.disabled  = !cat;
  filteredCasesList.style.display = "none";
  filteredCasesContainer.innerHTML = "";
  selectedFilename = null;
  if (!cat) {
    categoryCardsPanel.style.display = "none";
    return;
  }
  (categoriesData[cat] || []).forEach(({ subcategory, count }) => {
    const opt = document.createElement("option");
    opt.value = subcategory;
    opt.textContent = `${subcategory} (${count})`;
    selSubcategory.appendChild(opt);
  });
  // Show subcategory cards for this category
  renderCategoryCards(cat);
});

/* ── Subcategory → Show cases list ───────────────────────────────────────── */
selSubcategory.addEventListener("change", async () => {
  const cat = selCategory.value;
  const sub = selSubcategory.value;
  filteredCasesList.style.display = "none";
  filteredCasesContainer.innerHTML = "";
  selectedFilename = null;
  if (!sub) return;
  showSpinner(true);
  try {
    const res   = await fetch(`${API}/filenames?category=${encodeURIComponent(cat)}&subcategory=${encodeURIComponent(sub)}`);
    const files = await res.json();
    if (files.length) {
      filteredCasesContainer.innerHTML = files.map((f, i) => `
        <div class="filtered-case-row" data-filename="${f}">
          <span class="filtered-case-num">${i + 1}</span>
          <span class="filtered-case-name">📄 ${f}</span>
        </div>`).join("");
      filteredCasesList.style.display = "block";
      // Click to select a case
      filteredCasesContainer.querySelectorAll(".filtered-case-row").forEach(row => {
        row.addEventListener("click", () => {
          filteredCasesContainer.querySelectorAll(".filtered-case-row").forEach(r => r.classList.remove("selected"));
          row.classList.add("selected");
          selectedFilename = row.dataset.filename;
        });
      });
    } else {
      filteredCasesContainer.innerHTML = '<p style="color:var(--muted)">No cases found.</p>';
      filteredCasesList.style.display = "block";
    }
  } finally { showSpinner(false); }
});

/* ── Similarity Search ────────────────────────────────────────────────────── */
btnSearch.addEventListener("click", async () => {
  const tab         = currentTab();
  const globalSearch= chkGlobal.checked;
  const topN        = parseInt(selTopN.value, 10);
  const body        = { top_n: topN, global_search: globalSearch };

  if (tab === "by-file") {
    if (!selectedFilename) { alert("Please select a case from the list."); return; }
    body.filename = selectedFilename;
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
  // No longer renders the full overview — kept for initial data load
}

/* ── Render subcategory cards for a selected category ─────────────────────── */
function renderCategoryCards(cat) {
  const subcats = categoriesData[cat] || [];
  statsGrid.innerHTML = "";
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
  categoryCardsPanel.style.display = subcats.length ? "block" : "none";
}

// Event delegation for "View Cases" buttons
statsGrid.addEventListener("click", e => {
  const btn = e.target.closest(".btn-view-cases");
  if (btn) openCaseModal(btn.dataset.cat, btn.dataset.sub);
});

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
        btnAddCase.style.background = "#16a34a";
        showToast(`Case added successfully as '${data.case?.filename || "new case"}'.`, "success", 4000);
        if (clfFile) clfFile.value = "";
        if (clfText) clfText.value = "";
        loadCategories();
        setTimeout(() => {
          btnAddCase.textContent = "Add Case to Database";
          btnAddCase.style.background = "";
          btnAddCase.disabled = false;
        }, 2000);
      } else {
        const msg = data.error || "Failed to add case.";
        btnAddCase.textContent = "✘ Failed";
        btnAddCase.style.background = "#dc2626";
        showToast(msg, "error", 6000);
        setTimeout(() => {
          btnAddCase.textContent = "Add Case to Database";
          btnAddCase.style.background = "";
          btnAddCase.disabled = false;
        }, 3000);
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
