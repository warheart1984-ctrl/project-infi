const fs = require("node:fs");
const path = require("node:path");

const HIDDEN_NAMES = new Set([".git", "node_modules", ".runtime", "dist"]);

function listEntries(rootDir) {
  return fs.readdirSync(rootDir, { withFileTypes: true })
    .filter((entry) => !HIDDEN_NAMES.has(entry.name))
    .map((entry) => ({
      name: entry.name,
      path: path.join(rootDir, entry.name),
      kind: entry.isDirectory() ? "directory" : "file",
    }))
    .sort((a, b) => {
      if (a.kind !== b.kind) {
        return a.kind === "directory" ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });
}

function readFile(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function writeFile(filePath, content) {
  fs.writeFileSync(filePath, content, "utf8");
}

module.exports = {
  listEntries,
  readFile,
  writeFile,
};
