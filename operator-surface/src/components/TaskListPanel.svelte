<script lang="ts">
  let {
    tasks = [] as Array<Record<string, unknown>>,
    activeTaskId = null as string | null,
    onSelect,
    onRefresh,
  }: {
    tasks?: Array<Record<string, unknown>>;
    activeTaskId?: string | null;
    onSelect?: (taskId: string) => void;
    onRefresh?: () => void;
  } = $props();

  function label(task: Record<string, unknown>): string {
    const title = String(task.title ?? task.goal ?? task.task_id ?? "Task");
    const status = String(task.status ?? "");
    return status ? `${title} (${status})` : title;
  }
</script>

<div class="task-list">
  <header class="head">
    <span>Tasks</span>
    <button type="button" class="refresh" onclick={() => onRefresh?.()}>Refresh</button>
  </header>
  <ul>
    {#if tasks.length === 0}
      <li class="empty">No saved tasks yet.</li>
    {:else}
      {#each tasks as task (String(task.task_id))}
        <li>
          <button
            type="button"
            class:active={activeTaskId === String(task.task_id)}
            onclick={() => onSelect?.(String(task.task_id))}
          >
            {label(task)}
          </button>
        </li>
      {/each}
    {/if}
  </ul>
</div>

<style>
  .task-list {
    border-top: 1px solid var(--border);
    flex-shrink: 0;
    max-height: 180px;
    display: flex;
    flex-direction: column;
  }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.35rem 0.5rem;
    font-size: 0.68rem;
    text-transform: uppercase;
    color: var(--muted);
  }
  .refresh {
    font-size: 0.65rem;
    padding: 0.1rem 0.35rem;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    overflow-y: auto;
  }
  li button {
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    padding: 0.35rem 0.5rem;
    font-size: 0.72rem;
    color: var(--text);
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  li button:hover,
  li button.active {
    background: var(--bg-elevated);
  }
  .empty {
    padding: 0.5rem;
    font-size: 0.72rem;
    color: var(--muted);
  }
</style>
