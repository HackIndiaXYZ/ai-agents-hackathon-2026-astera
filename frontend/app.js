/* ═══════════════════════════════════════════════════════════════
   ASTERIA — Frontend JavaScript
   AI Agent for Bhojpuri + Assamese
═══════════════════════════════════════════════════════════════ */

const API_BASE = "";

// ── App State ─────────────────────────────────────────────────────────────
const state = {
  language: "bhojpuri",
  sessionId: generateId(),
  currentScheme: null,
  currentStep: 1,
  totalSteps: 7,
  isThinking: false,
  lastMessageId: null,
  lastQuery: null,
  lastResponse: null,
};

// ── Language Content ─────────────────────────────────────────────────────
const LANG_CONTENT = {
  bhojpuri: {
    heroTitle: "सरकारी योजना के जानकारी<br/><span class='gradient-text'>अपनी भाषा में</span>",
    heroSubtitle: "PM Kisan · Ayushman Bharat · Awas Yojana · Ujjwala · Jan Dhan · Fasal Bima",
    welcome: "नमस्ते! हऊ Asteria हईं — रउरा सरकारी योजना में मदद करे खातिर। <br/><br/><strong>का पूछे के बा?</strong> 🙏",
    placeholder: "अपनी बात लिखीं... (भोजपुरी में)",
    langHint: "भोजपुरी में लिखीं",
    chips: [
      ["🌾 PM Kisan", "PM Kisan ke baare mein batao"],
      ["🏥 Ayushman", "Ayushman Bharat ka card kaise banao"],
      ["🏠 PM Awas", "PM Awas Yojana mein apply karna hai"],
      ["🔥 Ujjwala", "Ujjwala Yojana mein LPG kaise milega"],
      ["🏦 Jan Dhan", "Jan Dhan account kaise kholein"],
      ["🌱 Fasal Bima", "Fasal Bima ke liye kya documents chahiye"],
    ],
    correctBtn: "✓ Sahi baa",
    wrongBtn: "✗ Galat baa",
    thinking: "Agent soch raha hai...",
    agentStatus: "Ready · ReAct Mode",
  },
  assamese: {
    heroTitle: "চৰকাৰী আঁচনিৰ তথ্য<br/><span class='gradient-text'>আপোনাৰ ভাষাত</span>",
    heroSubtitle: "PM Kisan · Ayushman Bharat · Awas Yojana · Ujjwala · Jan Dhan · Fasal Bima",
    welcome: "নমস্কাৰ! মই Asteria — আপোনাক চৰকাৰী আঁচনিৰ বিষয়ে সহায় কৰিবলৈ। <br/><br/><strong>কি জানিব বিচাৰে?</strong> 🙏",
    placeholder: "আপোনাৰ প্ৰশ্ন লিখক... (অসমীয়াত)",
    langHint: "অসমীয়াত লিখক",
    chips: [
      ["🌾 PM Kisan", "PM Kisan ৰ বিষয়ে কওক"],
      ["🏥 Ayushman", "Ayushman Bharat কাৰ্ড কেনেকৈ বনাব"],
      ["🏠 PM Awas", "PM Awas Yojana ত আবেদন কৰিব লাগে"],
      ["🔥 Ujjwala", "Ujjwala Yojana ত LPG কেনেকৈ পাব"],
      ["🏦 Jan Dhan", "Jan Dhan একাউণ্ট কেনেকৈ খুলিব"],
      ["🌱 Fasal Bima", "Fasal Bima ৰ বাবে কি কাগজ লাগিব"],
    ],
    correctBtn: "✓ শুদ্ধ",
    wrongBtn: "✗ ভুল",
    thinking: "Agent ভাবি আছে...",
    agentStatus: "সাজু · ReAct Mode",
  },
};

// ── Init ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  setLanguage("bhojpuri");
  loadStats();
  // Auto-refresh stats every 30s
  setInterval(loadStats, 30000);
});

// ── Language Switch ───────────────────────────────────────────────────────
function setLanguage(lang) {
  state.language = lang;
  const content = LANG_CONTENT[lang];

  // Update buttons
  document.querySelectorAll(".lang-btn").forEach((b) => b.classList.remove("active"));
  document.getElementById(`btn-${lang}`).classList.add("active");

  // Update hero
  document.getElementById("hero-title").innerHTML = content.heroTitle;
  document.getElementById("hero-subtitle").textContent = content.heroSubtitle;

  // Update welcome message
  document.getElementById("welcome-bubble").innerHTML = content.welcome;

  // Update chips
  const chipsEl = document.getElementById("scheme-chips");
  chipsEl.innerHTML = content.chips
    .map(([label, query]) => `<button class="chip" onclick="quickAsk('${query}')">${label}</button>`)
    .join("");

  // Update placeholder
  document.getElementById("user-input").placeholder = content.placeholder;
  document.getElementById("current-lang-hint").textContent = content.langHint;

  // Update agent status
  document.getElementById("agent-status").textContent = content.agentStatus;
}

// ── Quick Ask Chips ───────────────────────────────────────────────────────
function quickAsk(text) {
  document.getElementById("user-input").value = text;
  sendMessage();
}

// ── Send Message ──────────────────────────────────────────────────────────
async function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message || state.isThinking) return;

  input.value = "";
  input.style.height = "auto";
  state.isThinking = true;
  state.lastQuery = message;

  // Show user message
  appendMessage(message, "user");

  // Show typing indicator
  const typingId = showTyping();

  // Show thinking overlay
  showThinking(LANG_CONTENT[state.language].thinking);

  try {
    const resp = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        session_id: state.sessionId,
        language: state.language,
      }),
    });

    if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
    const data = await resp.json();

    removeTyping(typingId);
    hideThinking();

    state.lastMessageId = data.message_id;
    state.lastResponse = data.response;
    state.currentScheme = data.scheme || state.currentScheme;
    state.currentStep = data.current_step || state.currentStep;

    // Show agent response
    appendAgentMessage(data);

    // Show reasoning trace
    if (data.reasoning_trace?.length) {
      showReasoningTrace(data.reasoning_trace);
    }

    // Update scheme card
    if (data.scheme) {
      loadSchemeCard(data.scheme);
    }

    // Update step card
    if (data.intent === "APPLY_SCHEME" && data.current_step) {
      updateStepCard(data.current_step, 7);
    }

    // Refresh stats
    loadStats();
  } catch (err) {
    removeTyping(typingId);
    hideThinking();
    appendMessage(
      `Error: ${err.message}. Please check that the backend is running on port 8000.`,
      "agent",
      null,
      false
    );
  } finally {
    state.isThinking = false;
    document.getElementById("send-btn").disabled = false;
  }
}

// ── Message Rendering ─────────────────────────────────────────────────────
function appendMessage(text, role) {
  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = `message ${role === "user" ? "user-msg" : "agent-msg"}`;
  const avatar = role === "user" ? "👤" : "✦";
  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-content">
      <div class="msg-bubble">${text}</div>
      <div class="msg-meta">
        <span class="msg-time">${getTime()}</span>
      </div>
    </div>`;
  messages.appendChild(div);
  scrollToBottom();
  return div;
}

function appendAgentMessage(data) {
  const messages = document.getElementById("messages");
  const msgId = `msg-${Date.now()}`;
  const content = LANG_CONTENT[state.language];

  const intentBadge = data.intent
    ? `<span class="eval-badge">${getIntentEmoji(data.intent)} ${data.intent}</span>`
    : "";

  const toolsBadge = data.tools_used?.length
    ? `<span class="eval-badge">🔧 ${data.tools_used.length} tools</span>`
    : "";

  const div = document.createElement("div");
  div.className = "message agent-msg";
  div.id = msgId;
  div.innerHTML = `
    <div class="msg-avatar">✦</div>
    <div class="msg-content">
      <div class="msg-bubble">${formatResponse(data.response)}</div>
      <div class="msg-meta">
        <span class="msg-time">${getTime()}</span>
        ${intentBadge}
        ${toolsBadge}
      </div>
      <div class="feedback-btns">
        <button class="fb-btn correct" id="fb-correct-${msgId}"
          onclick="submitFeedback('${msgId}', 'correct')">
          ${content.correctBtn}
        </button>
        <button class="fb-btn wrong" id="fb-wrong-${msgId}"
          onclick="submitFeedback('${msgId}', 'wrong')">
          ${content.wrongBtn}
        </button>
      </div>
    </div>`;
  messages.appendChild(div);
  scrollToBottom();
}

function formatResponse(text) {
  // Convert newlines to <br>, bold text
  return text
    .replace(/\n\n/g, "<br/><br/>")
    .replace(/\n/g, "<br/>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");
}

function getIntentEmoji(intent) {
  const map = {
    APPLY_SCHEME: "📝",
    CHECK_ELIGIBILITY: "✅",
    GET_DOCUMENTS: "📋",
    KNOW_SCHEME: "ℹ️",
    LIST_SCHEMES: "📊",
    COMPLAINT: "⚠️",
    GENERAL_QA: "💬",
    GREETING: "👋",
  };
  return map[intent] || "🤖";
}

// ── Typing Indicator ──────────────────────────────────────────────────────
function showTyping() {
  const id = `typing-${Date.now()}`;
  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "message agent-msg typing-msg";
  div.id = id;
  div.innerHTML = `
    <div class="msg-avatar">✦</div>
    <div class="msg-content">
      <div class="msg-bubble">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;
  messages.appendChild(div);
  scrollToBottom();
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}

// ── Thinking Overlay ──────────────────────────────────────────────────────
function showThinking(text) {
  document.getElementById("thinking-overlay").classList.add("active");
  document.getElementById("thinking-text").textContent = text;
  document.getElementById("send-btn").disabled = true;
}

function hideThinking() {
  document.getElementById("thinking-overlay").classList.remove("active");
}

// ── Reasoning Trace ───────────────────────────────────────────────────────
function showReasoningTrace(steps) {
  const panel = document.getElementById("reasoning-panel");
  const stepsEl = document.getElementById("reasoning-steps");
  panel.style.display = "block";
  stepsEl.innerHTML = steps
    .map((s) => `<div class="reasoning-step">${s}</div>`)
    .join("");
}

function toggleReasoning() {
  const panel = document.getElementById("reasoning-panel");
  const arrow = document.getElementById("reasoning-arrow");
  const steps = document.getElementById("reasoning-steps");
  const isCollapsed = steps.style.display === "none";
  steps.style.display = isCollapsed ? "flex" : "none";
  arrow.textContent = isCollapsed ? "▼" : "▶";
}

// ── Feedback ──────────────────────────────────────────────────────────────
async function submitFeedback(msgId, feedback) {
  // Animate button
  document.getElementById(`fb-correct-${msgId}`)?.classList.toggle("active", feedback === "correct");
  document.getElementById(`fb-wrong-${msgId}`)?.classList.toggle("active", feedback === "wrong");

  try {
    await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        message_id: state.lastMessageId || msgId,
        feedback,
        query: state.lastQuery,
        response: state.lastResponse,
        language: state.language,
        domain: "civic_schemes",
        scheme: state.currentScheme,
      }),
    });
    // Update stats after feedback
    setTimeout(loadStats, 1000);
  } catch (err) {
    console.error("Feedback error:", err);
  }
}

// ── Stats ─────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const resp = await fetch(`${API_BASE}/stats`);
    if (!resp.ok) return;
    const data = await resp.json();
    const stats = data.dataset_stats || {};

    animateCount("stat-total", stats.total_pairs || 0);
    animateCount("stat-bho", stats.bhojpuri_pairs || 0);
    animateCount("stat-asm", stats.assamese_pairs || 0);
    animateCount("stat-pos", stats.positive_feedback || 0);
    animateCount("total-pairs", stats.total_pairs || 0);
  } catch (err) {
    // Backend not running yet — show zeros
    ["stat-total", "stat-bho", "stat-asm", "stat-pos"].forEach(
      (id) => (document.getElementById(id).textContent = "0")
    );
  }
}

function animateCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const current = parseInt(el.textContent) || 0;
  const diff = target - current;
  if (diff === 0) { el.textContent = target; return; }
  const step = Math.ceil(Math.abs(diff) / 20);
  let val = current;
  const timer = setInterval(() => {
    val += diff > 0 ? step : -step;
    if ((diff > 0 && val >= target) || (diff < 0 && val <= target)) {
      val = target;
      clearInterval(timer);
    }
    el.textContent = val;
  }, 30);
}

// ── Scheme Card ───────────────────────────────────────────────────────────
async function loadSchemeCard(schemeKey) {
  try {
    const resp = await fetch(`${API_BASE}/schemes/${schemeKey}?language=${state.language}`);
    if (!resp.ok) return;
    const data = await resp.json();

    const card = document.getElementById("scheme-card");
    const title = document.getElementById("scheme-card-title");
    const body = document.getElementById("scheme-card-body");

    title.textContent = data.name || schemeKey;
    body.innerHTML = `
      <div class="scheme-detail"><strong>Benefit:</strong> ${data.benefit || "—"}</div>
      <div class="scheme-detail"><strong>Domain:</strong> ${data.domain || "—"}</div>
      <div class="scheme-detail"><strong>Website:</strong> <a href="${data.website || "#"}" target="_blank" style="color:var(--accent-secondary)">${data.website || "—"}</a></div>
      <div class="scheme-helpline">📞 Helpline: <strong>${data.helpline || "—"}</strong></div>`;
    card.style.display = "block";
  } catch (err) {
    console.error("Scheme card error:", err);
  }
}

// ── Step Card ─────────────────────────────────────────────────────────────
function updateStepCard(step, total) {
  state.currentStep = step;
  state.totalSteps = total;

  const card = document.getElementById("step-card");
  document.getElementById("step-current").textContent = step;
  document.getElementById("step-total").textContent = total;
  document.getElementById("progress-bar").style.width = `${(step / total) * 100}%`;
  card.style.display = "block";
}

async function goNextStep() {
  try {
    const resp = await fetch(`${API_BASE}/next-step`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId }),
    });
    const data = await resp.json();
    updateStepCard(data.current_step, state.totalSteps);

    // Ask for next step guidance
    const nextMsg =
      state.language === "bhojpuri"
        ? `अगला कदम बताव (Step ${data.current_step})`
        : `পৰৱৰ্তী পদক্ষেপ কওক (Step ${data.current_step})`;
    document.getElementById("user-input").value = nextMsg;
    sendMessage();
  } catch (err) {
    console.error("Next step error:", err);
  }
}

// ── Export to HuggingFace ─────────────────────────────────────────────────
async function exportToHuggingFace() {
  const modal = document.getElementById("export-modal");
  const body = document.getElementById("export-modal-body");
  modal.style.display = "flex";
  body.innerHTML = `<div class="export-loading">🤗 Exporting to HuggingFace...<br/><br/>
    <div style="font-size:12px;color:var(--text-muted)">Uploading dataset for Afuu-coder/asteria-bhojpuri-assamese-civic-qa</div></div>`;

  try {
    const resp = await fetch(`${API_BASE}/export/huggingface`, { method: "POST" });
    const data = await resp.json();

    if (data.status === "success") {
      document.getElementById("export-check").textContent = "✓";
      body.innerHTML = `
        <div class="export-success">
          <div class="success-icon">🎉</div>
          <h4>Dataset Exported!</h4>
          <p style="color:var(--text-muted);font-size:13px;margin:8px 0 16px">
            ${data.total_pairs} Q&A pairs uploaded successfully
          </p>
          <div style="display:flex;gap:10px;justify-content:center">
            <div style="text-align:center">
              <div style="font-size:20px;font-weight:700;color:var(--accent-gold)">${data.bhojpuri || 0}</div>
              <div style="font-size:11px;color:var(--text-muted)">Bhojpuri</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:20px;font-weight:700;color:var(--accent-green)">${data.assamese || 0}</div>
              <div style="font-size:11px;color:var(--text-muted)">Assamese</div>
            </div>
          </div>
          <a href="${data.url}" target="_blank" style="display:block;margin-top:16px;padding:12px;background:rgba(124,92,252,0.1);border:1px solid rgba(124,92,252,0.3);border-radius:12px;text-decoration:none;color:var(--text-primary)">
            🤗 View on HuggingFace →
          </a>
        </div>`;
    } else {
      body.innerHTML = `<div class="export-loading" style="color:var(--accent-rose)">
        ❌ Export failed: ${data.message || "Unknown error"}<br/><br/>
        <small style="color:var(--text-muted)">Make sure HF_TOKEN is set in .env file</small>
      </div>`;
    }
  } catch (err) {
    body.innerHTML = `<div class="export-loading" style="color:var(--accent-rose)">
      ❌ Error: ${err.message}</div>`;
  }
}

function closeExportModal() {
  document.getElementById("export-modal").style.display = "none";
}

// ── Keyboard ──────────────────────────────────────────────────────────────
function handleKeyDown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

// ── Helpers ───────────────────────────────────────────────────────────────
function scrollToBottom() {
  const messages = document.getElementById("messages");
  messages.scrollTop = messages.scrollHeight;
}

function getTime() {
  return new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function generateId() {
  return "sess_" + Math.random().toString(36).substr(2, 9);
}
