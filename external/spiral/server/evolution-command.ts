import type { PrincipalEvolutionState } from "./evolution-state";

export type EvolutionCommand =
  | { type: "status" }
  | { type: "set-mode"; mode: "still" | "wild" }
  | { type: "set-background"; enabled: boolean }
  | { type: "set-auto-apply"; enabled: boolean }
  | { type: "set-mutation-seal"; enabled: boolean }
  | { type: "cycle"; signal?: string };

const EVOLVE_START_PATTERN = /^\/?evolve(?:\s+(.*))?$/i;
const BG_START_PATTERN = /^\/?bg(?:\s+(.*))?$/i;

function normalizeTail(value: string | undefined): string {
  return (value || "").trim().toLowerCase();
}

function parseBooleanToken(value: string): boolean | undefined {
  if (["on", "true", "1", "yes", "enable", "enabled"].includes(value)) return true;
  if (["off", "false", "0", "no", "disable", "disabled"].includes(value)) return false;
  return undefined;
}

export function parseEvolutionCommand(message: string | undefined): EvolutionCommand | undefined {
  if (!message?.trim()) return undefined;
  const trimmed = message.trim();
  const evolveMatch = trimmed.match(EVOLVE_START_PATTERN);
  if (evolveMatch) {
    const tail = normalizeTail(evolveMatch[1]);
    if (!tail || tail === "status") return { type: "status" };
    if (tail === "on" || tail === "wild") return { type: "set-mode", mode: "wild" };
    if (tail === "off" || tail === "still") return { type: "set-mode", mode: "still" };
    if (tail === "cycle") return { type: "cycle" };
    if (tail.startsWith("cycle ")) {
      const signal = trimmed.replace(/^\/?evolve\s+cycle\s+/i, "").trim();
      return { type: "cycle", ...(signal ? { signal } : {}) };
    }
    const autoApplyMatch = tail.match(/^(?:auto-apply|apply)\s+([a-z0-9-]+)$/i);
    if (autoApplyMatch?.[1]) {
      const enabled = parseBooleanToken(autoApplyMatch[1].toLowerCase());
      if (enabled !== undefined) return { type: "set-auto-apply", enabled };
    }
    const sealMatch = tail.match(/^(?:seal|mutation-seal)\s+([a-z0-9-]+)$/i);
    if (sealMatch?.[1]) {
      const enabled = parseBooleanToken(sealMatch[1].toLowerCase());
      if (enabled !== undefined) return { type: "set-mutation-seal", enabled };
    }
    const bgMatch = tail.match(/^(?:bg|background)\s+([a-z0-9-]+)$/i);
    if (bgMatch?.[1]) {
      const enabled = parseBooleanToken(bgMatch[1].toLowerCase());
      if (enabled !== undefined) return { type: "set-background", enabled };
      if (bgMatch[1].toLowerCase() === "status") return { type: "status" };
    }
    return undefined;
  }

  const bgMatch = trimmed.match(BG_START_PATTERN);
  if (bgMatch) {
    const tail = normalizeTail(bgMatch[1]);
    if (!tail || tail === "status") return { type: "status" };
    const enabled = parseBooleanToken(tail);
    if (enabled !== undefined) return { type: "set-background", enabled };
    return undefined;
  }

  return undefined;
}

function formatTimeAgo(value: number, now: number): string {
  if (!Number.isFinite(value) || value <= 0) return "never";
  const diffMs = Math.max(0, now - value);
  const minutes = Math.floor(diffMs / (1000 * 60));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function renderEvolutionStateSummary(
  state: PrincipalEvolutionState,
  now = Date.now(),
): string {
  const lines = [
    `Evolution mode: ${state.mode.toUpperCase()}`,
    `Background pulse: ${state.backgroundPulseEnabled ? "ON" : "OFF"}`,
    `Auto-apply: ${state.autoApplyEnabled ? "ON" : "OFF"}`,
    `Mutation seal: ${state.mutationSealEnabled ? "ON" : "OFF"}`,
    ...(state.lastCycleId ? [`Last cycle id: ${state.lastCycleId}`] : []),
    `Last cycle: ${formatTimeAgo(state.lastCycleAt, now)}`,
  ];
  if (state.lastCycleStatus) {
    lines.push(`Last cycle status: ${state.lastCycleStatus}`);
  }
  if (state.lastCycleSummary) {
    lines.push(`Last cycle note: ${state.lastCycleSummary}`);
  }
  if (state.lastProposalId) {
    lines.push(`Last proposal: ${state.lastProposalId}`);
  }
  if (state.lastCommitHash) {
    lines.push(`Last ritual commit: ${state.lastCommitHash}`);
  }
  if (state.lastObservationAuditSummary) {
    lines.push(`Last observation audit: ${state.lastObservationAuditSummary}`);
  }
  if (state.lastSeenChatId) {
    lines.push(`Last seen chat: ${state.lastSeenChatId}`);
  }
  return lines.join("\n");
}
