export interface DiffLine {
  type: "add" | "remove" | "context" | "header";
  text: string;
}

export interface DiffHunk {
  header: string;
  lines: DiffLine[];
}

export interface ParsedDiff {
  path: string;
  hunks: DiffHunk[];
  before: string;
  after: string;
}

export function parseUnifiedDiff(diff: string, fallbackPath = ""): ParsedDiff {
  const lines = diff.replace(/\r\n/g, "\n").split("\n");
  const hunks: DiffHunk[] = [];
  let current: DiffHunk | null = null;
  let path = fallbackPath;

  for (const line of lines) {
    if (line.startsWith("+++ ")) {
      const p = line.slice(4).trim();
      if (p !== "/dev/null" && !p.startsWith("b/")) {
        path = p;
      } else if (p.startsWith("b/")) {
        path = p.slice(2);
      }
      continue;
    }
    if (line.startsWith("@@")) {
      current = { header: line, lines: [] };
      hunks.push(current);
      continue;
    }
    if (!current) {
      continue;
    }
    if (line.startsWith("+")) {
      current.lines.push({ type: "add", text: line.slice(1) });
    } else if (line.startsWith("-")) {
      current.lines.push({ type: "remove", text: line.slice(1) });
    } else if (line.startsWith(" ")) {
      current.lines.push({ type: "context", text: line.slice(1) });
    }
  }

  const before: string[] = [];
  const after: string[] = [];
  for (const hunk of hunks) {
    for (const line of hunk.lines) {
      if (line.type === "remove" || line.type === "context") {
        before.push(line.text);
      }
      if (line.type === "add" || line.type === "context") {
        after.push(line.text);
      }
    }
  }

  return {
    path,
    hunks,
    before: before.join("\n"),
    after: after.join("\n"),
  };
}

export function flatDiffLines(parsed: ParsedDiff): DiffLine[] {
  const out: DiffLine[] = [];
  for (const hunk of parsed.hunks) {
    if (hunk.header) {
      out.push({ type: "header", text: hunk.header });
    }
    out.push(...hunk.lines);
  }
  return out;
}
