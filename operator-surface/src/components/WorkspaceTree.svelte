<script lang="ts">
  import { buildTree } from "../lib/workspaceTree";
  import WorkspaceTreeNode from "./WorkspaceTreeNode.svelte";

  interface Props {
    files: string[];
    selectedPath?: string | null;
    onSelect?: (path: string) => void;
  }

  let { files, selectedPath = null, onSelect }: Props = $props();

  const tree = $derived(buildTree(files));
</script>

<div class="workspace-tree">
  {#if files.length === 0}
    <p class="empty">No files in workspace yet.</p>
  {:else}
    {#each tree as node (node.path)}
      <WorkspaceTreeNode {node} {selectedPath} {onSelect} />
    {/each}
  {/if}
</div>

<style>
  .workspace-tree {
    font-size: 0.82rem;
    overflow: auto;
    max-height: 100%;
  }
  .empty {
    color: var(--muted);
    font-size: 0.8rem;
    margin: 0.5rem;
  }
</style>
