const { contextBridge, ipcRenderer } = require("electron");
const path = require("node:path");
const client = require("./core/node-client");
const files = require("./core/file-manager");
const commands = require("./core/commands");
const templates = require("./core/project-templates");

contextBridge.exposeInMainWorld("nodeAPI", {
  code: client.code,
  wire: client.wire,
  explain: client.explain,
  status: client.status,
  tools: client.tools,
  replay: client.replay,
  verifyTrace: client.verifyTrace,
  featureManifest: client.featureManifest,
  events: client.events,
  substrateEvents: client.substrateEvents,
  compareReceipts: client.compareReceipts,
  updateConfig: client.updateConfig,
  getConfig: client.getConfig,
});

contextBridge.exposeInMainWorld("fileAPI", {
  defaultRoot: () => process.cwd(),
  openFolder: () => ipcRenderer.invoke("nova:open-folder"),
  listEntries: files.listEntries,
  readFile: files.readFile,
  writeFile: files.writeFile,
  createProject: templates.createProject,
  basename: (filePath) => path.basename(filePath),
});

contextBridge.exposeInMainWorld("commandAPI", {
  loadCommands: commands.loadCommands,
});
