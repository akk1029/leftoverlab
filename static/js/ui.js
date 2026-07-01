// Small DOM + formatting helpers shared across views.

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

// Create an element from an HTML string.
export function h(html) {
  const tpl = document.createElement("template");
  tpl.innerHTML = html.trim();
  return tpl.content.firstElementChild;
}

export function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// <input type="date"> gives YYYY-MM-DD; the API wants DD/MM/YYYY.
export function toApiDate(isoDate) {
  if (!isoDate) return undefined;
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

export function fromApiDate(ddmmyyyy) {
  if (!ddmmyyyy) return "";
  const [d, m, y] = ddmmyyyy.split("/");
  return `${y}-${m}-${d}`;
}

export function money(n) {
  return `$${Number(n || 0).toFixed(2)}`;
}

let toastTimer;
export function toast(msg, isError = false) {
  let el = $("#toast");
  if (!el) {
    el = h('<div id="toast" class="toast"></div>');
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.toggle("error", isError);
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3400);
}

// Lightweight modal. `content` is a DOM node. Returns a close() fn.
export function modal(title, content) {
  const overlay = h(`
    <div class="modal-overlay">
      <div class="modal">
        <div class="modal-head">
          <h3>${escapeHtml(title)}</h3>
          <button class="icon-btn modal-close" aria-label="Close">✕</button>
        </div>
        <div class="modal-body"></div>
      </div>
    </div>`);
  overlay.querySelector(".modal-body").appendChild(content);
  const close = () => overlay.remove();
  overlay.querySelector(".modal-close").addEventListener("click", close);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
  document.body.appendChild(overlay);
  return close;
}

// Turn a <form> into a plain object (empty strings become undefined).
export function formData(form) {
  const out = {};
  new FormData(form).forEach((v, k) => {
    out[k] = v === "" ? undefined : v;
  });
  return out;
}

export function expiryBadge(days) {
  if (days < 0) return '<span class="badge danger">expired</span>';
  if (days <= 3) return `<span class="badge warn">${days}d left</span>`;
  return `<span class="badge">${days}d left</span>`;
}

export function loading(text = "Loading…") {
  return `<p class="muted center">${escapeHtml(text)}</p>`;
}
