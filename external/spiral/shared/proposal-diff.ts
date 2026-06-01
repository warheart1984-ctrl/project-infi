function isDiffContentLine(line: string): boolean {
  if (!line) return false;
  if (line.startsWith("+++ ") || line.startsWith("--- ")) return false;
  return line.startsWith("+") || line.startsWith("-");
}

function stripDiffMarker(line: string): string {
  return line.slice(1).trim();
}

function isCommentLike(value: string): boolean {
  if (!value) return true;
  if (value.startsWith("//")) return true;
  if (value.startsWith("/*")) return true;
  if (value.startsWith("*")) return true;
  if (value.startsWith("*/")) return true;
  if (value.startsWith("#")) return true;
  return false;
}

function hasCodeSignal(value: string): boolean {
  return (
    /\b(if|else|return|const|let|var|function|type|interface|class|import|export|await|for|while|switch|case|try|catch|new)\b/.test(
      value,
    ) || /[{}()[\];.=<>:+\-*/]/.test(value)
  );
}

export function getDiffChangedContentLines(diffPreview: string): string[] {
  return diffPreview
    .split(/\r?\n/)
    .filter(isDiffContentLine)
    .map(stripDiffMarker)
    .map((line) => line.trimEnd());
}

export function isCommentOnlyDiffPreview(diffPreview: string): boolean {
  const lines = getDiffChangedContentLines(diffPreview)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length === 0) return true;
  return lines.every((line) => isCommentLike(line));
}

export function hasConcreteCodeChange(diffPreview: string): boolean {
  const lines = getDiffChangedContentLines(diffPreview)
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !isCommentLike(line));
  if (lines.length === 0) return false;
  return lines.some((line) => hasCodeSignal(line));
}

export function isProposalApplyableDiff(diffPreview: string): boolean {
  if (isCommentOnlyDiffPreview(diffPreview)) return false;
  return hasConcreteCodeChange(diffPreview);
}
