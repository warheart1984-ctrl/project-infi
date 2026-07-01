const receipts = [];

function addFromNodeResponse(response) {
  const toolReceipt = response && response.result && Array.isArray(response.result.receipts)
    ? response.result.receipts[0]
    : "unknown_tool";
  const governance = response && response.governance ? response.governance : {};
  const nodeReceipt = response && response.receipt ? response.receipt : {};
  const traceId = governance.trace_id || governance.replay_id || nodeReceipt.trace_id || "";
  const receipt = {
    tool: toolReceipt,
    decision: governance.decision || "unknown",
    replay_id: traceId,
    trace_id: traceId,
    receipt_hash: nodeReceipt.receipt_hash || "",
    input_hash: nodeReceipt.input_hash || "",
    output_hash: nodeReceipt.output_hash || "",
    policy_version: governance.policy_version || nodeReceipt.policy_version || "",
    trace_file: response && response.trace_file ? response.trace_file : "",
    time: new Date().toLocaleTimeString(),
  };
  receipts.push(receipt);
  return receipt;
}

function addReceipt(receipt) {
  receipts.push(receipt);
  return receipt;
}

function getReceipts() {
  return receipts.slice();
}

function getLastReceipt() {
  return receipts[receipts.length - 1] || null;
}

function clearReceipts() {
  receipts.length = 0;
}

module.exports = {
  addFromNodeResponse,
  addReceipt,
  getReceipts,
  getLastReceipt,
  clearReceipts,
};
