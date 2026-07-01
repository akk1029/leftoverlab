import { api } from "../api.js";
import { $, escapeHtml, formData, modal, toast, h, loading } from "../ui.js";

const TYPES = ["experience", "recipe", "tip"];

export async function renderCommunity(root) {
  root.innerHTML = `
    <div class="card-head view-head">
      <h1 class="view-title">Community</h1>
      <button id="newPost">+ New post</button>
    </div>
    <div class="card">
      <label class="inline-filter">Filter
        <select id="typeFilter">
          <option value="">all types</option>
          ${TYPES.map((t) => `<option value="${t}">${t}</option>`).join("")}
        </select>
      </label>
    </div>
    <div id="feed">${loading()}</div>`;

  const feed = $("#feed", root);

  async function load() {
    feed.innerHTML = loading();
    try {
      const type = $("#typeFilter", root).value;
      const posts = await api.listPosts({ post_type: type, limit: 100 });
      if (!posts.length) { feed.innerHTML = `<p class="muted">No posts yet. Be the first to share!</p>`; return; }
      const me = await api.me();
      feed.innerHTML = "";
      posts.forEach((p) => feed.appendChild(postCard(p, me.id, load)));
    } catch (err) { feed.innerHTML = `<p class="muted">${escapeHtml(err.message)}</p>`; }
  }

  $("#typeFilter", root).addEventListener("change", load);
  $("#newPost", root).addEventListener("click", () => newPostModal(load));
  load();
}

function postCard(p, myId, reload) {
  const el = h(`
    <div class="card post">
      <div class="card-head">
        <h2>${escapeHtml(p.title)} <span class="badge">${escapeHtml(p.post_type)}</span></h2>
        ${p.author_id === myId ? `<button class="icon-btn danger" data-act="del" title="Delete">✕</button>` : ""}
      </div>
      <p class="pre">${escapeHtml(p.body)}</p>
      <div class="muted comment-toggle" role="button">💬 ${p.comments.length} comment(s) — view / add</div>
      <div class="comments hidden"></div>
    </div>`);

  const del = el.querySelector('[data-act="del"]');
  if (del) del.addEventListener("click", async () => {
    if (!confirm("Delete this post?")) return;
    try { await api.deletePost(p.id); toast("Post deleted."); reload(); }
    catch (err) { toast(err.message, true); }
  });

  const wrap = el.querySelector(".comments");
  el.querySelector(".comment-toggle").addEventListener("click", () => {
    wrap.classList.toggle("hidden");
    if (!wrap.dataset.loaded) { renderComments(wrap, p, myId); wrap.dataset.loaded = "1"; }
  });
  return el;
}

function renderComments(wrap, post, myId) {
  const list = h(`<ul class="list comment-list"></ul>`);
  const form = h(`
    <form class="add-item">
      <input name="body" placeholder="Add a comment…" required />
      <button type="submit" class="small">Post</button>
    </form>`);
  wrap.append(list, form);

  const draw = () => {
    list.innerHTML = "";
    if (!post.comments.length) { list.innerHTML = `<li class="muted">No comments yet.</li>`; return; }
    post.comments.forEach((c) => {
      const li = h(`<li><span>${escapeHtml(c.body)} <span class="muted">· ${escapeHtml(c.author_id)}</span></span>
        ${c.author_id === myId ? `<button class="icon-btn danger" title="Delete">✕</button>` : ""}</li>`);
      const b = li.querySelector(".icon-btn");
      if (b) b.addEventListener("click", async () => {
        try { await api.deleteComment(c.id); post.comments = post.comments.filter((x) => x.id !== c.id); draw(); }
        catch (err) { toast(err.message, true); }
      });
      list.appendChild(li);
    });
  };
  draw();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try {
      const c = await api.addComment(post.id, { body: d.body });
      post.comments.push(c); e.target.reset(); draw();
    } catch (err) { toast(err.message, true); }
  });
}

function newPostModal(reload) {
  const form = h(`
    <form class="modal-form">
      <label>Title<input name="title" required /></label>
      <label>Type<select name="post_type">${TYPES.map((t) => `<option value="${t}">${t}</option>`).join("")}</select></label>
      <label>Body<textarea name="body" rows="5" required></textarea></label>
      <button type="submit">Publish</button>
    </form>`);
  const close = modal("New post", form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    try { await api.createPost({ title: d.title, body: d.body, post_type: d.post_type }); toast("Posted!"); close(); reload(); }
    catch (err) { toast(err.message, true); }
  });
}
