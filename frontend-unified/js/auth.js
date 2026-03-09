/* ── Authentication (port 5000 Flask backend) ──────────────────── */

const Auth = (() => {

  async function checkSession() {
    try {
      const r = await fetch(`${CONFIG.SEARCH_API}/auth/me`, { credentials: 'include' });
      if (!r.ok) return null;
      const d = await r.json();
      return d.authenticated ? d.user : null;
    } catch {
      return null;
    }
  }

  async function logout() {
    try {
      await fetch(`${CONFIG.SEARCH_API}/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch {}
    window.location.href = '/login.html';
  }

  function setUserUI(user) {
    const initial = (user.name || 'U').charAt(0).toUpperCase();
    const el = (id) => document.getElementById(id);
    if (el('sb-avatar'))    el('sb-avatar').textContent    = initial;
    if (el('sb-name'))      el('sb-name').textContent      = user.name || 'User';
    if (el('topbar-avatar'))el('topbar-avatar').textContent= initial;
    if (el('topbar-name'))  el('topbar-name').textContent  = user.name || 'User';
  }

  async function init() {
    const user = await checkSession();
    if (!user) {
      window.location.href = '/login.html';
      return null;
    }
    setUserUI(user);
    document.getElementById('btn-logout')?.addEventListener('click', logout);
    return user;
  }

  return { init, checkSession, logout, setUserUI };
})();
