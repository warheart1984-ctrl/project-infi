(function () {
  function logDiagnostic(message) {
    const el = document.getElementById("diagnostics");
    const line = document.createElement("div");
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
  }

  function toggleDiagnostics() {
    const el = document.getElementById("diagnostics");
    el.style.display = el.style.display === "block" ? "none" : "block";
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.diagnostics = { logDiagnostic, toggleDiagnostics };
})();
