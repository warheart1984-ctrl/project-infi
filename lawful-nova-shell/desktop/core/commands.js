const fs = require("node:fs");
const path = require("node:path");

const COMMANDS_PATH = path.join(__dirname, "..", "commands.json");

function loadCommands() {
  return JSON.parse(fs.readFileSync(COMMANDS_PATH, "utf8"));
}

async function executeCommand(id, context) {
  const command = loadCommands().commands.find((entry) => entry.id === id);
  if (!command) {
    return null;
  }
  const actions = context.actions || {};
  switch (command.action.type) {
    case "node.tool":
      if (command.action.intent === "code") {
        return actions.code(selectArgs(command.action.args, context));
      }
      return actions.wire(selectArgs(command.action.args, context));
    case "ui.toggle":
      return actions.toggle(command.action.target);
    case "node.replay":
      return actions.replay(context.last_replay_id);
    case "node.config.update":
      return actions.updateConfig({ model: context.model });
    default:
      return null;
  }
}

function findByShortcut(shortcut) {
  return loadCommands().commands.find((entry) => normalizeShortcut(entry.shortcut) === normalizeShortcut(shortcut)) || null;
}

function selectArgs(keys, context) {
  const selected = {};
  for (const key of keys || []) {
    selected[key] = context[key];
  }
  return selected;
}

function normalizeShortcut(shortcut) {
  return String(shortcut || "").toLowerCase().replace(/\s+/g, "");
}

module.exports = {
  executeCommand,
  findByShortcut,
  loadCommands,
};
