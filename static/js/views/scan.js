import { api } from "../api.js";
import { $, escapeHtml, toApiDate, toast, loading } from "../ui.js";

export async function renderScan(root) {
  root.innerHTML = `
    <h1 class="view-title">Scan Ingredients</h1>
    <div class="card">
      <p class="muted">Upload a photo from your gallery (FR03) or capture one with your camera
        (FR04). The system detects ingredients (FR05). Note: detection currently runs a
        pluggable demo model — swap it for a real vision model server-side.</p>
      <form id="scanForm">
        <div class="row">
          <label>Gallery upload<input name="fileUpload" type="file" accept="image/*" /></label>
          <label>Camera capture<input name="fileCamera" type="file" accept="image/*" capture="environment" /></label>
        </div>
        <div class="row">
          <label>Max results<input name="maxResults" type="number" min="1" max="20" value="5" /></label>
          <label>Expiry to apply (optional, saves to inventory)<input name="expiry" type="date" /></label>
        </div>
        <div class="row">
          <button type="submit" data-mode="detect">Detect only</button>
          <button type="submit" data-mode="save" class="secondary">Detect & add to inventory</button>
        </div>
      </form>
    </div>
    <div class="card"><h2>Results</h2><div id="scanResults" class="muted">No scan yet.</div></div>`;

  let mode = "detect";
  root.querySelectorAll("button[data-mode]").forEach((b) =>
    b.addEventListener("click", () => (mode = b.dataset.mode)));

  $("#scanForm", root).addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.target;
    const file = f.fileCamera.files[0] || f.fileUpload.files[0];
    const source = f.fileCamera.files[0] ? "camera" : "image_upload";
    if (!file) return toast("Choose or capture an image first.", true);

    const out = $("#scanResults", root);
    out.innerHTML = loading("Analyzing image…");
    const maxResults = Number(f.maxResults.value) || 5;

    try {
      if (mode === "save") {
        const expiry = toApiDate(f.expiry.value);
        const res = await api.detectAndSave(file, { source, expiryDate: expiry, maxResults });
        out.innerHTML = renderSaved(res, !!expiry);
        toast(expiry ? "Detected & saved to inventory." : "Detected (set an expiry date to save).");
      } else {
        const res = await api.detect(file, maxResults);
        out.innerHTML = renderDetections(res.detections);
        toast("Detection complete.");
      }
    } catch (err) {
      out.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`;
      toast(err.message, true);
    }
  });
}

function bar(conf) {
  const pct = Math.round(conf * 100);
  return `<div class="bar"><span style="width:${pct}%"></span></div><span class="muted">${pct}% confidence</span>`;
}

function renderDetections(detections) {
  if (!detections?.length) return `<p class="muted">No ingredients detected.</p>`;
  return `<ul class="list">${detections.map((d) => `
    <li><span><strong>${escapeHtml(d.name)}</strong></span><span style="min-width:160px">${bar(d.confidence)}</span></li>`).join("")}</ul>`;
}

function renderSaved(res, hadExpiry) {
  if (!res.items?.length) return `<p class="muted">Nothing detected.</p>`;
  return `
    <p class="muted">Source: ${escapeHtml(res.source)}${hadExpiry ? "" : " — no expiry given, so items were detected but not saved."}</p>
    <ul class="list">${res.items.map((it) => `
      <li><span><strong>${escapeHtml(it.name)}</strong>
        ${it.saved ? `<span class="badge">saved ${escapeHtml(it.id)}</span>` : `<span class="badge warn">not saved</span>`}</span>
      <span style="min-width:160px">${bar(it.confidence)}</span></li>`).join("")}</ul>`;
}
