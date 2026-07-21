import { createHash } from 'node:crypto';

export interface CoeEvidenceRef {
  id: string;
  kind: string;
  uri?: string;
  hash?: string;
  signature?: string;
}

export interface CoeAuthorityRef {
  actor: string;
  roles: readonly string[];
  permissions: readonly string[];
}

export interface CoeTraceabilityRow {
  cisRequirement: string;
  referenceArchitecture: string;
  conformanceTest: string;
  evidenceArtifact: string;
  notes?: string;
}

export interface CoeRouteInput {
  intent: string;
  agent: string;
  policy: string;
  decision: string;
  pipeline: readonly string[];
  constraints?: readonly string[];
  traceability: readonly CoeTraceabilityRow[];
}

export interface CoeRoute extends Required<Omit<CoeRouteInput, 'constraints'>> {
  id: string;
  constraints: readonly string[];
}

export interface CoeScheduleInput {
  workflow: string;
  triggers: readonly string[];
  constraints: readonly string[];
  traceability: readonly CoeTraceabilityRow[];
}

export interface CoeSchedule extends CoeScheduleInput {
  id: string;
}

export interface CoePromotionWorkflowInput {
  fromType: string;
  toType: string;
  evidence: readonly CoeEvidenceRef[];
  authority: CoeAuthorityRef;
  traceability: readonly CoeTraceabilityRow[];
}

export interface CoePromotionWorkflow extends CoePromotionWorkflowInput {
  id: string;
}

export interface CoeValidationIssue {
  field: string;
  message: string;
}

export interface CoeValidationResult {
  subjectId: string;
  valid: boolean;
  issues: readonly CoeValidationIssue[];
}

export interface CoeExecutionReceipt {
  id: string;
  kind: 'route' | 'schedule' | 'promotion';
  subjectId: string;
  accepted: boolean;
  validation: CoeValidationResult;
  evidenceHash: string;
  traceabilityHash: string;
}

export interface CoeRuntimeSnapshot {
  packageName: '@aaes-os/coe-runtime';
  version: 'coe-v1';
  acceptedRoutes: number;
  acceptedSchedules: number;
  acceptedPromotions: number;
  rejectedSubjects: number;
  emittedReceipts: number;
  lastReceiptId?: string;
}

const VERSION = 'coe-v1' as const;

export function normalizeCoeRoute(input: CoeRouteInput): CoeRoute {
  const body = {
    intent: normalizeText(input.intent),
    agent: normalizeText(input.agent),
    policy: normalizeText(input.policy),
    decision: normalizeText(input.decision),
    pipeline: normalizeTextList(input.pipeline),
    constraints: normalizeTextList(input.constraints ?? []),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
  return { id: hash(body), ...body };
}

export function normalizeCoeSchedule(input: CoeScheduleInput): CoeSchedule {
  const body = {
    workflow: normalizeText(input.workflow),
    triggers: normalizeTextList(input.triggers),
    constraints: normalizeTextList(input.constraints),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
  return { id: hash(body), ...body };
}

export function normalizeCoePromotionWorkflow(input: CoePromotionWorkflowInput): CoePromotionWorkflow {
  const body = {
    fromType: normalizeText(input.fromType),
    toType: normalizeText(input.toType),
    evidence: input.evidence.map(normalizeEvidenceRef).sort((left, right) => left.id.localeCompare(right.id)),
    authority: normalizeAuthorityRef(input.authority),
    traceability: input.traceability.map(normalizeTraceabilityRow),
  };
  return { id: hash(body), ...body };
}

export function validateCoeRoute(route: CoeRouteInput | CoeRoute): CoeValidationResult {
  const normalized = normalizeCoeRoute(route);
  const issues: CoeValidationIssue[] = [];
  requireText(issues, 'intent', normalized.intent);
  requireText(issues, 'agent', normalized.agent);
  requireText(issues, 'policy', normalized.policy);
  requireText(issues, 'decision', normalized.decision);
  requireList(issues, 'pipeline', normalized.pipeline);
  validateTraceability(issues, normalized.traceability);
  return { subjectId: normalized.id, valid: issues.length === 0, issues };
}

export function validateCoeSchedule(schedule: CoeScheduleInput | CoeSchedule): CoeValidationResult {
  const normalized = normalizeCoeSchedule(schedule);
  const issues: CoeValidationIssue[] = [];
  requireText(issues, 'workflow', normalized.workflow);
  requireList(issues, 'triggers', normalized.triggers);
  requireList(issues, 'constraints', normalized.constraints);
  validateTraceability(issues, normalized.traceability);
  return { subjectId: normalized.id, valid: issues.length === 0, issues };
}

export function validateCoePromotionWorkflow(workflow: CoePromotionWorkflowInput | CoePromotionWorkflow): CoeValidationResult {
  const normalized = normalizeCoePromotionWorkflow(workflow);
  const issues: CoeValidationIssue[] = [];
  requireText(issues, 'fromType', normalized.fromType);
  requireText(issues, 'toType', normalized.toType);
  requireList(issues, 'evidence', normalized.evidence.map((ref) => ref.id));
  requireText(issues, 'authority.actor', normalized.authority.actor);
  requireList(issues, 'authority.roles', normalized.authority.roles);
  validateTraceability(issues, normalized.traceability);
  return { subjectId: normalized.id, valid: issues.length === 0, issues };
}

export class CoeRuntime {
  private readonly routes: CoeRoute[] = [];
  private readonly schedules: CoeSchedule[] = [];
  private readonly promotions: CoePromotionWorkflow[] = [];
  private readonly receipts: CoeExecutionReceipt[] = [];
  private rejected = 0;

  registerRoute(input: CoeRouteInput | CoeRoute): CoeExecutionReceipt {
    const route = normalizeCoeRoute(input);
    const validation = validateCoeRoute(route);
    if (validation.valid) {
      this.routes.push(route);
    } else {
      this.rejected += 1;
    }
    return this.recordReceipt('route', route.id, validation, route.traceability);
  }

  schedule(input: CoeScheduleInput | CoeSchedule): CoeExecutionReceipt {
    const schedule = normalizeCoeSchedule(input);
    const validation = validateCoeSchedule(schedule);
    if (validation.valid) {
      this.schedules.push(schedule);
    } else {
      this.rejected += 1;
    }
    return this.recordReceipt('schedule', schedule.id, validation, schedule.traceability);
  }

  promote(input: CoePromotionWorkflowInput | CoePromotionWorkflow): CoeExecutionReceipt {
    const promotion = normalizeCoePromotionWorkflow(input);
    const validation = validateCoePromotionWorkflow(promotion);
    if (validation.valid) {
      this.promotions.push(promotion);
    } else {
      this.rejected += 1;
    }
    return this.recordReceipt('promotion', promotion.id, validation, promotion.traceability, promotion.evidence);
  }

  snapshot(): CoeRuntimeSnapshot {
    return {
      packageName: '@aaes-os/coe-runtime',
      version: VERSION,
      acceptedRoutes: this.routes.length,
      acceptedSchedules: this.schedules.length,
      acceptedPromotions: this.promotions.length,
      rejectedSubjects: this.rejected,
      emittedReceipts: this.receipts.length,
      lastReceiptId: this.receipts[this.receipts.length - 1]?.id,
    };
  }

  listReceipts(): CoeExecutionReceipt[] {
    return this.receipts.map((receipt) => ({ ...receipt, validation: { ...receipt.validation, issues: [...receipt.validation.issues] } }));
  }

  private recordReceipt(
    kind: CoeExecutionReceipt['kind'],
    subjectId: string,
    validation: CoeValidationResult,
    traceability: readonly CoeTraceabilityRow[],
    evidence: readonly CoeEvidenceRef[] = [],
  ): CoeExecutionReceipt {
    const receiptBody = {
      kind,
      subjectId,
      accepted: validation.valid,
      evidenceHash: hash(evidence),
      traceabilityHash: hash(traceability),
      validation,
    };
    const receipt = { id: hash(receiptBody), ...receiptBody };
    this.receipts.push(receipt);
    return receipt;
  }
}

export function createCoeRuntime(): CoeRuntime {
  return new CoeRuntime();
}

export function summarizeCoeRuntime(runtime: CoeRuntime = new CoeRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} emitted ${snapshot.emittedReceipts} execution receipts`;
}

function validateTraceability(issues: CoeValidationIssue[], traceability: readonly CoeTraceabilityRow[]): void {
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

function requireText(issues: CoeValidationIssue[], field: string, value: string): void {
  if (!value) {
    issues.push({ field, message: `${field} is required` });
  }
}

function requireList(issues: CoeValidationIssue[], field: string, values: readonly string[]): void {
  if (values.length === 0) {
    issues.push({ field, message: `${field} requires at least one entry` });
  }
}

function normalizeEvidenceRef(ref: CoeEvidenceRef): CoeEvidenceRef {
  return {
    id: normalizeText(ref.id),
    kind: normalizeText(ref.kind),
    uri: ref.uri ? normalizeText(ref.uri) : undefined,
    hash: ref.hash ? normalizeText(ref.hash) : undefined,
    signature: ref.signature ? normalizeText(ref.signature) : undefined,
  };
}

function normalizeAuthorityRef(authority: CoeAuthorityRef): CoeAuthorityRef {
  return {
    actor: normalizeText(authority.actor),
    roles: normalizeTextList(authority.roles),
    permissions: normalizeTextList(authority.permissions),
  };
}

function normalizeTraceabilityRow(row: CoeTraceabilityRow): CoeTraceabilityRow {
  return {
    cisRequirement: normalizeText(row.cisRequirement),
    referenceArchitecture: normalizeText(row.referenceArchitecture),
    conformanceTest: normalizeText(row.conformanceTest),
    evidenceArtifact: normalizeText(row.evidenceArtifact),
    notes: row.notes ? normalizeText(row.notes) : undefined,
  };
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

function normalizeTextList(values: readonly string[]): readonly string[] {
  return values.map(normalizeText).filter(Boolean);
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
