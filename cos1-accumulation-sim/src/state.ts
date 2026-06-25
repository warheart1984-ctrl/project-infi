import {
  RAState,
  JPSSContributionEventInput,
  LineageChange,
  LedgerEntry,
  ValidationContext,
  ContinuityMetrics,
  AccumulationOrigin,
} from "./domain.js";
import {
  computeDriftSignals,
  computeFullContinuity,
  validateVAS1,
} from "./engine.js";
import { withEventTags } from "./epistemicClassifier.js";
import {
  advanceCycleFromEvent,
  allCyclesForAnalytics,
} from "./judgment/cycleAssembly.js";
import { inferAllCapabilityProfiles } from "./judgment/analytics/capability.js";
import type { JudgmentCycle } from "./judgment/types.js";
import { appendLedgerCycle } from "./ledger/continuityLedger.js";

const emptyPLA = {
  plaCount: 0,
  plaActors: 0,
  plaDepth: 0,
  plaToLaIntegrationRate: 0,
  plaToLaRatio: 0,
  clustering: 0,
  crossDomainRecurrence: 0,
  validationSurvival: 0,
  instrumentality: 0,
};

const emptyLA = { laCount: 0, laActors: 0, laDepth: 0 };
const emptySA = { saCount: 0, saActors: 0 };

const emptyCoupling = {
  plaCompatible: 0,
  plaTotal: 0,
  couplingStrength: 0,
};

const emptyGravity = {
  phenomenonGravity: 0,
  lineageGravity: 0,
  totalObservers: 0,
};

const emptyInvariants = {
  k1IdentityCoherence: true,
  k2GenerativeGrammar: false,
  k3Integrability: true,
  k4Reconstructability: true,
};

const emptyEpistemic = {
  observationCount: 0,
  interpretationCount: 0,
  integrationCount: 0,
  validationCount: 0,
  obsToInterpRatio: 0,
  interpToValidationRatio: 0,
  externalObservationCount: 0,
  profile: "nascent" as const,
};

export function emptyContinuity(): ContinuityMetrics {
  return {
    accumulationCount: 0,
    distinctActors: 0,
    mat3: false,
    plt1: false,
    thresholds: { plt1: false, mat3: false, stewardEmergence: false },
    accumulation: { value: 0, strata: { pla: 0, la: 0, sa: 0 } },
    reconstructability: {
      reconstructionCost: 0,
      reconstructionThreshold: 0.7,
      k4Satisfied: true,
    },
    drift: null,
    pla: emptyPLA,
    la: emptyLA,
    sa: emptySA,
    coupling: emptyCoupling,
    gravity: emptyGravity,
    invariants: emptyInvariants,
    interpretation: "nascent",
    epistemic: emptyEpistemic,
  };
}

export function initialState(): RAState {
  return {
    events: [],
    eventOrigins: {},
    ledgerCycles: [],
    cycleDrafts: [],
    capabilityProfiles: {},
    stewardCandidates: [],
    changes: {},
    ledger: {},
    invariants: {},
    consequences: [],
    continuity: emptyContinuity(),
  };
}

export function applyJudgmentCycle(state: RAState, cycle: JudgmentCycle): RAState {
  const ledgerCycles = appendLedgerCycle(state.ledgerCycles, cycle);
  const all = allCyclesForAnalytics(ledgerCycles, state.cycleDrafts);
  const capabilityProfiles = inferAllCapabilityProfiles(all);
  return { ...state, ledgerCycles, capabilityProfiles };
}

export function applyEvent(state: RAState, ev: JPSSContributionEventInput): RAState {
  const tagged = withEventTags(ev);
  const events = [...state.events, tagged];
  const assembled = advanceCycleFromEvent(state.cycleDrafts, state.ledgerCycles, tagged);
  const all = allCyclesForAnalytics(assembled.ledgerCycles, assembled.drafts);
  const capabilityProfiles = inferAllCapabilityProfiles(all);
  const { continuity, eventOrigins, stewardCandidates } = computeFullContinuity(
    events,
    state.continuity.drift,
    state.ledger,
  );
  return {
    ...state,
    events,
    ledgerCycles: assembled.ledgerCycles,
    cycleDrafts: assembled.drafts,
    capabilityProfiles,
    eventOrigins,
    stewardCandidates,
    continuity,
  };
}

function integrationOrigin(change: LineageChange): AccumulationOrigin {
  return change.originType ?? "SA";
}

export function registerChange(state: RAState, change: LineageChange): RAState {
  const ledgerEntry: LedgerEntry = {
    changeId: change.id,
    originType: change.originType ?? null,
    surpassmentEvidence: "",
    acceptanceEvidence: "",
    validationResult: "PENDING",
    driftSignals: null,
    finalStatus: change.status,
    notes: [],
  };
  const withChange: RAState = {
    ...state,
    changes: { ...state.changes, [change.id]: change },
    ledger: { ...state.ledger, [change.id]: ledgerEntry },
  };

  return applyEvent(withChange, {
    id: `INT_${change.id}`,
    actor: "SYSTEM",
    timestamp: change.acceptedAt ?? new Date().toISOString(),
    accumulationType: "A2",
    targetsLayer: "Governance",
    fromExposure: true,
    buildsOn: [change.id],
    origin: integrationOrigin(change),
    mode: "INTEGRATION",
  });
}

export function recordConsequence(
  state: RAState,
  changeId: string,
  metric: string,
  value: number,
  timestamp: string,
): RAState {
  const consequences = [...state.consequences, { changeId, metric, value, timestamp }];
  return { ...state, consequences };
}

export function runPostAcceptanceValidation(
  state: RAState,
  changeId: string,
  ctx: ValidationContext,
  baseline: number,
): RAState {
  const change = state.changes[changeId];
  if (!change) return state;
  const ledgerEntry = state.ledger[changeId];

  const validation = validateVAS1(ctx);
  const relevant = state.consequences.filter((c) => c.changeId === changeId);
  const drift = computeDriftSignals(relevant, baseline);

  let status = change.status;
  const notes = [...(ledgerEntry?.notes ?? [])];
  const originLabel = change.originType ?? "unknown";

  if (!validation.passed) {
    status = "REJECTED";
    notes.push(`VAS-1 failed (${originLabel}).`);
  } else if (drift.aggregatePSD >= 0.8) {
    status = "ROLLED_BACK";
    notes.push(`High post-surpassment drift (${originLabel}): rolled back.`);
  } else if (drift.aggregatePSD >= 0.6) {
    notes.push(`Critical drift (${originLabel}): flagged for review.`);
  } else if (drift.aggregatePSD < 0.3 && validation.passed) {
    status = "VALIDATED";
    notes.push(`Validated by reality and stable (${originLabel}).`);
  }

  const updatedChange: LineageChange = {
    ...change,
    status,
    validatedAt: validation.passed ? new Date().toISOString() : change.validatedAt,
  };

  const updatedLedger: LedgerEntry = {
    ...ledgerEntry,
    originType: ledgerEntry.originType ?? change.originType ?? null,
    validationResult: validation.passed ? "PASSED" : "FAILED",
    driftSignals: drift,
    finalStatus: status,
    notes,
  };

  const afterLedger: RAState = {
    ...state,
    changes: { ...state.changes, [changeId]: updatedChange },
    ledger: { ...state.ledger, [changeId]: updatedLedger },
  };

  return applyEvent(afterLedger, {
    id: `VAL_${changeId}_${Date.now()}`,
    actor: "SYSTEM",
    timestamp: new Date().toISOString(),
    accumulationType: "A1",
    targetsLayer: "Meta",
    fromExposure: true,
    buildsOn: [changeId],
    origin: change.originType ?? "SA",
    mode: "VALIDATION",
  });
}
