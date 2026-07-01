import { api } from "../api.js";
import { $, escapeHtml, toast, loading } from "../ui.js";

// Voice-controlled kitchen mode (FR15). On-device speech-to-text lives in the
// mobile app; here we let you type (or use the browser's Web Speech API if
// available) and see the resolved intent + spoken response.
export async function renderVoice(root) {
  root.innerHTML = `
    <h1 class="view-title">Voice Kitchen Mode</h1>
    <div class="card">
      <p class="muted">Hands-free cooking assistant. Load a recipe, then issue commands like
        <em>“next step”</em>, <em>“repeat”</em>, <em>“read ingredients”</em>, or
        <em>“set a timer for 5 minutes”</em>.</p>
      <label>Recipe to cook<select id="recipeSel"><option value="">— none —</option></select></label>
      <div class="voice-panel">
        <div class="step-box">
          <div class="muted">Current step <span id="stepNo">0</span></div>
          <div id="assistantSay" class="assistant-say">Say a command to begin.</div>
        </div>
        <form id="cmdForm" class="add-item">
          <input id="transcript" placeholder="Type a command (e.g. next step)…" autocomplete="off" required />
          <button type="submit" class="small">Send</button>
          <button type="button" id="micBtn" class="small secondary" title="Speak">🎤</button>
        </form>
        <div class="chips">
          ${["next step", "previous step", "repeat", "read ingredients", "set a timer for 5 minutes"]
            .map((c) => `<button class="chip" data-cmd="${c}">${c}</button>`).join("")}
        </div>
        <div id="timerBox" class="timer hidden"></div>
      </div>
    </div>`;

  let currentStep = 0;
  const sel = $("#recipeSel", root);
  const sayEl = $("#assistantSay", root);
  const stepNo = $("#stepNo", root);

  // Populate recipe dropdown.
  try {
    const recipes = await api.listRecipes({ limit: 100 });
    recipes.forEach((r) => sel.insertAdjacentHTML("beforeend", `<option value="${escapeHtml(r.id)}">${escapeHtml(r.title)}</option>`));
  } catch { /* ignore */ }

  async function send(text) {
    if (!text) return;
    sayEl.innerHTML = loading("…");
    try {
      const res = await api.voiceCommand({
        transcript: text,
        recipe_id: sel.value || null,
        current_step: currentStep,
      });
      sayEl.textContent = res.say;
      if (typeof res.data?.step === "number") { currentStep = res.data.step; stepNo.textContent = currentStep; }
      if (res.intent === "set_timer" && res.data?.seconds) startTimer(res.data.seconds);
      speak(res.say);
    } catch (err) {
      sayEl.textContent = err.message;
      toast(err.message, true);
    }
  }

  $("#cmdForm", root).addEventListener("submit", (e) => {
    e.preventDefault();
    const input = $("#transcript", root);
    send(input.value.trim());
    input.value = "";
  });
  root.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => send(c.dataset.cmd)));

  // Optional browser speech recognition.
  const micBtn = $("#micBtn", root);
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { micBtn.disabled = true; micBtn.title = "Speech recognition not supported in this browser"; }
  else {
    const rec = new SR();
    rec.lang = "en-US";
    micBtn.addEventListener("click", () => { try { rec.start(); toast("Listening…"); } catch { /* already running */ } });
    rec.onresult = (e) => send(e.results[0][0].transcript.trim());
    rec.onerror = () => toast("Mic error.", true);
  }

  let timerId;
  function startTimer(seconds) {
    clearInterval(timerId);
    const box = $("#timerBox", root);
    box.classList.remove("hidden");
    let left = seconds;
    const tick = () => {
      const m = String(Math.floor(left / 60)).padStart(2, "0");
      const s = String(left % 60).padStart(2, "0");
      box.textContent = `⏲ ${m}:${s}`;
      if (left <= 0) { clearInterval(timerId); box.textContent = "⏲ Time's up!"; toast("Timer finished!"); speak("Timer finished"); }
      left--;
    };
    tick();
    timerId = setInterval(tick, 1000);
  }

  function speak(text) {
    if (!window.speechSynthesis) return;
    try { window.speechSynthesis.cancel(); window.speechSynthesis.speak(new SpeechSynthesisUtterance(text)); }
    catch { /* ignore */ }
  }
}
