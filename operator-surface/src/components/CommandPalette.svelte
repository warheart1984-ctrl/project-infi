<script lang="ts">
  export interface PaletteCommand {
    id: string;
    label: string;
    hint?: string;
  }

  let {
    open = false,
    mode = "commands" as "commands" | "files",
    query = "",
    commands = [] as PaletteCommand[],
    files = [] as string[],
    onSelect,
    onClose,
    onQueryChange,
  }: {
    open?: boolean;
    mode?: "commands" | "files";
    query?: string;
    commands?: PaletteCommand[];
    files?: string[];
    onSelect?: (id: string) => void;
    onClose?: () => void;
    onQueryChange?: (value: string) => void;
  } = $props();

  let inputEl: HTMLInputElement | undefined = $state();

  const filteredCommands = $derived(
    commands.filter((cmd) => cmd.label.toLowerCase().includes(query.toLowerCase())),
  );

  const filteredFiles = $derived(
    files
      .filter((file) => file.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 40),
  );

  $effect(() => {
    if (open && inputEl) {
      inputEl.focus();
      inputEl.select();
    }
  });

  function onKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose?.();
    }
    if (e.key === "Enter") {
      e.preventDefault();
      if (mode === "files" && filteredFiles[0]) {
        onSelect?.(filteredFiles[0]);
      } else if (filteredCommands[0]) {
        onSelect?.(filteredCommands[0].id);
      }
    }
  }
</script>

{#if open}
  <div class="backdrop" role="presentation" onclick={() => onClose?.()}></div>
  <div class="palette" role="dialog" aria-label="Command palette">
    <input
      bind:this={inputEl}
      class="query"
      value={query}
      placeholder={mode === "files" ? "Open file…" : "Type a command…"}
      oninput={(e) => onQueryChange?.((e.currentTarget as HTMLInputElement).value)}
      onkeydown={onKeydown}
    />
    <ul class="list">
      {#if mode === "files"}
        {#each filteredFiles as file (file)}
          <li>
            <button type="button" onclick={() => onSelect?.(file)}>{file}</button>
          </li>
        {/each}
      {:else}
        {#each filteredCommands as cmd (cmd.id)}
          <li>
            <button type="button" onclick={() => onSelect?.(cmd.id)}>
              <span>{cmd.label}</span>
              {#if cmd.hint}
                <span class="hint">{cmd.hint}</span>
              {/if}
            </button>
          </li>
        {/each}
      {/if}
    </ul>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    z-index: 40;
  }
  .palette {
    position: fixed;
    top: 12%;
    left: 50%;
    transform: translateX(-50%);
    width: min(520px, 92vw);
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    z-index: 41;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
    overflow: hidden;
  }
  .query {
    width: 100%;
    border: none;
    border-bottom: 1px solid var(--border);
    border-radius: 0;
    padding: 0.65rem 0.75rem;
    font-size: 0.9rem;
    background: var(--bg-elevated);
  }
  .list {
    list-style: none;
    margin: 0;
    padding: 0.25rem 0;
    max-height: 320px;
    overflow-y: auto;
  }
  .list button {
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    padding: 0.45rem 0.75rem;
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    font-size: 0.82rem;
    color: var(--text);
    cursor: pointer;
  }
  .list button:hover {
    background: var(--bg-elevated);
  }
  .hint {
    color: var(--muted);
    font-size: 0.72rem;
  }
</style>
