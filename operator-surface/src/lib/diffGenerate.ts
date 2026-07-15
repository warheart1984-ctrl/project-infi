/** Build a unified diff string from original and edited file content. */

function splitLines(text: string): string[] {
  const normalized = text.replace(/\r\n/g, "\n");
  if (!normalized) {
    return [];
  }
  const parts = normalized.split("\n");
  if (normalized.endsWith("\n")) {
    parts.pop();
  }
  return parts;
}

function longestCommonSubsequence(a: string[], b: string[]): number[][] {
  const rows = a.length + 1;
  const cols = b.length + 1;
  const dp: number[][] = Array.from({ length: rows }, () => Array(cols).fill(0));
  for (let i = 1; i < rows; i += 1) {
    for (let j = 1; j < cols; j += 1) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  return dp;
}

export function buildUnifiedDiff(path: string, before: string, after: string): string {
  const oldLines = splitLines(before);
  const newLines = splitLines(after);
  if (oldLines.join("\n") === newLines.join("\n")) {
    return "";
  }

  const dp = longestCommonSubsequence(oldLines, newLines);
  const ops: Array<{ type: "equal" | "remove" | "add"; text: string }> = [];
  let i = oldLines.length;
  let j = newLines.length;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      ops.push({ type: "equal", text: oldLines[i - 1] });
      i -= 1;
      j -= 1;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      ops.push({ type: "add", text: newLines[j - 1] });
      j -= 1;
    } else {
      ops.push({ type: "remove", text: oldLines[i - 1] });
      i -= 1;
    }
  }
  ops.reverse();

  const header = [`--- a/${path}`, `+++ b/${path}`];
  const body: string[] = [];
  let oldIdx = 1;
  let newIdx = 1;
  let hunk: string[] = [];
  let hunkOld = 0;
  let hunkNew = 0;

  function flushHunk() {
    if (!hunk.length) {
      return;
    }
    const oldCount = hunk.filter((line) => line.startsWith(" ") || line.startsWith("-")).length;
    const newCount = hunk.filter((line) => line.startsWith(" ") || line.startsWith("+")).length;
    const startOld = oldIdx - hunkOld;
    const startNew = newIdx - hunkNew;
    body.push(`@@ -${startOld},${oldCount} +${startNew},${newCount} @@`);
    body.push(...hunk);
    hunk = [];
    hunkOld = 0;
    hunkNew = 0;
  }

  for (const op of ops) {
    if (op.type === "equal") {
      if (hunk.length) {
        hunk.push(` ${op.text}`);
        hunkOld += 1;
        hunkNew += 1;
        oldIdx += 1;
        newIdx += 1;
        if (hunk.length > 12) {
          flushHunk();
        }
      } else {
        oldIdx += 1;
        newIdx += 1;
      }
      continue;
    }
    if (op.type === "remove") {
      hunk.push(`-${op.text}`);
      hunkOld += 1;
      oldIdx += 1;
    } else {
      hunk.push(`+${op.text}`);
      hunkNew += 1;
      newIdx += 1;
    }
  }
  flushHunk();

  return [...header, ...body].join("\n") + (body.length ? "\n" : "");
}

export function hasContentDiff(before: string, after: string): boolean {
  return before.replace(/\r\n/g, "\n") !== after.replace(/\r\n/g, "\n");
}
