(function () {
  function showGovernanceInspector(decision) {
    const panel = document.getElementById("gov-inspector");
    const invariants = normalizeInvariants(decision);
    panel.innerHTML = `
      <h3>Governance Decision</h3>
      <div><strong>Decision:</strong> ${escapeHtml(decision.decision)}</div>
      <div><strong>Policy Version:</strong> ${escapeHtml(decision.policy_version)}</div>
      <div><strong>Replay ID:</strong> ${escapeHtml(decision.trace_id || decision.replay_id)}</div>
      <div><strong>Invariants Checked:</strong></div>
      <ul>${invariants.map((item) => `<li>${escapeHtml(item.name)}</li>`).join("")}</ul>
      <div><strong>Reasoning:</strong></div>
      <pre>${escapeHtml(decision.reasoning || (decision.receipts || []).join(", ") || decision.reason || "allowed by policy")}</pre>
    `;
    panel.style.display = "block";
  }

  function hideGovernanceInspector() {
    document.getElementById("gov-inspector").style.display = "none";
  }

  function showEvidenceBundle(evidence) {
    const panel = document.getElementById("gov-inspector");
    const checks = evidence.verification || {};
    const trace = evidence.trace || {};
    panel.innerHTML = `
      <h3>Evidence Bundle</h3>
      <div><strong>Trace:</strong> ${escapeHtml(evidence.trace_id)}</div>
      <div><strong>Policy:</strong> ${escapeHtml((evidence.policy || {}).version)}</div>
      ${renderCheck("Receipt Hash", checks.receipt_hash)}
      ${renderCheck("Input Hash", checks.input_hash)}
      ${renderCheck("Output Hash", checks.output_hash)}
      ${renderCheck("Original Code Hash", checks.original_code_hash)}
      <div><strong>Replay:</strong> ${escapeHtml(replayState(checks.replay))}</div>
      <div><strong>Trace Events:</strong> ${escapeHtml(String((trace.events || []).length))}</div>
      <div><strong>Continuity Events:</strong> ${escapeHtml(String((trace.continuity || []).length))}</div>
      <pre>${escapeHtml(JSON.stringify(evidence.cross_node || {}, null, 2))}</pre>
    `;
    panel.style.display = "block";
  }

  function showPolicyManifest(manifest, receipt) {
    const panel = document.getElementById("gov-inspector");
    panel.innerHTML = `
      <h3>Policy Manifest</h3>
      <div><strong>Trace:</strong> ${escapeHtml(receipt.trace_id || receipt.replay_id)}</div>
      <div><strong>Manifest Version:</strong> ${escapeHtml((manifest.node || {}).version)}</div>
      <pre>${escapeHtml(JSON.stringify(manifest, null, 2))}</pre>
    `;
    panel.style.display = "block";
  }

  function showTracePath(receipt, events) {
    const traceId = receipt.trace_id || receipt.replay_id;
    const filtered = events.filter((event) => event.payload && event.payload.trace_id === traceId);
    const panel = document.getElementById("gov-inspector");
    panel.innerHTML = `
      <h3>Trace Path</h3>
      <div><strong>Trace:</strong> ${escapeHtml(traceId)}</div>
      <ol>${filtered.map((event) => `<li>${escapeHtml(event.channel)} / ${escapeHtml(event.type)}</li>`).join("")}</ol>
      <pre>${escapeHtml(JSON.stringify(filtered, null, 2))}</pre>
    `;
    panel.style.display = "block";
  }

  function normalizeInvariants(decision) {
    if (Array.isArray(decision.invariants)) return decision.invariants;
    return (decision.receipts || []).map((name) => ({ name, pass: true }));
  }

  function renderCheck(label, check) {
    const state = check && check.valid ? "valid" : "drift";
    return `<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(state)}</div>`;
  }

  function replayState(replay) {
    if (!replay || replay.available === false) return replay && replay.reason ? replay.reason : "unavailable";
    return replay.deterministic ? "deterministic" : "drift";
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
  window.NovaDesktop.inspector = {
    showGovernanceInspector,
    showEvidenceBundle,
    showPolicyManifest,
    showTracePath,
    hideGovernanceInspector,
    normalizeInvariants,
  };
})();
