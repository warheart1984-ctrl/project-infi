(function () {
  let diffEditor = null;
  let currentModels = null;

  function initDiff(monaco, containerId) {
    const container = document.getElementById(containerId);
    diffEditor = monaco.editor.createDiffEditor(container, {
      theme: "vs-dark",
      renderSideBySide: true,
      automaticLayout: true,
      minimap: { enabled: false },
    });
  }

  function showDiff(monaco, originalCode, updatedCode) {
    if (currentModels) {
      currentModels.original.dispose();
      currentModels.modified.dispose();
    }
    currentModels = {
      original: monaco.editor.createModel(originalCode, "python"),
      modified: monaco.editor.createModel(updatedCode, "python"),
    };
    diffEditor.setModel(currentModels);
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.diff = { initDiff, showDiff };
})();
