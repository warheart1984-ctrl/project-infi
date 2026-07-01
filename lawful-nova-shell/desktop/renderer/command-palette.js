(function () {
  let commands = [];
  let onCommand = null;

  function initCommandPalette(handler) {
    commands = window.commandAPI.loadCommands().commands || [];
    onCommand = handler;
    const search = document.getElementById("command-search");
    search.oninput = () => render(search.value);
    search.onkeydown = (event) => {
      if (event.key === "Enter") {
        const first = document.querySelector(".command-item");
        if (first) first.click();
      }
      if (event.key === "Escape") hide();
    };
    render("");
  }

  function show() {
    const palette = document.getElementById("command-palette");
    palette.style.display = "block";
    document.getElementById("command-search").focus();
    render("");
  }

  function hide() {
    document.getElementById("command-palette").style.display = "none";
  }

  function toggle() {
    const palette = document.getElementById("command-palette");
    if (palette.style.display === "block") hide();
    else show();
  }

  function render(query) {
    const list = document.getElementById("command-list");
    const needle = String(query || "").toLowerCase();
    const filtered = commands.filter((command) => `${command.title} ${command.category}`.toLowerCase().includes(needle));
    list.innerHTML = filtered.map((command) => `
      <div class="command-item" data-id="${command.id}">
        <span>${escapeHtml(command.title)}</span>
        <span>${escapeHtml(command.shortcut || "")}</span>
      </div>
    `).join("");
    list.querySelectorAll(".command-item").forEach((item) => {
      item.onclick = () => {
        hide();
        onCommand(item.dataset.id);
      };
    });
  }

  function bindKeyboard(handler) {
    document.addEventListener("keydown", (event) => {
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "p") {
        event.preventDefault();
        toggle();
        return;
      }
      const shortcut = toShortcut(event);
      const command = commands.find((entry) => normalize(entry.shortcut) === normalize(shortcut));
      if (command) {
        event.preventDefault();
        handler(command.id);
      }
    });
  }

  function toShortcut(event) {
    const parts = [];
    if (event.ctrlKey) parts.push("Ctrl");
    if (event.shiftKey) parts.push("Shift");
    parts.push(event.key.length === 1 ? event.key.toUpperCase() : event.key);
    return parts.join("+");
  }

  function normalize(value) {
    return String(value || "").toLowerCase().replace(/\s+/g, "");
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
  window.NovaDesktop.commandPalette = { initCommandPalette, bindKeyboard, show, hide, toggle };
})();
