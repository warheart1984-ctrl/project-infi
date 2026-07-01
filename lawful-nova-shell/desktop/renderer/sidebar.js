(function () {
  let currentRoot = null;
  let onFileSelected = null;

  async function initSidebar(rootDir, onSelect) {
    currentRoot = rootDir;
    onFileSelected = onSelect;
    const sidebar = document.getElementById("sidebar");
    sidebar.innerHTML = "";

    let entries = [];
    try {
      entries = await window.fileAPI.listEntries(rootDir);
    } catch (error) {
      sidebar.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
      return;
    }

    if (entries.length === 0) {
      sidebar.innerHTML = '<div class="empty-state">No visible files</div>';
      return;
    }

    entries.forEach((entry) => {
      const item = document.createElement("div");
      item.className = entry.kind === "directory" ? "sidebar-dir" : "sidebar-file";
      item.textContent = entry.name;
      item.title = entry.path;
      item.onclick = async () => {
        if (entry.kind === "directory") {
          await initSidebar(entry.path, onSelect);
          return;
        }
        document.querySelectorAll(".sidebar-file.selected").forEach((node) => node.classList.remove("selected"));
        item.classList.add("selected");
        onFileSelected(entry.path);
      };
      sidebar.appendChild(item);
    });
  }

  async function openFolder() {
    const folder = await window.fileAPI.openFolder();
    if (folder) {
      await initSidebar(folder, onFileSelected);
    }
  }

  function getCurrentRoot() {
    return currentRoot;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]));
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.sidebar = { initSidebar, openFolder, getCurrentRoot };
})();
