(function () {
  let monacoApi = null;
  let pendingUpdatedCode = "";

  window.addEventListener("DOMContentLoaded", () => {
    require.config({ paths: { vs: "../node_modules/monaco-editor/min/vs" } });
    require(["vs/editor/editor.main"], async (monaco) => {
      monacoApi = monaco;
      window.NovaDesktop.editor.initEditor(monacoApi);
      window.NovaDesktop.diff.initDiff(monacoApi, "diff");
      window.NovaDesktop.settings.initSettings();
      window.NovaDesktop.modelSelect.initModelSelector();
      window.NovaDesktop.templates.initTemplates();
      window.NovaDesktop.status.initStatus();
      window.NovaDesktop.timeline.renderTimeline();
      window.NovaDesktop.receipts.renderReceipts();
      window.NovaDesktop.commandPalette.initCommandPalette(executeCommand);
      window.NovaDesktop.commandPalette.bindKeyboard(executeCommand);

      const root = await window.fileAPI.defaultRoot();
      await window.NovaDesktop.sidebar.initSidebar(root, (filePath) => {
        window.NovaDesktop.editor.loadFile(filePath);
      });

      document.getElementById("open-folder").onclick = () => window.NovaDesktop.sidebar.openFolder();
      document.getElementById("receipts-btn").onclick = () => window.NovaDesktop.receipts.toggleReceipts();
      document.getElementById("tools-btn").onclick = () => window.NovaDesktop.toolRegistry.toggleToolRegistry();
      document.getElementById("diagnostics-btn").onclick = () => window.NovaDesktop.diagnostics.toggleDiagnostics();
      document.getElementById("replay-btn").onclick = () => window.NovaDesktop.replay.replayLast();
      document.getElementById("apply-patch").onclick = async () => {
        await window.NovaDesktop.editor.applyUpdatedCode(pendingUpdatedCode);
        document.getElementById("apply-patch").disabled = true;
        window.NovaDesktop.diagnostics.logDiagnostic("Patch applied to disk");
      };
      document.getElementById("explain-btn").onclick = () => window.NovaDesktop.contextPanel.toggle();
      document.getElementById("diff-toggle-btn").onclick = () => window.NovaDesktop.studioPanels.toggleDiff();

      window.NovaDesktop.chat.initChat({
        onCodeInstruction: runCodeInstruction,
        onWireInstruction: runWireInstruction,
      });
    });
  });

  async function executeCommand(id) {
    if (id === "coder.apply_instruction") {
      const instruction = document.getElementById("chat-input").value.trim();
      if (instruction) await runCodeInstruction(instruction);
    } else if (id === "wiring.generate_glue") {
      const goal = document.getElementById("chat-input").value.trim();
      if (goal) await runWireInstruction(goal);
    } else if (id === "ui.toggle_diff") {
      window.NovaDesktop.studioPanels.toggleDiff();
    } else if (id === "ui.toggle_receipts") {
      window.NovaDesktop.receipts.toggleReceipts();
    } else if (id === "node.replay_last") {
      await window.NovaDesktop.replay.replayLast();
    } else if (id === "node.switch_model") {
      document.getElementById("model-select").focus();
    }
  }

  async function runCodeInstruction(instruction) {
    const filePath = window.NovaDesktop.editor.getCurrentFilePath();
    if (!filePath) {
      document.getElementById("status-panel").textContent = "Select a file before applying code";
      return;
    }
    const currentCode = window.NovaDesktop.editor.getCurrentCode();
    const start = performance.now();
    window.NovaDesktop.diagnostics.logDiagnostic("Tool invoked: coder_tool");
    const result = await window.nodeAPI.code({
      file_path: filePath,
      instruction,
      current_code: currentCode,
    });
    const elapsed = performance.now() - start;
    pendingUpdatedCode = result.result.updated_code || "";
    window.NovaDesktop.diff.showDiff(monacoApi, currentCode, pendingUpdatedCode);
    window.NovaDesktop.receipts.setLatency(elapsed);
    const receipt = window.NovaDesktop.receipts.addFromNodeResponse(result);
    window.NovaDesktop.timeline.addTimelineEvent(receipt);
    const profile = window.NovaDesktop.profiler.buildProfile(result, elapsed);
    window.NovaDesktop.profiler.showProfiler(profile);
    window.NovaDesktop.studioPanels.showWaterfall(profile);
    window.NovaDesktop.studioPanels.showInvariants(result.governance || {});
    window.NovaDesktop.inspector.showGovernanceInspector(result.governance || {});
    window.NovaDesktop.contextPanel.addPatch({
      tool: receipt.tool,
      decision: receipt.decision,
      replay_id: receipt.replay_id,
      diff: result.result.diff,
      explanation: governanceExplanation(result.governance),
      file_path: filePath,
      previous_code: currentCode,
      updated_code: pendingUpdatedCode,
      total_ms: elapsed,
    });
    window.NovaDesktop.diagnostics.logDiagnostic(`Governance decision: ${receipt.decision}`);
    document.getElementById("apply-patch").disabled = false;
  }

  async function runWireInstruction(goal) {
    const start = performance.now();
    window.NovaDesktop.diagnostics.logDiagnostic("Tool invoked: wiring_tool");
    const result = await window.nodeAPI.wire({
      goal,
      components: [window.NovaDesktop.editor.getCurrentFilePath()].filter(Boolean),
      context: "Nova Desktop Electron renderer connected to governed Lawful Nova Node",
    });
    const elapsed = performance.now() - start;
    const currentCode = window.NovaDesktop.editor.getCurrentCode();
    pendingUpdatedCode = result.result.glue_code || "";
    window.NovaDesktop.diff.showDiff(monacoApi, currentCode, pendingUpdatedCode);
    window.NovaDesktop.receipts.setLatency(elapsed);
    const receipt = window.NovaDesktop.receipts.addFromNodeResponse(result);
    window.NovaDesktop.timeline.addTimelineEvent(receipt);
    const profile = window.NovaDesktop.profiler.buildProfile(result, elapsed);
    window.NovaDesktop.profiler.showProfiler(profile);
    window.NovaDesktop.studioPanels.showWaterfall(profile);
    window.NovaDesktop.studioPanels.showInvariants(result.governance || {});
    window.NovaDesktop.inspector.showGovernanceInspector(result.governance || {});
    window.NovaDesktop.contextPanel.addPatch({
      tool: receipt.tool,
      decision: receipt.decision,
      replay_id: receipt.replay_id,
      diff: result.result.diff || result.result.glue_code || "",
      explanation: governanceExplanation(result.governance),
      file_path: window.NovaDesktop.editor.getCurrentFilePath(),
      previous_code: currentCode,
      updated_code: pendingUpdatedCode,
      total_ms: elapsed,
    });
    window.NovaDesktop.diagnostics.logDiagnostic(`Governance decision: ${receipt.decision}`);
    document.getElementById("apply-patch").disabled = false;
  }

  function governanceExplanation(governance) {
    if (!governance) return "No governance response";
    if (governance.reasoning) return governance.reasoning;
    if (governance.reason) return governance.reason;
    return `Governance receipts: ${(governance.receipts || []).join(", ")}`;
  }
})();
