const DEFAULT_MODEL = "qwen2.5-coder:3b";

let config = {
  nodeUrl: "http://localhost:8000",
  model: DEFAULT_MODEL,
};

let transport = globalThis.fetch;

function updateConfig(nextConfig = {}) {
  const cleanConfig = Object.fromEntries(
    Object.entries(nextConfig).filter(([, value]) => value !== undefined && value !== null)
  );
  config = {
    ...config,
    ...cleanConfig,
    model: cleanConfig.model || config.model || DEFAULT_MODEL,
    nodeUrl: normalizeNodeUrl(cleanConfig.nodeUrl || config.nodeUrl),
  };
  return getConfig();
}

function getConfig() {
  return { ...config };
}

function setTransport(nextTransport) {
  transport = nextTransport || globalThis.fetch;
}

async function code(task) {
  return postTool({ intent: "code", model: config.model, ...task });
}

async function wire(task) {
  return postTool({ intent: "wire", model: config.model, ...task });
}

async function explain(task) {
  return postTool({ intent: "explain", model: config.model, ...task });
}

async function status() {
  return request(`${config.nodeUrl}/node/status`, { method: "GET" });
}

async function tools() {
  return request(`${config.nodeUrl}/node/tools`, { method: "GET" });
}

async function replay(traceId) {
  return request(`${config.nodeUrl}/node/replay/${encodeURIComponent(traceId)}`, { method: "POST" });
}

async function verifyTrace(traceId) {
  return request(`${config.nodeUrl}/node/verify/${encodeURIComponent(traceId)}`, { method: "GET" });
}

async function featureManifest() {
  return request(`${config.nodeUrl}/node/feature-manifest`, { method: "GET" });
}

async function events({ prefix, limit } = {}) {
  const params = new URLSearchParams();
  if (prefix) params.set("prefix", prefix);
  if (limit) params.set("limit", String(limit));
  const query = params.toString();
  return request(`${config.nodeUrl}/node/events${query ? `?${query}` : ""}`, { method: "GET" });
}

async function substrateEvents({ streamId, type, limit } = {}) {
  const params = new URLSearchParams();
  if (streamId) params.set("stream_id", streamId);
  if (type) params.set("type_", type);
  if (limit) params.set("limit", String(limit));
  const query = params.toString();
  return request(`${config.nodeUrl}/node/substrate-events${query ? `?${query}` : ""}`, { method: "GET" });
}

async function compareReceipts(left, right) {
  return request(`${config.nodeUrl}/node/compare-receipts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ left, right }),
  });
}

async function postTool(payload) {
  return request(`${config.nodeUrl}/node/tool`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function request(url, options) {
  if (typeof transport !== "function") {
    throw new Error("No fetch transport available for Nova Desktop");
  }
  const response = await transport(url, options);
  const data = await response.json();
  if (response.ok === false) {
    const reason = data && data.error ? JSON.stringify(data.error) : "request failed";
    throw new Error(reason);
  }
  return data;
}

function normalizeNodeUrl(nodeUrl) {
  return String(nodeUrl || "http://localhost:8000").replace(/\/+$/, "");
}

module.exports = {
  code,
  wire,
  explain,
  status,
  tools,
  replay,
  verifyTrace,
  featureManifest,
  events,
  substrateEvents,
  compareReceipts,
  updateConfig,
  getConfig,
  setTransport,
};
