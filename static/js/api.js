// LeftoverLab API client — wraps every /api/v1 endpoint.
// Same-origin, so no CORS config needed.

const API_BASE = "/api/v1";
const TOKEN_KEY = "leftoverlab_token";

export const token = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

// Raised on any non-2xx response, with a human-readable message.
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function formatError(data, status) {
  if (data && data.detail) {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((e) => `${(e.loc || []).slice(-1)[0] || "field"}: ${e.msg}`)
        .join("; ");
    }
    return JSON.stringify(data.detail);
  }
  return `Request failed (${status})`;
}

// Callback the app registers so a 401 can bounce the user to login.
let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

async function request(path, { method = "GET", body, form, multipart, auth = true } = {}) {
  const headers = {};
  const opts = { method, headers };

  if (auth) {
    const t = token.get();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }

  if (multipart) {
    opts.body = multipart; // FormData; browser sets the boundary header.
  } else if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    opts.body = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(API_BASE + path, opts);
  if (res.status === 204) return null;

  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }

  if (!res.ok) {
    if (res.status === 401) { token.clear(); onUnauthorized(); }
    throw new ApiError(formatError(data, res.status), res.status);
  }
  return data;
}

const qs = (params) => {
  const clean = Object.fromEntries(
    Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== null && v !== "")
  );
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
};

export const api = {
  // --- auth / profile ---
  register: (payload) => request("/auth/register", { method: "POST", auth: false, body: payload }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", auth: false, form: { username: email, password } }),
  me: () => request("/auth/me"),
  updateProfile: (payload) => request("/users/me", { method: "PATCH", body: payload }),

  // --- ingredients ---
  listIngredients: () => request("/ingredients"),
  expiring: (withinDays = 3) => request(`/ingredients/expiring${qs({ within_days: withinDays })}`),
  createIngredient: (payload) => request("/ingredients", { method: "POST", body: payload }),
  updateIngredient: (id, payload) => request(`/ingredients/${id}`, { method: "PATCH", body: payload }),
  deleteIngredient: (id) => request(`/ingredients/${id}`, { method: "DELETE" }),
  storageGuidance: (id) => request(`/ingredients/${id}/storage-guidance`),

  // --- images / detection ---
  detect: (file, maxResults = 5) => {
    const fd = new FormData();
    fd.append("file", file);
    return request(`/images/detect${qs({ max_results: maxResults })}`, { method: "POST", multipart: fd });
  },
  detectAndSave: (file, { source = "image_upload", expiryDate, maxResults = 5 } = {}) => {
    const fd = new FormData();
    fd.append("file", file);
    return request(
      `/images/detect-and-save${qs({ source, expiry_date: expiryDate, max_results: maxResults })}`,
      { method: "POST", multipart: fd }
    );
  },

  // --- recipes ---
  listRecipes: (filters) => request(`/recipes${qs(filters)}`),
  recommendations: (limit = 10) => request(`/recipes/recommendations${qs({ limit })}`),
  savedRecipes: () => request("/recipes/saved"),
  getRecipe: (id) => request(`/recipes/${id}`),
  createRecipe: (payload) => request("/recipes", { method: "POST", body: payload }),
  updateRecipe: (id, payload) => request(`/recipes/${id}`, { method: "PATCH", body: payload }),
  deleteRecipe: (id) => request(`/recipes/${id}`, { method: "DELETE" }),
  saveRecipe: (id) => request(`/recipes/${id}/save`, { method: "POST" }),
  unsaveRecipe: (id) => request(`/recipes/${id}/save`, { method: "DELETE" }),

  // --- shopping lists ---
  listShoppingLists: () => request("/shopping-lists"),
  getShoppingList: (id) => request(`/shopping-lists/${id}`),
  createShoppingList: (payload) => request("/shopping-lists", { method: "POST", body: payload }),
  generateShoppingList: (payload) => request("/shopping-lists/generate", { method: "POST", body: payload }),
  deleteShoppingList: (id) => request(`/shopping-lists/${id}`, { method: "DELETE" }),
  addShoppingItem: (id, payload) => request(`/shopping-lists/${id}/items`, { method: "POST", body: payload }),
  updateShoppingItem: (id, itemId, payload) =>
    request(`/shopping-lists/${id}/items/${itemId}`, { method: "PATCH", body: payload }),
  deleteShoppingItem: (id, itemId) =>
    request(`/shopping-lists/${id}/items/${itemId}`, { method: "DELETE" }),

  // --- meal plans ---
  listMealPlans: () => request("/meal-plans"),
  getMealPlan: (id) => request(`/meal-plans/${id}`),
  generateMealPlan: (payload) => request("/meal-plans/generate", { method: "POST", body: payload }),
  deleteMealPlan: (id) => request(`/meal-plans/${id}`, { method: "DELETE" }),

  // --- sustainability ---
  dashboard: () => request("/sustainability/dashboard"),
  listRecords: () => request("/sustainability/records"),
  addRecord: (payload) => request("/sustainability/records", { method: "POST", body: payload }),

  // --- community ---
  listPosts: (filters) => request(`/community/posts${qs(filters)}`),
  getPost: (id) => request(`/community/posts/${id}`),
  createPost: (payload) => request("/community/posts", { method: "POST", body: payload }),
  deletePost: (id) => request(`/community/posts/${id}`, { method: "DELETE" }),
  addComment: (postId, payload) => request(`/community/posts/${postId}/comments`, { method: "POST", body: payload }),
  deleteComment: (id) => request(`/community/comments/${id}`, { method: "DELETE" }),

  // --- voice ---
  voiceCommand: (payload) => request("/voice/command", { method: "POST", body: payload }),
};
