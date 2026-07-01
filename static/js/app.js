import { api, token, setUnauthorizedHandler } from "./api.js";
import { $, toast, formData } from "./ui.js";
import { renderDashboard } from "./views/dashboard.js";
import { renderInventory } from "./views/inventory.js";
import { renderScan } from "./views/scan.js";
import { renderRecipes, renderRecommendations, renderSaved } from "./views/recipes.js";
import { renderShopping } from "./views/shopping.js";
import { renderMealPlan } from "./views/mealplan.js";
import { renderSustainability } from "./views/sustainability.js";
import { renderCommunity } from "./views/community.js";
import { renderVoice } from "./views/voice.js";
import { renderProfile } from "./views/profile.js";

const view = $("#view");
const navigate = (key) => { location.hash = `#/${key}`; };

const ROUTES = {
  dashboard:       { label: "Dashboard",        icon: "🏠", render: (r) => renderDashboard(r, { navigate }) },
  inventory:       { label: "Inventory",        icon: "📦", render: renderInventory },
  scan:            { label: "Scan",             icon: "📷", render: renderScan },
  recipes:         { label: "Recipes",          icon: "📖", render: renderRecipes },
  recommendations: { label: "Recommendations",  icon: "🍳", render: renderRecommendations },
  saved:           { label: "Saved",            icon: "❤️", render: renderSaved },
  shopping:        { label: "Shopping",         icon: "🛒", render: renderShopping },
  mealplan:        { label: "Meal Planner",     icon: "🗓️", render: renderMealPlan },
  sustainability:  { label: "Sustainability",   icon: "🌍", render: renderSustainability },
  community:       { label: "Community",        icon: "💬", render: renderCommunity },
  voice:           { label: "Voice Mode",       icon: "🎤", render: renderVoice },
  profile:         { label: "Profile",          icon: "⚙️", render: (r) => renderProfile(r, { onChange: refreshUser }) },
};

function buildNav() {
  const nav = $("#nav");
  nav.innerHTML = "";
  Object.entries(ROUTES).forEach(([key, r]) => {
    const a = document.createElement("a");
    a.href = `#/${key}`;
    a.dataset.key = key;
    a.className = "nav-link";
    a.innerHTML = `<span class="nav-icon">${r.icon}</span><span>${r.label}</span>`;
    nav.appendChild(a);
  });
}

async function router() {
  if (!token.get()) return showAuth();

  let key = (location.hash.replace(/^#\//, "") || "dashboard");
  if (!ROUTES[key]) key = "dashboard";

  $$(".nav-link").forEach((a) => a.classList.toggle("active", a.dataset.key === key));
  document.body.classList.remove("nav-open");
  view.innerHTML = "";
  try {
    await ROUTES[key].render(view);
  } catch (err) {
    view.innerHTML = `<p class="muted">${err.message}</p>`;
  }
}

function $$(sel) { return [...document.querySelectorAll(sel)]; }

// ---------------- auth ----------------
function showAuth() {
  $("#appShell").classList.add("hidden");
  $("#authScreen").classList.remove("hidden");
}

async function showApp() {
  $("#authScreen").classList.add("hidden");
  $("#appShell").classList.remove("hidden");
  await refreshUser();
  router();
}

async function refreshUser(user) {
  try {
    const me = user || await api.me();
    $("#userEmail").textContent = me.email;
    $("#userMeta").textContent = `${me.id} · ${me.dietary_preference}`;
  } catch { /* ignore */ }
}

function wireAuth() {
  $$(".auth-tab").forEach((tab) => tab.addEventListener("click", () => {
    $$(".auth-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    $("#loginForm").classList.toggle("hidden", tab.dataset.tab !== "login");
    $("#registerForm").classList.toggle("hidden", tab.dataset.tab !== "register");
  }));

  $("#loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      const tok = await api.login(d.email, d.password);
      token.set(tok.access_token);
      toast("Welcome back!");
      showApp();
    } catch (err) { toast(err.message, true); }
  });

  $("#registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await api.register({
        email: d.email,
        full_name: d.full_name || null,
        password: d.password,
        dietary_preference: d.dietary_preference,
      });
      const tok = await api.login(d.email, d.password);
      token.set(tok.access_token);
      toast("Account created!");
      showApp();
    } catch (err) { toast(err.message, true); }
  });

  $("#logoutBtn").addEventListener("click", () => {
    token.clear();
    toast("Logged out.");
    showAuth();
  });

  $("#menuToggle").addEventListener("click", () => document.body.classList.toggle("nav-open"));
}

// ---------------- boot ----------------
setUnauthorizedHandler(showAuth);
buildNav();
wireAuth();
window.addEventListener("hashchange", router);

(async function init() {
  if (token.get()) {
    try { await api.me(); return showApp(); }
    catch { token.clear(); }
  }
  showAuth();
})();
