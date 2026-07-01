(function () {
  const receipts = [];
  let replayCount = 0;
  let lastLatency = 0;

  function addReceipt(receipt) {
    receipts.push(receipt);
    renderReceipts();
  }

  function addFromNodeResponse(response) {
    const nodeReceipt = response.receipt || {};
    const traceId = response.governance ? response.governance.trace_id || response.governance.replay_id : nodeReceipt.trace_id || "";
    const receipt = {
      tool: response.result && response.result.receipts ? response.result.receipts[0] : "unknown_tool",
      decision: response.governance ? response.governance.decision : "unknown",
      replay_id: traceId,
      trace_id: traceId,
      receipt_hash: nodeReceipt.receipt_hash || "",
      input_hash: nodeReceipt.input_hash || "",
      output_hash: nodeReceipt.output_hash || "",
      policy_version: response.governance ? response.governance.policy_version || nodeReceipt.policy_version : nodeReceipt.policy_version || "",
      trace_file: response.trace_file || "",
      time: new Date().toLocaleTimeString(),
      diff: response.result ? response.result.diff : "",
    };
    addReceipt(receipt);
    return receipt;
  }

  function renderReceipts() {
    const drawer = document.getElementById("receipts-drawer");
    drawer.innerHTML = "";

    if (receipts.length === 0) {
      drawer.innerHTML = '<div class="empty-state">No tool receipts yet</div>';
      return;
    }

    receipts.forEach((r, index) => {
      const item = document.createElement("div");
      item.className = "receipt-item";
      item.innerHTML = `
        <div><strong>Tool:</strong> ${escapeHtml(r.tool)}</div>
        <div><strong>Decision:</strong> ${escapeHtml(r.decision)}</div>
        <div><strong>Trace ID:</strong> <button class="link-button" data-action="trace" data-index="${index}">${escapeHtml(r.replay_id)}</button></div>
        <div><strong>Policy:</strong> <button class="link-button" data-action="policy" data-index="${index}">${escapeHtml(r.policy_version || "manifest")}</button></div>
        <div><strong>Receipt Hash:</strong> <button class="link-button hash" data-action="verify" data-index="${index}">${escapeHtml(r.receipt_hash || "verify")}</button></div>
        <div><strong>Time:</strong> ${escapeHtml(r.time)}</div>
        <div class="receipt-actions">
          <button data-action="verify" data-index="${index}">Verify</button>
          <button data-action="replay" data-index="${index}">Replay</button>
        </div>
      `;
      drawer.appendChild(item);
    });
    drawer.querySelectorAll("button[data-action]").forEach((button) => {
      button.onclick = () => handleReceiptAction(button.dataset.action, Number(button.dataset.index));
    });
  }

  async function handleReceiptAction(action, index) {
    const receipt = receipts[index];
    if (!receipt) return;
    if (action === "replay") {
      await window.NovaDesktop.replay.replayReceipt(receipt);
      return;
    }
    if (action === "policy") {
      const manifest = await window.nodeAPI.featureManifest();
      window.NovaDesktop.inspector.showPolicyManifest(manifest.manifest || manifest, receipt);
      return;
    }
    if (action === "trace") {
      const events = await window.nodeAPI.events({ limit: 500 });
      window.NovaDesktop.inspector.showTracePath(receipt, events.events || []);
      return;
    }
    const evidence = await window.nodeAPI.verifyTrace(receipt.trace_id || receipt.replay_id);
    window.NovaDesktop.inspector.showEvidenceBundle(evidence);
  }

  function toggleReceipts() {
    const drawer = document.getElementById("receipts-drawer");
    drawer.style.display = drawer.style.display === "block" ? "none" : "block";
    renderReceipts();
  }

  function getReceipts() {
    return receipts.slice();
  }

  function getLastReceipt() {
    return receipts[receipts.length - 1] || null;
  }

  function recordReplay() {
    replayCount += 1;
  }

  function setLatency(ms) {
    lastLatency = Math.round(ms || 0);
  }

  function getSummary() {
    return {
      receipts: receipts.length,
      replays: replayCount,
      latency: lastLatency,
    };
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]));
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.receipts = {
    addReceipt,
    addFromNodeResponse,
    renderReceipts,
    toggleReceipts,
    getReceipts,
    getLastReceipt,
    handleReceiptAction,
    recordReplay,
    setLatency,
    getSummary,
  };
})();
