const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

test("node client posts code and wire tasks to configured node tool endpoint", async () => {
  const calls = [];
  const client = require("../core/node-client");
  client.updateConfig({ nodeUrl: "http://127.0.0.1:8080/", model: "phi3" });
  client.setTransport(async (url, options) => {
    calls.push({ url, options });
    return {
      ok: true,
      json: async () => ({ result: { receipts: ["coder_tool"] }, governance: { decision: "allowed" } }),
    };
  });

  await client.code({ file_path: "src/app.py", instruction: "Add health", current_code: "print('x')" });
  await client.wire({ goal: "Connect coder", components: ["main.py"] });
  await client.explain({ file_path: "src/app.py", patch: "+ok", instruction: "Explain patch" });

  assert.equal(calls[0].url, "http://127.0.0.1:8080/node/tool");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    intent: "code",
    model: "phi3",
    file_path: "src/app.py",
    instruction: "Add health",
    current_code: "print('x')",
  });
  assert.deepEqual(JSON.parse(calls[1].options.body), {
    intent: "wire",
    model: "phi3",
    goal: "Connect coder",
    components: ["main.py"],
  });
  assert.deepEqual(JSON.parse(calls[2].options.body), {
    intent: "explain",
    model: "phi3",
    file_path: "src/app.py",
    patch: "+ok",
    instruction: "Explain patch",
  });
});

test("desktop defaults to the verified local coder model and lists downloaded models", () => {
  delete require.cache[require.resolve("../core/node-client")];
  const client = require("../core/node-client");
  client.updateConfig({ model: undefined });
  assert.equal(client.getConfig().model, "qwen2.5-coder:3b");

  const html = fs.readFileSync(path.join(__dirname, "..", "renderer", "index.html"), "utf8");
  for (const model of [
    "qwen2.5-coder:3b",
    "qwen2.5-coder:7b",
    "deepseek-coder:6.7b",
    "coding-substrate-1:latest",
    "gemma4:latest",
  ]) {
    assert.match(html, new RegExp(`<option value="${model.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}">`));
  }
});

test("node client reads status and replays by trace id", async () => {
  const calls = [];
  const client = require("../core/node-client");
  client.updateConfig({ nodeUrl: "http://localhost:8000" });
  client.setTransport(async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({ ok: true }) };
  });

  await client.status();
  await client.replay("trace-123");

  assert.equal(calls[0].url, "http://localhost:8000/node/status");
  assert.equal(calls[0].options.method, "GET");
  assert.equal(calls[1].url, "http://localhost:8000/node/replay/trace-123");
  assert.equal(calls[1].options.method, "POST");
});

test("node client fetches independently verifiable evidence surfaces", async () => {
  const calls = [];
  const client = require("../core/node-client");
  client.updateConfig({ nodeUrl: "http://localhost:8000" });
  client.setTransport(async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({ ok: true }) };
  });

  await client.verifyTrace("trace-verify");
  await client.featureManifest();
  await client.events({ prefix: "tool.", limit: 25 });
  await client.substrateEvents({ streamId: "capability:code", limit: 10 });
  await client.compareReceipts({ receipt_hash: "sha256:a" }, { receipt_hash: "sha256:b" });

  assert.equal(calls[0].url, "http://localhost:8000/node/verify/trace-verify");
  assert.equal(calls[0].options.method, "GET");
  assert.equal(calls[1].url, "http://localhost:8000/node/feature-manifest");
  assert.equal(calls[2].url, "http://localhost:8000/node/events?prefix=tool.&limit=25");
  assert.equal(calls[2].options.method, "GET");
  assert.equal(calls[3].url, "http://localhost:8000/node/substrate-events?stream_id=capability%3Acode&limit=10");
  assert.equal(calls[3].options.method, "GET");
  assert.equal(calls[4].url, "http://localhost:8000/node/compare-receipts");
  assert.deepEqual(JSON.parse(calls[4].options.body), {
    left: { receipt_hash: "sha256:a" },
    right: { receipt_hash: "sha256:b" },
  });
});

test("file manager lists visible entries and reads/writes files", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "nova-desktop-"));
  fs.mkdirSync(path.join(root, "src"));
  fs.writeFileSync(path.join(root, "src", "app.py"), "print('hello')\n", "utf8");
  fs.mkdirSync(path.join(root, ".git"));
  fs.writeFileSync(path.join(root, ".git", "HEAD"), "ref", "utf8");

  const files = require("../core/file-manager");
  const entries = files.listEntries(root);

  assert.deepEqual(entries.map((entry) => entry.name), ["src"]);
  assert.equal(entries[0].kind, "directory");
  assert.equal(files.readFile(path.join(root, "src", "app.py")), "print('hello')\n");
  files.writeFile(path.join(root, "src", "app.py"), "print('updated')\n");
  assert.equal(fs.readFileSync(path.join(root, "src", "app.py"), "utf8"), "print('updated')\n");
});

test("receipts store normalizes node responses for drawer and replay", () => {
  const store = require("../core/receipts-store");
  store.clearReceipts();
  const receipt = store.addFromNodeResponse({
    result: { receipts: ["coder_tool"] },
    governance: { decision: "allowed", trace_id: "trace-abc" },
    receipt: { receipt_hash: "sha256:receipt" },
    trace_file: "tool-receipts/trace-abc.json",
  });

  assert.equal(receipt.tool, "coder_tool");
  assert.equal(receipt.decision, "allowed");
  assert.equal(receipt.replay_id, "trace-abc");
  assert.equal(receipt.trace_id, "trace-abc");
  assert.equal(receipt.receipt_hash, "sha256:receipt");
  assert.equal(receipt.trace_file, "tool-receipts/trace-abc.json");
  assert.equal(store.getReceipts().length, 1);
  assert.equal(store.getLastReceipt().replay_id, "trace-abc");
});

test("command registry executes keyboard driven node and ui actions", async () => {
  const commands = require("../core/commands");
  const events = [];
  const context = {
    file_path: "src/app.py",
    instruction: "Add endpoint",
    current_code: "print('x')",
    last_replay_id: "trace-1",
    model: "mistral",
    actions: {
      code: async (task) => events.push(["code", task]),
      wire: async (task) => events.push(["wire", task]),
      replay: async (id) => events.push(["replay", id]),
      updateConfig: (cfg) => events.push(["config", cfg]),
      toggle: (target) => events.push(["toggle", target]),
    },
  };

  await commands.executeCommand("coder.apply_instruction", context);
  await commands.executeCommand("ui.toggle_receipts", context);
  await commands.executeCommand("node.replay_last", context);
  await commands.executeCommand("node.switch_model", context);

  assert.deepEqual(events[0], ["code", {
    file_path: "src/app.py",
    instruction: "Add endpoint",
    current_code: "print('x')",
  }]);
  assert.deepEqual(events[1], ["toggle", "receipts"]);
  assert.deepEqual(events[2], ["replay", "trace-1"]);
  assert.deepEqual(events[3], ["config", { model: "mistral" }]);
});

test("project templates create python node and rust health projects", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "nova-templates-"));
  const templates = require("../core/project-templates");

  const pythonRoot = templates.createProject({ rootDir: root, type: "python", name: "api_py" });
  const nodeRoot = templates.createProject({ rootDir: root, type: "node", name: "api_node" });
  const rustRoot = templates.createProject({ rootDir: root, type: "rust", name: "api_rust" });

  assert.match(fs.readFileSync(path.join(pythonRoot, "app.py"), "utf8"), /\/v1\/health/);
  assert.match(fs.readFileSync(path.join(nodeRoot, "index.js"), "utf8"), /\/v1\/health/);
  assert.match(fs.readFileSync(path.join(rustRoot, "src", "main.rs"), "utf8"), /\/v1\/health/);
  assert.ok(fs.existsSync(path.join(pythonRoot, "README.md")));
  assert.ok(fs.existsSync(path.join(nodeRoot, "package.json")));
  assert.ok(fs.existsSync(path.join(rustRoot, "Cargo.toml")));
});

test("studio metrics track timeline profiler and rollback metadata", () => {
  const metrics = require("../core/studio-state");
  metrics.resetStudioState();

  const patch = metrics.addPatchEvent({
    tool: "coder_tool",
    decision: "allowed",
    replay_id: "trace-2",
    diff: "+hello",
    explanation: "boundedness continuity provenance",
    file_path: "src/app.py",
    previous_code: "old",
    updated_code: "new",
    total_ms: 42,
  });
  const replay = metrics.addReplayEvent({ replay_id: "trace-2", decision: "allowed" });
  const profile = metrics.profileInvocation({
    tool: "coder_tool",
    diff: "a\nb\nc",
    total_ms: 40,
    governance_ms: 5,
    inference_ms: 30,
  });

  assert.equal(patch.kind, "patch");
  assert.equal(replay.kind, "replay");
  assert.equal(metrics.getTimeline().length, 2);
  assert.equal(metrics.getRecentPatches()[0].previous_code, "old");
  assert.equal(profile.diff_lines, 3);
  assert.equal(metrics.getHeartbeatSummary().receipts_count, 1);
  assert.equal(metrics.getHintForLine(1).explanation, "boundedness continuity provenance");
});
