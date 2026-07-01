import { api } from "../api.js";
import { $, escapeHtml, formData, modal, toast, h, money, loading } from "../ui.js";

const CATEGORIES = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"];

// ---------------- Browse + filter + create ----------------
export async function renderRecipes(root) {
  root.innerHTML = `
    <div class="card-head view-head">
      <h1 class="view-title">Recipes</h1>
      <button id="newRecipe">+ New recipe</button>
    </div>
    <div class="card">
      <form id="filters" class="filters">
        <label>Search<input name="search" placeholder="title / description" /></label>
        <label>Category<select name="category"><option value="">any</option>${CATEGORIES.map((c) => `<option>${c}</option>`).join("")}</select></label>
        <label>Max time (min)<input name="max_cooking_time" type="number" min="0" /></label>
        <label>Max cost<input name="max_cost" type="number" min="0" step="0.01" /></label>
        <label>Dietary tag<input name="dietary_tag" placeholder="Vegan" /></label>
        <button type="submit">Filter</button>
      </form>
    </div>
    <div id="recipeGrid" class="recipe-grid">${loading()}</div>`;

  const grid = $("#recipeGrid", root);

  async function load(filters) {
    grid.innerHTML = loading();
    try {
      const recipes = await api.listRecipes(filters);
      if (!recipes.length) {
        grid.innerHTML = `<p class="muted">No recipes found. Create one, or run <code>python -m scripts.seed</code> for samples.</p>`;
        return;
      }
      grid.innerHTML = "";
      recipes.forEach((r) => grid.appendChild(card(r, () => load(current()))));
    } catch (err) {
      grid.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
    }
  }

  const current = () => {
    const d = formData($("#filters", root));
    return {
      search: d.search,
      category: d.category,
      max_cooking_time: d.max_cooking_time,
      max_cost: d.max_cost,
      dietary_tag: d.dietary_tag,
    };
  };

  $("#filters", root).addEventListener("submit", (e) => { e.preventDefault(); load(current()); });
  $("#newRecipe", root).addEventListener("click", () => createModal(() => load(current())));
  load({});
}

function card(r, reload) {
  const el = h(`
    <div class="card recipe-card">
      <span class="badge">${escapeHtml(r.category)}</span>
      <h3>${escapeHtml(r.title)}</h3>
      <p class="muted clamp">${escapeHtml(r.description || "No description.")}</p>
      <div class="meta muted">
        ${r.cooking_time_minutes != null ? `⏱ ${r.cooking_time_minutes}m` : ""}
        ${r.estimated_cost != null ? ` · ${money(r.estimated_cost)}` : ""}
        ${r.dietary_tags ? ` · ${escapeHtml(r.dietary_tags)}` : ""}
      </div>
      <div class="row-actions">
        <button class="small" data-act="view">View</button>
        <button class="small secondary" data-act="save">♥ Save</button>
      </div>
    </div>`);
  el.querySelector('[data-act="view"]').addEventListener("click", () => detailModal(r.id, reload));
  el.querySelector('[data-act="save"]').addEventListener("click", async () => {
    try { await api.saveRecipe(r.id); toast("Saved to your collection."); }
    catch (err) { toast(err.message, true); }
  });
  return el;
}

async function detailModal(id, reload) {
  const body = h(`<div>${loading()}</div>`);
  const close = modal("Recipe", body);
  try {
    const r = await api.getRecipe(id);
    const me = await api.me();
    const mine = r.author_id === me.id;
    body.innerHTML = `
      <span class="badge">${escapeHtml(r.category)}</span>
      <h2>${escapeHtml(r.title)}</h2>
      <p>${escapeHtml(r.description || "")}</p>
      <div class="meta muted">
        ${r.cooking_time_minutes != null ? `⏱ ${r.cooking_time_minutes} min` : ""}
        ${r.estimated_cost != null ? ` · ${money(r.estimated_cost)}` : ""}
        ${r.dietary_tags ? ` · ${escapeHtml(r.dietary_tags)}` : ""}
      </div>
      <h4>Ingredients</h4>
      <ul>${(r.ingredients_text || "").split(/[\n,;]+/).filter(Boolean).map((i) => `<li>${escapeHtml(i.trim())}</li>`).join("") || "<li class='muted'>—</li>"}</ul>
      <h4>Instructions</h4>
      <p class="pre">${escapeHtml(r.instructions || "—")}</p>
      <div class="row-actions">
        <button data-act="save">♥ Save</button>
        ${mine ? `<button class="danger" data-act="del">Delete</button>` : ""}
      </div>`;
    body.querySelector('[data-act="save"]').addEventListener("click", async () => {
      try { await api.saveRecipe(r.id); toast("Saved."); } catch (err) { toast(err.message, true); }
    });
    const del = body.querySelector('[data-act="del"]');
    if (del) del.addEventListener("click", async () => {
      if (!confirm("Delete this recipe?")) return;
      try { await api.deleteRecipe(r.id); toast("Deleted."); close(); reload?.(); }
      catch (err) { toast(err.message, true); }
    });
  } catch (err) {
    body.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
  }
}

function createModal(reload) {
  const form = h(`
    <form class="modal-form">
      <label>Title<input name="title" required /></label>
      <label>Category<select name="category">${CATEGORIES.map((c) => `<option>${c}</option>`).join("")}</select></label>
      <label>Description<textarea name="description" rows="2"></textarea></label>
      <label>Ingredients (one per line)<textarea name="ingredients_text" rows="4" placeholder="Tomato&#10;Garlic"></textarea></label>
      <label>Instructions<textarea name="instructions" rows="4"></textarea></label>
      <div class="row">
        <label>Cooking time (min)<input name="cooking_time_minutes" type="number" min="0" /></label>
        <label>Estimated cost<input name="estimated_cost" type="number" min="0" step="0.01" /></label>
      </div>
      <label>Dietary tags (comma-separated)<input name="dietary_tags" placeholder="Vegan,Gluten-Free" /></label>
      <button type="submit">Create recipe</button>
    </form>`);
  const close = modal("New recipe", form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await api.createRecipe({
        title: d.title,
        category: d.category,
        description: d.description || null,
        ingredients_text: d.ingredients_text || "",
        instructions: d.instructions || "",
        cooking_time_minutes: d.cooking_time_minutes ? Number(d.cooking_time_minutes) : null,
        estimated_cost: d.estimated_cost ? Number(d.estimated_cost) : null,
        dietary_tags: d.dietary_tags || null,
      });
      toast("Recipe created."); close(); reload?.();
    } catch (err) { toast(err.message, true); }
  });
}

// ---------------- Recommendations ----------------
export async function renderRecommendations(root) {
  root.innerHTML = `
    <h1 class="view-title">Recommended for you</h1>

    <div class="card">
      <div class="card-head">
        <h2>🍲 Generate from TheMealDB</h2>
        <button id="genBtn">Generate recipes</button>
      </div>
      <p class="muted">Real recipes matched to your inventory. Automatically respects your
        dietary preference and filters out your declared allergies.</p>
      <div class="row-actions genopts">
        <label class="check"><input type="checkbox" id="optDietary" checked /> Respect dietary preference</label>
        <label class="check"><input type="checkbox" id="optAllergy" checked /> Exclude my allergies</label>
      </div>
      <div id="genResults" class="recipe-grid" style="margin-top:14px"></div>
    </div>

    <div class="card">
      <h2>📖 From your recipe library</h2>
      <p class="muted">Ranked by how much of each saved/seeded recipe you already have.</p>
      <div id="recs">${loading()}</div>
    </div>`;

  // --- local library recommendations ---
  const box = $("#recs", root);
  try {
    const recs = await api.recommendations(20);
    if (!recs.length) {
      box.innerHTML = `<p class="muted">No matches yet. Add ingredients, and seed/create some recipes.</p>`;
    } else {
      box.innerHTML = "";
      recs.forEach((r) => {
        const pct = Math.round(r.match_score * 100);
        box.insertAdjacentHTML("beforeend", `
          <div class="rec-row">
            <div class="card-head"><h3>${escapeHtml(r.recipe.title)} <span class="badge">${escapeHtml(r.recipe.category)}</span></h3><strong>${pct}%</strong></div>
            <div class="bar"><span style="width:${pct}%"></span></div>
            <div class="meta muted">Have: ${r.matched_ingredients.map(escapeHtml).join(", ") || "—"}<br>Need: ${r.missing_ingredients.map(escapeHtml).join(", ") || "—"}</div>
          </div>`);
      });
    }
  } catch (err) {
    box.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
  }

  // --- TheMealDB generation ---
  const grid = $("#genResults", root);
  $("#genBtn", root).addEventListener("click", async () => {
    grid.innerHTML = loading("Searching TheMealDB for recipes you can make…");
    try {
      const res = await api.generateFromMealDB({
        limit: 12,
        respectDietary: $("#optDietary", root).checked,
        respectAllergies: $("#optAllergy", root).checked,
      });
      if (!res.recipes.length) {
        grid.innerHTML = `<p class="muted">No safe matches found. Add more common ingredients (e.g. chicken, tomato, onion, rice) to your inventory, or loosen the filters above.</p>`;
        return;
      }
      const note = `Preference: <strong>${escapeHtml(res.dietary_preference)}</strong>` +
        (res.allergies_applied.length ? ` · avoiding: ${res.allergies_applied.map(escapeHtml).join(", ")}` : "");
      grid.innerHTML = `<p class="muted" style="grid-column:1/-1">${note}</p>`;
      res.recipes.forEach((r) => grid.appendChild(genCard(r)));
    } catch (err) {
      grid.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
    }
  });
}

function genCard(r) {
  const pct = Math.round(r.match_score * 100);
  const el = h(`
    <div class="card recipe-card gen-card">
      ${r.thumbnail ? `<img class="thumb" src="${escapeHtml(r.thumbnail)}" alt="" loading="lazy" />` : ""}
      <span class="badge">${escapeHtml(r.category || "Recipe")}${r.area ? " · " + escapeHtml(r.area) : ""}</span>
      <h3>${escapeHtml(r.title)}</h3>
      <div class="bar"><span style="width:${pct}%"></span></div>
      <div class="meta muted">${pct}% on hand · need: ${r.missing_ingredients.slice(0, 6).map(escapeHtml).join(", ") || "—"}</div>
      <div class="row-actions">
        <button class="small" data-act="view">View</button>
        <button class="small secondary" data-act="import">＋ Import</button>
      </div>
    </div>`);
  el.querySelector('[data-act="import"]').addEventListener("click", async (e) => {
    e.target.disabled = true;
    try { const saved = await api.importGenerated(r.mealdb_id); toast(`Imported as ${saved.id}.`); }
    catch (err) { toast(err.message, true); e.target.disabled = false; }
  });
  el.querySelector('[data-act="view"]').addEventListener("click", () => genDetailModal(r));
  return el;
}

function genDetailModal(r) {
  const body = h(`
    <div>
      ${r.thumbnail ? `<img class="thumb-lg" src="${escapeHtml(r.thumbnail)}" alt="" />` : ""}
      <span class="badge">${escapeHtml(r.category || "Recipe")}${r.area ? " · " + escapeHtml(r.area) : ""}</span>
      <div class="meta muted">${Math.round(r.match_score * 100)}% of ingredients on hand${r.tags.length ? " · " + r.tags.map(escapeHtml).join(", ") : ""}</div>
      <h4>Ingredients</h4>
      <ul>${r.ingredients.map((i) => {
        const have = r.matched_ingredients.includes(i);
        return `<li>${have ? "✅ " : "🛒 "}${escapeHtml(i)}</li>`;
      }).join("")}</ul>
      <h4>Instructions</h4>
      <p class="pre">${escapeHtml(r.instructions || "—")}</p>
      ${r.youtube_url ? `<p><a href="${escapeHtml(r.youtube_url)}" target="_blank" rel="noopener">▶ Watch on YouTube</a></p>` : ""}
      <button data-act="import">＋ Import to my recipes</button>
    </div>`);
  const close = modal(r.title, body);
  body.querySelector('[data-act="import"]').addEventListener("click", async (e) => {
    e.target.disabled = true;
    try { const saved = await api.importGenerated(r.mealdb_id); toast(`Imported as ${saved.id}.`); close(); }
    catch (err) { toast(err.message, true); e.target.disabled = false; }
  });
}

// ---------------- Saved recipes ----------------
export async function renderSaved(root) {
  root.innerHTML = `<h1 class="view-title">Saved Recipes</h1><div id="savedGrid" class="recipe-grid">${loading()}</div>`;
  const grid = $("#savedGrid", root);
  async function load() {
    grid.innerHTML = loading();
    try {
      const recipes = await api.savedRecipes();
      if (!recipes.length) { grid.innerHTML = `<p class="muted">No saved recipes yet.</p>`; return; }
      grid.innerHTML = "";
      recipes.forEach((r) => {
        const el = card(r, load);
        const btn = el.querySelector('[data-act="save"]');
        btn.textContent = "♡ Unsave";
        btn.replaceWith(btn.cloneNode(true));
        el.querySelector('[data-act="save"]').addEventListener("click", async () => {
          try { await api.unsaveRecipe(r.id); toast("Removed."); load(); }
          catch (err) { toast(err.message, true); }
        });
        grid.appendChild(el);
      });
    } catch (err) { grid.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`; }
  }
  load();
}
