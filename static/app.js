(() => {
  "use strict";

  // ── State ──────────────────────────────────────────────────────────────
  let activeConversationId = null;
  let conversations = [];
  let pendingFile = null;       // File object waiting to be sent
  let isResponding = false;     // true while waiting for LLM response

  // ── DOM ────────────────────────────────────────────────────────────────
  const chatMain         = document.getElementById("chat-main");
  const centeredHero     = document.getElementById("centered-hero");
  const newChatBtn       = document.getElementById("new-chat-btn");
  const conversationListEl = document.getElementById("conversation-list");
  const messageStreamEl  = document.getElementById("message-stream");
  const docChipRowEl     = document.getElementById("doc-chip-row");
  const attachedFilesRow = document.getElementById("attached-files-row");
  const uploadStatusRow  = document.getElementById("upload-status-row");
  const attachBtn        = document.getElementById("attach-btn");
  const fileInput        = document.getElementById("file-input");
  const questionInput    = document.getElementById("question-input");
  const sendBtn          = document.getElementById("send-btn");
  const connectionDot    = document.getElementById("connection-dot");
  const connectionLabel  = document.getElementById("connection-label");
  const confirmModal        = document.getElementById("confirm-modal");
  const confirmModalTitle   = document.getElementById("confirm-modal-title");
  const confirmModalBody    = document.getElementById("confirm-modal-body");
  const confirmModalCancel  = document.getElementById("confirm-modal-cancel");
  const confirmModalConfirm = document.getElementById("confirm-modal-confirm");

  // ── API helpers ─────────────────────────────────────────────────────────
  async function api(path, options = {}) {
    const response = await fetch(path, options);
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`${response.status} ${response.statusText}: ${detail}`);
    }
    if (response.status === 204) return null;
    return response.json();
  }

  const getConversations  = () => api("/conversations");
  const createConversation= () => api("/conversations", { method: "POST" });
  const getMessages       = (id) => api(`/conversations/${id}/messages`);
  const getDocuments      = (id) => api(`/conversations/${id}/documents`);
  const deleteConversation= (id) => api(`/conversations/${id}`, { method: "DELETE" });
  const checkHealth       = () => api("/health");

  const sendChat = (question, conversationId) =>
    api("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, conversation_id: conversationId }),
    });

  async function uploadFile(file, conversationId) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("conversation_id", conversationId);
    const response = await fetch("/upload", { method: "POST", body: formData });
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`${response.status} ${response.statusText}: ${detail}`);
    }
    return response.json();
  }

  // ── Empty / chat mode ───────────────────────────────────────────────────
  function setEmptyMode(empty) {
    if (empty) {
      chatMain.classList.add("empty-mode");
    } else {
      chatMain.classList.remove("empty-mode");
    }
  }

  // ── Themed confirm modal (replaces window.confirm) ──────────────────────
  function showConfirmModal(title, body) {
    confirmModalTitle.textContent = title;
    confirmModalBody.textContent = body;
    confirmModal.hidden = false;

    return new Promise((resolve) => {
      function cleanup(result) {
        confirmModal.hidden = true;
        confirmModalConfirm.removeEventListener("click", onConfirm);
        confirmModalCancel.removeEventListener("click", onCancel);
        confirmModal.removeEventListener("click", onOverlayClick);
        document.removeEventListener("keydown", onKeydown);
        resolve(result);
      }
      function onConfirm() { cleanup(true); }
      function onCancel() { cleanup(false); }
      function onOverlayClick(e) { if (e.target === confirmModal) cleanup(false); }
      function onKeydown(e) {
        if (e.key === "Escape") cleanup(false);
        if (e.key === "Enter") cleanup(true);
      }

      confirmModalConfirm.addEventListener("click", onConfirm);
      confirmModalCancel.addEventListener("click", onCancel);
      confirmModal.addEventListener("click", onOverlayClick);
      document.addEventListener("keydown", onKeydown);
      confirmModalConfirm.focus();
    });
  }

  // ── Rendering ───────────────────────────────────────────────────────────
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderConversationList() {
    conversationListEl.innerHTML = "";
    for (const convo of conversations) {
      const item = document.createElement("div");
      item.className = "conversation-item" + (convo.id === activeConversationId ? " active" : "");
      item.tabIndex = 0;

      const title = document.createElement("span");
      title.className = "title";
      title.textContent = convo.title || "New chat";
      item.appendChild(title);

      const deleteBtn = document.createElement("button");
      deleteBtn.className = "delete-btn";
      deleteBtn.title = "Delete conversation";
      deleteBtn.innerHTML =
        '<svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M2 4h10M5 4V2.5h4V4M3.5 4l.5 8h6l.5-8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
      deleteBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const ok = await showConfirmModal(
          "Delete this chat?",
          `"${convo.title || "This chat"}" will be permanently deleted. This cannot be undone.`
        );
        if (!ok) return;
        await deleteConversation(convo.id);
        if (convo.id === activeConversationId) activeConversationId = null;
        await refreshConversationList();
        if (!activeConversationId) await selectOrCreateInitialConversation();
      });
      item.appendChild(deleteBtn);

      item.addEventListener("click", () => selectConversation(convo.id));
      conversationListEl.appendChild(item);
    }
  }

  function appendMessage(role, content, sources = [], isError = false) {
    setEmptyMode(false);

    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    if (role === "assistant") {
      // label row
      const label = document.createElement("div");
      label.className = "assistant-label";
      label.innerHTML = `
        <span class="assistant-label-dot">
          <svg width="14" height="14" viewBox="60 40 390 450" xmlns="http://www.w3.org/2000/svg">
            <path d="M 256 480 C 340 480, 385 410, 395 320 L 415 130 L 370 180 L 335 50 L 295 160 L 255 30 L 215 170 L 175 50 L 142 180 L 97 130 L 117 320 C 127 410, 172 480, 256 480 Z" fill="#2E1B0E"/>
            <path d="M 256 465 C 330 465, 365 400, 375 320 L 390 150 L 360 190 L 330 70 L 290 170 L 255 50 L 220 170 L 182 70 L 152 190 L 122 150 L 137 320 C 147 400, 182 465, 256 465 Z" fill="#5E3A21"/>
            <path d="M 256 50 C 270 120, 270 180, 256 240 C 242 180, 242 120, 256 50 Z" fill="#754728"/>
            <ellipse cx="175" cy="275" rx="42" ry="52" fill="#241308" transform="rotate(-15 175 275)"/>
            <ellipse cx="337" cy="275" rx="42" ry="52" fill="#241308" transform="rotate(15 337 275)"/>
            <ellipse cx="178" cy="278" rx="33" ry="42" fill="#0A0A0A" transform="rotate(-12 178 278)"/>
            <ellipse cx="334" cy="278" rx="33" ry="42" fill="#0A0A0A" transform="rotate(12 334 278)"/>
            <circle cx="188" cy="260" r="12" fill="#FFFFFF"/>
            <circle cx="324" cy="260" r="12" fill="#FFFFFF"/>
            <path d="M 215 375 C 235 395, 277 395, 297 375" fill="none" stroke="#1A0E05" stroke-width="7" stroke-linecap="round"/>
          </svg>
        </span>
        Groot
      `;
      row.appendChild(label);
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble" + (isError ? " bubble-error" : "");
    bubble.textContent = content;

    if (role === "assistant" && sources && sources.length > 0) {
      const sourcesLine = document.createElement("span");
      sourcesLine.className = "sources-line mono";
      sourcesLine.textContent = `sources: ${sources.join(", ")}`;
      bubble.appendChild(sourcesLine);
    }

    row.appendChild(bubble);
    messageStreamEl.appendChild(row);
    messageStreamEl.scrollTop = messageStreamEl.scrollHeight;
    return row;
  }

  function appendTypingIndicator() {
    setEmptyMode(false);
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.id = "typing-indicator-row";

    const label = document.createElement("div");
    label.className = "assistant-label";
    label.innerHTML = `
      <span class="assistant-label-dot">
        <svg width="14" height="14" viewBox="60 40 390 450" xmlns="http://www.w3.org/2000/svg">
          <path d="M 256 480 C 340 480, 385 410, 395 320 L 415 130 L 370 180 L 335 50 L 295 160 L 255 30 L 215 170 L 175 50 L 142 180 L 97 130 L 117 320 C 127 410, 172 480, 256 480 Z" fill="#2E1B0E"/>
          <path d="M 256 465 C 330 465, 365 400, 375 320 L 390 150 L 360 190 L 330 70 L 290 170 L 255 50 L 220 170 L 182 70 L 152 190 L 122 150 L 137 320 C 147 400, 182 465, 256 465 Z" fill="#5E3A21"/>
          <path d="M 256 50 C 270 120, 270 180, 256 240 C 242 180, 242 120, 256 50 Z" fill="#754728"/>
          <ellipse cx="175" cy="275" rx="42" ry="52" fill="#241308" transform="rotate(-15 175 275)"/>
          <ellipse cx="337" cy="275" rx="42" ry="52" fill="#241308" transform="rotate(15 337 275)"/>
          <ellipse cx="178" cy="278" rx="33" ry="42" fill="#0A0A0A" transform="rotate(-12 178 278)"/>
          <ellipse cx="334" cy="278" rx="33" ry="42" fill="#0A0A0A" transform="rotate(12 334 278)"/>
          <circle cx="188" cy="260" r="12" fill="#FFFFFF"/>
          <circle cx="324" cy="260" r="12" fill="#FFFFFF"/>
          <path d="M 215 375 C 235 395, 277 395, 297 375" fill="none" stroke="#1A0E05" stroke-width="7" stroke-linecap="round"/>
        </svg>
      </span>
      Groot
    `;
    row.appendChild(label);

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = '<span class="typing-indicator"><span></span><span></span><span></span></span>';
    row.appendChild(bubble);

    messageStreamEl.appendChild(row);
    messageStreamEl.scrollTop = messageStreamEl.scrollHeight;
  }

  function removeTypingIndicator() {
    const row = document.getElementById("typing-indicator-row");
    if (row) row.remove();
  }

  function renderDocChips(docs) {
    docChipRowEl.innerHTML = "";
    if (!docs || docs.length === 0) {
      docChipRowEl.hidden = true;
      return;
    }
    docChipRowEl.hidden = false;
    for (const doc of docs) {
      const chip = document.createElement("span");
      chip.className = "doc-chip mono";
      chip.innerHTML = `📄 ${escapeHtml(doc.filename)} · <span class="chunk-count">${doc.num_chunks} chunks</span>`;
      docChipRowEl.appendChild(chip);
    }
  }

  // ── Pending file chip in input bar ──────────────────────────────────────
  function showPendingFileChip(file) {
    pendingFile = file;
    attachedFilesRow.hidden = false;
    attachedFilesRow.innerHTML = "";

    const chip = document.createElement("div");
    chip.className = "attached-chip";
    chip.innerHTML = `
      <svg width="11" height="11" viewBox="0 0 12 12" fill="none" style="flex-shrink:0">
        <rect x="1" y="1" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.2"/>
        <path d="M3.5 4.5h5M3.5 6.5h5M3.5 8.5h3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
      </svg>
      <span title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
      <button class="remove-file" title="Remove attachment" aria-label="Remove attachment">
        <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
          <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
      </button>
    `;

    chip.querySelector(".remove-file").addEventListener("click", clearPendingFile);
    attachedFilesRow.appendChild(chip);

    // Enable send even if textarea is empty (file alone is enough to trigger upload)
    updateSendBtnState();
  }

  function clearPendingFile() {
    pendingFile = null;
    attachedFilesRow.hidden = true;
    attachedFilesRow.innerHTML = "";
    fileInput.value = "";
    updateSendBtnState();
  }

  // ── Upload / ingestion progress indicator ───────────────────────────────
  function showUploadStatus(filename) {
    uploadStatusRow.hidden = false;
    uploadStatusRow.innerHTML = `
      <span class="upload-spinner" aria-hidden="true"></span>
      <span class="upload-status-text mono">Indexing "${escapeHtml(filename)}"…</span>
    `;
  }

  function hideUploadStatus() {
    uploadStatusRow.hidden = true;
    uploadStatusRow.innerHTML = "";
  }

  function updateSendBtnState() {
    const hasText = questionInput.value.trim().length > 0;
    const hasFile = !!pendingFile;
    sendBtn.disabled = (!hasText && !hasFile) || isResponding;
  }

  // ── Connection status ───────────────────────────────────────────────────
  function setConnectionStatus(ok) {
    connectionDot.classList.remove("ok", "down");
    connectionDot.classList.add(ok ? "ok" : "down");
    connectionLabel.textContent = ok ? "model online" : "model unreachable";
  }

  // ── Conversation flows ──────────────────────────────────────────────────
  async function refreshConversationList() {
    conversations = await getConversations();
    renderConversationList();
  }

  async function selectConversation(id) {
    activeConversationId = id;
    renderConversationList();
    messageStreamEl.innerHTML = "";

    let hasMessages = false;
    try {
      const messages = await getMessages(id);
      if (messages.length > 0) {
        hasMessages = true;
        for (const m of messages) appendMessage(m.role, m.content);
      }
    } catch (e) {
      console.error("Failed to load messages:", e);
    }

    setEmptyMode(!hasMessages);

    try {
      const docs = await getDocuments(id);
      renderDocChips(docs);
    } catch (e) {
      console.error("Failed to load documents:", e);
      renderDocChips([]);
    }
  }

  async function selectOrCreateInitialConversation() {
    if (conversations.length > 0) {
      await selectConversation(conversations[0].id);
    } else {
      const convo = await createConversation();
      await refreshConversationList();
      await selectConversation(convo.id);
    }
  }

  async function startNewChat() {
    const convo = await createConversation();
    await refreshConversationList();
    await selectConversation(convo.id);
    clearPendingFile();
    questionInput.focus();
  }

  // ── Lock/unlock UI during response ──────────────────────────────────────
  function setResponding(val) {
    isResponding = val;
    attachBtn.disabled = val;
    updateSendBtnState();
  }

  // ── Send message (optionally with a pending file first) ─────────────────
  async function handleSend() {
    const question = questionInput.value.trim();
    const fileToUpload = pendingFile;

    if (!question && !fileToUpload) return;

    questionInput.value = "";
    autoResizeTextarea();
    clearPendingFile();
    setResponding(true);

    // Ensure we have an active conversation
    if (!activeConversationId) {
      const convo = await createConversation();
      await refreshConversationList();
      activeConversationId = convo.id;
      renderConversationList();
    }

    // 1. Upload file if attached (silent — no chat message)
    if (fileToUpload) {
      showUploadStatus(fileToUpload.name);
      try {
        await uploadFile(fileToUpload, activeConversationId);
        const docs = await getDocuments(activeConversationId);
        renderDocChips(docs);
      } catch (e) {
        console.error("Upload failed:", e);
        appendMessage(
          "assistant",
          `❌ Failed to index "${fileToUpload.name}".\n\n${e.message}\n\nYou can still continue chatting normally.`,
          [],
          true
        );
        hideUploadStatus();
        setResponding(false);
        return;
      }
      hideUploadStatus();
    }

    // 2. Send text question (if any)
    if (question) {
      appendMessage("user", question);
      appendTypingIndicator();

      try {
        const result = await sendChat(question, activeConversationId);
        removeTypingIndicator();
        appendMessage("assistant", result.answer, result.sources, result.error);

        if (activeConversationId !== result.conversation_id) {
          activeConversationId = result.conversation_id;
        }
        await refreshConversationList();

        // Pick up generated title after a delay
        setTimeout(async () => { await refreshConversationList(); }, 4000);

      } catch (e) {
        removeTypingIndicator();
        appendMessage("assistant", "Network error — couldn't reach the server. Please try again.", [], true);
        console.error("Chat request failed:", e);
      }
    } else if (fileToUpload) {
      // File-only send: show a confirmation in chat
      setEmptyMode(false);
      appendMessage(
        "assistant",
        `✅ "${fileToUpload.name}" indexed successfully. You can now ask questions about this document.`
      );
    }

    setResponding(false);
  }

  function autoResizeTextarea() {
    questionInput.style.height = "auto";
    questionInput.style.height = Math.min(questionInput.scrollHeight, 160) + "px";
    updateSendBtnState();
  }

  // ── File selection ──────────────────────────────────────────────────────
  function handleFileSelected() {
    const file = fileInput.files[0];
    fileInput.value = "";
    if (!file) return;
    showPendingFileChip(file);
    questionInput.focus();
  }

  // ── Event wiring ────────────────────────────────────────────────────────
  newChatBtn.addEventListener("click", startNewChat);
  attachBtn.addEventListener("click", () => { if (!isResponding) fileInput.click(); });
  fileInput.addEventListener("change", handleFileSelected);
  sendBtn.addEventListener("click", handleSend);

  questionInput.addEventListener("input", autoResizeTextarea);
  questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) handleSend();
    }
  });

  // ── Boot ─────────────────────────────────────────────────────────────────
  async function init() {
    setEmptyMode(true);

    try {
      await refreshConversationList();
      await selectOrCreateInitialConversation();
    } catch (e) {
      console.error("Failed to initialize conversations:", e);
      setEmptyMode(true);
    }

    try {
      const health = await checkHealth();
      setConnectionStatus(health.llm_reachable);
    } catch (e) {
      setConnectionStatus(false);
    }

    setInterval(async () => {
      try {
        const health = await checkHealth();
        setConnectionStatus(health.llm_reachable);
      } catch (e) { setConnectionStatus(false); }
    }, 30000);
  }

  init();
})();