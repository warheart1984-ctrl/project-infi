(function () {
  function initSettings() {
    const config = window.nodeAPI.getConfig();
    const nodeInput = document.getElementById("settings-node-url");
    const modelInput = document.getElementById("settings-model");
    const state = document.getElementById("settings-state");

    nodeInput.value = config.nodeUrl;
    modelInput.value = config.model;

    document.getElementById("settings-save").onclick = () => {
      window.nodeAPI.updateConfig({
        nodeUrl: nodeInput.value.trim(),
        model: modelInput.value.trim(),
      });
      state.textContent = "Saved";
      setTimeout(() => {
        state.textContent = "";
      }, 1600);
    };
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.settings = { initSettings };
})();
