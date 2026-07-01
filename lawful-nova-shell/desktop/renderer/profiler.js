(function () {
  function showProfiler(stats) {
    const el = document.getElementById("profiler");
    el.style.display = "block";
    el.innerHTML = `
      <h3>Tool Invocation Profile</h3>
      <div class="profiler-row">Tool: ${escapeHtml(stats.tool)}</div>
      <div class="profiler-row">Inference: ${Math.round(stats.inference_ms || 0)} ms</div>
      <div class="profiler-row">Governance: ${Math.round(stats.governance_ms || stats.gov_ms || 0)} ms</div>
      <div class="profiler-row">Diff Size: ${Math.round(stats.diff_lines || 0)} lines</div>
      <div class="profiler-row">Total: ${Math.round(stats.total_ms || 0)} ms</div>
    `;
  }

  function buildProfile(result, totalMs) {
    const diff = result.result && result.result.diff ? result.result.diff : "";
    return {
      tool: result.result && result.result.receipts ? result.result.receipts[0] : "unknown_tool",
      inference_ms: result.governance ? result.governance.inference_ms || 0 : 0,
      governance_ms: result.governance ? result.governance.gov_ms || 0 : 0,
      diff_lines: diff ? diff.split("\n").filter(Boolean).length : 0,
      total_ms: totalMs,
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
  window.NovaDesktop.profiler = { showProfiler, buildProfile };
})();
