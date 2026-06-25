<script lang="ts">
  import type { ActivityLine } from "../lib/formatActivity";
  import PatchDiff from "./PatchDiff.svelte";

  interface Props {
    line: ActivityLine;
    onApprove?: () => void;
    onReject?: () => void;
    busy?: boolean;
  }

  let { line, onApprove, onReject, busy = false }: Props = $props();

  let expanded = $state(false);

  const toneClass = $derived(
    line.tone === "success"
      ? "tone-success"
      : line.tone === "warn"
        ? "tone-warn"
        : line.tone === "error"
          ? "tone-error"
          : "tone-info",
  );
</script>

<article class="activity-item {toneClass}">
  <header class="activity-head">
    <span class="activity-title">{line.title}</span>
    {#if line.parsedDiff || line.fields.length > 0}
      <button type="button" class="ghost-btn small" onclick={() => (expanded = !expanded)}>
        {expanded ? "Hide" : "Details"}
      </button>
    {/if}
  </header>

  {#if expanded && line.fields.length > 0}
    <dl class="field-list">
      {#each line.fields as field}
        <div class="field-row">
          <dt>{field.label}</dt>
          <dd>{field.value}</dd>
        </div>
      {/each}
    </dl>
  {/if}

  {#if expanded && line.parsedDiff}
    <PatchDiff diff={line.parsedDiff} />
  {/if}

  {#if line.showApprovalActions}
    <div class="approval-row">
      <button type="button" class="primary-btn" disabled={busy} onclick={() => onApprove?.()}>
        Approve patch
      </button>
      <button type="button" class="danger-btn" disabled={busy} onclick={() => onReject?.()}>
        Reject
      </button>
    </div>
  {/if}
</article>

<style>
  .activity-item {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.65rem 0.75rem;
    background: var(--panel);
  }
  .activity-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }
  .activity-title {
    font-size: 0.9rem;
    font-weight: 600;
  }
  .field-list {
    margin: 0.5rem 0 0;
    font-size: 0.8rem;
  }
  .field-row {
    display: grid;
    grid-template-columns: 5rem 1fr;
    gap: 0.35rem;
    margin-bottom: 0.25rem;
  }
  .field-row dt {
    color: var(--muted);
    margin: 0;
  }
  .field-row dd {
    margin: 0;
    word-break: break-word;
  }
  .approval-row {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.65rem;
  }
  .tone-success {
    border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
  }
  .tone-warn {
    border-color: color-mix(in srgb, #c9a227 50%, var(--border));
  }
  .tone-error {
    border-color: color-mix(in srgb, #c44 50%, var(--border));
  }
</style>
