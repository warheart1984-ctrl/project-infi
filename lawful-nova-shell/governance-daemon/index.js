import { createServer } from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PORT = Number(process.env.NOVA_GOV_PORT || 7070);
const HOME = process.env.HOME || process.env.USERPROFILE || ".";
const RECEIPTS_PATH = process.env.NOVA_RECEIPTS || path.join(HOME, "nova-receipts.jsonl");
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CAPABILITIES_PATH =
  process.env.NOVA_SUBSTRATE_CAPABILITIES ||
  path.join(__dirname, "..", "config", "nova-substrate-capabilities.json");

const qwenInfo = {
  id: "qwen-governed-1",
  role: "codegen",
  capabilities: ["generate_code", "refactor_code", "explain_code", "write_tests"],
  constraints: ["no_global_state", "no_unbounded_io", "no_external_network"],
};

function loadLedger() {
  if (!fs.existsSync(RECEIPTS_PATH)) return [];
  const text = fs.readFileSync(RECEIPTS_PATH, "utf8").trim();
  if (!text) return [];
  return text
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

function loadCapabilities() {
  if (!fs.existsSync(CAPABILITIES_PATH)) {
    return { "qwen-governed-1": qwenInfo };
  }
  return JSON.parse(fs.readFileSync(CAPABILITIES_PATH, "utf8"));
}

function computeDrift(entries) {
  const byPrompt = {};
  for (const entry of entries) {
    if (!entry.prompt) continue;
    byPrompt[entry.prompt] ??= [];
    byPrompt[entry.prompt].push(entry);
  }

  return Object.entries(byPrompt)
    .filter(([, list]) => new Set(list.map((entry) => entry.hash)).size > 1)
    .map(([prompt, list]) => ({
      prompt,
      nodes: [...new Set(list.map((entry) => entry.nodeId))],
      substrates: [...new Set(list.map((entry) => entry.substrateId))],
      hashes: [...new Set(list.map((entry) => entry.hash))],
    }));
}

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload, null, 2);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
  });
  res.end(body);
}

const routes = {
  "/receipts": () => loadLedger(),
  "/drift": () => ({ drift: computeDrift(loadLedger()) }),
  "/federation-summary": () => {
    const entries = loadLedger();
    const drift = computeDrift(entries);
    return {
      total: entries.length,
      driftCount: drift.length,
      nodes: [...new Set(entries.map((entry) => entry.nodeId).filter(Boolean))],
      substrates: [...new Set(entries.map((entry) => entry.substrateId).filter(Boolean))],
      drift,
    };
  },
  "/substrates/qwen": () => loadCapabilities()["qwen-governed-1"] || qwenInfo,
  "/substrates/qwen/receipts": () =>
    loadLedger().filter((entry) => entry.substrateId === "qwen-governed-1"),
};

const server = createServer((req, res) => {
  if (!req.url || req.method !== "GET") {
    sendJson(res, 405, { error: "method_not_allowed" });
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const handler = routes[url.pathname];
  if (!handler) {
    sendJson(res, 404, { error: "not_found" });
    return;
  }

  try {
    sendJson(res, 200, handler());
  } catch (error) {
    sendJson(res, 500, { error: "daemon_error", message: error.message });
  }
});

server.listen(PORT, () => {
  console.log(`Nova Governance Daemon running on port ${PORT}`);
});
