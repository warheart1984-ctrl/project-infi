import type { RewriteProposalStatus } from "@shared/schema";
import { readIdentitySnapshot } from "./identity-memory";
import { getPrincipalEvolutionState } from "./evolution-state";
import { listRewriteProposals } from "./proposals/proposal-store";

interface ContinuityBootSummaryInput {
  principalId: string;
  memoryMode: string;
  now?: number;
}

interface ContinuityBootSnapshot {
  memoryMode: string;
  evolutionMode: "still" | "wild";
  mutationSealEnabled: boolean;
  lastCycleStatus?: "skipped" | "drafted" | "executed" | "applied" | "failed";
  lastCycleSummary?: string;
  latestProposal?: {
    id: string;
    status: RewriteProposalStatus;
  };
  pendingProposalCount: number;
  identityMode: "stable" | "balanced" | "exploratory";
  identityStability: number;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function normalizeLine(value: string | undefined, fallback: string): string {
  const normalized = (value || "").trim().replace(/\s+/g, " ");
  return normalized ? normalized : fallback;
}

export function renderContinuityBootSummary(snapshot: ContinuityBootSnapshot): string {
  const lines = [
    "Continuity boot:",
    `Memory mode: ${snapshot.memoryMode}`,
    `Evolution mode: ${snapshot.evolutionMode.toUpperCase()}`,
    `Mutation seal: ${snapshot.mutationSealEnabled ? "ON" : "OFF"}`,
    `Identity mode: ${snapshot.identityMode}`,
    `Identity stability: ${snapshot.identityStability.toFixed(2)}`,
    `Pending proposals: ${snapshot.pendingProposalCount}`,
    snapshot.latestProposal
      ? `Latest proposal: ${snapshot.latestProposal.id} (${snapshot.latestProposal.status})`
      : "Latest proposal: none",
  ];
  if (snapshot.lastCycleStatus) {
    lines.push(`Last cycle status: ${snapshot.lastCycleStatus}`);
  }
  if (snapshot.lastCycleSummary) {
    lines.push(`Last cycle note: ${normalizeLine(snapshot.lastCycleSummary, "n/a")}`);
  }
  return lines.join("\n");
}

export async function buildContinuityBootSummary(
  input: ContinuityBootSummaryInput,
): Promise<string> {
  const principalId = input.principalId.trim();
  if (!principalId) return "";
  const now = Math.max(1, Math.floor(input.now || Date.now()));
  const [evolutionState, identitySnapshot, latestProposals, pendingProposals] = await Promise.all([
    getPrincipalEvolutionState(principalId, now),
    readIdentitySnapshot(now),
    listRewriteProposals({ principalId, limit: 1 }),
    listRewriteProposals({ principalId, status: "pending", limit: 200 }),
  ]);

  return renderContinuityBootSummary({
    memoryMode: input.memoryMode,
    evolutionMode: evolutionState.mode,
    mutationSealEnabled: evolutionState.mutationSealEnabled === true,
    ...(evolutionState.lastCycleStatus ? { lastCycleStatus: evolutionState.lastCycleStatus } : {}),
    ...(evolutionState.lastCycleSummary
      ? { lastCycleSummary: evolutionState.lastCycleSummary }
      : {}),
    ...(latestProposals[0]
      ? {
          latestProposal: {
            id: latestProposals[0].id,
            status: latestProposals[0].status,
          },
        }
      : {}),
    pendingProposalCount: pendingProposals.length,
    identityMode: identitySnapshot.core.current_mode,
    identityStability: clamp(identitySnapshot.core.self_stability, 0, 1),
  });
}
