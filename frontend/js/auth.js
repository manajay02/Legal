/* ── Auth page logic ──────────────────────────────────────────────────────── */
const API = "http://localhost:5000/api";

const loginCard   = document.getElementById("login-card");
const signupCard  = document.getElementById("signup-card");
const loginForm   = document.getElementById("login-form");
const signupForm  = document.getElementById("signup-form");
const loginError  = document.getElementById("login-error");
const signupError = document.getElementById("signup-error");

/* Toggle between login & signup */
document.getElementById("show-signup").addEventListener("click", e => {
  e.preventDefault();
  loginCard.style.display = "none";
  signupCard.style.display = "block";
  signupError.style.display = "none";
});
document.getElementById("show-login").addEventListener("click", e => {
  e.preventDefault();
  signupCard.style.display = "none";
  loginCard.style.display = "block";
  loginError.style.display = "none";
});

/* Helper: set button loading state */
function setLoading(btn, loading) {
  const text   = btn.querySelector(".btn-text");
  const loader = btn.querySelector(".btn-loader");
  btn.disabled        = loading;
  text.style.display  = loading ? "none"  : "inline";
  loader.style.display = loading ? "inline-block" : "none";
}

/* Helper: show error */
function showError(el, msg) {
  el.textContent = msg;
  el.style.display = "block";
}

/* ── Login ────────────────────────────────────────────────────────────────── */
loginForm.addEventListener("submit", async e => {
  e.preventDefault();
  loginError.style.display = "none";
  const btn = document.getElementById("login-btn");
  setLoading(btn, true);

  try {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        email:    document.getElementById("login-email").value.trim(),
        password: document.getElementById("login-password").value,
      })
    });
    const data = await res.json();
    if (data.success) {
      window.location.href = "/";
    } else {
      showError(loginError, data.error || "Login failed.");
    }
  } catch {
    showError(loginError, "Unable to connect to server.");
  } finally {
    setLoading(btn, false);
  }
});

/* ── Signup ───────────────────────────────────────────────────────────────── */
signupForm.addEventListener("submit", async e => {
  e.preventDefault();
  signupError.style.display = "none";

  const password = document.getElementById("signup-password").value;
  const confirm  = document.getElementById("signup-confirm").value;
  if (password !== confirm) {
    showError(signupError, "Passwords do not match.");
    return;
  }

  const btn = document.getElementById("signup-btn");
  setLoading(btn, true);

  try {
    const res = await fetch(`${API}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        name:     document.getElementById("signup-name").value.trim(),
        email:    document.getElementById("signup-email").value.trim(),
        password: password,
      })
    });
    const data = await res.json();
    if (data.success) {
      window.location.href = "/";
    } else {
      showError(signupError, data.error || "Signup failed.");
    }
  } catch {
    showError(signupError, "Unable to connect to server.");
  } finally {
    setLoading(btn, false);
  }
});
