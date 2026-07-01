const timeline = [];
const patches = [];
const replays = [];
let lastProfile = null;

function addPatchEvent(event) {
  const entry = {
    kind: "patch",
    id: event.replay_id || event.id || "",
    tool: event.tool || "unknown_tool",
    decision: event.decision || "unknown",
    time: event.time || new Date().toLocaleTimeString(),
    diff: event.diff || "",
    explanation: event.explanation || "",
    file_path: event.file_path || "",
    previous_code: event.previous_code || "",
    updated_code: event.updated_code || "",
    total_ms: Math.round(Number(event.total_ms || 0)),
  };
  timeline.push(entry);
  patches.unshift(entry);
  return entry;
}

function addReplayEvent(event) {
  const entry = {
    kind: "replay",
    id: event.replay_id || event.id || "",
    decision: event.decision || "unknown",
    deterministic: Boolean(event.deterministic),
    time: event.time || new Date().toLocaleTimeString(),
  };
  timeline.push(entry);
  replays.unshift(entry);
  return entry;
}

function profileInvocation(stats) {
  lastProfile = {
    tool: stats.tool || "unknown_tool",
    inference_ms: Math.round(Number(stats.inference_ms || 0)),
    governance_ms: Math.round(Number(stats.governance_ms || stats.gov_ms || 0)),
    diff_lines: countDiffLines(stats.diff || ""),
    total_ms: Math.round(Number(stats.total_ms || 0)),
  };
  return lastProfile;
}

function getHintForLine(lineNumber) {
  return patches.find((patch) => patch.line === lineNumber) || patches[0] || null;
}

function getTimeline() {
  return timeline.slice();
}

function getRecentPatches() {
  return patches.slice();
}

function getReplays() {
  return replays.slice();
}

function getLastProfile() {
  return lastProfile;
}

function getHeartbeatSummary() {
  return {
    receipts_count: patches.length,
    replay_count: replays.length,
    last_latency_ms: lastProfile ? lastProfile.total_ms : 0,
  };
}

function resetStudioState() {
  timeline.length = 0;
  patches.length = 0;
  replays.length = 0;
  lastProfile = null;
}

function countDiffLines(diff) {
  if (!diff) {
    return 0;
  }
  return String(diff).split("\n").filter(Boolean).length;
}

module.exports = {
  addPatchEvent,
  addReplayEvent,
  profileInvocation,
  getTimeline,
  getRecentPatches,
  getReplays,
  getLastProfile,
  getHeartbeatSummary,
  getHintForLine,
  resetStudioState,
};
