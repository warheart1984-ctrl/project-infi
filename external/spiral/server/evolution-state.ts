import { existsSync } from "fs";
import { mkdir, readFile, writeFile, appendFile } from "fs/promises";
import path from "path";

export type EvolutionMode = "still" | "wild";
export type EvolutionTrigger = "manual" | "pulse";

export interface PrincipalEvolutionState {
  mode: EvolutionMode;
  backgroundPulseEnabled: boolean;
  autoApplyEnabled: boolean;
  mutationSealEnabled: boolean;
  updatedAt: number;
  lastCycleId?: number;
  lastSeenChatId?: string;
  lastCycleAt: number;
  lastCycleTrigger?: EvolutionTrigger;
  lastCycleChatId?: string;
  lastCycleStatus?: "skipped" | "drafted" | "executed" | "applied" | "failed";
  lastCycleSummary?: string;
  lastProposalId?: string;
  lastCommitHash?: string;
  lastObservationAuditAt: number;
  lastObservationAuditSummary?: string;
}

interface EvolutionStateFileV1 {
  schemaVersion: "evolution-state.v1";
  principals: Record<string, PrincipalEvolutionState>;
}

interface EvolutionLedgerEntry {
  schemaVersion: "evolution-ledger.v1";
  timestamp: number;
  principalId: string;
  type:
    | "mode"
    | "background"
    | "auto-apply"
    | "mutation-seal"
    | "observation-audit"
    | "cycle-skipped"
    | "cycle-drafted"
    | "cycle-executed"
    | "cycle-applied"
    | "cycle-failed";
  detail: string;
  chatId?: string;
  proposalId?: string;
  cycleId?: number;
  mode?: EvolutionMode;
  trigger?: EvolutionTrigger;
  signal?: string;
  commitHash?: string;
  driftIndex?: {
    filesTouched: number;
    linesAdded: number;
    linesDeleted: number;
    semanticDiffScore: number;
    invariantImpact: "none" | "low" | "medium" | "high";
  };
}

const EVOLUTION_STATE_SCHEMA_VERSION = "evolution-state.v1";
const EVOLUTION_LEDGER_SCHEMA_VERSION = "evolution-ledger.v1";

export const EVOLUTION_STATE_PATH = path.join(process.cwd(), ".local", "evolution-state.json");
export const EVOLUTION_LEDGER_PATH = path.join(process.cwd(), ".local", "evolution-ledger.jsonl");

function normalizePrincipalId(value: string): string {
  return value.trim().slice(0, 200);
}

function normalizeChatId(value: string | undefined): string | undefined {
  if (!value) return undefined;
  const normalized = value.trim();
  return normalized ? normalized : undefined;
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
}

function normalizeOptionalTimestamp(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.floor(value));
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(",")}]`;
  }
  const entries = Object.entries(value as Record<string, unknown>).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );
  return `{${entries
    .map(([key, nested]) => `${JSON.stringify(key)}:${stableStringify(nested)}`)
    .join(",")}}`;
}

function defaultPrincipalEvolutionState(now = Date.now()): PrincipalEvolutionState {
  const timestamp = normalizeTimestamp(now);
  return {
    mode: "still",
    backgroundPulseEnabled: true,
    autoApplyEnabled: false,
    mutationSealEnabled: false,
    updatedAt: timestamp,
    lastCycleAt: 0,
    lastObservationAuditAt: 0,
  };
}

function parseStateFile(raw: string): EvolutionStateFileV1 | undefined {
  try {
    const parsed = JSON.parse(raw) as Partial<EvolutionStateFileV1>;
    if (parsed.schemaVersion !== EVOLUTION_STATE_SCHEMA_VERSION) return undefined;
    if (!parsed.principals || typeof parsed.principals !== "object") return undefined;
    const principals: Record<string, PrincipalEvolutionState> = {};
    for (const [rawPrincipalId, value] of Object.entries(parsed.principals)) {
      const principalId = normalizePrincipalId(rawPrincipalId);
      if (!principalId) continue;
      const state = value as Partial<PrincipalEvolutionState>;
      principals[principalId] = {
        mode: state.mode === "wild" ? "wild" : "still",
        backgroundPulseEnabled: state.backgroundPulseEnabled !== false,
        autoApplyEnabled: state.autoApplyEnabled === true,
        mutationSealEnabled: state.mutationSealEnabled === true,
        updatedAt: normalizeTimestamp(state.updatedAt ?? Date.now()),
        ...(normalizeChatId(state.lastSeenChatId)
          ? { lastSeenChatId: normalizeChatId(state.lastSeenChatId) }
          : {}),
        lastCycleAt: normalizeOptionalTimestamp(state.lastCycleAt ?? 0),
        lastObservationAuditAt: normalizeOptionalTimestamp(state.lastObservationAuditAt ?? 0),
        ...(state.lastCycleTrigger === "manual" || state.lastCycleTrigger === "pulse"
          ? { lastCycleTrigger: state.lastCycleTrigger }
          : {}),
        ...(normalizeChatId(state.lastCycleChatId)
          ? { lastCycleChatId: normalizeChatId(state.lastCycleChatId) }
          : {}),
        ...(state.lastCycleStatus
          ? {
              lastCycleStatus:
                state.lastCycleStatus === "skipped" ||
                state.lastCycleStatus === "drafted" ||
                state.lastCycleStatus === "executed" ||
                state.lastCycleStatus === "applied" ||
                state.lastCycleStatus === "failed"
                  ? state.lastCycleStatus
                  : undefined,
            }
          : {}),
        ...(typeof state.lastCycleSummary === "string" && state.lastCycleSummary.trim()
          ? { lastCycleSummary: state.lastCycleSummary.trim().slice(0, 1000) }
          : {}),
        ...(typeof state.lastProposalId === "string" && state.lastProposalId.trim()
          ? { lastProposalId: state.lastProposalId.trim().slice(0, 120) }
          : {}),
        ...(typeof state.lastCommitHash === "string" && state.lastCommitHash.trim()
          ? { lastCommitHash: state.lastCommitHash.trim().slice(0, 64) }
          : {}),
        ...(typeof state.lastObservationAuditSummary === "string" &&
        state.lastObservationAuditSummary.trim()
          ? { lastObservationAuditSummary: state.lastObservationAuditSummary.trim().slice(0, 1000) }
          : {}),
        ...(Number.isFinite(state.lastCycleId)
          ? { lastCycleId: Math.max(1, Math.floor(state.lastCycleId as number)) }
          : {}),
      };
    }
    return {
      schemaVersion: EVOLUTION_STATE_SCHEMA_VERSION,
      principals,
    };
  } catch {
    return undefined;
  }
}

export async function readEvolutionState(): Promise<EvolutionStateFileV1> {
  try {
    if (!existsSync(EVOLUTION_STATE_PATH)) {
      return {
        schemaVersion: EVOLUTION_STATE_SCHEMA_VERSION,
        principals: {},
      };
    }
    const raw = await readFile(EVOLUTION_STATE_PATH, "utf8");
    const parsed = parseStateFile(raw);
    if (parsed) return parsed;
  } catch {
    // Fall through to empty default.
  }
  return {
    schemaVersion: EVOLUTION_STATE_SCHEMA_VERSION,
    principals: {},
  };
}

async function writeEvolutionState(state: EvolutionStateFileV1): Promise<void> {
  const normalizedPrincipals = Object.fromEntries(
    Object.entries(state.principals)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([principalId, value]) => {
        const normalized: PrincipalEvolutionState = {
          ...value,
          updatedAt: normalizeTimestamp(value.updatedAt),
          lastCycleAt: normalizeOptionalTimestamp(value.lastCycleAt || 0),
          lastObservationAuditAt: normalizeOptionalTimestamp(value.lastObservationAuditAt || 0),
        };
        return [principalId, normalized];
      }),
  );
  const payload: EvolutionStateFileV1 = {
    schemaVersion: EVOLUTION_STATE_SCHEMA_VERSION,
    principals: normalizedPrincipals,
  };
  await mkdir(path.dirname(EVOLUTION_STATE_PATH), { recursive: true });
  await writeFile(EVOLUTION_STATE_PATH, `${stableStringify(payload)}\n`, "utf8");
}

export async function getPrincipalEvolutionState(
  principalIdRaw: string,
  now = Date.now(),
): Promise<PrincipalEvolutionState> {
  const principalId = normalizePrincipalId(principalIdRaw);
  if (!principalId) {
    return defaultPrincipalEvolutionState(now);
  }
  const state = await readEvolutionState();
  return state.principals[principalId] || defaultPrincipalEvolutionState(now);
}

export async function updatePrincipalEvolutionState(
  principalIdRaw: string,
  update: (current: PrincipalEvolutionState) => PrincipalEvolutionState,
  now = Date.now(),
): Promise<PrincipalEvolutionState> {
  const principalId = normalizePrincipalId(principalIdRaw);
  if (!principalId) {
    return defaultPrincipalEvolutionState(now);
  }
  const currentState = await readEvolutionState();
  const current = currentState.principals[principalId] || defaultPrincipalEvolutionState(now);
  const next = update(current);
  const normalizedNext: PrincipalEvolutionState = {
    ...current,
    ...next,
    updatedAt: normalizeTimestamp(now),
    lastCycleAt: normalizeOptionalTimestamp(next.lastCycleAt ?? current.lastCycleAt ?? 0),
    lastObservationAuditAt: normalizeOptionalTimestamp(
      next.lastObservationAuditAt ?? current.lastObservationAuditAt ?? 0,
    ),
    mode: next.mode === "wild" ? "wild" : "still",
    backgroundPulseEnabled: next.backgroundPulseEnabled !== false,
    autoApplyEnabled: next.autoApplyEnabled === true,
    mutationSealEnabled: next.mutationSealEnabled === true,
    ...(normalizeChatId(next.lastSeenChatId)
      ? { lastSeenChatId: normalizeChatId(next.lastSeenChatId) }
      : {}),
    ...(normalizeChatId(next.lastCycleChatId)
      ? { lastCycleChatId: normalizeChatId(next.lastCycleChatId) }
      : {}),
    ...(Number.isFinite(next.lastCycleId)
      ? { lastCycleId: Math.max(1, Math.floor(next.lastCycleId as number)) }
      : {}),
    ...(typeof next.lastCommitHash === "string" && next.lastCommitHash.trim()
      ? { lastCommitHash: next.lastCommitHash.trim().slice(0, 64) }
      : {}),
    ...(typeof next.lastObservationAuditSummary === "string" &&
    next.lastObservationAuditSummary.trim()
      ? { lastObservationAuditSummary: next.lastObservationAuditSummary.trim().slice(0, 1000) }
      : {}),
  };
  currentState.principals[principalId] = normalizedNext;
  await writeEvolutionState(currentState);
  return normalizedNext;
}

export async function recordEvolutionContext(
  principalId: string,
  chatId: string,
  now = Date.now(),
): Promise<PrincipalEvolutionState> {
  const normalizedChatId = normalizeChatId(chatId);
  return updatePrincipalEvolutionState(
    principalId,
    (current) => ({
      ...current,
      ...(normalizedChatId ? { lastSeenChatId: normalizedChatId } : {}),
    }),
    now,
  );
}

export async function appendEvolutionLedger(entry: Omit<EvolutionLedgerEntry, "schemaVersion">): Promise<void> {
  const normalizedPrincipalId = normalizePrincipalId(entry.principalId);
  if (!normalizedPrincipalId) return;
  const payload: EvolutionLedgerEntry = {
    schemaVersion: EVOLUTION_LEDGER_SCHEMA_VERSION,
    timestamp: normalizeTimestamp(entry.timestamp),
    principalId: normalizedPrincipalId,
    type: entry.type,
    detail: entry.detail.trim().slice(0, 1200),
    ...(normalizeChatId(entry.chatId) ? { chatId: normalizeChatId(entry.chatId) } : {}),
    ...(entry.proposalId && entry.proposalId.trim()
      ? { proposalId: entry.proposalId.trim().slice(0, 120) }
      : {}),
    ...(Number.isFinite(entry.cycleId) && (entry.cycleId || 0) > 0
      ? { cycleId: Math.floor(entry.cycleId as number) }
      : {}),
    ...(entry.mode === "still" || entry.mode === "wild" ? { mode: entry.mode } : {}),
    ...(entry.trigger === "manual" || entry.trigger === "pulse"
      ? { trigger: entry.trigger }
      : {}),
    ...(entry.signal && entry.signal.trim() ? { signal: entry.signal.trim().slice(0, 280) } : {}),
    ...(entry.commitHash && entry.commitHash.trim()
      ? { commitHash: entry.commitHash.trim().slice(0, 64) }
      : {}),
    ...(entry.driftIndex
      ? {
          driftIndex: {
            filesTouched: Math.max(0, Math.floor(entry.driftIndex.filesTouched || 0)),
            linesAdded: Math.max(0, Math.floor(entry.driftIndex.linesAdded || 0)),
            linesDeleted: Math.max(0, Math.floor(entry.driftIndex.linesDeleted || 0)),
            semanticDiffScore: Number.isFinite(entry.driftIndex.semanticDiffScore)
              ? Number(entry.driftIndex.semanticDiffScore.toFixed(6))
              : 0,
            invariantImpact:
              entry.driftIndex.invariantImpact === "none" ||
              entry.driftIndex.invariantImpact === "low" ||
              entry.driftIndex.invariantImpact === "medium" ||
              entry.driftIndex.invariantImpact === "high"
                ? entry.driftIndex.invariantImpact
                : "none",
          },
        }
      : {}),
  };
  await mkdir(path.dirname(EVOLUTION_LEDGER_PATH), { recursive: true });
  await appendFile(EVOLUTION_LEDGER_PATH, `${stableStringify(payload)}\n`, "utf8");
}
