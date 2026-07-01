(function () {
  let editor = null;
  let currentFilePath = null;

  function initEditor(monaco) {
    editor = monaco.editor.create(document.getElementById("editor"), {
      value: "",
      language: "python",
      theme: "vs-dark",
      automaticLayout: true,
      minimap: { enabled: false },
      fontSize: 13,
    });
    editor.onDidChangeCursorPosition((event) => {
      const hint = window.NovaDesktop.contextPanel && window.NovaDesktop.contextPanel.getHintForLine(event.position.lineNumber);
      if (hint && hint.explanation) {
        document.getElementById("status-panel").textContent = hint.explanation;
      }
    });
  }

  async function loadFile(filePath) {
    currentFilePath = filePath;
    const content = await window.fileAPI.readFile(filePath);
    editor.setValue(content);
    document.getElementById("current-file").textContent = filePath;
    document.getElementById("topbar-current-file").textContent = filePath;
  }

  function getCurrentCode() {
    return editor ? editor.getValue() : "";
  }

  async function applyUpdatedCode(updatedCode) {
    if (!currentFilePath) {
      return;
    }
    await window.fileAPI.writeFile(currentFilePath, updatedCode);
    editor.setValue(updatedCode);
  }

  function getCurrentFilePath() {
    return currentFilePath;
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.editor = {
    initEditor,
    loadFile,
    getCurrentCode,
    applyUpdatedCode,
    getCurrentFilePath,
  };
})();
