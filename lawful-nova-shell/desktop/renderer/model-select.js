(function () {
  function initModelSelector() {
    const select = document.getElementById("model-select");
    const config = window.nodeAPI.getConfig();
    select.value = config.model || "qwen2.5-coder:3b";
    select.onchange = () => {
      window.nodeAPI.updateConfig({ model: select.value });
      document.getElementById("settings-model").value = select.value;
    };
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.modelSelect = { initModelSelector };
})();
