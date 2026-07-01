import { api } from "../api.js";
import { $, escapeHtml, formData, money, toast, loading } from "../ui.js";

export async function renderSustainability(root) {
  root.innerHTML = `
    <h1 class="view-title">Sustainability Dashboard</h1>
    <div id="dash">${loading()}</div>
    <div class="grid-2">
      <div class="card">
        <h2>Log a food-saving action</h2>
        <form id="recForm">
          <label>Description<input name="description" placeholder="Used up leftover chicken" /></label>
          <div class="row">
            <label>Money saved<input name="money_saved" type="number" min="0.01" step="0.01" required /></label>
            <label>CO₂e reduced (kg)<input name="carbon_reduction_kg" type="number" min="0.01" step="0.01" required /></label>
          </div>
          <label>Food saved (kg)<input name="food_saved_kg" type="number" min="0" step="0.01" value="0" /></label>
          <button type="submit">Log action</button>
        </form>
      </div>
      <div class="card">
        <h2>Recent actions</h2>
        <ul class="list" id="recList">${loading()}</ul>
      </div>
    </div>`;

  async function loadDash() {
    const el = $("#dash", root);
    try {
      const d = await api.dashboard();
      el.innerHTML = `
        <div class="stat-grid">
          <div class="stat card"><div class="stat-num">${money(d.total_money_saved)}</div><div class="stat-label">Total money saved</div></div>
          <div class="stat card"><div class="stat-num">${d.total_carbon_reduction_kg} kg</div><div class="stat-label">CO₂e avoided</div></div>
          <div class="stat card"><div class="stat-num">${d.total_food_saved_kg} kg</div><div class="stat-label">Food rescued</div></div>
          <div class="stat card"><div class="stat-num">${d.records_count}</div><div class="stat-label">Actions logged</div></div>
        </div>
        <div class="card">
          <h2>🏆 Achievements</h2>
          ${d.achievements.length
            ? `<div class="achievements">${d.achievements.map((a) => `<span class="achievement">${escapeHtml(a)}</span>`).join("")}</div>`
            : `<p class="muted">Log actions to unlock achievements.</p>`}
        </div>`;
    } catch (err) { el.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`; }
  }

  async function loadList() {
    const ul = $("#recList", root);
    try {
      const rows = await api.listRecords();
      if (!rows.length) { ul.innerHTML = `<li class="muted">No actions logged yet.</li>`; return; }
      ul.innerHTML = rows.map((r) => `
        <li><span><strong>${escapeHtml(r.description || "Food saved")}</strong>
          <span class="muted"> · ${new Date(r.created_at).toLocaleDateString()}</span></span>
          <span class="badge">${money(r.money_saved)} · ${r.carbon_reduction_kg}kg</span></li>`).join("");
    } catch (err) { ul.innerHTML = `<li class="muted">${escapeHtml(err.message)}</li>`; }
  }

  $("#recForm", root).addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await api.addRecord({
        description: d.description || null,
        money_saved: parseFloat(d.money_saved),
        carbon_reduction_kg: parseFloat(d.carbon_reduction_kg),
        food_saved_kg: parseFloat(d.food_saved_kg) || 0,
      });
      e.target.reset();
      toast("Action logged. Nice work! 🌱");
      loadDash(); loadList();
    } catch (err) { toast(err.message, true); }
  });

  loadDash(); loadList();
}
