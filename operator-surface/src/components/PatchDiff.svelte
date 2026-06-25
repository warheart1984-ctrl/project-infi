<script lang="ts">
  import type { ParsedDiff } from "../lib/diffParse";
  import { flatDiffLines } from "../lib/diffParse";

  interface Props {
    diff: ParsedDiff;
    onOpenPath?: (path: string) => void;
  }

  let { diff, onOpenPath }: Props = $props();

  const lines = $derived(flatDiffLines(diff));
</script>

<div class="patch-diff">
  <div class="patch-head">
    {#if diff.path && onOpenPath}
      <button type="button" class="path-link" onclick={() => onOpenPath(diff.path)}>
        {diff.path}
      </button>
    {:else if diff.path}
      <span class="path-label">{diff.path}</span>
    {/if}
  </div>
  <div class="columns">
    <div class="col">
      <div class="col-label">Before</div>
      <pre class="code">{diff.before || "(empty)"}</pre>
    </div>
    <div class="col">
      <div class="col-label">After</div>
      <pre class="code">{diff.after || "(empty)"}</pre>
    </div>
  </div>
  {#if lines.length}
    <details class="hunks">
      <summary>Unified diff ({lines.length} lines)</summary>
      <pre class="hunk-lines">
{#each lines as line (line.text + line.type)}
<span class={line.type}>{line.type === "add" ? "+" : line.type === "remove" ? "-" : line.type === "header" ? "" : " "}{line.text}{line.type === "header" ? "\n" : ""}</span>
{/each}</pre>
    </details>
  {/if}
</div>

<style>
  .patch-diff {
    margin-top: 0.35rem;
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
  }
  .patch-head {
    padding: 0.35rem 0.5rem;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border);
    font-size: 0.72rem;
  }
  .path-link {
    background: none;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    padding: 0;
    text-decoration: underline;
  }
  .path-label {
    font-family: var(--font-mono);
    color: var(--muted);
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
  }
  .col {
    min-width: 0;
    border-right: 1px solid var(--border);
  }
  .col:last-child {
    border-right: none;
  }
  .col-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted);
    padding: 0.25rem 0.5rem;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
  }
  .code {
    margin: 0;
    padding: 0.45rem 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 10rem;
    overflow: auto;
    background: var(--bg-elevated);
  }
  .hunks {
    padding: 0.35rem 0.5rem 0.5rem;
    font-size: 0.7rem;
  }
  .hunk-lines {
    margin: 0.35rem 0 0;
    padding: 0.4rem;
    background: var(--bg-elevated);
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    max-height: 8rem;
    overflow: auto;
    white-space: pre-wrap;
  }
  .hunk-lines :global(.add) {
    color: #7dcea0;
  }
  .hunk-lines :global(.remove) {
    color: #f1948a;
  }
  .hunk-lines :global(.context) {
    color: var(--muted);
  }
  .hunk-lines :global(.header) {
    color: #93c5fd;
  }
</style>
