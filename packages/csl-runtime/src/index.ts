import { createHash } from 'node:crypto';

export interface CslFieldInput {
  name: string;
  type: string;
  required?: boolean;
  description?: string;
}

export interface CslField {
  name: string;
  type: string;
  required: boolean;
  description?: string;
}

export interface CslDynamicsInput {
  generates?: readonly string[];
  resolves?: readonly string[];
}

export interface CslDynamics {
  generates: readonly string[];
  resolves: readonly string[];
}

export interface CslHorizonInput {
  promotesTo: string;
  expandsTo?: readonly string[];
}

export interface CslHorizon {
  promotesTo: string;
  expandsTo: readonly string[];
}

export interface CslTraceabilityRow {
  cisRequirement: string;
  referenceArchitecture: string;
  conformanceTest: string;
  evidenceArtifact: string;
  notes?: string;
}

export interface CslArtifactTypeInput {
  name: string;
  tier: number;
  kind: string;
  fields: readonly CslFieldInput[];
  dynamics: CslDynamicsInput;
  horizon: CslHorizonInput;
  traceability: readonly CslTraceabilityRow[];
}

export interface CslArtifactType {
  id: string;
  name: string;
  tier: number;
  kind: string;
  fields: readonly CslField[];
  dynamics: CslDynamics;
  horizon: CslHorizon;
  traceability: readonly CslTraceabilityRow[];
}

export interface CslValidationIssue {
  field: string;
  message: string;
}

export interface CslValidationResult {
  artifactId: string;
  valid: boolean;
  issues: readonly CslValidationIssue[];
}

export interface CslRegistrationResult {
  accepted: boolean;
  artifact: CslArtifactType;
  validation: CslValidationResult;
}

export interface CslRuntimeSnapshot {
  packageName: '@aaes-os/csl-runtime';
  version: 'csl-v1';
  totalArtifacts: number;
  acceptedArtifacts: number;
  rejectedArtifacts: number;
  lastArtifactId?: string;
}

const VERSION = 'csl-v1' as const;
const NAME_PATTERN = /^[A-Za-z][A-Za-z0-9_-]*$/;

export function normalizeCslArtifactType(input: CslArtifactTypeInput): CslArtifactType {
  const normalized = normalizeArtifactCore(input);
  return {
    ...normalized,
    id: buildCslArtifactId(normalized),
  };
}

export function buildCslArtifactId(artifact: Omit<CslArtifactType, 'id'> | CslArtifactTypeInput): string {
  const normalized = 'id' in artifact ? cloneArtifactBody(artifact) : normalizeArtifactCore(artifact);
  return createHash('sha256').update(stableStringify(normalized)).digest('hex');
}

export function validateCslArtifactType(artifact: CslArtifactTypeInput | CslArtifactType): CslValidationResult {
  const normalized = normalizeCslArtifactType(artifact);
  const issues: CslValidationIssue[] = [];

  if (!normalized.name) {
    issues.push({ field: 'name', message: 'artifact name is required' });
  } else if (!NAME_PATTERN.test(normalized.name)) {
    issues.push({ field: 'name', message: 'artifact name must start with a letter and contain only letters, numbers, underscores, or hyphens' });
  }
  if (!Number.isInteger(normalized.tier) || normalized.tier < 0) {
    issues.push({ field: 'tier', message: 'tier must be a non-negative integer' });
  }
  if (!normalized.kind) {
    issues.push({ field: 'kind', message: 'kind is required' });
  }
  if (normalized.fields.length === 0) {
    issues.push({ field: 'fields', message: 'at least one field is required' });
  }

  const fieldNames = new Set<string>();
  for (const [index, field] of normalized.fields.entries()) {
    if (!field.name) {
      issues.push({ field: `fields[${index}].name`, message: 'field name is required' });
    } else if (!NAME_PATTERN.test(field.name)) {
      issues.push({ field: `fields[${index}].name`, message: 'field name must start with a letter and contain only letters, numbers, underscores, or hyphens' });
    }
    if (fieldNames.has(field.name)) {
      issues.push({ field: `fields[${index}].name`, message: 'field names must be unique' });
    }
    fieldNames.add(field.name);
    if (!field.type) {
      issues.push({ field: `fields[${index}].type`, message: 'field type is required' });
    }
  }

  if (!normalized.horizon.promotesTo) {
    issues.push({ field: 'horizon.promotesTo', message: 'promotion target is required' });
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

  return { artifactId: normalized.id, valid: issues.length === 0, issues };
}

export class CslRuntime {
  private readonly artifacts: CslArtifactType[] = [];
  private accepted = 0;
  private rejected = 0;

  constructor(seed: readonly (CslArtifactTypeInput | CslArtifactType)[] = []) {
    for (const artifact of seed) {
      this.registerArtifact(artifact);
    }
  }

  registerArtifact(artifact: CslArtifactTypeInput | CslArtifactType): CslRegistrationResult {
    const normalized = normalizeCslArtifactType(artifact);
    const validation = validateCslArtifactType(normalized);
    if (!validation.valid) {
      this.rejected += 1;
      return { accepted: false, artifact: normalized, validation };
    }

    this.accepted += 1;
    this.artifacts.push(normalized);
    return { accepted: true, artifact: normalized, validation };
  }

  validateArtifact(artifact: CslArtifactTypeInput | CslArtifactType): CslValidationResult {
    return validateCslArtifactType(artifact);
  }

  listArtifacts(): CslArtifactType[] {
    return this.artifacts.map(cloneArtifact);
  }

  findArtifact(identifier: string): CslArtifactType | undefined {
    const needle = normalizeIdentifier(identifier);
    const artifact = this.artifacts.find((entry) => normalizeIdentifier(entry.id) === needle || normalizeIdentifier(entry.name) === needle);
    return artifact ? cloneArtifact(artifact) : undefined;
  }

  snapshot(): CslRuntimeSnapshot {
    return {
      packageName: '@aaes-os/csl-runtime',
      version: VERSION,
      totalArtifacts: this.artifacts.length + this.rejected,
      acceptedArtifacts: this.accepted,
      rejectedArtifacts: this.rejected,
      lastArtifactId: this.artifacts[this.artifacts.length - 1]?.id,
    };
  }
}

export function createCslRuntime(seed: readonly (CslArtifactTypeInput | CslArtifactType)[] = []): CslRuntime {
  return new CslRuntime(seed);
}

export function summarizeCslRuntime(runtime: CslRuntime = new CslRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} accepted ${snapshot.acceptedArtifacts} constitutional artifact schemas`;
}

function normalizeArtifactCore(input: CslArtifactTypeInput): Omit<CslArtifactType, 'id'> {
  return {
    name: normalizeText(input.name),
    tier: input.tier,
    kind: normalizeText(input.kind),
    fields: input.fields.map(normalizeField).sort((left, right) => left.name.localeCompare(right.name)),
    dynamics: normalizeDynamics(input.dynamics),
    horizon: normalizeHorizon(input.horizon),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
}

function normalizeField(field: CslFieldInput): CslField {
  return {
    name: normalizeText(field.name),
    type: normalizeText(field.type),
    required: field.required ?? false,
    description: field.description ? normalizeText(field.description) : undefined,
  };
}

function normalizeDynamics(dynamics: CslDynamicsInput): CslDynamics {
  return {
    generates: normalizeTextList(dynamics.generates ?? []),
    resolves: normalizeTextList(dynamics.resolves ?? []),
  };
}

function normalizeHorizon(horizon: CslHorizonInput): CslHorizon {
  return {
    promotesTo: normalizeText(horizon.promotesTo),
    expandsTo: normalizeTextList(horizon.expandsTo ?? []),
  };
}

function normalizeTraceabilityRow(row: CslTraceabilityRow): CslTraceabilityRow {
  return {
    cisRequirement: normalizeText(row.cisRequirement),
    referenceArchitecture: normalizeText(row.referenceArchitecture),
    conformanceTest: normalizeText(row.conformanceTest),
    evidenceArtifact: normalizeText(row.evidenceArtifact),
    notes: row.notes ? normalizeText(row.notes) : undefined,
  };
}

function cloneArtifact(artifact: CslArtifactType): CslArtifactType {
  return {
    ...artifact,
    fields: artifact.fields.map(normalizeField),
    dynamics: normalizeDynamics(artifact.dynamics),
    horizon: normalizeHorizon(artifact.horizon),
    traceability: artifact.traceability.map(normalizeTraceabilityRow),
  };
}

function cloneArtifactBody(artifact: CslArtifactTypeInput | CslArtifactType): Omit<CslArtifactType, 'id'> {
  return normalizeArtifactCore(artifact);
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

function normalizeTextList(values: readonly string[]): readonly string[] {
  return values.map(normalizeText).filter(Boolean).sort((left, right) => left.localeCompare(right));
}

function normalizeIdentifier(value: string): string {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '');
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
