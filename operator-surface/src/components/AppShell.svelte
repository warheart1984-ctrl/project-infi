<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    kernelOk: boolean;
    kernelUrl: string;
    workspaceLabel: string;
    taskStatus: string;
    canStop?: boolean;
    stopping?: boolean;
    onStop?: () => void;
    onMenu: (action: string) => void;
    children: Snippet;
    statusLeft?: Snippet;
    statusRight?: Snippet;
  }

  let {
    kernelOk,
    kernelUrl,
    workspaceLabel,
    taskStatus,
    canStop = false,
    stopping = false,
    onStop,
    onMenu,
    children,
    statusLeft,
    statusRight,
  }: Props = $props();
</script>

<div class="shell">
  <header class="titlebar">
    <div class="brand">
      <span class="logo">◆</span>
      <span class="name">Operator</span>
      <span class="tag">Coding Agent</span>
    </div>
    <nav class="menus">
      <button type="button" class="menu-btn" onclick={() => onMenu("new-task")}>File</button>
      <button type="button" class="menu-btn" onclick={() => onMenu("refresh-workspace")}>View</button>
      <button type="button" class="menu-btn" onclick={() => onMenu("settings")}>Settings</button>
      <button type="button" class="menu-btn" onclick={() => onMenu("docs")}>Help</button>
    </nav>
    <div class="titlebar-right">
      {#if canStop}
        <button
          type="button"
          class="stop-btn"
          disabled={stopping}
          onclick={() => onStop?.()}
        >
          {stopping ? "Stopping…" : "Stop"}
        </button>
      {/if}
      <span class="kernel-dot" class:ok={kernelOk} class:bad={!kernelOk}></span>
      <span class="kernel-label">{kernelOk ? "Kernel online" : "Kernel offline"}</span>
    </div>
  </header>

  <main class="shell-body">
    {@render children()}
  </main>

  <footer class="statusbar">
    <div class="status-left">
      {#if statusLeft}
        {@render statusLeft()}
      {:else}
        <span>{workspaceLabel}</span>
      {/if}
    </div>
    <div class="status-center">
      <span class="status-pill">{taskStatus || "idle"}</span>
    </div>
    <div class="status-right">
      {#if statusRight}
        {@render statusRight()}
      {:else}
        <span class="mono">{kernelUrl}</span>
      {/if}
    </div>
  </footer>
</div>

<style>
  .shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg);
    color: var(--text);
  }
  .titlebar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.45rem 0.75rem;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
    -webkit-app-region: drag;
    user-select: none;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    min-width: 10rem;
  }
  .logo {
    color: var(--accent);
    font-size: 0.85rem;
  }
  .name {
    font-weight: 700;
    letter-spacing: 0.02em;
  }
  .tag {
    font-size: 0.7rem;
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.1rem 0.35rem;
  }
  .menus {
    display: flex;
    gap: 0.25rem;
    -webkit-app-region: no-drag;
  }
  .menu-btn {
    background: transparent;
    border: none;
    color: var(--muted);
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
  }
  .menu-btn:hover {
    background: var(--bg-hover);
    color: var(--text);
  }
  .titlebar-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    color: var(--muted);
    -webkit-app-region: no-drag;
  }
  .stop-btn {
    background: #4a2020;
    border: 1px solid var(--danger);
    color: #ffc9c9;
    font-size: 0.72rem;
    padding: 0.2rem 0.55rem;
    border-radius: 4px;
  }
  .stop-btn:hover:not(:disabled) {
    background: #6b2828;
  }
  .kernel-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--danger);
  }
  .kernel-dot.ok {
    background: var(--success);
  }
  .shell-body {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  .statusbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.3rem 0.75rem;
    border-top: 1px solid var(--border);
    background: var(--panel);
    font-size: 0.72rem;
    color: var(--muted);
  }
  .status-pill {
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
    color: var(--accent);
  }
  .mono {
    font-family: var(--font-mono);
    font-size: 0.68rem;
  }
</style>
