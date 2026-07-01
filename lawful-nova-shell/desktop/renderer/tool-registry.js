(function () {
  async function loadToolRegistry() {
    const el = document.getElementById("tool-registry");
    try {
      const payload = await window.nodeAPI.tools();
      el.innerHTML = `<h3>Tool Registry</h3>${(payload.tools || []).map((tool) => `
        <div class="tool-item">
          <div><strong>${escapeHtml(tool.name)}</strong> ${escapeHtml(tool.profile)}</div>
          <div>${escapeHtml(tool.description)}</div>
          <div>Stateless: ${tool.stateless ? "true" : "false"}</div>
          <div>${escapeHtml((tool.capabilities || []).join(", "))}</div>
        </div>
      `).join("")}`;
    } catch (error) {
      el.innerHTML = '<div class="empty-state">Tool registry unavailable</div>';
    }
  }

  function toggleToolRegistry() {
    const el = document.getElementById("tool-registry");
    el.style.display = el.style.display === "block" ? "none" : "block";
    if (el.style.display === "block") loadToolRegistry();
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
  window.NovaDesktop.toolRegistry = { loadToolRegistry, toggleToolRegistry };
})();
