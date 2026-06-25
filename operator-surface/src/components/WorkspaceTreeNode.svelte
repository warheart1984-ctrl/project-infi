<script lang="ts">
  import WorkspaceTreeNode from "./WorkspaceTreeNode.svelte";
  import type { TreeNode } from "../lib/workspaceTree";

  interface Props {
    node: TreeNode;
    depth?: number;
    selectedPath?: string | null;
    onSelect?: (path: string) => void;
  }

  let { node, depth = 0, selectedPath = null, onSelect }: Props = $props();

  let expanded = $state(depth < 2);

  const isDir = $derived(!node.isFile);

  function toggle() {
    if (isDir) expanded = !expanded;
    else onSelect?.(node.path);
  }

  function selectFile() {
    if (!isDir) onSelect?.(node.path);
  }
</script>

{#if node.name}
  <div class="tree-row" style="padding-left: {depth * 12}px">
    <button
      type="button"
      class="tree-btn"
      class:selected={node.isFile && selectedPath === node.path}
      onclick={toggle}
      ondblclick={selectFile}
    >
      <span class="icon">{isDir ? (expanded ? "📂" : "📁") : "📄"}</span>
      <span class="label">{node.name}</span>
    </button>
  </div>
{/if}

{#if isDir && expanded}
  {#each node.children as child (child.path)}
    <WorkspaceTreeNode
      node={child}
      depth={node.name ? depth + 1 : depth}
      {selectedPath}
      {onSelect}
    />
  {/each}
{/if}

<style>
  .tree-row {
    display: flex;
    align-items: center;
  }
  .tree-btn {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    padding: 0.2rem 0.35rem;
    border-radius: 4px;
    font-size: 0.82rem;
    color: inherit;
  }
  .tree-btn:hover {
    background: var(--bg-hover);
  }
  .tree-btn.selected {
    background: var(--accent-dim);
    color: #fff;
  }
  .icon {
    width: 1.1rem;
    flex-shrink: 0;
  }
  .label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
