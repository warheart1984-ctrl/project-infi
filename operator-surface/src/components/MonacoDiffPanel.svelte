<script lang="ts">
  import { onDestroy } from "svelte";
  import loader from "@monaco-editor/loader";

  let {
    path = "",
    original = "",
    modified = "",
    onClose,
  }: {
    path?: string;
    original?: string;
    modified?: string;
    onClose?: () => void;
  } = $props();

  let container: HTMLDivElement | undefined = $state();
  let diffEditor: import("monaco-editor").editor.IStandaloneDiffEditor | null = null;
  let monacoApi: typeof import("monaco-editor") | null = null;

  function disposeDiffEditor() {
    diffEditor?.dispose();
    diffEditor = null;
  }

  async function ensureDiffEditor() {
    if (!container) {
      return;
    }
    if (!monacoApi) {
      monacoApi = await loader.init();
    }
    if (!container) {
      return;
    }
    if (!diffEditor) {
      diffEditor = monacoApi.editor.createDiffEditor(container, {
        theme: "vs-dark",
        automaticLayout: true,
        readOnly: true,
        renderSideBySide: true,
        minimap: { enabled: false },
        fontSize: 13,
      });
    }
    diffEditor.setModel({
      original: monacoApi.editor.createModel(original, "plaintext"),
      modified: monacoApi.editor.createModel(modified, "plaintext"),
    });
  }

  $effect(() => {
    if (!container) {
      return;
    }
    void ensureDiffEditor();
  });

  $effect(() => {
    if (!diffEditor || !monacoApi) {
      return;
    }
    const models = diffEditor.getModel();
    if (!models) {
      return;
    }
    if (models.original.getValue() !== original) {
      models.original.setValue(original);
    }
    if (models.modified.getValue() !== modified) {
      models.modified.setValue(modified);
    }
  });

  onDestroy(() => {
    disposeDiffEditor();
  });
</script>

<div class="diff-panel">
  <header class="head">
    <span>Review changes — {path}</span>
    <button type="button" class="close" onclick={() => onClose?.()}>Close (Esc)</button>
  </header>
  <div class="host" bind:this={container}></div>
</div>

<style>
  .diff-panel {
    position: absolute;
    inset: 0;
    z-index: 20;
    display: flex;
    flex-direction: column;
    background: #0c0e14;
  }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.78rem;
    color: var(--muted);
    flex-shrink: 0;
  }
  .close {
    font-size: 0.72rem;
  }
  .host {
    flex: 1;
    min-height: 0;
  }
</style>
