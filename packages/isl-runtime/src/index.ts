import { createHash } from 'node:crypto';

export type IslPrimitive = string | number | boolean | null;

export type IslContextValue =
  | IslPrimitive
  | readonly IslContextValue[]
  | { readonly [key: string]: IslContextValue };

export interface IslEvidenceRef {
  id: string;
  kind: string;
  uri?: string;
  hash?: string;
  signature?: string;
}

export interface IslAuthorityRef {
  actor: string;
  roles: readonly string[];
  permissions: readonly string[];
}

export interface IslTraceabilityRow {
  cisRequirement: string;
  referenceArchitecture: string;
  conformanceTest: string;
  evidenceArtifact: string;
  notes?: string;
}

export interface IslIntentInput {
  actor: string;
  target: string;
  purpose: string;
  context?: Record<string, IslContextValue>;
  evidence: readonly IslEvidenceRef[];
  authority: IslAuthorityRef;
  traceability: readonly IslTraceabilityRow[];
}

export interface IslIntent extends Required<Omit<IslIntentInput, 'context'>> {
  context: Record<string, IslContextValue>;
  id: string;
}

export interface IslValidationIssue {
  field: string;
  message: string;
}

export interface IslValidationResult {
  intentId: string;
  valid: boolean;
  issues: IslValidationIssue[];
}

export interface IslSubmissionResult {
  accepted: boolean;
  intent: IslIntent;
  validation: IslValidationResult;
}

export interface IslRuntimeSnapshot {
  packageName: '@aaes-os/isl-runtime';
  version: 'sock-v1';
  totalIntents: number;
  acceptedIntents: number;
  rejectedIntents: number;
  lastIntentId?: string;
}

const VERSION = 'sock-v1' as const;

export function normalizeIslIntent(input: IslIntentInput): IslIntent {
  const normalized = normalizeIntentCore(input);

  return {
    ...normalized,
    id: buildIslIntentId(normalized),
  };
}

export function buildIslIntentId(intent: Omit<IslIntent, 'id'> | IslIntentInput): string {
  const normalized = 'id' in intent ? cloneIntentBody(intent) : normalizeIntentCore(intent);
  return createHash('sha256').update(stableStringify(normalized)).digest('hex');
}

export function validateIslIntent(intent: IslIntentInput | IslIntent): IslValidationResult {
  const normalized = normalizeIslIntent(intent);
  const issues: IslValidationIssue[] = [];

  if (!normalized.actor) {
    issues.push({ field: 'actor', message: 'actor is required' });
  }
  if (!normalized.target) {
    issues.push({ field: 'target', message: 'target is required' });
  }
  if (!normalized.purpose) {
    issues.push({ field: 'purpose', message: 'purpose is required' });
  }
  if (normalized.evidence.length === 0) {
    issues.push({ field: 'evidence', message: 'at least one evidence reference is required' });
  }
  for (const [index, ref] of normalized.evidence.entries()) {
    if (!ref.id) {
      issues.push({ field: `evidence[${index}].id`, message: 'evidence id is required' });
    }
    if (!ref.kind) {
      issues.push({ field: `evidence[${index}].kind`, message: 'evidence kind is required' });
    }
  }
  if (!normalized.authority.actor) {
    issues.push({ field: 'authority.actor', message: 'authority actor is required' });
  }
  if (normalized.authority.roles.length === 0) {
    issues.push({ field: 'authority.roles', message: 'at least one authority role is required' });
  }
  for (const [index, role] of normalized.authority.roles.entries()) {
    if (!role) {
      issues.push({ field: `authority.roles[${index}]`, message: 'authority role is required' });
    }
  }
  for (const [index, permission] of normalized.authority.permissions.entries()) {
    if (!permission) {
      issues.push({ field: `authority.permissions[${index}]`, message: 'authority permission is required' });
    }
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

  return { intentId: normalized.id, valid: issues.length === 0, issues };
}

export class IslRuntime {
  private readonly intents: IslIntent[] = [];
  private accepted = 0;
  private rejected = 0;

  constructor(seed: readonly (IslIntentInput | IslIntent)[] = []) {
    for (const intent of seed) {
      this.submitIntent(intent);
    }
  }

  submitIntent(intent: IslIntentInput | IslIntent): IslSubmissionResult {
    const normalized = normalizeIslIntent(intent);
    const validation = validateIslIntent(normalized);
    if (!validation.valid) {
      this.rejected += 1;
      return { accepted: false, intent: normalized, validation };
    }

    this.accepted += 1;
    this.intents.push(normalized);
    return { accepted: true, intent: normalized, validation };
  }

  validateIntent(intent: IslIntentInput | IslIntent): IslValidationResult {
    return validateIslIntent(intent);
  }

  listIntents(): IslIntent[] {
    return this.intents.map(cloneIntent);
  }

  findIntent(intentId: string): IslIntent | undefined {
    return this.intents.find((intent) => intent.id === intentId);
  }

  snapshot(): IslRuntimeSnapshot {
    return {
      packageName: '@aaes-os/isl-runtime',
      version: VERSION,
      totalIntents: this.intents.length + this.rejected,
      acceptedIntents: this.accepted,
      rejectedIntents: this.rejected,
      lastIntentId: this.intents[this.intents.length - 1]?.id,
    };
  }
}

export function createIslRuntime(seed: readonly (IslIntentInput | IslIntent)[] = []): IslRuntime {
  return new IslRuntime(seed);
}

export function summarizeIslRuntime(runtime: IslRuntime = new IslRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} accepted ${snapshot.acceptedIntents} governed intents`;
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

function normalizeAuthorityRef(authority: IslAuthorityRef): IslAuthorityRef {
  return {
    actor: normalizeText(authority.actor),
    roles: authority.roles.map(normalizeText),
    permissions: authority.permissions.map(normalizeText),
  };
}

function normalizeEvidenceRef(ref: IslEvidenceRef): IslEvidenceRef {
  return {
    id: normalizeText(ref.id),
    kind: normalizeText(ref.kind),
    uri: ref.uri ? normalizeText(ref.uri) : undefined,
    hash: ref.hash ? normalizeText(ref.hash) : undefined,
    signature: ref.signature ? normalizeText(ref.signature) : undefined,
  };
}

function normalizeTraceabilityRow(row: IslTraceabilityRow): IslTraceabilityRow {
  return {
    cisRequirement: normalizeText(row.cisRequirement),
    referenceArchitecture: normalizeText(row.referenceArchitecture),
    conformanceTest: normalizeText(row.conformanceTest),
    evidenceArtifact: normalizeText(row.evidenceArtifact),
    notes: row.notes ? normalizeText(row.notes) : undefined,
  };
}

function normalizeContext(context: Record<string, IslContextValue>): Record<string, IslContextValue> {
  const entries = Object.entries(context).map(([key, value]) => [normalizeText(key), normalizeContextValue(value)] as const);
  entries.sort(([left], [right]) => left.localeCompare(right));
  return Object.fromEntries(entries);
}

function normalizeContextValue(value: IslContextValue): IslContextValue {
  if (Array.isArray(value)) {
    return value.map((entry) => normalizeContextValue(entry));
  }
  if (value && typeof value === 'object') {
    return normalizeContext(value as Record<string, IslContextValue>);
  }
  if (typeof value === 'string') {
    return normalizeText(value);
  }
  return value;
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

function cloneIntent(intent: IslIntent): IslIntent {
  return {
    ...intent,
    context: normalizeContext(intent.context),
    evidence: intent.evidence.map(normalizeEvidenceRef),
    authority: normalizeAuthorityRef(intent.authority),
    traceability: intent.traceability.map(normalizeTraceabilityRow),
  };
}

function normalizeIntentCore(input: IslIntentInput): Omit<IslIntent, 'id'> {
  return {
    actor: normalizeText(input.actor),
    target: normalizeText(input.target),
    purpose: normalizeText(input.purpose),
    context: normalizeContext(input.context ?? {}),
    evidence: input.evidence.map(normalizeEvidenceRef),
    authority: normalizeAuthorityRef(input.authority),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
}

function cloneIntentBody(intent: IslIntentInput | IslIntent): Omit<IslIntent, 'id'> {
  return {
    actor: normalizeText(intent.actor),
    target: normalizeText(intent.target),
    purpose: normalizeText(intent.purpose),
    context: normalizeContext(intent.context ?? {}),
    evidence: intent.evidence.map(normalizeEvidenceRef),
    authority: normalizeAuthorityRef(intent.authority),
    traceability: intent.traceability.map(normalizeTraceabilityRow),
  };
}
