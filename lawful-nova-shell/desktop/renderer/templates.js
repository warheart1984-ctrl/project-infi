(function () {
  function initTemplates() {
    document.getElementById("wizard-create").onclick = async () => {
      const type = document.getElementById("wizard-type").value;
      const name = document.getElementById("wizard-name").value.trim();
      if (!name) return;
      const rootDir = window.NovaDesktop.sidebar.getCurrentRoot() || await window.fileAPI.defaultRoot();
      const created = await window.fileAPI.createProject({ rootDir, type, name });
      window.NovaDesktop.diagnostics.logDiagnostic(`Project created: ${created}`);
      document.getElementById("wizard").style.display = "none";
      await window.NovaDesktop.sidebar.initSidebar(rootDir, (filePath) => window.NovaDesktop.editor.loadFile(filePath));
    };
    document.getElementById("wizard-close").onclick = () => {
      document.getElementById("wizard").style.display = "none";
    };
  }

  function showWizard() {
    document.getElementById("wizard").style.display = "block";
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.templates = { initTemplates, showWizard };
})();
