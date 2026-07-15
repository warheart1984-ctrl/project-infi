export interface TreeNode {
  name: string;
  path: string;
  children: TreeNode[];
  isFile: boolean;
}

export function buildTree(files: string[]): TreeNode[] {
  const root: TreeNode[] = [];
  const index = new Map<string, TreeNode>();

  const sorted = [...files].sort((a, b) => a.localeCompare(b));
  for (const filePath of sorted) {
    const parts = filePath.split("/").filter(Boolean);
    if (parts.length === 0) {
      continue;
    }
    let parentPath = "";
    let level = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isFile = i === parts.length - 1;
      const fullPath = parentPath ? `${parentPath}/${part}` : part;

      let node = index.get(fullPath);
      if (!node) {
        node = {
          name: part,
          path: isFile ? filePath : fullPath,
          children: [],
          isFile,
        };
        index.set(fullPath, node);
        level.push(node);
      }
      parentPath = fullPath;
      level = node.children;
    }
  }

  const sortNodes = (nodes: TreeNode[]): TreeNode[] => {
    nodes.sort((a, b) => {
      if (a.isFile !== b.isFile) {
        return a.isFile ? 1 : -1;
      }
      return a.name.localeCompare(b.name);
    });
    for (const n of nodes) {
      if (n.children.length) {
        sortNodes(n.children);
      }
    }
    return nodes;
  };

  return sortNodes(root);
}
