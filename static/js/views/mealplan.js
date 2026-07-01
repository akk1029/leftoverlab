import { api } from "../api.js";
import { $, escapeHtml, toApiDate, formData, toast, h, loading } from "../ui.js";

const SLOTS = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"];
const DAY_NAMES = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"];

export async function renderMealPlan(root) {
  const today = new Date().toISOString().slice(0, 10);
  root.innerHTML = `
    <h1 class="view-title">Smart Meal Planner</h1>
    <div class="card">
      <h2>Generate a weekly plan</h2>
      <p class="muted">Prioritises recipes that use up ingredients you already have (and soon-to-expire stock).</p>
      <form id="genForm">
        <div class="row">
          <label>Week start<input name="week_start" type="date" value="${today}" required /></label>
          <label>Days<input name="days" type="number" min="1" max="14" value="7" /></label>
        </div>
        <label>Plan name<input name="name" value="Weekly Plan" /></label>
        <fieldset class="meals">
          <legend>Meals per day</legend>
          ${SLOTS.map((s, i) => `<label class="check"><input type="checkbox" value="${s}" ${i < 3 ? "checked" : ""}/> ${s}</label>`).join("")}
        </fieldset>
        <label class="check"><input type="checkbox" name="respect" checked /> Respect my dietary preference</label>
        <button type="submit">Generate plan</button>
      </form>
    </div>
    <div id="plans">${loading()}</div>`;

  $("#genForm", root).addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    const meals = [...e.target.querySelectorAll(".meals input:checked")].map((i) => i.value);
    if (!meals.length) return toast("Select at least one meal.", true);
    try {
      await api.generateMealPlan({
        week_start: toApiDate(d.week_start),
        name: d.name || "Weekly Plan",
        days: Number(d.days) || 7,
        meals_per_day: meals,
        respect_dietary_preference: e.target.respect.checked,
      });
      toast("Meal plan generated.");
      load();
    } catch (err) { toast(err.message, true); }
  });

  const box = $("#plans", root);
  async function load() {
    box.innerHTML = loading();
    try {
      const plans = await api.listMealPlans();
      if (!plans.length) { box.innerHTML = `<p class="muted">No plans yet — generate one above.</p>`; return; }
      box.innerHTML = "";
      plans.forEach((p) => box.appendChild(planCard(p, load)));
    } catch (err) { box.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`; }
  }
  load();
}

function planCard(p, reload) {
  const byDay = {};
  p.entries.forEach((e) => { (byDay[e.day_offset] ||= []).push(e); });

  const days = Object.keys(byDay).map(Number).sort((a, b) => a - b).map((day) => `
    <div class="day-col">
      <h4>${DAY_NAMES[day] || `Day ${day + 1}`}</h4>
      ${byDay[day].map((e) => `
        <div class="meal-slot">
          <span class="slot-label">${escapeHtml(e.meal_slot)}</span>
          <span>${e.recipe ? escapeHtml(e.recipe.title) : '<span class="muted">—</span>'}</span>
        </div>`).join("")}
    </div>`).join("");

  const el = h(`
    <div class="card">
      <div class="card-head">
        <h2>${escapeHtml(p.name)} <span class="muted">· starts ${escapeHtml(p.week_start)}</span></h2>
        <button class="icon-btn danger" title="Delete plan">✕</button>
      </div>
      <div class="week-grid">${days}</div>
    </div>`);
  el.querySelector(".icon-btn").addEventListener("click", async () => {
    if (!confirm(`Delete "${p.name}"?`)) return;
    try { await api.deleteMealPlan(p.id); toast("Deleted."); reload(); }
    catch (err) { toast(err.message, true); }
  });
  return el;
}
