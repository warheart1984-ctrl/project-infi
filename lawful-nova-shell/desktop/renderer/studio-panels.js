(function () {
  function showReplayOverlay(original, replayed) {
    const el = document.getElementById("replay-overlay");
    el.innerHTML = `
      <button id="replay-close">Close</button>
      <div class="replay-section">
        <h3>Original Output</h3>
        <pre>${escapeHtml(toText(original))}</pre>
      </div>
      <div class="replay-section">
        <h3>Replayed Output</h3>
        <pre>${escapeHtml(toText(replayed))}</pre>
      </div>
    `;
    el.style.display = "block";
    document.getElementById("replay-close").onclick = hideReplayOverlay;
  }

  function hideReplayOverlay() {
    document.getElementById("replay-overlay").style.display = "none";
  }

  function showInvariants(decision) {
    const el = document.getElementById("invariants");
    const invariants = window.NovaDesktop.inspector.normalizeInvariants(decision);
    el.classList.toggle("has-items", invariants.length > 0);
    el.innerHTML = invariants.map((item) => `
      <div class="invariant ${item.pass === false ? "fail" : "pass"}">
        <div><strong>${escapeHtml(item.name)}</strong></div>
        <div>${item.pass === false ? "Fail" : "Pass"}</div>
      </div>
    `).join("");
  }

  function showWaterfall(stats) {
    const el = document.getElementById("profiler");
    const steps = [
      { label: "Governance", ms: stats.governance_ms || 0 },
      { label: "Inference", ms: stats.inference_ms || 0 },
      { label: "Diff Generation", ms: stats.diff_lines || 0 },
      { label: "Total", ms: stats.total_ms || 0 },
    ];
    el.style.display = "block";
    el.innerHTML += `<h3>Invocation Waterfall</h3>${steps.map((step) => `
      <div class="waterfall-step">
        <div><strong>${escapeHtml(step.label)}</strong></div>
        <div>${Math.round(step.ms)} ${step.label === "Diff Generation" ? "lines" : "ms"}</div>
      </div>
    `).join("")}`;
  }

  function toggleDiff() {
    document.getElementById("editor-diff-container").classList.toggle("diff-hidden");
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

  function toText(value) {
    return typeof value === "string" ? value : JSON.stringify(value, null, 2);
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.studioPanels = {
    showReplayOverlay,
    hideReplayOverlay,
    showInvariants,
    showWaterfall,
    toggleDiff,
  };
})();
