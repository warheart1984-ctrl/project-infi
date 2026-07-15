import { createHash } from 'node:crypto';

export type CccReplayMode = 'historical' | 'counterfactual' | 'comparison';

export interface CccEvidenceRef {
  id: string;
  kind: string;
  uri?: string;
  hash?: string;
  signature?: string;
}

export interface CccReplayContractInput {
  mode: CccReplayMode;
  deterministic: boolean;
  ledgerReferences: readonly CccEvidenceRef[];
}

export interface CccReplayContract extends CccReplayContractInput {
  ledgerReferences: readonly CccEvidenceRef[];
}

export interface CccTimelineInput {
  events: readonly string[];
  states: readonly string[];
  transitions: readonly string[];
}

export interface CccTimeline extends CccTimelineInput {
  events: readonly string[];
  states: readonly string[];
  transitions: readonly string[];
}

export interface CccTraceabilityRow {
  cisRequirement: string;
  referenceArchitecture: string;
  conformanceTest: string;
  evidenceArtifact: string;
  notes?: string;
}

export interface CccContinuityInput {
  invariant: string;
  scope: string;
  replayContract: CccReplayContractInput;
  timeline: CccTimelineInput;
  traceability: readonly CccTraceabilityRow[];
}

export interface CccContinuity {
  id: string;
  invariant: string;
  scope: string;
  replayContract: CccReplayContract;
  timeline: CccTimeline;
  traceability: readonly CccTraceabilityRow[];
}

export interface CccValidationIssue {
  field: string;
  message: string;
}

export interface CccValidationResult {
  continuityId: string;
  valid: boolean;
  issues: readonly CccValidationIssue[];
}

export interface CccRegistrationResult {
  accepted: boolean;
  continuity: CccContinuity;
  validation: CccValidationResult;
}

export interface CccReplayResult {
  continuityId: string;
  replayId: string;
  mode: CccReplayMode;
  deterministic: boolean;
  accepted: boolean;
  validation: CccValidationResult;
  timelineHash: string;
  ledgerHash: string;
}

export interface CccRuntimeSnapshot {
  packageName: '@aaes-os/ccc-runtime';
  version: 'ccc-v1';
  totalContinuities: number;
  acceptedContinuities: number;
  rejectedContinuities: number;
  totalReplays: number;
  lastContinuityId?: string;
  lastReplayId?: string;
}

const VERSION = 'ccc-v1' as const;
const REPLAY_MODES: readonly CccReplayMode[] = ['historical', 'counterfactual', 'comparison'];

export function normalizeCccContinuity(input: CccContinuityInput): CccContinuity {
  const normalized = normalizeContinuityCore(input);
  return {
    ...normalized,
    id: buildCccContinuityId(normalized),
  };
}

export function buildCccContinuityId(continuity: Omit<CccContinuity, 'id'> | CccContinuityInput): string {
  const normalized = 'id' in continuity ? cloneContinuityBody(continuity) : normalizeContinuityCore(continuity);
  return createHash('sha256').update(stableStringify(normalized)).digest('hex');
}

export function validateCccContinuity(continuity: CccContinuityInput | CccContinuity): CccValidationResult {
  const normalized = normalizeCccContinuity(continuity);
  const issues: CccValidationIssue[] = [];

  if (!normalized.invariant) {
    issues.push({ field: 'invariant', message: 'invariant is required' });
  }
  if (!normalized.scope) {
    issues.push({ field: 'scope', message: 'scope is required' });
  }
  if (!REPLAY_MODES.includes(normalized.replayContract.mode)) {
    issues.push({ field: 'replayContract.mode', message: 'replay mode is invalid' });
  }
  if (normalized.replayContract.deterministic && normalized.replayContract.ledgerReferences.length === 0) {
    issues.push({ field: 'replayContract.ledgerReferences', message: 'deterministic replay requires at least one ledger reference' });
  }
  for (const [index, ref] of normalized.replayContract.ledgerReferences.entries()) {
    if (!ref.id) {
      issues.push({ field: `replayContract.ledgerReferences[${index}].id`, message: 'ledger reference id is required' });
    }
    if (!ref.kind) {
      issues.push({ field: `replayContract.ledgerReferences[${index}].kind`, message: 'ledger reference kind is required' });
    }
  }
  if (normalized.timeline.events.length === 0) {
    issues.push({ field: 'timeline.events', message: 'at least one timeline event is required' });
  }
  if (normalized.timeline.states.length === 0) {
    issues.push({ field: 'timeline.states', message: 'at least one timeline state is required' });
  }
  if (normalized.timeline.transitions.length > 0 && normalized.timeline.states.length < 2) {
    issues.push({ field: 'timeline.transitions', message: 'transitions require at least two states' });
  }
  if (normalized.traceability.length === 0) {
    issues.push({ field: 'traceability', message: 'at least one traceability row is required' });
  }
  for (const [index, row] of normalized.traceability.entries()) {
    if (!row.cisRequirement) {
      issues.push({ field: `traceability[${index}].cisRequirement`, message: 'cis requirement is required' });
    }
    if (!row.referenceArchitecture) {
      issues.push({ field: `traceability[${index}].referenceArchitecture`, message: 'reference architecture is required' });
    }
    if (!row.conformanceTest) {
      issues.push({ field: `traceability[${index}].conformanceTest`, message: 'conformance test is required' });
    }
    if (!row.evidenceArtifact) {
      issues.push({ field: `traceability[${index}].evidenceArtifact`, message: 'evidence artifact is required' });
    }
  }

  return { continuityId: normalized.id, valid: issues.length === 0, issues };
}

export function replayCccContinuity(continuity: CccContinuityInput | CccContinuity): CccReplayResult {
  const normalized = normalizeCccContinuity(continuity);
  const validation = validateCccContinuity(normalized);
  const timelineHash = createHash('sha256').update(stableStringify(normalized.timeline)).digest('hex');
  const ledgerHash = createHash('sha256').update(stableStringify(normalized.replayContract.ledgerReferences)).digest('hex');
  const replayBody = {
    continuityId: normalized.id,
    mode: normalized.replayContract.mode,
    deterministic: normalized.replayContract.deterministic,
    valid: validation.valid,
    timelineHash,
    ledgerHash,
  };

  return {
    continuityId: normalized.id,
    replayId: createHash('sha256').update(stableStringify(replayBody)).digest('hex'),
    mode: normalized.replayContract.mode,
    deterministic: normalized.replayContract.deterministic,
    accepted: validation.valid,
    validation,
    timelineHash,
    ledgerHash,
  };
}

export class CccRuntime {
  private readonly continuities: CccContinuity[] = [];
  private accepted = 0;
  private rejected = 0;
  private replays = 0;
  private lastReplayId: string | undefined;

  constructor(seed: readonly (CccContinuityInput | CccContinuity)[] = []) {
    for (const continuity of seed) {
      this.registerContinuity(continuity);
    }
  }

  registerContinuity(continuity: CccContinuityInput | CccContinuity): CccRegistrationResult {
    const normalized = normalizeCccContinuity(continuity);
    const validation = validateCccContinuity(normalized);
    if (!validation.valid) {
      this.rejected += 1;
      return { accepted: false, continuity: normalized, validation };
    }

    this.accepted += 1;
    this.continuities.push(normalized);
    return { accepted: true, continuity: normalized, validation };
  }

  replay(continuity: CccContinuityInput | CccContinuity): CccReplayResult {
    const result = replayCccContinuity(continuity);
    this.replays += 1;
    this.lastReplayId = result.replayId;
    return result;
  }

  validateContinuity(continuity: CccContinuityInput | CccContinuity): CccValidationResult {
    return validateCccContinuity(continuity);
  }

  listContinuities(): CccContinuity[] {
    return this.continuities.map(cloneContinuity);
  }

  snapshot(): CccRuntimeSnapshot {
    return {
      packageName: '@aaes-os/ccc-runtime',
      version: VERSION,
      totalContinuities: this.continuities.length + this.rejected,
      acceptedContinuities: this.accepted,
      rejectedContinuities: this.rejected,
      totalReplays: this.replays,
      lastContinuityId: this.continuities[this.continuities.length - 1]?.id,
      lastReplayId: this.lastReplayId,
    };
  }
}

export function createCccRuntime(seed: readonly (CccContinuityInput | CccContinuity)[] = []): CccRuntime {
  return new CccRuntime(seed);
}

export function summarizeCccRuntime(runtime: CccRuntime = new CccRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} accepted ${snapshot.acceptedContinuities} continuity contracts`;
}

function normalizeContinuityCore(input: CccContinuityInput): Omit<CccContinuity, 'id'> {
  return {
    invariant: normalizeText(input.invariant),
    scope: normalizeText(input.scope),
    replayContract: normalizeReplayContract(input.replayContract),
    timeline: normalizeTimeline(input.timeline),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
}

function normalizeReplayContract(contract: CccReplayContractInput): CccReplayContract {
  return {
    mode: contract.mode,
    deterministic: contract.deterministic,
    ledgerReferences: contract.ledgerReferences.map(normalizeEvidenceRef).sort((left, right) => left.id.localeCompare(right.id)),
  };
}

function normalizeTimeline(timeline: CccTimelineInput): CccTimeline {
  return {
    events: normalizeTextList(timeline.events),
    states: normalizeTextList(timeline.states),
    transitions: normalizeTextList(timeline.transitions),
  };
}

function normalizeEvidenceRef(ref: CccEvidenceRef): CccEvidenceRef {
  return {
    id: normalizeText(ref.id),
    kind: normalizeText(ref.kind),
    uri: ref.uri ? normalizeText(ref.uri) : undefined,
    hash: ref.hash ? normalizeText(ref.hash) : undefined,
    signature: ref.signature ? normalizeText(ref.signature) : undefined,
  };
}

function normalizeTraceabilityRow(row: CccTraceabilityRow): CccTraceabilityRow {
  return {
    cisRequirement: normalizeText(row.cisRequirement),
    referenceArchitecture: normalizeText(row.referenceArchitecture),
    conformanceTest: normalizeText(row.conformanceTest),
    evidenceArtifact: normalizeText(row.evidenceArtifact),
    notes: row.notes ? normalizeText(row.notes) : undefined,
  };
}

function cloneContinuity(continuity: CccContinuity): CccContinuity {
  return {
    ...continuity,
    replayContract: normalizeReplayContract(continuity.replayContract),
    timeline: normalizeTimeline(continuity.timeline),
    traceability: continuity.traceability.map(normalizeTraceabilityRow),
  };
}

function cloneContinuityBody(continuity: CccContinuityInput | CccContinuity): Omit<CccContinuity, 'id'> {
  return normalizeContinuityCore(continuity);
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

function normalizeTextList(values: readonly string[]): readonly string[] {
  return values.map(normalizeText).filter(Boolean);
}

function stableStringify(value: unknown): string {
  return JSON.stringify(stableValue(value));
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => stableValue(entry));
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => [key, stableValue(entry)] as const);
    return Object.fromEntries(entries);
  }
  return value;
}
