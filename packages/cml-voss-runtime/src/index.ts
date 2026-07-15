import { createHash } from 'node:crypto';

export type CmlVossFamilyKind = 'constraint-language' | 'verification-model' | 'binding-protocol';

export interface CmlVossTraceabilityRow {
  cisRequirement: string;
  referenceArchitecture: string;
  conformanceTest: string;
  evidenceArtifact: string;
  notes?: string;
}

export interface CmlVossFamilyInput {
  id: 'CML-2' | 'CVM-1' | 'The Voss Binding' | string;
  name: string;
  kind: CmlVossFamilyKind;
  purpose: string;
  canonicalSource: string;
  aliases: readonly string[];
  traceability: readonly CmlVossTraceabilityRow[];
}

export interface CmlVossFamily extends CmlVossFamilyInput {
  hash: string;
  aliases: readonly string[];
  traceability: readonly CmlVossTraceabilityRow[];
}

export interface CmlVossBindingInput {
  id: string;
  fromFamily: string;
  toFamily: string;
  relation: string;
  invariant: string;
  traceability: readonly CmlVossTraceabilityRow[];
}

export interface CmlVossBinding extends CmlVossBindingInput {
  hash: string;
  traceability: readonly CmlVossTraceabilityRow[];
}

export interface CmlVossValidationIssue {
  field: string;
  message: string;
}

export interface CmlVossValidationResult {
  subjectId: string;
  valid: boolean;
  issues: readonly CmlVossValidationIssue[];
}

export interface CmlVossRuntimeSnapshot {
  packageName: '@aaes-os/cml-voss-runtime';
  version: 'cml-voss-v1';
  totalFamilies: number;
  totalBindings: number;
  rejectedSubjects: number;
  familyIds: readonly string[];
  bindingIds: readonly string[];
}

const VERSION = 'cml-voss-v1' as const;

const DEFAULT_TRACEABILITY: readonly CmlVossTraceabilityRow[] = [
  {
    cisRequirement: 'CML-VOSS-LIVE-001',
    referenceArchitecture: 'ULX Language Registry / CML-2 CVM-1 The Voss Binding',
    conformanceTest: 'packages/cml-voss-runtime/src/index.test.ts',
    evidenceArtifact: 'cml-voss-runtime',
  },
];

export const DEFAULT_CML_VOSS_FAMILIES: readonly CmlVossFamilyInput[] = [
  {
    id: 'CML-2',
    name: 'CML-2',
    kind: 'constraint-language',
    purpose: 'Document-forward constitutional meaning language family promoted to a live governed corpus surface.',
    canonicalSource: 'docs/specifications/README.md',
    aliases: ['cml2', 'constitutional meaning language 2'],
    traceability: DEFAULT_TRACEABILITY,
  },
  {
    id: 'CVM-1',
    name: 'CVM-1',
    kind: 'verification-model',
    purpose: 'Document-forward constitutional verification model family promoted to a live governed corpus surface.',
    canonicalSource: 'docs/specifications/README.md',
    aliases: ['cvm1', 'constitutional verification model 1'],
    traceability: DEFAULT_TRACEABILITY,
  },
  {
    id: 'The Voss Binding',
    name: 'The Voss Binding',
    kind: 'binding-protocol',
    purpose: 'Named corpus binding family promoted to a live governed bridge between CML and CVM surfaces.',
    canonicalSource: 'docs/specifications/README.md',
    aliases: ['voss binding', 'voss'],
    traceability: DEFAULT_TRACEABILITY,
  },
];

export function normalizeCmlVossFamily(input: CmlVossFamilyInput): CmlVossFamily {
  const body = {
    id: normalizeText(input.id),
    name: normalizeText(input.name),
    kind: input.kind,
    purpose: normalizeText(input.purpose),
    canonicalSource: normalizeText(input.canonicalSource),
    aliases: normalizeTextList(input.aliases),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
  return { hash: hash(body), ...body };
}

export function normalizeCmlVossBinding(input: CmlVossBindingInput): CmlVossBinding {
  const body = {
    id: normalizeText(input.id),
    fromFamily: normalizeText(input.fromFamily),
    toFamily: normalizeText(input.toFamily),
    relation: normalizeText(input.relation),
    invariant: normalizeText(input.invariant),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
  return { hash: hash(body), ...body };
}

export function validateCmlVossFamily(input: CmlVossFamilyInput | CmlVossFamily): CmlVossValidationResult {
  const family = normalizeCmlVossFamily(input);
  const issues: CmlVossValidationIssue[] = [];
  requireText(issues, 'id', family.id);
  requireText(issues, 'name', family.name);
  requireText(issues, 'purpose', family.purpose);
  requireText(issues, 'canonicalSource', family.canonicalSource);
  requireTraceability(issues, family.traceability);
  return { subjectId: family.id, valid: issues.length === 0, issues };
}

export function validateCmlVossBinding(input: CmlVossBindingInput | CmlVossBinding): CmlVossValidationResult {
  const binding = normalizeCmlVossBinding(input);
  const issues: CmlVossValidationIssue[] = [];
  requireText(issues, 'id', binding.id);
  requireText(issues, 'fromFamily', binding.fromFamily);
  requireText(issues, 'toFamily', binding.toFamily);
  requireText(issues, 'relation', binding.relation);
  requireText(issues, 'invariant', binding.invariant);
  requireTraceability(issues, binding.traceability);
  return { subjectId: binding.id, valid: issues.length === 0, issues };
}

export class CmlVossRuntime {
  private readonly families: CmlVossFamily[] = [];
  private readonly bindings: CmlVossBinding[] = [];
  private rejected = 0;

  constructor(seed: readonly CmlVossFamilyInput[] = DEFAULT_CML_VOSS_FAMILIES) {
    for (const family of seed) {
      this.registerFamily(family);
    }
    this.registerBinding({
      id: 'voss-cml2-cvm1',
      fromFamily: 'CML-2',
      toFamily: 'CVM-1',
      relation: 'binds-meaning-to-verification',
      invariant: 'The Voss Binding keeps CML-2 meaning claims traceable to CVM-1 verification claims.',
      traceability: DEFAULT_TRACEABILITY,
    });
  }

  registerFamily(input: CmlVossFamilyInput | CmlVossFamily): CmlVossValidationResult {
    const family = normalizeCmlVossFamily(input);
    const validation = validateCmlVossFamily(family);
    if (!validation.valid) {
      this.rejected += 1;
      return validation;
    }
    this.families.push(family);
    return validation;
  }

  registerBinding(input: CmlVossBindingInput | CmlVossBinding): CmlVossValidationResult {
    const binding = normalizeCmlVossBinding(input);
    const validation = validateCmlVossBinding(binding);
    if (!validation.valid) {
      this.rejected += 1;
      return validation;
    }
    this.bindings.push(binding);
    return validation;
  }

  findFamily(identifier: string): CmlVossFamily | undefined {
    const needle = normalizeIdentifier(identifier);
    const family = this.families.find((entry) => {
      if (normalizeIdentifier(entry.id) === needle || normalizeIdentifier(entry.name) === needle) {
        return true;
      }
      return entry.aliases.some((alias) => normalizeIdentifier(alias) === needle);
    });
    return family ? cloneFamily(family) : undefined;
  }

  listFamilies(): CmlVossFamily[] {
    return this.families.map(cloneFamily);
  }

  listBindings(): CmlVossBinding[] {
    return this.bindings.map(cloneBinding);
  }

  snapshot(): CmlVossRuntimeSnapshot {
    return {
      packageName: '@aaes-os/cml-voss-runtime',
      version: VERSION,
      totalFamilies: this.families.length,
      totalBindings: this.bindings.length,
      rejectedSubjects: this.rejected,
      familyIds: this.families.map((family) => family.id),
      bindingIds: this.bindings.map((binding) => binding.id),
    };
  }
}

export function createCmlVossRuntime(seed: readonly CmlVossFamilyInput[] = DEFAULT_CML_VOSS_FAMILIES): CmlVossRuntime {
  return new CmlVossRuntime(seed);
}

export function summarizeCmlVossRuntime(runtime: CmlVossRuntime = new CmlVossRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} exposes ${snapshot.totalFamilies} live corpus families and ${snapshot.totalBindings} bindings`;
}

function normalizeTraceabilityRow(row: CmlVossTraceabilityRow): CmlVossTraceabilityRow {
  return {
    cisRequirement: normalizeText(row.cisRequirement),
    referenceArchitecture: normalizeText(row.referenceArchitecture),
    conformanceTest: normalizeText(row.conformanceTest),
    evidenceArtifact: normalizeText(row.evidenceArtifact),
    notes: row.notes ? normalizeText(row.notes) : undefined,
  };
}

function cloneFamily(family: CmlVossFamily): CmlVossFamily {
  return normalizeCmlVossFamily(family);
}

function cloneBinding(binding: CmlVossBinding): CmlVossBinding {
  return normalizeCmlVossBinding(binding);
}

function requireTraceability(issues: CmlVossValidationIssue[], traceability: readonly CmlVossTraceabilityRow[]): void {
  if (traceability.length === 0) {
    issues.push({ field: 'traceability', message: 'at least one traceability row is required' });
  }
  for (const [index, row] of traceability.entries()) {
    requireText(issues, `traceability[${index}].cisRequirement`, row.cisRequirement);
    requireText(issues, `traceability[${index}].referenceArchitecture`, row.referenceArchitecture);
    requireText(issues, `traceability[${index}].conformanceTest`, row.conformanceTest);
    requireText(issues, `traceability[${index}].evidenceArtifact`, row.evidenceArtifact);
  }
}

function requireText(issues: CmlVossValidationIssue[], field: string, value: string): void {
  if (!value) {
    issues.push({ field, message: `${field} is required` });
  }
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

function hash(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(stableValue(value))).digest('hex');
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
