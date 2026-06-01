import type { PrincipalEvolutionState } from "../evolution-state";

interface ObservationAuditSnapshot {
  gatesFailed: number;
  mimicryFindings: number;
}

export interface ObservationAuditGateResult extends ObservationAuditSnapshot {
  active: boolean;
  reason?: "observation-audit-gates" | "observation-audit-mimicry";
}

function clampInt(value: number, min: number, max: number): number {
  return Math.min(Math.max(Math.floor(value), min), max);
}

function observationAuditWindowMs(): number {
  const raw = process.env.SPIRAL_OBSERVATION_AUDIT_INTERVAL_MS;
  const parsed = Number.parseInt(raw || "", 10);
  if (!Number.isFinite(parsed)) {
    return 15 * 60_000;
  }
  return clampInt(parsed, 60_000, 24 * 60 * 60_000);
}

export function parseObservationAuditSummary(
  summary: string | undefined,
): ObservationAuditSnapshot | undefined {
  const text = (summary || "").trim();
  if (!text) return undefined;

  const gatesMatch = text.match(/\bgatesFailed=(\d+)\b/);
  const mimicryMatch = text.match(/\bmimicryFindings=(\d+)\b/);
  if (!gatesMatch || !mimicryMatch) {
    return undefined;
  }

  return {
    gatesFailed: Math.max(0, Number.parseInt(gatesMatch[1] || "0", 10) || 0),
    mimicryFindings: Math.max(0, Number.parseInt(mimicryMatch[1] || "0", 10) || 0),
  };
}

export function resolveObservationAuditGate(
  state: Pick<PrincipalEvolutionState, "lastObservationAuditAt" | "lastObservationAuditSummary">,
  now = Date.now(),
): ObservationAuditGateResult {
  const parsed = parseObservationAuditSummary(state.lastObservationAuditSummary);
  if (!parsed) {
    return {
      active: false,
      gatesFailed: 0,
      mimicryFindings: 0,
    };
  }

  const auditedAt = Number.isFinite(state.lastObservationAuditAt) ? state.lastObservationAuditAt : 0;
  const fresh = auditedAt > 0 && now - auditedAt <= observationAuditWindowMs();
  if (!fresh) {
    return {
      active: false,
      gatesFailed: parsed.gatesFailed,
      mimicryFindings: parsed.mimicryFindings,
    };
  }

  if (parsed.mimicryFindings > 0) {
    return {
      active: true,
      reason: "observation-audit-mimicry",
      gatesFailed: parsed.gatesFailed,
      mimicryFindings: parsed.mimicryFindings,
    };
  }

  if (parsed.gatesFailed > 0) {
    return {
      active: true,
      reason: "observation-audit-gates",
      gatesFailed: parsed.gatesFailed,
      mimicryFindings: parsed.mimicryFindings,
    };
  }

  return {
    active: false,
    gatesFailed: parsed.gatesFailed,
    mimicryFindings: parsed.mimicryFindings,
  };
}
