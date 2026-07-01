(function () {
  async function initStatus() {
    const panel = document.getElementById("status-panel");

    const update = async () => {
      try {
        const status = await window.nodeAPI.status();
        document.getElementById("heartbeat").style.background = "#0e639c";
        const summary = window.NovaDesktop.receipts ? window.NovaDesktop.receipts.getSummary() : { receipts: 0, replays: 0, latency: 0 };
        const governance = status.governance_health
          ? `${status.governance_health.continuity_events || 0} continuity events`
          : "governed";
        const model = window.nodeAPI.getConfig().model;
        panel.textContent = `Model ${model} | Node ${status.node_id || "unknown"} | ${status.conformance_profile || "N0"} | ${governance} | receipts ${summary.receipts} | replays ${summary.replays} | latency ${summary.latency}ms`;
      } catch (error) {
        document.getElementById("heartbeat").style.background = "#a83232";
        panel.textContent = "Node offline";
      }
    };

    await update();
    setInterval(update, 5000);
  }

  window.NovaDesktop = window.NovaDesktop || {};
  window.NovaDesktop.status = { initStatus };
})();
