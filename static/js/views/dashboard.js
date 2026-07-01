import { api } from "../api.js";
import { escapeHtml, expiryBadge, money, loading } from "../ui.js";

export async function renderDashboard(root, { navigate } = {}) {
  root.innerHTML = `<h1 class="view-title">Dashboard</h1><div id="dashBody">${loading()}</div>`;
  const body = root.querySelector("#dashBody");

  try {
    const [ingredients, expiring, dash, saved] = await Promise.all([
      api.listIngredients(),
      api.expiring(3),
      api.dashboard(),
      api.savedRecipes(),
    ]);

    body.innerHTML = `
      <div class="stat-grid">
        <div class="stat card"><div class="stat-num">${ingredients.length}</div><div class="stat-label">Ingredients in stock</div></div>
        <div class="stat card ${expiring.length ? "stat-warn" : ""}"><div class="stat-num">${expiring.length}</div><div class="stat-label">Expiring within 3 days</div></div>
        <div class="stat card"><div class="stat-num">${money(dash.total_money_saved)}</div><div class="stat-label">Money saved</div></div>
        <div class="stat card"><div class="stat-num">${dash.total_carbon_reduction_kg} kg</div><div class="stat-label">CO₂e avoided</div></div>
        <div class="stat card"><div class="stat-num">${saved.length}</div><div class="stat-label">Saved recipes</div></div>
        <div class="stat card"><div class="stat-num">${dash.records_count}</div><div class="stat-label">Food-saving actions</div></div>
      </div>

      <div class="card">
        <div class="card-head"><h2>⚠️ Use these soon</h2><button class="link" data-go="inventory">View inventory →</button></div>
        <ul class="list" id="expList"></ul>
      </div>

      <div class="card">
        <div class="card-head"><h2>Quick actions</h2></div>
        <div class="quick-actions">
          <button data-go="scan">📷 Scan ingredients</button>
          <button data-go="recommendations">🍳 Recommend recipes</button>
          <button data-go="mealplan">🗓️ Plan my week</button>
          <button data-go="shopping">🛒 Shopping lists</button>
        </div>
      </div>`;

    const expList = body.querySelector("#expList");
    if (!expiring.length) {
      expList.innerHTML = `<li class="muted">Nothing expiring soon — nice and fresh! 🎉</li>`;
    } else {
      expiring.forEach((ing) => {
        expList.insertAdjacentHTML("beforeend", `
          <li><span><strong>${escapeHtml(ing.name)}</strong>
          <span class="muted"> · exp ${ing.expiry_date_display}</span></span>
          ${expiryBadge(ing.days_until_expiry)}</li>`);
      });
    }

    body.querySelectorAll("[data-go]").forEach((b) =>
      b.addEventListener("click", () => navigate(b.dataset.go)));
  } catch (err) {
    body.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
  }
}
