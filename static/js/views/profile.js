import { api } from "../api.js";
import { $, escapeHtml, formData, toast, loading } from "../ui.js";

const PREFS = ["None", "Vegetarian", "Vegan", "Halal", "Gluten-Free"];

export async function renderProfile(root, { onChange } = {}) {
  root.innerHTML = `<h1 class="view-title">Profile & Settings</h1><div id="profBody">${loading()}</div>`;
  const body = $("#profBody", root);

  try {
    const me = await api.me();
    body.innerHTML = `
      <div class="grid-2">
        <div class="card">
          <h2>Account</h2>
          <p class="muted">User ID</p><p><strong>${escapeHtml(me.id)}</strong></p>
          <p class="muted">Email</p><p><strong>${escapeHtml(me.email)}</strong></p>
          <p class="muted">Member since</p><p>${new Date(me.created_at).toLocaleDateString()}</p>
        </div>
        <div class="card">
          <h2>Preferences</h2>
          <form id="profForm">
            <label>Full name<input name="full_name" value="${escapeHtml(me.full_name || "")}" /></label>
            <label>Dietary preference
              <select name="dietary_preference">
                ${PREFS.map((p) => `<option ${p === me.dietary_preference ? "selected" : ""}>${p}</option>`).join("")}
              </select>
            </label>
            <label>Allergies (comma-separated)<input name="allergies" value="${escapeHtml(me.allergies || "")}" placeholder="peanuts, shellfish" /></label>
            <button type="submit">Save changes</button>
          </form>
        </div>
      </div>`;

    $("#profForm", root).addEventListener("submit", async (e) => {
      e.preventDefault();
      const d = formData(e.target);
      try {
        const updated = await api.updateProfile({
          full_name: d.full_name || null,
          dietary_preference: d.dietary_preference,
          allergies: d.allergies || null,
        });
        toast("Profile updated.");
        onChange?.(updated);
      } catch (err) { toast(err.message, true); }
    });
  } catch (err) {
    body.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
  }
}
