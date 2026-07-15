import { createHash } from 'node:crypto';

export type UgrPrimitive = string | number | boolean | null;

export type UgrValue =
  | UgrPrimitive
  | readonly UgrValue[]
  | { readonly [key: string]: UgrValue };

export type UgrRiskProfile = 'low' | 'medium' | 'high';
export type UgrMeshRelation =
  | 'EVOLVES_FROM'
  | 'JUSTIFIED_BY'
  | 'SUPERSEDES'
  | 'RESPONDS_TO'
  | 'PRECEDES'
  | 'FOLLOWS'
  | 'RELATED_TO';
export type UgrQueryForm = 'SELECT' | 'SEARCH' | 'TRACE' | 'AGGREGATE' | 'COMPARE';
export type UgrScopeName = 'objects' | 'worlds' | 'modules' | 'artifacts' | 'ledger' | 'mesh';

export interface UgrKnowledgeObject {
  id: string;
  kind: string;
  name: string;
  domain: string;
  summary: string;
  tags: readonly string[];
  concepts: readonly string[];
  stabilityScore: number;
  riskProfile: UgrRiskProfile;
  lineage: readonly string[];
  metadata: Record<string, UgrValue>;
}

export interface UgrWorld extends UgrKnowledgeObject {
  constitutionRef: string;
  rules: readonly string[];
  agents: readonly string[];
  arenas: readonly string[];
  state: Record<string, UgrValue>;
  historyRef: string;
}

export interface UgrMeshLink {
  from: string;
  to: string;
  relation: UgrMeshRelation;
  weight: number;
}

export interface UplModule {
  id: string;
  typedId: string;
  domain: string;
  constitutionBinding: string;
  evidencePolicy: string;
  replayable: boolean;
  worlds: readonly string[];
  lineage: readonly string[];
  metadata: Record<string, UgrValue>;
}

export interface CrfArtifact {
  artifactId: string;
  version: string;
  createdAt: string;
  timeline: readonly string[];
  governanceState: Record<string, UgrValue>;
  impactGraph: readonly UgrMeshLink[];
  lineage: readonly string[];
  evidenceBundle: readonly string[];
  signatures: readonly string[];
}

export interface UgrChangeInput {
  changeType: string;
  artifactRef: string;
  lineage: readonly string[];
  councilVoteSummary: string;
  before: Record<string, UgrValue>;
  after: Record<string, UgrValue>;
  timestamp?: string;
  entryId?: string;
}

export interface UgrChangeEntry extends UgrChangeInput {
  entryId: string;
  timestamp: string;
}

export interface UgrQueryCondition {
  field: string;
  operator: '=' | 'CONTAINS' | '~' | 'BETWEEN';
  value: UgrValue | readonly [UgrValue, UgrValue];
}

export interface UgrQueryOptions {
  limit?: number;
  orderBy?: {
    field: string;
    direction: 'ASC' | 'DESC';
  };
  groupBy?: string;
  include?: readonly string[];
}

export interface UgrQueryPlan {
  form: UgrQueryForm;
  target: string;
  scope: UgrScopeName;
  conditions: readonly UgrQueryCondition[];
  options: UgrQueryOptions;
}

export interface UgrComparison {
  leftId: string;
  rightId: string;
  equal: boolean;
  differences: readonly string[];
  left: Record<string, UgrValue>;
  right: Record<string, UgrValue>;
}

export interface UgrRuntimeSnapshot {
  packageName: '@aaes-os/ugr-runtime';
  version: 'ugr-v1';
  totalObjects: number;
  totalWorlds: number;
  totalModules: number;
  totalArtifacts: number;
  totalChangeEntries: number;
  totalMeshLinks: number;
  lastQuery?: string;
  fingerprint: string;
}

export interface UgrRuntimeSeed {
  objects?: readonly UgrKnowledgeObject[];
  worlds?: readonly UgrWorld[];
  modules?: readonly UplModule[];
  artifacts?: readonly CrfArtifact[];
  changes?: readonly UgrChangeInput[];
  links?: readonly UgrMeshLink[];
}

const VERSION = 'ugr-v1' as const;

export class UgrRuntime {
  private readonly objects = new Map<string, UgrKnowledgeObject>();
  private readonly worlds = new Map<string, UgrWorld>();
  private readonly modules = new Map<string, UplModule>();
  private readonly artifacts = new Map<string, CrfArtifact>();
  private readonly changes: UgrChangeEntry[] = [];
  private readonly links: UgrMeshLink[] = [];
  private lastQuery: string | undefined;

  constructor(seed: UgrRuntimeSeed = {}) {
    for (const object of seed.objects ?? []) {
      this.registerObject(object);
    }
    for (const world of seed.worlds ?? []) {
      this.registerWorld(world);
    }
    for (const module of seed.modules ?? []) {
      this.registerModule(module);
    }
    for (const artifact of seed.artifacts ?? []) {
      this.registerArtifact(artifact);
    }
    for (const change of seed.changes ?? []) {
      this.appendChange(change);
    }
    for (const link of seed.links ?? []) {
      this.link(link);
    }
  }

  registerObject(object: UgrKnowledgeObject): UgrKnowledgeObject {
    const normalized = cloneKnowledgeObject(object);
    this.objects.set(normalized.id, normalized);
    return cloneKnowledgeObject(normalized);
  }

  registerWorld(world: UgrWorld): UgrWorld {
    const normalized = cloneWorld(world);
    this.worlds.set(normalized.id, normalized);
    this.objects.set(normalized.id, normalized);
    return cloneWorld(normalized);
  }

  registerModule(module: UplModule): UplModule {
    const normalized = cloneModule(module);
    this.modules.set(normalized.id, normalized);
    return cloneModule(normalized);
  }

  registerArtifact(artifact: CrfArtifact): CrfArtifact {
    const normalized = cloneArtifact(artifact);
    this.artifacts.set(normalized.artifactId, normalized);
    return cloneArtifact(normalized);
  }

  appendChange(input: UgrChangeInput): UgrChangeEntry {
    const entryBase = {
      changeType: normalizeText(input.changeType),
      artifactRef: normalizeText(input.artifactRef),
      lineage: normalizeStrings(input.lineage),
      councilVoteSummary: normalizeText(input.councilVoteSummary),
      before: normalizeRecord(input.before),
      after: normalizeRecord(input.after),
      timestamp: input.timestamp ?? new Date().toISOString(),
    };
    const entryId = input.entryId ?? `change-${hashJson(entryBase).slice(0, 16)}`;
    const entry: UgrChangeEntry = {
      ...entryBase,
      entryId,
    };
    this.changes.push(entry);
    return cloneChangeEntry(entry);
  }

  link(link: UgrMeshLink): UgrMeshLink {
    const normalized = {
      from: normalizeText(link.from),
      to: normalizeText(link.to),
      relation: link.relation,
      weight: Number.isFinite(link.weight) ? link.weight : 1,
    };
    this.links.push(normalized);
    return { ...normalized };
  }

  resolveObject(id: string): UgrKnowledgeObject | undefined {
    return this.objects.get(normalizeText(id)) ? cloneKnowledgeObject(this.objects.get(normalizeText(id)) as UgrKnowledgeObject) : undefined;
  }

  resolveWorld(id: string): UgrWorld | undefined {
    return this.worlds.get(normalizeText(id)) ? cloneWorld(this.worlds.get(normalizeText(id)) as UgrWorld) : undefined;
  }

  resolveModule(id: string): UplModule | undefined {
    return this.modules.get(normalizeText(id)) ? cloneModule(this.modules.get(normalizeText(id)) as UplModule) : undefined;
  }

  resolveArtifact(id: string): CrfArtifact | undefined {
    return this.artifacts.get(normalizeText(id)) ? cloneArtifact(this.artifacts.get(normalizeText(id)) as CrfArtifact) : undefined;
  }

  listObjects(): UgrKnowledgeObject[] {
    return Array.from(this.objects.values()).map(cloneKnowledgeObject);
  }

  listWorlds(): UgrWorld[] {
    return Array.from(this.worlds.values()).map(cloneWorld);
  }

  listModules(): UplModule[] {
    return Array.from(this.modules.values()).map(cloneModule);
  }

  listArtifacts(): CrfArtifact[] {
    return Array.from(this.artifacts.values()).map(cloneArtifact);
  }

  listChanges(): UgrChangeEntry[] {
    return this.changes.map(cloneChangeEntry);
  }

  listLinks(): UgrMeshLink[] {
    return this.links.map((link) => ({ ...link }));
  }

  getLineage(id: string): string[] {
    const normalizedId = normalizeText(id);
    const object = this.objects.get(normalizedId);
    const world = this.worlds.get(normalizedId);
    const lineage = new Set<string>([
      ...normalizeStrings(object?.lineage ?? []),
      ...normalizeStrings(world?.lineage ?? []),
    ]);

    for (const link of this.links) {
      if (normalizeText(link.from) === normalizedId) {
        lineage.add(link.to);
      }
      if (normalizeText(link.to) === normalizedId) {
        lineage.add(link.from);
      }
    }

    return Array.from(lineage);
  }

  getMeshNeighbors(id: string): UgrMeshLink[] {
    const normalizedId = normalizeText(id);
    return this.links.filter((link) => normalizeText(link.from) === normalizedId || normalizeText(link.to) === normalizedId).map((link) => ({ ...link }));
  }

  replayState(): UgrRuntimeSnapshot {
    return this.snapshot();
  }

  replayChange(entryId: string): UgrChangeEntry | undefined {
    const entry = this.changes.find((candidate) => candidate.entryId === normalizeText(entryId));
    return entry ? cloneChangeEntry(entry) : undefined;
  }

  diff(leftId: string, rightId: string): {
    leftId: string;
    rightId: string;
    changes: readonly string[];
    left: Record<string, UgrValue>;
    right: Record<string, UgrValue>;
  } {
    const left = this.resolveEntity(leftId);
    const right = this.resolveEntity(rightId);
    if (!left || !right) {
      throw new Error('UGR diff requires both entities to exist');
    }

    return {
      leftId: normalizeText(leftId),
      rightId: normalizeText(rightId),
      changes: diffKeys(left, right),
      left: cloneRecord(left),
      right: cloneRecord(right),
    };
  }

  impact(entryId: string): {
    entryId: string;
    artifactRef: string;
    lineage: readonly string[];
    councilVoteSummary: string;
    before: Record<string, UgrValue>;
    after: Record<string, UgrValue>;
  } | undefined {
    const entry = this.replayChange(entryId);
    if (!entry) {
      return undefined;
    }

    return {
      entryId: entry.entryId,
      artifactRef: entry.artifactRef,
      lineage: [...entry.lineage],
      councilVoteSummary: entry.councilVoteSummary,
      before: cloneRecord(entry.before),
      after: cloneRecord(entry.after),
    };
  }

  query(expression: string): Array<Record<string, unknown>> {
    const plan = parseUgrQuery(expression);
    this.lastQuery = expression.trim();
    const records = this.getScopeRecords(plan.scope);
    const filtered = applyQueryFilters(records, plan.conditions);

    switch (plan.form) {
      case 'SELECT':
      case 'SEARCH':
        return applyProjection(filtered, plan.target, plan.options);
      case 'TRACE':
        return applyTrace(filtered, plan.target, plan.options);
      case 'AGGREGATE':
        return applyAggregation(filtered, plan);
      case 'COMPARE':
        return [this.executeCompare(filtered, plan)];
      default:
        return [];
    }
  }

  select(expression: string): Array<Record<string, unknown>> {
    return this.query(expression.startsWith('SELECT') ? expression : `SELECT * FROM ${expression}`);
  }

  search(expression: string): Array<Record<string, unknown>> {
    return this.query(expression.startsWith('SEARCH') ? expression : `SEARCH * FROM ${expression}`);
  }

  trace(expression: string): Array<Record<string, unknown>> {
    return this.query(expression.startsWith('TRACE') ? expression : `TRACE * FROM ${expression}`);
  }

  aggregate(expression: string): Array<Record<string, unknown>> {
    return this.query(expression.startsWith('AGGREGATE') ? expression : `AGGREGATE * FROM ${expression}`);
  }

  compare(leftId: string, rightId: string): UgrComparison {
    const left = this.resolveEntity(leftId);
    const right = this.resolveEntity(rightId);
    if (!left || !right) {
      throw new Error('UGR comparison requires both entities');
    }

    const leftClone = cloneRecord(left);
    const rightClone = cloneRecord(right);
    return {
      leftId: normalizeText(leftId),
      rightId: normalizeText(rightId),
      equal: stableStringify(leftClone) === stableStringify(rightClone),
      differences: diffKeys(leftClone, rightClone),
      left: leftClone,
      right: rightClone,
    };
  }

  snapshot(): UgrRuntimeSnapshot {
    return {
      packageName: '@aaes-os/ugr-runtime',
      version: VERSION,
      totalObjects: this.objects.size,
      totalWorlds: this.worlds.size,
      totalModules: this.modules.size,
      totalArtifacts: this.artifacts.size,
      totalChangeEntries: this.changes.length,
      totalMeshLinks: this.links.length,
      lastQuery: this.lastQuery,
      fingerprint: fingerprintRuntime(this),
    };
  }

  private executeCompare(filtered: readonly unknown[], plan: UgrQueryPlan): Record<string, unknown> {
    const leftId = getConditionValue(plan.conditions, 'leftId') ?? extractCompareTarget(plan.target, 0);
    const rightId = getConditionValue(plan.conditions, 'rightId') ?? extractCompareTarget(plan.target, 1);
    if (!leftId || !rightId) {
      throw new Error('COMPARE queries require leftId and rightId');
    }

    const comparison = this.compare(String(leftId), String(rightId));
    return {
      ...comparison,
      scopeSize: filtered.length,
    };
  }

  private resolveEntity(id: string): Record<string, UgrValue> | undefined {
    const normalizedId = normalizeText(id);
    const entity = (
      this.worlds.get(normalizedId) ||
      this.objects.get(normalizedId) ||
      this.modules.get(normalizedId) ||
      this.artifacts.get(normalizedId) ||
      this.changes.find((entry) => entry.entryId === normalizedId) ||
      undefined
    );
    return entity ? cloneRecord(entity as unknown as Record<string, UgrValue>) : undefined;
  }

  private getScopeRecords(scope: UgrScopeName): readonly Record<string, unknown>[] {
    switch (scope) {
      case 'worlds':
        return toQueryRecords(this.listWorlds());
      case 'modules':
        return toQueryRecords(this.listModules());
      case 'artifacts':
        return toQueryRecords(this.listArtifacts());
      case 'ledger':
        return toQueryRecords(this.listChanges());
      case 'mesh':
        return toQueryRecords(this.listLinks());
      case 'objects':
      default:
        return toQueryRecords(this.listObjects());
    }
  }
}

export function createUgrRuntime(seed: UgrRuntimeSeed = {}): UgrRuntime {
  return new UgrRuntime(seed);
}

export function buildUgrRuntimeStatus(runtime: UgrRuntime = new UgrRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} tracks ${snapshot.totalWorlds} worlds, ${snapshot.totalModules} UPL modules, and ${snapshot.totalArtifacts} CRF artifacts`;
}

export function parseUgrQuery(expression: string): UgrQueryPlan {
  const input = expression.trim();
  const match = /^(SELECT|SEARCH|TRACE|AGGREGATE|COMPARE)\s+(.+?)\s+FROM\s+([A-Za-z0-9_-]+)(?:\s+WHERE\s+(.+?))?(?:\s+WITH\s+(.+))?$/i.exec(input);
  if (!match) {
    throw new Error(`invalid UGR query: ${expression}`);
  }

  const form = match[1].toUpperCase() as UgrQueryForm;
  const target = normalizeText(match[2]);
  const scope = normalizeScope(match[3]);
  const conditions = parseConditions(match[4] ?? '');
  const options = parseOptions(match[5] ?? '');

  return { form, target, scope, conditions, options };
}

function normalizeScope(scope: string): UgrScopeName {
  const normalized = normalizeText(scope).toLowerCase();
  if (normalized === 'world' || normalized === 'worlds') {
    return 'worlds';
  }
  if (normalized === 'module' || normalized === 'modules' || normalized === 'upl') {
    return 'modules';
  }
  if (normalized === 'artifact' || normalized === 'artifacts' || normalized === 'crf') {
    return 'artifacts';
  }
  if (normalized === 'ledger' || normalized === 'change-ledger' || normalized === 'governance') {
    return 'ledger';
  }
  if (normalized === 'mesh' || normalized === 'links') {
    return 'mesh';
  }
  return 'objects';
}

function parseConditions(whereClause: string): readonly UgrQueryCondition[] {
  const clause = whereClause.trim();
  if (!clause) {
    return [];
  }

  const tokens = tokenize(clause);
  const conditions: UgrQueryCondition[] = [];
  let index = 0;
  while (index < tokens.length) {
    const field = tokens[index++];
    if (!field) {
      break;
    }
    const operatorToken = tokens[index++];
    if (!operatorToken) {
      throw new Error(`invalid UGR query condition near ${field}`);
    }
    const operator = operatorToken.toUpperCase() as UgrQueryCondition['operator'];

    if (operator === 'BETWEEN') {
      const left = parseValue(tokens[index++]);
      const andToken = tokens[index++];
      const right = parseValue(tokens[index++]);
      if (andToken?.toUpperCase() !== 'AND') {
        throw new Error('BETWEEN conditions require AND');
      }
      conditions.push({ field, operator, value: [left, right] });
    } else {
      const value = parseValue(tokens[index++]);
      conditions.push({ field, operator: operator as '=' | 'CONTAINS' | '~', value });
    }

    if (tokens[index]?.toUpperCase() === 'AND') {
      index += 1;
    }
  }

  return conditions;
}

function parseOptions(optionsClause: string): UgrQueryOptions {
  const clause = optionsClause.trim();
  if (!clause) {
    return {};
  }

  const tokens = tokenize(clause);
  const options: UgrQueryOptions = {};
  let index = 0;

  while (index < tokens.length) {
    const token = tokens[index++];
    if (!token) {
      break;
    }

    switch (token.toUpperCase()) {
      case 'LIMIT': {
        const count = Number(tokens[index++] ?? '0');
        if (!Number.isFinite(count) || count < 0) {
          throw new Error('LIMIT requires a non-negative number');
        }
        options.limit = count;
        break;
      }
      case 'ORDER': {
        if (tokens[index]?.toUpperCase() !== 'BY') {
          throw new Error('ORDER requires BY');
        }
        index += 1;
        const field = tokens[index++];
        const directionToken = tokens[index]?.toUpperCase();
        const direction = directionToken === 'DESC' ? 'DESC' : 'ASC';
        if (directionToken === 'ASC' || directionToken === 'DESC') {
          index += 1;
        }
        if (!field) {
          throw new Error('ORDER BY requires a field');
        }
        options.orderBy = { field, direction };
        break;
      }
      case 'GROUP': {
        if (tokens[index]?.toUpperCase() !== 'BY') {
          throw new Error('GROUP requires BY');
        }
        index += 1;
        const field = tokens[index++];
        if (!field) {
          throw new Error('GROUP BY requires a field');
        }
        options.groupBy = field;
        break;
      }
      case 'INCLUDE': {
        const includeValues: string[] = [];
        while (index < tokens.length) {
          const value = tokens[index++];
          if (!value) {
            break;
          }
          if (value === ',') {
            continue;
          }
          if (value.toUpperCase() === 'AND') {
            index -= 1;
            break;
          }
          includeValues.push(value.replace(/,$/, ''));
          if (tokens[index] === ',') {
            index += 1;
          } else if (tokens[index]?.toUpperCase() !== 'AND') {
            break;
          }
        }
        options.include = includeValues;
        break;
      }
      default:
        break;
    }
  }

  return options;
}

function applyQueryFilters(records: readonly Record<string, unknown>[], conditions: readonly UgrQueryCondition[]): Record<string, unknown>[] {
  return records.filter((record) => conditions.every((condition) => evaluateCondition(record, condition)));
}

function evaluateCondition(record: Record<string, unknown>, condition: UgrQueryCondition): boolean {
  const actual = resolveField(record, condition.field);
  const expected = condition.value;

  switch (condition.operator) {
    case '=':
      return compareScalar(actual, expected);
    case '~':
      return containsText(actual, expected);
    case 'CONTAINS':
      return containsValue(actual, expected);
    case 'BETWEEN': {
      if (!Array.isArray(expected) || expected.length !== 2) {
        return false;
      }
      return betweenValues(actual, expected[0], expected[1]);
    }
    default:
      return false;
  }
}

function applyProjection(records: readonly Record<string, unknown>[], target: string, options: UgrQueryOptions): Record<string, unknown>[] {
  const projectionTarget = target === '*' ? '' : target;
  const include = new Set<string>(options.include ?? []);
  const projected = records.map((record) => {
    if (!projectionTarget) {
      return cloneRecord(record);
    }
    const projectedRecord: Record<string, unknown> = {
      id: record.id,
      [projectionTarget]: resolveField(record, projectionTarget),
    };
    for (const field of include) {
      projectedRecord[field] = resolveField(record, field);
    }
    return projectedRecord;
  });

  return applyOrderAndLimit(projected, options);
}

function applyTrace(records: readonly Record<string, unknown>[], target: string, options: UgrQueryOptions): Record<string, unknown>[] {
  const traced = records.map((record) => ({
    ...cloneRecord(record),
    trace: {
      target,
      lineage: cloneLineage(record),
      mesh: getEmbeddedMesh(record),
    },
  }));
  return applyOrderAndLimit(traced, options);
}

function applyAggregation(records: readonly Record<string, unknown>[], plan: UgrQueryPlan): Record<string, unknown>[] {
  const groupField = plan.options.groupBy ?? plan.target;
  const groups = new Map<string, number>();

  for (const record of records) {
    const value = resolveField(record, groupField);
    const key = stringifyValue(value);
    groups.set(key, (groups.get(key) ?? 0) + 1);
  }

  const aggregated = Array.from(groups.entries()).map(([group, count]) => ({
    groupBy: groupField,
    group,
    count,
  }));
  return applyOrderAndLimit(aggregated, plan.options);
}

function applyOrderAndLimit(records: readonly Record<string, unknown>[], options: UgrQueryOptions): Record<string, unknown>[] {
  let output = [...records];
  if (options.orderBy) {
    const direction = options.orderBy.direction === 'DESC' ? -1 : 1;
    output.sort((left, right) => compareByField(left, right, options.orderBy?.field ?? 'id') * direction);
  }
  if (typeof options.limit === 'number') {
    output = output.slice(0, options.limit);
  }
  return output;
}

function compareByField(left: Record<string, unknown>, right: Record<string, unknown>, field: string): number {
  const a = stringifyValue(resolveField(left, field));
  const b = stringifyValue(resolveField(right, field));
  return a.localeCompare(b);
}

function getConditionValue(conditions: readonly UgrQueryCondition[], field: string): UgrValue | undefined {
  return conditions.find((condition) => condition.field === field && condition.operator === '=')?.value as UgrValue | undefined;
}

function extractCompareTarget(target: string, index: number): string | undefined {
  const parts = target.split(/\s+VS\s+|,|\//i).map((part) => normalizeText(part)).filter(Boolean);
  return parts[index];
}

function tokenize(value: string): string[] {
  return value.match(/"[^"]*"|'[^']*'|\S+/g)?.map((token) => token.trim()).filter(Boolean) ?? [];
}

function parseValue(token: string | undefined): UgrValue {
  if (token === undefined) {
    return null;
  }
  const trimmed = token.trim().replace(/,$/, '');
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }
  if (trimmed === 'true') {
    return true;
  }
  if (trimmed === 'false') {
    return false;
  }
  const numeric = Number(trimmed);
  if (!Number.isNaN(numeric) && trimmed !== '') {
    return numeric;
  }
  return trimmed;
}

function compareScalar(actual: unknown, expected: UgrValue): boolean {
  if (Array.isArray(actual)) {
    return actual.some((item) => compareScalar(item, expected));
  }
  if (actual && typeof actual === 'object') {
    return stringifyValue(actual).toLowerCase() === stringifyValue(expected).toLowerCase();
  }
  return stringifyValue(actual).toLowerCase() === stringifyValue(expected).toLowerCase();
}

function containsValue(actual: unknown, expected: UgrValue): boolean {
  if (Array.isArray(actual)) {
    return actual.some((item) => compareScalar(item, expected) || containsText(item, expected));
  }
  if (typeof actual === 'string') {
    return actual.toLowerCase().includes(stringifyValue(expected).toLowerCase());
  }
  return false;
}

function containsText(actual: unknown, expected: UgrValue): boolean {
  return stringifyValue(actual).toLowerCase().includes(stringifyValue(expected).toLowerCase());
}

function betweenValues(actual: unknown, low: UgrValue, high: UgrValue): boolean {
  const actualValue = stringifyValue(actual);
  const lowValue = stringifyValue(low);
  const highValue = stringifyValue(high);
  if (isFiniteNumber(actual) && isFiniteNumber(low) && isFiniteNumber(high)) {
    const numberActual = Number(actual);
    return numberActual >= Number(low) && numberActual <= Number(high);
  }
  return actualValue >= lowValue && actualValue <= highValue;
}

function isFiniteNumber(value: unknown): boolean {
  return typeof value === 'number' && Number.isFinite(value);
}

function resolveField(record: Record<string, unknown>, field: string): unknown {
  const path = normalizeText(field).split('.');
  let current: unknown = record;
  for (const segment of path) {
    if (!current || typeof current !== 'object') {
      return undefined;
    }
    current = (current as Record<string, unknown>)[segment];
  }
  return current;
}

function cloneKnowledgeObject(object: UgrKnowledgeObject): UgrKnowledgeObject {
  return {
    ...object,
    tags: [...object.tags],
    concepts: [...object.concepts],
    lineage: [...object.lineage],
    metadata: cloneRecord(object.metadata),
  };
}

function cloneWorld(world: UgrWorld): UgrWorld {
  return {
    ...cloneKnowledgeObject(world),
    constitutionRef: world.constitutionRef,
    rules: [...world.rules],
    agents: [...world.agents],
    arenas: [...world.arenas],
    state: cloneRecord(world.state),
    historyRef: world.historyRef,
  };
}

function cloneModule(module: UplModule): UplModule {
  return {
    ...module,
    worlds: [...module.worlds],
    lineage: [...module.lineage],
    metadata: cloneRecord(module.metadata),
  };
}

function cloneArtifact(artifact: CrfArtifact): CrfArtifact {
  return {
    ...artifact,
    timeline: [...artifact.timeline],
    governanceState: cloneRecord(artifact.governanceState),
    impactGraph: artifact.impactGraph.map((link) => ({ ...link })),
    lineage: [...artifact.lineage],
    evidenceBundle: [...artifact.evidenceBundle],
    signatures: [...artifact.signatures],
  };
}

function cloneChangeEntry(entry: UgrChangeEntry): UgrChangeEntry {
  return {
    ...entry,
    lineage: [...entry.lineage],
    before: cloneRecord(entry.before),
    after: cloneRecord(entry.after),
  };
}

function cloneRecord<T extends Record<string, unknown>>(value: T): T {
  return Object.fromEntries(Object.entries(value).map(([key, entry]) => [key, cloneValue(entry)])) as T;
}

function toQueryRecords<T extends object>(values: readonly T[]): Record<string, unknown>[] {
  return values.map((value) => cloneRecord(value as unknown as Record<string, unknown>));
}

function cloneValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => cloneValue(entry));
  }
  if (value && typeof value === 'object') {
    return cloneRecord(value as Record<string, unknown>);
  }
  return value;
}

function normalizeRecord(value: Record<string, UgrValue>): Record<string, UgrValue> {
  return Object.fromEntries(Object.entries(value).map(([key, entry]) => [normalizeText(key), normalizeValue(entry)]));
}

function normalizeValue(value: UgrValue): UgrValue {
  if (Array.isArray(value)) {
    return value.map((entry) => normalizeValue(entry));
  }
  if (value && typeof value === 'object') {
    return normalizeRecord(value as Record<string, UgrValue>);
  }
  if (typeof value === 'string') {
    return normalizeText(value);
  }
  return value;
}

function normalizeStrings(values: readonly string[]): string[] {
  return [...values].map((value) => normalizeText(value)).filter(Boolean);
}

function normalizeText(value: string): string {
  return String(value ?? '').trim().replace(/\s+/g, ' ');
}

function diffKeys(left: Record<string, unknown>, right: Record<string, unknown>): string[] {
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  const differences: string[] = [];
  for (const key of keys) {
    if (stableStringify(left[key]) !== stableStringify(right[key])) {
      differences.push(key);
    }
  }
  return differences.sort((a, b) => a.localeCompare(b));
}

function cloneLineage(record: Record<string, unknown>): string[] {
  const lineage = record.lineage;
  if (Array.isArray(lineage)) {
    return lineage.map((entry) => stringifyValue(entry));
  }
  return [];
}

function getEmbeddedMesh(record: Record<string, unknown>): Array<Record<string, unknown>> {
  const mesh = record.mesh;
  if (!Array.isArray(mesh)) {
    return [];
  }
  return mesh.map((entry) => cloneRecord(entry as Record<string, unknown>));
}

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  if (typeof value === 'string') {
    return value;
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return stableStringify(value);
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => `${JSON.stringify(key)}:${stableStringify(entry)}`);
    return `{${entries.join(',')}}`;
  }
  return JSON.stringify(value);
}

function hashJson(value: unknown): string {
  return createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

function fingerprintRuntime(runtime: UgrRuntime): string {
  return `sha256:${hashJson({
    objects: runtime.listObjects().map(({ id, kind, name, domain }) => ({ id, kind, name, domain })),
    worlds: runtime.listWorlds().map(({ id, kind, name, domain }) => ({ id, kind, name, domain })),
    modules: runtime.listModules().map(({ id, typedId, domain }) => ({ id, typedId, domain })),
    artifacts: runtime.listArtifacts().map(({ artifactId, version }) => ({ artifactId, version })),
    changes: runtime.listChanges().map(({ entryId, changeType, artifactRef }) => ({ entryId, changeType, artifactRef })),
    links: runtime.listLinks().map(({ from, to, relation }) => ({ from, to, relation })),
  })}`;
}

export * from './models.js';
export * from './storage/sql.js';
export * from './storage/graph.js';
export * from './storage/vector.js';
export * from './adapters.js';
export * from './adapters/postgres.js';
export * from './adapters/neo4j.js';
export * from './adapters/pgvector.js';
export * from './drivers/postgres.js';
export * from './drivers/neo4j.js';
export * from './drivers/pgvector.js';
export * from './api.js';
export * from './runtime.js';
export * from './runtime-env.js';
export * from './cli.js';
