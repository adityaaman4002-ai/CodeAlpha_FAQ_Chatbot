const messagesEl = document.getElementById("messages");
const form = document.getElementById("composer");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const confidenceBadge = document.getElementById("confidenceBadge");
const topicList = document.getElementById("topicList");
const ticketNo = document.getElementById("ticketNo");

let ticketCount = 1;

function pad(n) {
  return String(n).padStart(6, "0");
}

function addMessage(text, sender, meta) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);

  messagesEl.appendChild(wrap);

  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = `meta ${meta.low ? "low" : ""}`;
    metaEl.textContent = meta.text;
    metaEl.style.marginLeft = sender === "user" ? "auto" : "0";
    metaEl.style.textAlign = sender === "user" ? "right" : "left";
    messagesEl.appendChild(metaEl);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  const wrap = document.createElement("div");
  wrap.className = "msg bot typing";
  wrap.id = "typingIndicator";
  wrap.innerHTML = `<div class="bubble"><span></span><span></span><span></span></div>`;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

async function sendMessage(text) {
  addMessage(text, "user");
  input.value = "";
  sendBtn.disabled = true;
  showTyping();
  ticketCount += 1;
  ticketNo.textContent = `TICKET #${pad(ticketCount)}`;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();

    hideTyping();

    const confidencePct = Math.round((data.confidence || 0) * 100);
    const metaText = data.matched
      ? `matched · "${data.matched_question}" · ${confidencePct}% confidence · ${data.category}`
      : `no confident match · ${confidencePct}% confidence`;

    addMessage(data.answer, "bot", { text: metaText, low: !data.matched });
    confidenceBadge.textContent = `confidence: ${confidencePct}%`;
  } catch (err) {
    hideTyping();
    addMessage("Something went wrong reaching the server. Please make sure the Flask app is running and try again.", "bot");
    confidenceBadge.textContent = "connection error";
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  sendMessage(text);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => sendMessage(chip.dataset.q));
});

async function loadCategories() {
  try {
    const res = await fetch("/api/categories");
    const data = await res.json();
    topicList.innerHTML = "";
    data.categories.forEach((cat) => {
      const li = document.createElement("li");
      li.textContent = cat;
      topicList.appendChild(li);
    });
  } catch (err) {
    topicList.innerHTML = "<li>Unable to load topics</li>";
  }
}

loadCategories();
