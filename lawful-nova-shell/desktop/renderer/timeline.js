(function () {
  const timeline = [];

  function addTimelineEvent(receipt) {
    timeline.push({
      id: receipt.replay_id || receipt.id || "",
      tool: receipt.tool || "unknown_tool",
      decision: receipt.decision || "unknown",
      time: receipt.time || new Date().toLocaleTimeString(),
      diff: receipt.diff || null,
      kind: receipt.kind || "patch",
    });
    renderTimeline();
  }

  function renderTimeline() {
    const el = document.getElementById("timeline");
    if (!timeline.length) {
      el.innerHTML = '<div class="empty-state">No governed actions yet</div>';
      return;
    }
    el.innerHTML = timeline.map((t) => `
      <div class="timeline-item">
        <div><strong>${escapeHtml(t.time)}</strong> ${escapeHtml(t.kind)}</div>
        <div>Tool: ${escapeHtml(t.tool)}</div>
        <div>Decision: ${escapeHtml(t.decision)}</div>
        <div>Replay ID: ${escapeHtml(t.id)}</div>
      </div>
    `).join("");
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
  window.NovaDesktop.timeline = { addTimelineEvent, renderTimeline };
})();
