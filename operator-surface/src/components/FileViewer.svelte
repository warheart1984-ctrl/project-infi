<script lang="ts">
  import { onDestroy } from "svelte";
  import loader from "@monaco-editor/loader";

  let {
    path = "",
    content = "",
    lineCount = 0,
    loading = false,
    error = "",
    onChange,
  }: {
    path?: string;
    content?: string;
    lineCount?: number;
    loading?: boolean;
    error?: string;
    onChange?: (value: string) => void;
  } = $props();

  let container: HTMLDivElement | undefined = $state();
  let editor: import("monaco-editor").editor.IStandaloneCodeEditor | null = null;
  let monacoApi: typeof import("monaco-editor") | null = null;
  let lastPath = "";
  let suppressChange = false;

  function languageForPath(filePath: string): string {
    const ext = filePath.split(".").pop()?.toLowerCase() ?? "";
    const map: Record<string, string> = {
      ts: "typescript",
      tsx: "typescript",
      js: "javascript",
      jsx: "javascript",
      py: "python",
      json: "json",
      md: "markdown",
      css: "css",
      html: "html",
      svelte: "html",
      yaml: "yaml",
      yml: "yaml",
      rs: "rust",
      go: "go",
    };
    return map[ext] ?? "plaintext";
  }

  function disposeEditor() {
    editor?.dispose();
    editor = null;
  }

  async function ensureEditor() {
    if (!container || !path || loading || error) {
      return;
    }
    if (!monacoApi) {
      monacoApi = await loader.init();
    }
    if (!container) {
      return;
    }
    if (!editor) {
      editor = monacoApi.editor.create(container, {
        value: content,
        language: languageForPath(path),
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 13,
        scrollBeyondLastLine: false,
        wordWrap: "on",
      });
      editor.onDidChangeModelContent(() => {
        if (suppressChange || !editor) {
          return;
        }
        onChange?.(editor.getValue());
      });
      lastPath = path;
      return;
    }
    if (path !== lastPath) {
      lastPath = path;
      const model = editor.getModel();
      if (model && monacoApi) {
        monacoApi.editor.setModelLanguage(model, languageForPath(path));
      }
    }
    const current = editor.getValue();
    if (current !== content) {
      suppressChange = true;
      editor.setValue(content);
      suppressChange = false;
    }
  }

  $effect(() => {
    if (!container || !path || loading || error) {
      disposeEditor();
      return;
    }
    void ensureEditor();
  });

  onDestroy(() => {
    disposeEditor();
  });
</script>

<div class="viewer">
  {#if !path}
    <p class="empty">Select a file in the workspace tree.</p>
  {:else if loading}
    <p class="empty">Loading {path}…</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="header">
      <span class="path">{path}</span>
      <span class="meta">{lineCount} lines</span>
    </div>
    <div class="editor-host" bind:this={container}></div>
  {/if}
</div>

<style>
  .viewer {
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100%;
  }
  .header {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.35rem 0.5rem;
    border-bottom: 1px solid #2a3142;
    font-size: 0.75rem;
    color: #9aa3b8;
    flex-shrink: 0;
  }
  .path {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .editor-host {
    flex: 1;
    min-height: 0;
  }
  .empty,
  .error {
    padding: 0.75rem;
    font-size: 0.85rem;
    color: #7a8499;
  }
  .error {
    color: #ffb4b4;
  }
</style>
