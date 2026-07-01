(function () {
  async function replayLast() {
    const last = window.NovaDesktop.receipts.getLastReceipt();
    return replayReceipt(last);
  }

  async function replayReceipt(last) {
    if (!last || !last.replay_id) {
      return null;
    }
    const data = await window.nodeAPI.replay(last.replay_id);
    console.log("Replay:", data);
    window.NovaDesktop.receipts.recordReplay();
    window.NovaDesktop.timeline.addTimelineEvent({
      kind: "replay",
      tool: last.tool,
      decision: data.deterministic === false ? "drift" : "allowed",
      replay_id: last.replay_id,
    });
    window.NovaDesktop.studioPanels.showReplayOverlay(data.original_output, data.replayed_output);
    return data;
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.replay = { replayLast, replayReceipt };
})();
