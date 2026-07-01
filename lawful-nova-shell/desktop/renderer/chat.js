(function () {
  function initChat({ onCodeInstruction, onWireInstruction }) {
    const input = document.getElementById("chat-input");
    const codeButton = document.getElementById("chat-send");
    const wireButton = document.getElementById("wire-send");

    codeButton.onclick = () => {
      const text = input.value.trim();
      if (!text) return;
      onCodeInstruction(text);
      input.value = "";
    };

    wireButton.onclick = () => {
      const text = input.value.trim();
      if (!text) return;
      onWireInstruction(text);
      input.value = "";
    };
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.chat = { initChat };
})();
