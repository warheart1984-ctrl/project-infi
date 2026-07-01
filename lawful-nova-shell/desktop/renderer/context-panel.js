(function () {
  const patches = [];

  function addPatch(metadata) {
    patches.unshift(metadata);
    render();
  }

  function render() {
    const panel = document.getElementById("context-panel");
    if (!patches.length) {
      panel.innerHTML = '<div class="empty-state">No patch context yet</div>';
      return;
    }
    panel.innerHTML = `<h3>Smart Context</h3>${patches.map((patch, index) => `
      <div class="context-item">
        <div><strong>${escapeHtml(patch.file_path || "patch")}</strong></div>
        <div>${escapeHtml(patch.explanation || "Governed patch proposal")}</div>
        <div>Diff lines: ${escapeHtml(String((patch.diff || "").split("\n").filter(Boolean).length))}</div>
        <button class="rollback-btn" data-index="${index}">Rollback</button>
      </div>
    `).join("")}`;
    panel.querySelectorAll(".rollback-btn").forEach((button) => {
      button.onclick = () => {
        const patch = patches[Number(button.dataset.index)];
        if (patch && patch.previous_code) {
          window.NovaDesktop.editor.applyUpdatedCode(patch.previous_code);
        }
      };
    });
  }

  function toggle() {
    const panel = document.getElementById("context-panel");
    panel.style.display = panel.style.display === "block" ? "none" : "block";
    render();
  }

  function getHintForLine(lineNumber) {
    return patches.find((patch) => patch.line === lineNumber) || patches[0] || null;
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
  window.NovaDesktop.contextPanel = { addPatch, render, toggle, getHintForLine };
})();
