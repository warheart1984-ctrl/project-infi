import {
  formatSelfInspectionQuery,
  formatSelfInspectionSummary,
  getSelfInspectionIndex,
  querySelfInspection,
} from "./self-inspection";

export type SelfInspectCommand =
  | { type: "summary" }
  | { type: "query"; query: string };

const SUMMARY_ONLY_PATTERN =
  /^(?:(?:can|could|would)\s+you\s+|please\s+)?(?:self\s*[- ]?inspect|code trace|mirror mode|self-view mode|code trace mode)[\s:;,.!?-]*$/i;
const QUERY_START_PATTERN =
  /^(?:(?:can|could|would)\s+you\s+|please\s+)?(?:self\s*[- ]?inspect|code trace)\b[\s:;,\-]+(.+)$/i;
const QUERY_INLINE_PATTERN =
  /\b(?:self\s*[- ]?inspect|code trace)\b[\s:;,\-]+(.+)$/i;

function normalizeQuery(raw: string): string {
  return raw
    .trim()
    .replace(/^[`"'([{]+/, "")
    .replace(/[`"')\]}]+$/, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseSelfInspectCommand(message: string | undefined): SelfInspectCommand | undefined {
  if (!message?.trim()) return undefined;
  const trimmed = message.trim();

  if (SUMMARY_ONLY_PATTERN.test(trimmed)) {
    return { type: "summary" };
  }

  const startMatch = trimmed.match(QUERY_START_PATTERN);
  if (startMatch?.[1]) {
    const query = normalizeQuery(startMatch[1]);
    if (query) {
      return {
        type: "query",
        query,
      };
    }
    return { type: "summary" };
  }

  const inlineMatch = trimmed.match(QUERY_INLINE_PATTERN);
  if (inlineMatch?.[1]) {
    const query = normalizeQuery(inlineMatch[1]);
    if (query) {
      return {
        type: "query",
        query,
      };
    }
  }

  return undefined;
}

export async function executeSelfInspectCommand(command: SelfInspectCommand): Promise<string> {
  if (command.type === "summary") {
    const index = await getSelfInspectionIndex();
    return formatSelfInspectionSummary(index);
  }

  const result = await querySelfInspection(command.query);
  return formatSelfInspectionQuery(result);
}
