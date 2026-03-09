/* ── App Orchestrator ───────────────────────────────────────────── */
/* Must be loaded BEFORE all other modules in index.html            */

const App = (() => {
  /* ── Toast notification ─────────────────────────────────────────── */
  function toast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.id = id;
    const icons = { success:'✓', error:'✕', warning:'⚠', info:'ℹ' };
    el.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-msg">${esc(message)}</span>
      <button class="toast-close" onclick="App.dismissToast('${id}')">✕</button>`;
    container.appendChild(el);
    requestAnimationFrame(() => el.classList.add('show'));
    setTimeout(() => dismissToast(id), duration);
  }

  function dismissToast(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('show');
    el.classList.add('hide');
    el.addEventListener('transitionend', () => el.remove(), { once: true });
  }

  /* ── Loading overlay ─────────────────────────────────────────────  */
  function showLoading(msg = 'Processing…') {
    let ov = document.getElementById('loading-overlay');
    if (!ov) return;
    const span = ov.querySelector('.loading-msg');
    if (span) span.textContent = msg;
    ov.style.display = '';
    requestAnimationFrame(() => ov.classList.add('show'));
  }

  function hideLoading() {
    const ov = document.getElementById('loading-overlay');
    if (!ov) return;
    ov.classList.remove('show');
    setTimeout(() => { ov.style.display = 'none'; }, 300);
  }

  /* ── Navigation ──────────────────────────────────────────────────── */
  const PANEL_TITLES = {
    dashboard:  'Dashboard',
    similarity: 'Case Similarity Search',
    scorer:     'Argument Strength Scorer',
    extractor:  'Document Extractor',
    compliance: 'Compliance Auditor',
  };

  function navigate(target) {
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.sb-item').forEach(i => i.classList.remove('active'));

    const panel = document.getElementById(`panel-${target}`);
    const sbItem = document.querySelector(`.sb-item[data-panel="${target}"]`);
    if (panel) panel.classList.add('active');
    if (sbItem) sbItem.classList.add('active');

    const titleEl = document.getElementById('topbar-page');
    if (titleEl) titleEl.textContent = PANEL_TITLES[target] || target;

    // Close sidebar on mobile
    if (window.innerWidth < 768) document.body.classList.add('sidebar-collapsed');
  }

  function setupNav() {
    document.querySelectorAll('.sb-item[data-panel]').forEach(item => {
      item.addEventListener('click', () => navigate(item.dataset.panel));
    });

    // Dashboard "Go to" cards
    document.querySelectorAll('.feature-card[data-goto]').forEach(card => {
      card.addEventListener('click', () => navigate(card.dataset.goto));
    });

    // Sidebar toggle
    const toggle = document.getElementById('sidebar-toggle');
    if (toggle) toggle.addEventListener('click', () => document.body.classList.toggle('sidebar-collapsed'));

    // Default panel
    navigate('dashboard');
  }

  /* ── Service health polling ─────────────────────────────────────── */
  async function checkServiceHealth(name, url, svcId) {
    const updateStatus = (online) => {
      // Topbar pill (id="svc-{key}")
      const pill = document.getElementById(`svc-${svcId}`);
      if (pill) {
        pill.className = `svc-pill ${online ? 'online' : 'offline'}`;
      }
      // Dashboard card status (id="svc-status-{key}")
      const cardStatus = document.getElementById(`svc-status-${svcId}`);
      if (cardStatus) {
        const dot  = cardStatus.querySelector('.pulse-dot');
        const span = cardStatus.querySelector('span');
        if (dot)  dot.className  = `pulse-dot ${online ? 'online' : 'offline'}`;
        if (span) span.textContent = online ? 'Online' : 'Offline';
      }
    };
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(3000) });
      updateStatus(r.ok);
    } catch {
      updateStatus(false);
    }
  }

  async function pollAllHealth() {
    await Promise.allSettled([
      checkServiceHealth('Search',     CONFIG.HEALTH.search,     'search'),
      checkServiceHealth('Scorer',     CONFIG.HEALTH.scorer,     'scorer'),
      checkServiceHealth('Extractor',  CONFIG.HEALTH.extractor,  'extractor'),
      checkServiceHealth('Compliance', CONFIG.HEALTH.compliance, 'compliance'),
    ]);
  }

  /* ── Bootstrap ───────────────────────────────────────────────────── */
  async function boot() {
    setupNav();

    // Auth guard (redirects to login.html if not authenticated)
    await Auth.init();

    // Init all modules in parallel
    await Promise.allSettled([
      Similarity.init(),
      Scorer.init(),
      Extractor.init(),
      Compliance.init(),
    ]);

    // Initial health check + periodic refresh
    await pollAllHealth();
    setInterval(pollAllHealth, 30000);
  }

  function esc(s) {
    return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  return { toast, dismissToast, showLoading, hideLoading, navigate, pollAllHealth, boot };
})();

document.addEventListener('DOMContentLoaded', () => App.boot());
