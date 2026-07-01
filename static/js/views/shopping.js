import { api } from "../api.js";
import { $, escapeHtml, formData, modal, toast, h, loading } from "../ui.js";

export async function renderShopping(root) {
  root.innerHTML = `
    <div class="card-head view-head">
      <h1 class="view-title">Shopping Lists</h1>
      <div class="row-actions">
        <button id="newList">+ New list</button>
        <button id="genList" class="secondary">⚙ Generate from recipes</button>
      </div>
    </div>
    <div id="lists">${loading()}</div>`;

  const box = $("#lists", root);

  async function load() {
    box.innerHTML = loading();
    try {
      const lists = await api.listShoppingLists();
      if (!lists.length) { box.innerHTML = `<p class="muted">No shopping lists yet.</p>`; return; }
      box.innerHTML = "";
      lists.forEach((l) => box.appendChild(listCard(l, load)));
    } catch (err) { box.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`; }
  }

  $("#newList", root).addEventListener("click", () => newListModal(load));
  $("#genList", root).addEventListener("click", () => generateModal(load));
  load();
}

function listCard(l, reload) {
  const el = h(`
    <div class="card">
      <div class="card-head">
        <h2>${escapeHtml(l.name)} <span class="muted">(${escapeHtml(l.id)})</span></h2>
        <button class="icon-btn danger" data-act="del" title="Delete list">✕</button>
      </div>
      <ul class="list checklist"></ul>
      <form class="add-item">
        <input name="name" placeholder="Add item…" required />
        <input name="quantity" type="number" min="0.01" step="0.01" value="1" style="max-width:90px" />
        <button type="submit" class="small">Add</button>
      </form>
    </div>`);

  const ul = el.querySelector(".checklist");
  if (!l.items.length) ul.innerHTML = `<li class="muted">Empty list.</li>`;
  l.items.forEach((it) => ul.appendChild(itemRow(l.id, it, reload)));

  el.querySelector('[data-act="del"]').addEventListener("click", async () => {
    if (!confirm(`Delete list "${l.name}"?`)) return;
    try { await api.deleteShoppingList(l.id); toast("List deleted."); reload(); }
    catch (err) { toast(err.message, true); }
  });

  el.querySelector(".add-item").addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await api.addShoppingItem(l.id, { name: d.name, quantity: parseFloat(d.quantity) || 1 });
      toast("Item added."); reload();
    } catch (err) { toast(err.message, true); }
  });
  return el;
}

function itemRow(listId, it, reload) {
  const li = h(`
    <li class="${it.is_purchased ? "done" : ""}">
      <label class="check">
        <input type="checkbox" ${it.is_purchased ? "checked" : ""} />
        <span>${escapeHtml(it.name)} <span class="muted">· ${it.quantity}${it.unit ? " " + escapeHtml(it.unit) : ""}</span></span>
      </label>
      <button class="icon-btn danger" title="Remove">✕</button>
    </li>`);
  li.querySelector("input").addEventListener("change", async (e) => {
    try { await api.updateShoppingItem(listId, it.id, { is_purchased: e.target.checked }); reload(); }
    catch (err) { toast(err.message, true); }
  });
  li.querySelector(".icon-btn").addEventListener("click", async () => {
    try { await api.deleteShoppingItem(listId, it.id); reload(); }
    catch (err) { toast(err.message, true); }
  });
  return li;
}

function newListModal(reload) {
  const form = h(`
    <form class="modal-form">
      <label>List name<input name="name" value="My Shopping List" required /></label>
      <label>Initial items (one per line, optional)<textarea name="items" rows="4" placeholder="Milk&#10;Eggs"></textarea></label>
      <button type="submit">Create list</button>
    </form>`);
  const close = modal("New shopping list", form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    const items = (d.items || "").split(/\n+/).map((s) => s.trim()).filter(Boolean)
      .map((name) => ({ name, quantity: 1 }));
    try { await api.createShoppingList({ name: d.name, items }); toast("List created."); close(); reload(); }
    catch (err) { toast(err.message, true); }
  });
}

async function generateModal(reload) {
  const body = h(`<div>${loading("Loading recipes…")}</div>`);
  const close = modal("Generate list from recipes", body);
  try {
    const recipes = await api.listRecipes({ limit: 100 });
    if (!recipes.length) { body.innerHTML = `<p class="muted">No recipes to pick from. Seed or create recipes first.</p>`; return; }
    body.innerHTML = `
      <form class="modal-form">
        <label>List name<input name="name" value="Generated Shopping List" required /></label>
        <label class="check"><input type="checkbox" name="exclude_owned" checked /> Exclude ingredients I already own</label>
        <p class="muted">Select recipes:</p>
        <div class="pick-list">${recipes.map((r) => `
          <label class="check"><input type="checkbox" value="${escapeHtml(r.id)}" /> ${escapeHtml(r.title)} <span class="muted">(${escapeHtml(r.category)})</span></label>`).join("")}</div>
        <button type="submit">Generate</button>
      </form>`;
    body.querySelector("form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const ids = [...body.querySelectorAll(".pick-list input:checked")].map((i) => i.value);
      if (!ids.length) return toast("Pick at least one recipe.", true);
      const d = formData(e.target);
      try {
        await api.generateShoppingList({
          recipe_ids: ids,
          name: d.name,
          exclude_owned: body.querySelector('[name="exclude_owned"]').checked,
        });
        toast("Shopping list generated."); close(); reload();
      } catch (err) { toast(err.message, true); }
    });
  } catch (err) { body.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`; }
}
