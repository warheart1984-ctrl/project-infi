<script lang="ts">

  import { onDestroy, onMount } from "svelte";

  import AppShell from "./components/AppShell.svelte";

  import ActivityItem from "./components/ActivityItem.svelte";

  import CommandPalette from "./components/CommandPalette.svelte";

  import FileViewer from "./components/FileViewer.svelte";

  import MonacoDiffPanel from "./components/MonacoDiffPanel.svelte";

  import SettingsModal from "./components/SettingsModal.svelte";

  import TaskListPanel from "./components/TaskListPanel.svelte";
  import WorkspaceTree from "./components/WorkspaceTree.svelte";

  import * as api from "./lib/api";

  import {

    errorActivityLine,

    formatActivity,

    type ActivityLine,

  } from "./lib/formatActivity";

  import {

    loadSettings,

    saveSettings,

    type OperatorSettings,

  } from "./lib/settings";

  import { buildUnifiedDiff, hasContentDiff } from "./lib/diffGenerate";

  import type { AgentEvent } from "./lib/types";



  let settings = $state<OperatorSettings>(loadSettings());

  let kernelOk = $state(false);

  let prompt = $state("");

  let busy = $state(false);

  let stopping = $state(false);

  let taskId = $state<string | null>(null);

  let taskStatus = $state<string>("idle");

  let activity = $state<ActivityLine[]>([]);

  let lastSeq = $state(0);

  let workspaceFiles = $state<string[]>([]);

  let selectedPath = $state<string | null>(null);

  let fileContent = $state("");

  let editedContent = $state("");

  let fileLineCount = $state(0);

  let fileLoading = $state(false);

  let fileError = $state<string | null>(null);

  let manualDiffOpen = $state(false);

  let paletteOpen = $state(false);

  let paletteMode = $state<"commands" | "files">("commands");

  let paletteQuery = $state("");

  let taskSummaries = $state<Array<Record<string, unknown>>>([]);

  let settingsOpen = $state(false);

  let stream: EventSource | null = null;

  const isDirty = $derived(
    !!selectedPath && hasContentDiff(fileContent, editedContent),
  );

  const paletteCommands = $derived([
    { id: "open-file", label: "Open File", hint: "Ctrl+P" },
    { id: "new-task", label: "New Task" },
    { id: "review-changes", label: "Review Changes", hint: "Ctrl+S" },
    { id: "send-message", label: "Send Agent Message", hint: "Ctrl+Enter" },
    { id: "refresh-workspace", label: "Refresh Workspace" },
    { id: "settings", label: "Settings" },
  ]);



  const canStop = $derived(

    !!taskId &&

      ["running", "queued", "awaiting_approval", "cancelling"].includes(taskStatus),

  );



  const workspaceLabel = $derived(

    workspaceFiles.length > 0 ? `${workspaceFiles.length} workspace files` : "Workspace",

  );



  function closeStream() {

    if (stream) {

      stream.close();

      stream = null;

    }

  }



  function applyEvent(event: AgentEvent) {

    lastSeq = Math.max(lastSeq, event.seq);

    activity = [...activity, formatActivity(event)];



    if (event.type === "patch_preview") {

      taskStatus = "awaiting_approval";

    }

    if (event.type === "task_completed") {

      const st = String((event.payload ?? {}).status ?? "");

      taskStatus = st || "completed";

    }

    if (event.type === "patch_applied" || event.type === "patch_rejected") {

      if (taskStatus === "awaiting_approval") {

        taskStatus = event.type === "patch_applied" ? "running" : "rejected";

      }

    }

    if (event.type === "task_cancelled") {

      taskStatus = "cancelled";

    }

    if (event.type === "error") {

      taskStatus = "failed";

    }

    if (event.type === "task_started") {

      taskStatus = "running";

    }

  }



  function openStream(id: string, fromSeq = 0) {

    closeStream();

    stream = api.streamEvents(settings, id, fromSeq, applyEvent);

  }



  async function refreshHealth() {

    kernelOk = await api.checkHealth(settings);

  }



  async function refreshTasks() {
    if (!kernelOk) {
      taskSummaries = [];
      return;
    }
    try {
      taskSummaries = await api.listTasks(settings);
    } catch {
      taskSummaries = [];
    }
  }

  async function resumeTask(id: string) {
    busy = true;
    try {
      closeStream();
      taskId = id;
      const meta = await api.getTask(settings, id);
      taskStatus = String(meta.status ?? "paused");
      activity = [];
      lastSeq = 0;
      openStream(id, 0);
      if (meta.summary) {
        activity = [
          {
            id: `summary-${id}`,
            title: "Task summary",
            detail: String(meta.summary),
            tone: "info" as const,
            showApprovalActions: false,
          },
        ];
      }
    } catch (err) {
      activity = [
        ...activity,
        errorActivityLine("Resume failed", err instanceof Error ? err.message : "Resume failed"),
      ];
    } finally {
      busy = false;
    }
  }

  async function refreshWorkspace() {

    if (!kernelOk) {

      workspaceFiles = [];

      return;

    }

    try {

      const tree = await api.fetchWorkspaceTree(settings);

      workspaceFiles = tree.files ?? [];

    } catch (err) {

      workspaceFiles = [];

      activity = [

        ...activity,

        errorActivityLine(

          "Workspace",

          err instanceof Error ? err.message : "Failed to load workspace tree",

        ),

      ];

    }

  }



  async function loadFile(path: string) {

    selectedPath = path;

    fileLoading = true;

    fileError = null;

    try {

      const data = await api.fetchWorkspaceFile(settings, path);

      fileContent = data.content;

      editedContent = data.content;

      fileLineCount = data.line_count;

    } catch (err) {

      fileContent = "";

      editedContent = "";

      fileLineCount = 0;

      fileError = err instanceof Error ? err.message : "Failed to read file";

    } finally {

      fileLoading = false;

    }

  }



  function onFileEdited(value: string) {
    editedContent = value;
  }

  function openPalette(mode: "commands" | "files" = "commands") {
    paletteMode = mode;
    paletteQuery = "";
    paletteOpen = true;
  }

  function closePalette() {
    paletteOpen = false;
    paletteQuery = "";
  }

  async function reviewChanges() {
    if (!selectedPath || !isDirty) {
      return;
    }
    manualDiffOpen = true;
  }

  function closeManualDiff() {
    manualDiffOpen = false;
  }

  async function applyManualPatch() {
    if (!selectedPath || !isDirty) {
      return;
    }
    busy = true;
    try {
      let diff = buildUnifiedDiff(selectedPath, fileContent, editedContent);
      if (!diff.trim()) {
        const preview = await api.previewWorkspacePatch(
          settings,
          selectedPath,
          fileContent,
          editedContent,
        );
        diff = preview.diff;
      }
      if (!diff.trim()) {
        activity = [
          ...activity,
          errorActivityLine("Patch", "No changes to apply"),
        ];
        return;
      }
      await api.applyWorkspacePatch(settings, selectedPath, diff);
      fileContent = editedContent;
      manualDiffOpen = false;
      activity = [
        ...activity,
        {
          id: `manual-patch-${Date.now()}`,
          title: "Patch applied",
          detail: selectedPath,
          tone: "success" as const,
          showApprovalActions: false,
        },
      ];
      await refreshWorkspace();
    } catch (err) {
      activity = [
        ...activity,
        errorActivityLine(
          "Apply patch failed",
          err instanceof Error ? err.message : "Apply patch failed",
        ),
      ];
    } finally {
      busy = false;
    }
  }

  function onPaletteSelect(id: string) {
    if (paletteMode === "files") {
      closePalette();
      loadFile(id);
      return;
    }
    closePalette();
    if (id === "open-file") {
      openPalette("files");
      return;
    }
    if (id === "review-changes") {
      reviewChanges();
      return;
    }
    if (id === "send-message") {
      sendPrompt();
      return;
    }
    handleMenu(id);
  }

  function onGlobalKeydown(e: KeyboardEvent) {
    if (e.ctrlKey && e.key.toLowerCase() === "p" && !e.shiftKey) {
      e.preventDefault();
      openPalette("files");
      return;
    }
    if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "p") {
      e.preventDefault();
      openPalette("commands");
      return;
    }
    if (e.ctrlKey && e.key.toLowerCase() === "s") {
      e.preventDefault();
      reviewChanges();
      return;
    }
    if (e.ctrlKey && e.key === "Enter") {
      e.preventDefault();
      sendPrompt();
      return;
    }
    if (e.key === "Escape" && manualDiffOpen) {
      e.preventDefault();
      closeManualDiff();
    }
  }

  async function sendPrompt() {

    const text = prompt.trim();

    if (!text || busy) {

      return;

    }

    busy = true;

    try {

      if (!taskId) {

        const created = await api.createTask(settings, text);

        taskId = created.task_id;

        taskStatus = created.status;

        activity = [];

        lastSeq = 0;

        openStream(created.task_id, 0);

      } else {

        const res = await api.appendMessage(settings, taskId, text);

        taskStatus = res.status;

      }

      prompt = "";

    } catch (err) {

      activity = [

        ...activity,

        errorActivityLine(

          "Send failed",

          err instanceof Error ? err.message : "Request failed",

        ),

      ];

    } finally {

      busy = false;

    }

  }



  function onComposerKeydown(e: KeyboardEvent) {

    if (e.key === "Enter" && !e.shiftKey) {

      e.preventDefault();

      sendPrompt();

    }

  }



  async function stopTask() {

    if (!taskId) {

      return;

    }

    stopping = true;

    busy = true;

    try {

      await api.cancelTask(settings, taskId);

    } catch (err) {

      activity = [

        ...activity,

        errorActivityLine(

          "Cancel failed",

          err instanceof Error ? err.message : "Cancel failed",

        ),

      ];

    } finally {

      busy = false;

      stopping = false;

    }

  }



  async function approvePending() {

    if (!taskId) {

      return;

    }

    busy = true;

    try {

      const res = await api.approvePatch(settings, taskId);

      taskStatus = res.status;

    } catch (err) {

      activity = [

        ...activity,

        errorActivityLine(

          "Approve failed",

          err instanceof Error ? err.message : "Approve failed",

        ),

      ];

    } finally {

      busy = false;

    }

  }



  async function rejectPending() {

    if (!taskId) {

      return;

    }

    busy = true;

    try {

      const res = await api.rejectPatch(settings, taskId, "Rejected from desktop UI");

      taskStatus = res.status;

    } catch (err) {

      activity = [

        ...activity,

        errorActivityLine(

          "Reject failed",

          err instanceof Error ? err.message : "Reject failed",

        ),

      ];

    } finally {

      busy = false;

    }

  }



  function handleMenu(action: string) {

    if (action === "settings") {

      settingsOpen = true;

      return;

    }

    if (action === "refresh-workspace") {

      refreshWorkspace();

      return;

    }

    if (action === "new-task") {

      closeStream();

      taskId = null;

      taskStatus = "idle";

      activity = [];

      lastSeq = 0;

      prompt = "";

    }

  }



  function onSettingsSaved(next: OperatorSettings) {

    settings = next;

    saveSettings(settings);

    settingsOpen = false;

    refreshHealth().then(() => {
      refreshWorkspace();
      refreshTasks();
    });

  }



  onMount(() => {

    refreshHealth().then(() => {
      refreshWorkspace();
      refreshTasks();
    });

    window.addEventListener("keydown", onGlobalKeydown);

  });



  onDestroy(() => {

    window.removeEventListener("keydown", onGlobalKeydown);

    closeStream();

  });

</script>



<AppShell

  {kernelOk}

  kernelUrl={settings.kernelUrl}

  {workspaceLabel}

  {taskStatus}

  canStop={canStop}

  {stopping}

  onStop={stopTask}

  onMenu={handleMenu}

>

  {#snippet children()}

    <div class="workspace">

      <section class="panel tree-panel">

        <header class="panel-head">Files</header>

        <WorkspaceTree

          files={workspaceFiles}

          selectedPath={selectedPath}

          onSelect={(path) => loadFile(path)}

        />

        <TaskListPanel
          tasks={taskSummaries}
          activeTaskId={taskId}
          onSelect={resumeTask}
          onRefresh={refreshTasks}
        />

      </section>



      <section class="panel activity-panel">

        <header class="panel-head">Activity</header>

        <div class="activity-scroll">

          {#if activity.length === 0}

            <p class="empty">

              Send a goal to start an operator task. Events stream from the kernel on port

              8790.

            </p>

          {:else}

            {#each activity as line (line.id)}

              <ActivityItem

                {line}

                {busy}

                onApprove={line.showApprovalActions ? approvePending : undefined}

                onReject={line.showApprovalActions ? rejectPending : undefined}

              />

            {/each}

          {/if}

        </div>

        <footer class="composer">

          <textarea

            bind:value={prompt}

            rows="2"

            placeholder="Describe what the operator should do…"

            disabled={busy || !kernelOk}

            onkeydown={onComposerKeydown}

          ></textarea>

          <button

            type="button"

            class="primary"

            disabled={busy || !kernelOk || !prompt.trim()}

            onclick={sendPrompt}

          >

            {busy ? "Working…" : taskId ? "Send" : "Start task"}

          </button>

        </footer>

      </section>



      <section class="panel viewer-panel">

        <header class="panel-head editor-head">
          <span>Editor</span>
          {#if isDirty}
            <button type="button" class="review-btn" onclick={reviewChanges}>Review changes</button>
          {/if}
        </header>

        <div class="viewer-wrap">
          <FileViewer
            path={selectedPath ?? ""}
            content={editedContent}
            lineCount={fileLineCount}
            loading={fileLoading}
            error={fileError ?? ""}
            onChange={onFileEdited}
          />
          {#if manualDiffOpen && selectedPath}
            <div class="diff-overlay">
              <MonacoDiffPanel
                path={selectedPath}
                original={fileContent}
                modified={editedContent}
                onClose={closeManualDiff}
              />
              <footer class="diff-actions">
                <button type="button" onclick={closeManualDiff}>Cancel</button>
                <button type="button" class="primary" disabled={busy} onclick={applyManualPatch}>
                  Apply patch
                </button>
              </footer>
            </div>
          {/if}
        </div>

      </section>

    </div>

  {/snippet}

</AppShell>



<SettingsModal

  open={settingsOpen}

  {settings}

  onClose={() => (settingsOpen = false)}

  onSave={onSettingsSaved}

/>

<CommandPalette
  open={paletteOpen}
  mode={paletteMode}
  query={paletteQuery}
  commands={paletteCommands}
  files={workspaceFiles}
  onSelect={onPaletteSelect}
  onClose={closePalette}
  onQueryChange={(value) => (paletteQuery = value)}
/>

<style>

  .workspace {

    display: grid;

    grid-template-columns: minmax(180px, 22%) minmax(280px, 1fr) minmax(220px, 32%);

    gap: 0;

    height: 100%;

    min-height: 0;

  }

  .panel {

    display: flex;

    flex-direction: column;

    min-height: 0;

    border-right: 1px solid var(--border);

    background: var(--bg-elevated);

  }

  .panel:last-child {

    border-right: none;

  }

  .panel-head {

    padding: 0.45rem 0.65rem;

    font-size: 0.72rem;

    font-weight: 600;

    text-transform: uppercase;

    letter-spacing: 0.06em;

    color: var(--muted);

    border-bottom: 1px solid var(--border);

    flex-shrink: 0;

  }

  .activity-panel {

    background: var(--bg);

  }

  .activity-scroll {

    flex: 1;

    min-height: 0;

    overflow-y: auto;

    padding: 0.5rem;

    display: flex;

    flex-direction: column;

    gap: 0.5rem;

  }

  .composer {

    display: flex;

    gap: 0.5rem;

    padding: 0.5rem;

    border-top: 1px solid var(--border);

    background: var(--panel);

    flex-shrink: 0;

  }

  .composer textarea {

    flex: 1;

    resize: vertical;

    min-height: 2.5rem;

    max-height: 8rem;

  }

  .composer button {

    align-self: flex-end;

    white-space: nowrap;

  }

  .empty {

    margin: 0.5rem;

    color: var(--muted);

    font-size: 13px;

    line-height: 1.5;

  }

  .editor-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }

  .review-btn {
    font-size: 0.68rem;
    padding: 0.15rem 0.45rem;
  }

  .viewer-wrap {
    position: relative;
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  .diff-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    background: var(--bg);
    z-index: 10;
  }

  .diff-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    padding: 0.45rem 0.6rem;
    border-top: 1px solid var(--border);
    background: var(--panel);
    flex-shrink: 0;
  }

</style>

