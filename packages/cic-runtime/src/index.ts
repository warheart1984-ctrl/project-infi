import { createHash } from 'node:crypto';

export type CicPrimitive = string | number | boolean | null;
export type CicValue = CicPrimitive | readonly CicValue[] | { readonly [key: string]: CicValue };
export type CicOperator = '=' | '!=' | '<' | '<=' | '>' | '>=';

export interface CicConditionInput {
  path: string;
  operator: CicOperator;
  value: CicValue;
}

export interface CicCondition extends CicConditionInput {
  path: string;
}

export interface CicBindingInput {
  artifactField: string;
  semanticConcept: string;
}

export interface CicBinding extends CicBindingInput {
  artifactField: string;
  semanticConcept: string;
}

export interface CicTraceabilityRow {
  cisRequirement: string;
  referenceArchitecture: string;
  conformanceTest: string;
  evidenceArtifact: string;
  notes?: string;
}

export interface CicRuleInput {
  id: string;
  conditions: readonly CicConditionInput[];
  conclusion: string;
  bindings: readonly CicBindingInput[];
  traceability: readonly CicTraceabilityRow[];
}

export interface CicRule {
  id: string;
  hash: string;
  conditions: readonly CicCondition[];
  conclusion: string;
  bindings: readonly CicBinding[];
  traceability: readonly CicTraceabilityRow[];
}

export interface CicValidationIssue {
  field: string;
  message: string;
}

export interface CicValidationResult {
  ruleId: string;
  valid: boolean;
  issues: readonly CicValidationIssue[];
}

export interface CicRegistrationResult {
  accepted: boolean;
  rule: CicRule;
  validation: CicValidationResult;
}

export interface CicConditionEvaluation {
  path: string;
  operator: CicOperator;
  expected: CicValue;
  actual: CicValue | undefined;
  matched: boolean;
}

export interface CicRuleEvaluation {
  ruleId: string;
  matched: boolean;
  conclusion?: string;
  bindings: readonly CicBinding[];
  conditions: readonly CicConditionEvaluation[];
  traceability: readonly CicTraceabilityRow[];
}

export interface CicSemanticGraph {
  id: string;
  inputHash: string;
  matchedRuleIds: readonly string[];
  conclusions: readonly string[];
  bindings: readonly CicBinding[];
  evaluations: readonly CicRuleEvaluation[];
}

export interface CicRuntimeSnapshot {
  packageName: '@aaes-os/cic-runtime';
  version: 'cic-v1';
  totalRules: number;
  acceptedRules: number;
  rejectedRules: number;
  totalInferences: number;
  lastRuleId?: string;
  lastGraphId?: string;
}

const VERSION = 'cic-v1' as const;
const VALID_OPERATORS: readonly CicOperator[] = ['=', '!=', '<', '<=', '>', '>='];

export function normalizeCicRule(input: CicRuleInput): CicRule {
  const normalized = normalizeRuleCore(input);
  return {
    ...normalized,
    hash: buildCicRuleHash(normalized),
  };
}

export function buildCicRuleHash(rule: Omit<CicRule, 'hash'> | CicRuleInput): string {
  const normalized = 'hash' in rule ? cloneRuleBody(rule) : normalizeRuleCore(rule);
  return createHash('sha256').update(stableStringify(normalized)).digest('hex');
}

export function validateCicRule(rule: CicRuleInput | CicRule): CicValidationResult {
  const normalized = normalizeCicRule(rule);
  const issues: CicValidationIssue[] = [];

  if (!normalized.id) {
    issues.push({ field: 'id', message: 'rule id is required' });
  }
  if (normalized.conditions.length === 0) {
    issues.push({ field: 'conditions', message: 'at least one condition is required' });
  }
  for (const [index, condition] of normalized.conditions.entries()) {
    if (!condition.path) {
      issues.push({ field: `conditions[${index}].path`, message: 'condition path is required' });
    }
    if (!VALID_OPERATORS.includes(condition.operator)) {
      issues.push({ field: `conditions[${index}].operator`, message: 'condition operator is invalid' });
    }
  }
  if (!normalized.conclusion) {
    issues.push({ field: 'conclusion', message: 'conclusion is required' });
  }
  for (const [index, binding] of normalized.bindings.entries()) {
    if (!binding.artifactField) {
      issues.push({ field: `bindings[${index}].artifactField`, message: 'artifact field is required' });
    }
    if (!binding.semanticConcept) {
      issues.push({ field: `bindings[${index}].semanticConcept`, message: 'semantic concept is required' });
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

  return { ruleId: normalized.id, valid: issues.length === 0, issues };
}

export function evaluateCicRule(rule: CicRuleInput | CicRule, input: Record<string, CicValue>): CicRuleEvaluation {
  const normalized = normalizeCicRule(rule);
  const conditions = normalized.conditions.map((condition) => evaluateCondition(condition, input));
  const matched = conditions.every((condition) => condition.matched);

  return {
    ruleId: normalized.id,
    matched,
    conclusion: matched ? normalized.conclusion : undefined,
    bindings: matched ? normalized.bindings.map(cloneBinding) : [],
    conditions,
    traceability: normalized.traceability.map(normalizeTraceabilityRow),
  };
}

export class CicRuntime {
  private readonly rules: CicRule[] = [];
  private accepted = 0;
  private rejected = 0;
  private inferences = 0;
  private lastGraphId: string | undefined;

  constructor(seed: readonly (CicRuleInput | CicRule)[] = []) {
    for (const rule of seed) {
      this.registerRule(rule);
    }
  }

  registerRule(rule: CicRuleInput | CicRule): CicRegistrationResult {
    const normalized = normalizeCicRule(rule);
    const validation = validateCicRule(normalized);
    if (!validation.valid) {
      this.rejected += 1;
      return { accepted: false, rule: normalized, validation };
    }

    this.accepted += 1;
    this.rules.push(normalized);
    return { accepted: true, rule: normalized, validation };
  }

  infer(input: Record<string, CicValue>): CicSemanticGraph {
    const normalizedInput = normalizeContext(input);
    const evaluations = this.rules.map((rule) => evaluateCicRule(rule, normalizedInput));
    const matched = evaluations.filter((evaluation) => evaluation.matched);
    const graphBody = {
      inputHash: createHash('sha256').update(stableStringify(normalizedInput)).digest('hex'),
      matchedRuleIds: matched.map((evaluation) => evaluation.ruleId),
      conclusions: matched.map((evaluation) => evaluation.conclusion).filter(isString),
      bindings: matched.flatMap((evaluation) => evaluation.bindings).map(cloneBinding),
      evaluations,
    };
    const graphId = createHash('sha256').update(stableStringify(graphBody)).digest('hex');

    this.inferences += 1;
    this.lastGraphId = graphId;

    return {
      id: graphId,
      ...graphBody,
    };
  }

  validateRule(rule: CicRuleInput | CicRule): CicValidationResult {
    return validateCicRule(rule);
  }

  listRules(): CicRule[] {
    return this.rules.map(cloneRule);
  }

  snapshot(): CicRuntimeSnapshot {
    return {
      packageName: '@aaes-os/cic-runtime',
      version: VERSION,
      totalRules: this.rules.length + this.rejected,
      acceptedRules: this.accepted,
      rejectedRules: this.rejected,
      totalInferences: this.inferences,
      lastRuleId: this.rules[this.rules.length - 1]?.id,
      lastGraphId: this.lastGraphId,
    };
  }
}

export function createCicRuntime(seed: readonly (CicRuleInput | CicRule)[] = []): CicRuntime {
  return new CicRuntime(seed);
}

export function summarizeCicRuntime(runtime: CicRuntime = new CicRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} accepted ${snapshot.acceptedRules} constitutional inference rules`;
}

function evaluateCondition(condition: CicCondition, input: Record<string, CicValue>): CicConditionEvaluation {
  const actual = getPath(input, condition.path);
  const matched = compareValues(actual, condition.operator, condition.value);
  return {
    path: condition.path,
    operator: condition.operator,
    expected: condition.value,
    actual,
    matched,
  };
}

function compareValues(actual: CicValue | undefined, operator: CicOperator, expected: CicValue): boolean {
  if (operator === '=') {
    return stableStringify(actual) === stableStringify(expected);
  }
  if (operator === '!=') {
    return stableStringify(actual) !== stableStringify(expected);
  }
  if (typeof actual !== 'number' || typeof expected !== 'number') {
    return false;
  }
  if (operator === '<') return actual < expected;
  if (operator === '<=') return actual <= expected;
  if (operator === '>') return actual > expected;
  return actual >= expected;
}

function getPath(input: Record<string, CicValue>, path: string): CicValue | undefined {
  const parts = path.split('.').map(normalizeText).filter(Boolean);
  let current: CicValue | undefined = input;
  for (const part of parts) {
    if (!current || typeof current !== 'object' || Array.isArray(current)) {
      return undefined;
    }
    current = (current as Record<string, CicValue>)[part];
  }
  return current;
}

function normalizeRuleCore(input: CicRuleInput): Omit<CicRule, 'hash'> {
  return {
    id: normalizeText(input.id),
    conditions: input.conditions.map(normalizeCondition),
    conclusion: normalizeText(input.conclusion),
    bindings: input.bindings.map(cloneBinding).sort((left, right) => left.artifactField.localeCompare(right.artifactField)),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
}

function normalizeCondition(condition: CicConditionInput): CicCondition {
  return {
    path: normalizeText(condition.path),
    operator: condition.operator,
    value: normalizeContextValue(condition.value),
  };
}

function cloneBinding(binding: CicBindingInput): CicBinding {
  return {
    artifactField: normalizeText(binding.artifactField),
    semanticConcept: normalizeText(binding.semanticConcept),
  };
}

function normalizeTraceabilityRow(row: CicTraceabilityRow): CicTraceabilityRow {
  return {
    cisRequirement: normalizeText(row.cisRequirement),
    referenceArchitecture: normalizeText(row.referenceArchitecture),
    conformanceTest: normalizeText(row.conformanceTest),
    evidenceArtifact: normalizeText(row.evidenceArtifact),
    notes: row.notes ? normalizeText(row.notes) : undefined,
  };
}

function cloneRule(rule: CicRule): CicRule {
  return {
    ...rule,
    conditions: rule.conditions.map(normalizeCondition),
    bindings: rule.bindings.map(cloneBinding),
    traceability: rule.traceability.map(normalizeTraceabilityRow),
  };
}

function cloneRuleBody(rule: CicRuleInput | CicRule): Omit<CicRule, 'hash'> {
  return normalizeRuleCore(rule);
}

function normalizeContext(context: Record<string, CicValue>): Record<string, CicValue> {
  const entries = Object.entries(context).map(([key, value]) => [normalizeText(key), normalizeContextValue(value)] as const);
  entries.sort(([left], [right]) => left.localeCompare(right));
  return Object.fromEntries(entries);
}

function normalizeContextValue(value: CicValue): CicValue {
  if (Array.isArray(value)) {
    return value.map((entry) => normalizeContextValue(entry));
  }
  if (value && typeof value === 'object') {
    return normalizeContext(value as Record<string, CicValue>);
  }
  if (typeof value === 'string') {
    return normalizeText(value);
  }
  return value;
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
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

function isString(value: string | undefined): value is string {
  return typeof value === 'string';
}
