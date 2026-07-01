import { api } from "../api.js";
import { $, escapeHtml, expiryBadge, toApiDate, fromApiDate, formData, modal, toast, h, loading } from "../ui.js";

export async function renderInventory(root) {
  root.innerHTML = `
    <h1 class="view-title">Inventory & Expiry</h1>
    <div class="grid-2">
      <div class="card">
        <h2>Add ingredient</h2>
        <form id="addForm">
          <label>Name<input name="name" required placeholder="Tomato" /></label>
          <div class="row">
            <label>Quantity<input name="quantity" type="number" min="0.01" step="0.01" value="1" required /></label>
            <label>Unit<input name="unit" placeholder="pcs" /></label>
          </div>
          <label>Expiry date<input name="expiry_date" type="date" required /></label>
          <label>Storage location<input name="storage_location" placeholder="Fridge" /></label>
          <button type="submit">Add to inventory</button>
        </form>
      </div>
      <div class="card">
        <div class="card-head">
          <h2>My inventory</h2>
          <label class="inline-filter">Show expiring within
            <select id="filterDays">
              <option value="">all</option>
              <option value="3">3 days</option>
              <option value="7">7 days</option>
              <option value="14">14 days</option>
            </select>
          </label>
        </div>
        <ul class="list" id="invList">${loading()}</ul>
      </div>
    </div>`;

  const list = $("#invList", root);

  async function load() {
    list.innerHTML = loading();
    try {
      const days = $("#filterDays", root).value;
      const items = days ? await api.expiring(Number(days)) : await api.listIngredients();
      if (!items.length) {
        list.innerHTML = `<li class="muted">No ingredients${days ? " expiring in that window" : " yet"}.</li>`;
        return;
      }
      list.innerHTML = "";
      items.forEach((ing) => list.appendChild(row(ing, load)));
    } catch (err) {
      list.innerHTML = `<li class="muted">${escapeHtml(err.message)}</li>`;
    }
  }

  $("#filterDays", root).addEventListener("change", load);

  $("#addForm", root).addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await api.createIngredient({
        name: d.name,
        quantity: parseFloat(d.quantity),
        unit: d.unit || null,
        storage_location: d.storage_location || null,
        expiry_date: toApiDate(d.expiry_date),
      });
      e.target.reset();
      e.target.quantity.value = 1;
      toast("Ingredient added.");
      load();
    } catch (err) { toast(err.message, true); }
  });

  load();
}

function row(ing, reload) {
  const li = h(`
    <li>
      <span>
        <strong>${escapeHtml(ing.name)}</strong>
        <span class="muted"> · ${ing.quantity}${ing.unit ? " " + escapeHtml(ing.unit) : ""}
          · exp ${ing.expiry_date_display}${ing.storage_location ? " · " + escapeHtml(ing.storage_location) : ""}</span>
      </span>
      <span class="row-actions">
        ${expiryBadge(ing.days_until_expiry)}
        <button class="icon-btn" data-act="guide" title="Storage tips">💡</button>
        <button class="icon-btn" data-act="edit" title="Edit">✎</button>
        <button class="icon-btn danger" data-act="del" title="Delete">✕</button>
      </span>
    </li>`);

  li.querySelector('[data-act="del"]').addEventListener("click", async () => {
    if (!confirm(`Delete ${ing.name}?`)) return;
    try { await api.deleteIngredient(ing.id); toast("Removed."); reload(); }
    catch (err) { toast(err.message, true); }
  });
  li.querySelector('[data-act="edit"]').addEventListener("click", () => editModal(ing, reload));
  li.querySelector('[data-act="guide"]').addEventListener("click", () => guideModal(ing));
  return li;
}

function editModal(ing, reload) {
  const form = h(`
    <form class="modal-form">
      <label>Name<input name="name" value="${escapeHtml(ing.name)}" required /></label>
      <div class="row">
        <label>Quantity<input name="quantity" type="number" min="0.01" step="0.01" value="${ing.quantity}" required /></label>
        <label>Unit<input name="unit" value="${escapeHtml(ing.unit || "")}" /></label>
      </div>
      <label>Expiry date<input name="expiry_date" type="date" value="${fromApiDate(ing.expiry_date_display)}" required /></label>
      <label>Storage location<input name="storage_location" value="${escapeHtml(ing.storage_location || "")}" /></label>
      <button type="submit">Save changes</button>
    </form>`);
  const close = modal(`Edit ${ing.name}`, form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      await api.updateIngredient(ing.id, {
        name: d.name,
        quantity: parseFloat(d.quantity),
        unit: d.unit || null,
        storage_location: d.storage_location || null,
        expiry_date: toApiDate(d.expiry_date),
      });
      toast("Updated."); close(); reload();
    } catch (err) { toast(err.message, true); }
  });
}

async function guideModal(ing) {
  const body = h(`<div>${loading("Fetching storage guidance…")}</div>`);
  const close = modal(`Storage tips: ${ing.name}`, body);
  try {
    const g = await api.storageGuidance(ing.id);
    body.innerHTML = `
      <p><strong>Storage:</strong> ${escapeHtml(g.storage)}</p>
      ${g.fridge_days != null ? `<p><strong>Fridge:</strong> up to ${g.fridge_days} days</p>` : ""}
      ${g.freezer_days != null ? `<p><strong>Freezer:</strong> up to ${g.freezer_days} days</p>` : ""}
      ${g.reheating ? `<p><strong>Reheating:</strong> ${escapeHtml(g.reheating)}</p>` : ""}
      ${g.safety_tips?.length ? `<p><strong>Safety:</strong></p><ul>${g.safety_tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>` : ""}`;
  } catch (err) {
    body.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
    void close;
  }
}
