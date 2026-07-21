import crypto from 'node:crypto';

export type KnowledgeKind =
  | 'world'
  | 'constitution'
  | 'rule'
  | 'evidence'
  | 'agent'
  | 'arena'
  | 'concept'
  | 'document'
  | 'metric'
  | 'ledger'
  | 'profile'
  | 'policy'
  | 'package'
  | 'crf';

export type KnowledgeScope = 'worlds' | 'objects' | 'docs' | 'metrics' | 'mesh' | 'lineage';

export type UgqlVerb = 'SELECT' | 'SEARCH' | 'TRACE' | 'AGGREGATE' | 'COMPARE';

export type ChangeType =
  | 'PROFILE_CREATED'
  | 'PROFILE_MODIFIED'
  | 'PROFILE_DELETED'
  | 'RULE_CREATED'
  | 'RULE_MODIFIED'
  | 'RULE_DELETED'
  | 'STEWARD_CONTRACT_UPDATED'
  | 'CONSTITUTIONAL_CLAUSE_ADDED'
  | 'CONSTITUTIONAL_CLAUSE_REVISED';

export type RelationType =
  | 'IS_A'
  | 'PART_OF'
  | 'MITIGATES'
  | 'DEPENDS_ON'
  | 'SIMILAR_TO'
  | 'EVOLVES_FROM'
  | 'JUSTIFIED_BY'
  | 'SUPERSEDES'
  | 'RESPONDS_TO'
  | 'PRECEDES'
  | 'FOLLOWS';

export interface KnowledgeObject {
  id: string;
  kind: KnowledgeKind;
  name: string;
  domain: string;
  summary: string;
  tags: string[];
  concepts: string[];
  stabilityScore: number;
  riskProfile: 'low' | 'medium' | 'high' | 'critical';
  lineage: string[];
  metadata: Record<string, unknown>;
}

export interface KnowledgeWorld extends KnowledgeObject {
  kind: 'world';
  constitutionRef: string;
  rules: string[];
  agents: string[];
  arenas: string[];
  state: string;
  historyRef: string;
}

export interface KnowledgeMeshLink {
  fromWorldId: string;
  toWorldId: string;
  similarity: number;
  stability: number;
  reason: string;
}

export interface KnowledgeLineageNode {
  nodeId: string;
  refId: string;
  kind: KnowledgeKind | 'incident' | 'change-ledger' | 'concept-lineage';
  timestamp: string;
  links: Array<{
    relationType: RelationType;
    targetNodeId: string;
  }>;
}

export interface GovernanceStateSnapshot {
  timestamp: string;
  profiles: string[];
  rules: string[];
  stewardContracts: string[];
  constitutionClauses: string[];
  authorityModes: string[];
  arenas: string[];
  intentChains: Record<string, string[]>;
}

export interface ConstitutionalChangeLedgerEntry {
  entryId: string;
  timestamp: string;
  changeType: ChangeType;
  artifactRef: string;
  domain: string;
  subsystem: string;
  tags: string[];
  lineage: {
    previousVersion: string | null;
    justificationEvidence: string[];
    relatedIncidents: string[];
    councilVote: {
      for: number;
      against: number;
      abstain: number;
    };
  };
  beforeState: GovernanceStateSnapshot;
  afterState: GovernanceStateSnapshot;
  intentIds: string[];
  hash: string;
  signature: string;
}

interface ConstitutionalChangeLedgerSeed {
  entryId: string;
  timestamp: string;
  changeType: ChangeType;
  artifactRef: string;
  domain: string;
  subsystem: string;
  tags: string[];
  previousVersion: string | null;
  justificationEvidence: string[];
  relatedIncidents: string[];
  councilVote: {
    for: number;
    against: number;
    abstain: number;
  };
  beforeState: GovernanceStateSnapshot;
  afterState: GovernanceStateSnapshot;
  intentIds: string[];
}

export interface UplModule {
  id: string;
  name: string;
  kind: 'domain' | 'governance' | 'world';
  domain: string;
  summary: string;
  concepts: string[];
  rules: string[];
  worlds: string[];
  evidencePolicies: string[];
  authorityModes: string[];
}

export interface CrfArtifact {
  id: string;
  profile: string;
  environment: string;
  incidentRef: string;
  hash: string;
  signature: string;
  timeline: Array<{
    timestamp: string;
    event: string;
    state: string;
  }>;
  governanceState: GovernanceStateSnapshot;
  impact: {
    affectedProfiles: string[];
    affectedRules: string[];
    affectedArenas: string[];
    affectedAuthorityModes: string[];
    affectedIntents: string[];
  };
  lineage: {
    previousVersion: string | null;
    evidenceIds: string[];
    councilVote: {
      for: number;
      against: number;
      abstain: number;
    };
  };
}

export interface UgqlCondition {
  field: string;
  operator: '=' | '>' | '>=' | '<' | '<=' | 'CONTAINS' | 'MATCHES' | 'BETWEEN';
  value: string | number | [string, string];
}

export interface UgqlOptions {
  limit?: number;
  orderBy?: {
    field: string;
    direction: 'ASC' | 'DESC';
  };
  groupBy?: string;
  include?: string[];
}

export interface UgqlQuery {
  verb: UgqlVerb;
  target: string;
  scope: KnowledgeScope;
  conditions: UgqlCondition[];
  options: UgqlOptions;
  raw: string;
}

export interface UgqlResult {
  query: UgqlQuery;
  results: Array<Record<string, unknown>>;
  meta: {
    count: number;
    executionTimeMs: number;
    scope: KnowledgeScope;
    target: string;
    verb: UgqlVerb;
  };
}

interface KnowledgeStore {
  objects: KnowledgeObject[];
  worlds: KnowledgeWorld[];
  meshLinks: KnowledgeMeshLink[];
  lineage: KnowledgeLineageNode[];
  ledgerEntries: ConstitutionalChangeLedgerEntry[];
  uplModules: UplModule[];
  crfArtifacts: CrfArtifact[];
}

const seedStore: KnowledgeStore = buildSeedStore();

export function getKnowledgeStore(): KnowledgeStore {
  return seedStore;
}

export function getKnowledgeObject(id: string): KnowledgeObject | null {
  return seedStore.objects.find((object) => object.id === id) ?? null;
}

export function getKnowledgeWorld(id: string): KnowledgeWorld | null {
  return seedStore.worlds.find((world) => world.id === id) ?? null;
}

export function getKnowledgeLineage(subjectId: string): KnowledgeLineageNode[] {
  const lineage = seedStore.lineage.filter((node) => node.refId === subjectId || node.nodeId === subjectId);
  if (lineage.length > 0) {
    return lineage;
  }
  const object = getKnowledgeObject(subjectId) ?? getKnowledgeWorld(subjectId);
  if (!object) {
    return [];
  }
  return [
    {
      nodeId: `${subjectId}-lineage`,
      refId: subjectId,
      kind: object.kind,
      timestamp: new Date().toISOString(),
      links: object.lineage.map((entry) => ({
        relationType: 'EVOLVES_FROM' as const,
        targetNodeId: entry,
      })),
    },
  ];
}

export function getMeshNeighbors(worldId: string): {
  world: KnowledgeWorld | null;
  neighbors: Array<{
    world: KnowledgeWorld;
    link: KnowledgeMeshLink;
  }>;
} {
  const world = getKnowledgeWorld(worldId);
  if (!world) {
    return { world: null, neighbors: [] };
  }
  const neighbors = seedStore.meshLinks
    .filter((link) => link.fromWorldId === worldId || link.toWorldId === worldId)
    .map((link) => {
      const neighborId = link.fromWorldId === worldId ? link.toWorldId : link.fromWorldId;
      const neighbor = getKnowledgeWorld(neighborId);
      return neighbor
        ? { world: neighbor, link }
        : null;
    })
    .filter((entry): entry is { world: KnowledgeWorld; link: KnowledgeMeshLink } => entry !== null);
  return { world, neighbors };
}

export function searchKnowledge(text: string, domain?: string | null): Array<Record<string, unknown>> {
  const needle = normalizeString(text);
  return seedStore.objects
    .filter((object) => {
      if (domain && object.domain !== domain) {
        return false;
      }
      const haystack = normalizeString([
        object.id,
        object.name,
        object.summary,
        ...object.tags,
        ...object.concepts,
        JSON.stringify(object.metadata),
      ].join(' '));
      return haystack.includes(needle);
    })
    .map((object) => serializeKnowledgeObject(object, ['lineage']));
}

export function queryKnowledge(ugql: string): UgqlResult {
  const started = Date.now();
  const query = parseUgql(ugql);
  const base = getScopeObjects(query.scope);
  const matches = applyConditions(base, query.conditions);
  const ranked = rankQueryResults(matches, query);
  const sliced = applyOptions(ranked, query.options);
  const results = query.verb === 'TRACE'
    ? buildTraceResults(query, sliced)
    : query.verb === 'AGGREGATE'
      ? buildAggregateResults(query, sliced)
      : query.verb === 'COMPARE'
        ? buildCompareResults(query, sliced)
        : sliced.map((object) => serializeKnowledgeObject(object, query.options.include));
  return {
    query,
    results,
    meta: {
      count: results.length,
      executionTimeMs: Math.max(1, Date.now() - started),
      scope: query.scope,
      target: query.target,
      verb: query.verb,
    },
  };
}

export function getChangeLedgerEntries(filters: {
  changeType?: ChangeType[] | null;
  domain?: string | null;
  subsystem?: string | null;
  dateRange?: { from?: string | null; to?: string | null } | null;
  tags?: string[] | null;
} = {}): ConstitutionalChangeLedgerEntry[] {
  return seedStore.ledgerEntries.filter((entry) => {
    if (filters.changeType && filters.changeType.length > 0 && !filters.changeType.includes(entry.changeType)) {
      return false;
    }
    if (filters.domain && entry.domain !== filters.domain) {
      return false;
    }
    if (filters.subsystem && entry.subsystem !== filters.subsystem) {
      return false;
    }
    if (filters.dateRange?.from && entry.timestamp < filters.dateRange.from) {
      return false;
    }
    if (filters.dateRange?.to && entry.timestamp > filters.dateRange.to) {
      return false;
    }
    if (filters.tags && filters.tags.length > 0 && !filters.tags.every((tag) => entry.tags.includes(tag))) {
      return false;
    }
    return true;
  });
}

export function getChangeLedgerEntry(entryId: string): ConstitutionalChangeLedgerEntry | null {
  return seedStore.ledgerEntries.find((entry) => entry.entryId === entryId) ?? null;
}

export function getGovernanceHistory(intentId: string): { intentId: string; governanceChain: string[] } {
  return {
    intentId,
    governanceChain: seedStore.ledgerEntries
      .filter((entry) => entry.intentIds.includes(intentId))
      .map((entry) => entry.entryId),
  };
}

export function replayGovernanceState(timestamp: string): GovernanceStateSnapshot {
  const ordered = [...seedStore.ledgerEntries].sort((left, right) => left.timestamp.localeCompare(right.timestamp));
  let snapshot = ordered[0]?.beforeState ?? seedStore.ledgerEntries[0]?.beforeState ?? baselineGovernanceState();
  for (const entry of ordered) {
    if (entry.timestamp <= timestamp) {
      snapshot = entry.afterState;
      continue;
    }
    break;
  }
  return cloneSnapshot(snapshot);
}

export function replayChange(entryId: string): {
  entryId: string;
  beforeState: GovernanceStateSnapshot;
  afterState: GovernanceStateSnapshot;
  impact: {
    profilesChanged: string[];
    rulesChanged: string[];
    authorityModesChanged: string[];
    arenasAffected: string[];
  };
  lineage: ConstitutionalChangeLedgerEntry['lineage'];
} | null {
  const entry = getChangeLedgerEntry(entryId);
  if (!entry) {
    return null;
  }
  return {
    entryId: entry.entryId,
    beforeState: cloneSnapshot(entry.beforeState),
    afterState: cloneSnapshot(entry.afterState),
    impact: {
      profilesChanged: diffSet(entry.beforeState.profiles, entry.afterState.profiles),
      rulesChanged: diffSet(entry.beforeState.rules, entry.afterState.rules),
      authorityModesChanged: diffSet(entry.beforeState.authorityModes, entry.afterState.authorityModes),
      arenasAffected: diffSet(entry.beforeState.arenas, entry.afterState.arenas),
    },
    lineage: {
      previousVersion: entry.lineage.previousVersion,
      justificationEvidence: [...entry.lineage.justificationEvidence],
      relatedIncidents: [...entry.lineage.relatedIncidents],
      councilVote: { ...entry.lineage.councilVote },
    },
  };
}

export function diffGovernanceStates(fromTimestamp: string, toTimestamp: string): {
  from: string;
  to: string;
  profile_diffs: Array<{
    profile_id: string;
    changes: Record<string, { from: string | null; to: string | null }>;
  }>;
  rule_diffs: Array<{
    rule_id: string;
    changes: Record<string, { from: string | null; to: string | null }>;
  }>;
  authority_diffs: Array<{
    profile_id: string;
    authority_mode: { from: string | null; to: string | null };
  }>;
  arena_diffs: Array<{
    profile_id: string;
    required_arenas: { added: string[]; removed: string[] };
  }>;
} {
  const fromState = replayGovernanceState(fromTimestamp);
  const toState = replayGovernanceState(toTimestamp);
  return {
    from: fromTimestamp,
    to: toTimestamp,
    profile_diffs: diffNamedCollections(fromState.profiles, toState.profiles, 'profile') as Array<{
      profile_id: string;
      changes: Record<string, { from: string | null; to: string | null }>;
    }>,
    rule_diffs: diffNamedCollections(fromState.rules, toState.rules, 'rule') as Array<{
      rule_id: string;
      changes: Record<string, { from: string | null; to: string | null }>;
    }>,
    authority_diffs: [{
      profile_id: 'profile-prod-critical',
      authority_mode: {
        from: fromState.authorityModes[0] ?? null,
        to: toState.authorityModes[0] ?? null,
      },
    }],
    arena_diffs: [{
      profile_id: 'profile-prod-critical',
      required_arenas: {
        added: diffSet(toState.arenas, fromState.arenas),
        removed: diffSet(fromState.arenas, toState.arenas),
      },
    }],
  };
}

export function getChangeTimeline(filters: {
  changeType?: ChangeType[] | null;
  domain?: string | null;
  tags?: string[] | null;
} = {}): { timeline: KnowledgeLineageNode[] } {
  const entries = getChangeLedgerEntries(filters);
  return {
    timeline: entries.map((entry, index) => ({
      nodeId: `node-${String(index + 1).padStart(3, '0')}`,
      refId: entry.entryId,
      kind: 'change-ledger',
      timestamp: entry.timestamp,
      links: [
        ...(index > 0 ? [{ relationType: 'PRECEDES' as const, targetNodeId: `node-${String(index).padStart(3, '0')}` }] : []),
        ...(entry.lineage.previousVersion ? [{ relationType: 'SUPERSEDES' as const, targetNodeId: entry.lineage.previousVersion }] : []),
        ...entry.lineage.relatedIncidents.map((incident) => ({
          relationType: 'RESPONDS_TO' as const,
          targetNodeId: incident,
        })),
      ],
    })),
  };
}

export function getLineageGraph(subjectId: string): {
  nodes: KnowledgeLineageNode[];
} {
  const entry = getChangeLedgerEntry(subjectId);
  const object = getKnowledgeObject(subjectId) ?? getKnowledgeWorld(subjectId);
  const related = seedStore.lineage.filter((node) => node.refId === subjectId || node.nodeId === subjectId);
  if (entry) {
    return { nodes: timelineGraphFromLedgerEntry(entry) };
  }
  if (related.length > 0) {
    return { nodes: related };
  }
  if (object) {
    return {
      nodes: [
        {
          nodeId: `${object.id}-lineage`,
          refId: object.id,
          kind: object.kind,
          timestamp: object.metadata.timestamp ? String(object.metadata.timestamp) : new Date().toISOString(),
          links: object.lineage.map((lineageId) => ({
            relationType: 'EVOLVES_FROM' as const,
            targetNodeId: lineageId,
          })),
        },
      ],
    };
  }
  return { nodes: [] };
}

export function getGovernanceImpactMap(entryId: string): {
  entryId: string;
  impactMap: {
    profiles: string[];
    rules: string[];
    arenas: string[];
    authorityModes: string[];
    affectedIntents: string[];
  };
} | null {
  const entry = getChangeLedgerEntry(entryId);
  if (!entry) {
    return null;
  }
  return {
    entryId: entry.entryId,
    impactMap: {
      profiles: diffSet(entry.beforeState.profiles, entry.afterState.profiles),
      rules: diffSet(entry.beforeState.rules, entry.afterState.rules),
      arenas: diffSet(entry.beforeState.arenas, entry.afterState.arenas),
      authorityModes: diffSet(entry.beforeState.authorityModes, entry.afterState.authorityModes),
      affectedIntents: [...entry.intentIds],
    },
  };
}

export function getUplModules(): UplModule[] {
  return seedStore.uplModules.map((module) => ({ ...module, concepts: [...module.concepts], rules: [...module.rules], worlds: [...module.worlds], evidencePolicies: [...module.evidencePolicies], authorityModes: [...module.authorityModes] }));
}

export function getCrfArtifacts(): CrfArtifact[] {
  return seedStore.crfArtifacts.map((artifact) => ({
    ...artifact,
    timeline: artifact.timeline.map((event) => ({ ...event })),
    governanceState: cloneSnapshot(artifact.governanceState),
    impact: {
      affectedProfiles: [...artifact.impact.affectedProfiles],
      affectedRules: [...artifact.impact.affectedRules],
      affectedArenas: [...artifact.impact.affectedArenas],
      affectedAuthorityModes: [...artifact.impact.affectedAuthorityModes],
      affectedIntents: [...artifact.impact.affectedIntents],
    },
    lineage: {
      previousVersion: artifact.lineage.previousVersion,
      evidenceIds: [...artifact.lineage.evidenceIds],
      councilVote: { ...artifact.lineage.councilVote },
    },
  }));
}

export function validateCrfArtifact(artifact: CrfArtifact): { valid: boolean; reasons: string[] } {
  const reasons: string[] = [];
  if (!artifact.id || !artifact.profile || !artifact.environment || !artifact.incidentRef) {
    reasons.push('missing required CRF header fields');
  }
  if (!artifact.hash || !artifact.signature) {
    reasons.push('missing cryptographic proof fields');
  }
  if (artifact.timeline.length === 0) {
    reasons.push('timeline is empty');
  }
  if (artifact.lineage.evidenceIds.length === 0) {
    reasons.push('lineage evidence is required');
  }
  return { valid: reasons.length === 0, reasons };
}

function buildTraceResults(query: UgqlQuery, objects: KnowledgeObject[]): Array<Record<string, unknown>> {
  const subject = query.target.trim().replace(/^concept\s+/i, '').replace(/^world\s+/i, '').replace(/^object\s+/i, '');
  const traceSource = objects.find((object) => normalizeString(object.id).includes(normalizeString(subject)) || normalizeString(object.name).includes(normalizeString(subject)));
  if (!traceSource) {
    return [];
  }
  return getKnowledgeLineage(traceSource.id).map((node) => ({
    nodeId: node.nodeId,
    refId: node.refId,
    kind: node.kind,
    timestamp: node.timestamp,
    links: node.links,
  }));
}

function buildAggregateResults(query: UgqlQuery, objects: KnowledgeObject[]): Array<Record<string, unknown>> {
  const groupBy = query.options.groupBy ?? 'domain';
  const buckets = new Map<string, KnowledgeObject[]>();
  for (const object of objects) {
    const key = String(resolveFieldValue(object, groupBy) ?? 'unknown');
    const bucket = buckets.get(key) ?? [];
    bucket.push(object);
    buckets.set(key, bucket);
  }
  return [...buckets.entries()].map(([key, bucket]) => ({
    [groupBy]: key,
    count: bucket.length,
    averageStability: round(bucket.reduce((sum, object) => sum + object.stabilityScore, 0) / Math.max(1, bucket.length)),
    kinds: uniqueValues(bucket.map((object) => object.kind)),
  }));
}

function buildCompareResults(_query: UgqlQuery, objects: KnowledgeObject[]): Array<Record<string, unknown>> {
  if (objects.length < 2) {
    return objects.map((object) => serializeKnowledgeObject(object));
  }
  const left = objects[0]!;
  const right = objects[1]!;
  return [{
    left: serializeKnowledgeObject(left),
    right: serializeKnowledgeObject(right),
    diff: {
      stabilityScore: {
        from: left.stabilityScore,
        to: right.stabilityScore,
      },
      tagsAdded: diffSet(left.tags, right.tags),
      tagsRemoved: diffSet(right.tags, left.tags),
      conceptsAdded: diffSet(left.concepts, right.concepts),
      conceptsRemoved: diffSet(right.concepts, left.concepts),
    },
  }];
}

function applyOptions(objects: KnowledgeObject[], options: UgqlOptions): KnowledgeObject[] {
  let ordered = [...objects];
  if (options.orderBy) {
    const { field, direction } = options.orderBy;
    ordered.sort((left, right) => compareValues(resolveFieldValue(left, field), resolveFieldValue(right, field), direction));
  }
  if (typeof options.limit === 'number' && Number.isFinite(options.limit)) {
    ordered = ordered.slice(0, Math.max(0, options.limit));
  }
  return ordered;
}

function rankQueryResults(objects: KnowledgeObject[], query: UgqlQuery): KnowledgeObject[] {
  if (query.verb !== 'SEARCH') {
    return objects;
  }
  const needle = normalizeString(query.target.replace(/^docs$/i, '').trim());
  return [...objects].sort((left, right) => {
    const leftScore = searchScore(left, needle);
    const rightScore = searchScore(right, needle);
    return rightScore - leftScore;
  });
}

function searchScore(object: KnowledgeObject, needle: string): number {
  const haystack = normalizeString([
    object.id,
    object.name,
    object.summary,
    object.domain,
    object.tags.join(' '),
    object.concepts.join(' '),
    JSON.stringify(object.metadata),
  ].join(' '));
  if (!needle) {
    return 0;
  }
  const hits = haystack.split(needle).length - 1;
  return hits + (haystack.includes(needle) ? 1 : 0);
}

function applyConditions(objects: KnowledgeObject[], conditions: UgqlCondition[]): KnowledgeObject[] {
  return objects.filter((object) => conditions.every((condition) => matchesCondition(object, condition)));
}

function matchesCondition(object: KnowledgeObject, condition: UgqlCondition): boolean {
  const fieldValue = resolveFieldValue(object, condition.field);
  if (condition.operator === 'BETWEEN') {
    if (typeof fieldValue !== 'string' || !Array.isArray(condition.value)) {
      return false;
    }
    const [from, to] = condition.value;
    return fieldValue >= from && fieldValue <= to;
  }
  if (condition.operator === 'CONTAINS') {
    const needle = String(condition.value).toLowerCase();
    if (Array.isArray(fieldValue)) {
      return fieldValue.map((item) => String(item).toLowerCase()).includes(needle);
    }
    return normalizeString(fieldValue).includes(needle);
  }
  if (condition.operator === 'MATCHES') {
    return normalizeString(fieldValue).includes(normalizeString(condition.value));
  }
  if (typeof fieldValue === 'number') {
    const numeric = typeof condition.value === 'number' ? condition.value : Number(condition.value);
    if (Number.isNaN(numeric)) {
      return false;
    }
    if (condition.operator === '=') return fieldValue === numeric;
    if (condition.operator === '>') return fieldValue > numeric;
    if (condition.operator === '>=') return fieldValue >= numeric;
    if (condition.operator === '<') return fieldValue < numeric;
    if (condition.operator === '<=') return fieldValue <= numeric;
  }
  const left = normalizeString(fieldValue);
  const right = normalizeString(condition.value);
  if (condition.operator === '=') {
    return left === right;
  }
  if (condition.operator === '>') {
    return left > right;
  }
  if (condition.operator === '>=') {
    return left >= right;
  }
  if (condition.operator === '<') {
    return left < right;
  }
  if (condition.operator === '<=') {
    return left <= right;
  }
  return false;
}

function resolveFieldValue(object: KnowledgeObject, field: string): unknown {
  const normalized = field.trim().toLowerCase();
  switch (normalized) {
    case 'id':
      return object.id;
    case 'name':
      return object.name;
    case 'kind':
      return object.kind;
    case 'domain':
      return object.domain;
    case 'summary':
      return object.summary;
    case 'tags':
      return object.tags;
    case 'concepts':
      return object.concepts;
    case 'stability_score':
    case 'stabilityscore':
      return object.stabilityScore;
    case 'risk_profile':
    case 'riskprofile':
      return object.riskProfile;
    case 'lineage':
      return object.lineage;
    default:
      return object.metadata[field] ?? object.metadata[normalized] ?? undefined;
  }
}

export function parseUgql(ugql: string): UgqlQuery {
  const raw = ugql.trim();
  if (!raw) {
    throw new Error('UGQL query is required');
  }
  const compact = raw.replace(/\s+/g, ' ').trim();
  const verbMatch = compact.match(/^(SELECT|SEARCH|TRACE|AGGREGATE|COMPARE)\b/i);
  if (!verbMatch) {
    throw new Error('UGQL verb must be SELECT, SEARCH, TRACE, AGGREGATE, or COMPARE');
  }
  const verb = verbMatch[1]!.toUpperCase() as UgqlVerb;
  const fromIndex = findWordIndex(compact, 'FROM');
  const whereIndex = findWordIndex(compact, 'WHERE');
  const withIndex = findWordIndex(compact, 'WITH');
  const target = compact.slice(verbMatch[0].length, fromIndex >= 0 ? fromIndex : (whereIndex >= 0 ? whereIndex : (withIndex >= 0 ? withIndex : compact.length))).trim();
  const scope = parseScope(compact.slice(fromIndex + 4, whereIndex >= 0 ? whereIndex : (withIndex >= 0 ? withIndex : compact.length)).trim());
  const whereSection = whereIndex >= 0
    ? compact.slice(whereIndex + 5, withIndex >= 0 ? withIndex : compact.length).trim()
    : '';
  const withSection = withIndex >= 0 ? compact.slice(withIndex + 4).trim() : '';
  return {
    verb,
    target,
    scope,
    conditions: parseConditions(whereSection),
    options: parseOptions(withSection),
    raw,
  };
}

function parseScope(scope: string): KnowledgeScope {
  const normalized = scope.toLowerCase();
  if (normalized.includes('lineage')) return 'lineage';
  if (normalized.includes('mesh')) return 'mesh';
  if (normalized.includes('metrics')) return 'metrics';
  if (normalized.includes('docs')) return 'docs';
  if (normalized.includes('world')) return 'worlds';
  return 'objects';
}

function parseConditions(input: string): UgqlCondition[] {
  if (!input) {
    return [];
  }
  return splitTopLevelAnd(input).map((chunk) => {
    const between = chunk.match(/^([\w.]+)\s+BETWEEN\s+(.+)\s+AND\s+(.+)$/i);
    if (between) {
      return {
        field: between[1]!,
        operator: 'BETWEEN' as const,
        value: [stripQuotes(between[2]!), stripQuotes(between[3]!)] as [string, string],
      };
    }
    const contains = chunk.match(/^([\w.]+)\s+CONTAINS\s+(.+)$/i);
    if (contains) {
      return {
        field: contains[1]!,
        operator: 'CONTAINS' as const,
        value: stripQuotes(contains[2]!),
      };
    }
    const matches = chunk.match(/^([\w.]+)\s*~\s*(.+)$/i);
    if (matches) {
      return {
        field: matches[1]!,
        operator: 'MATCHES' as const,
        value: stripQuotes(matches[2]!),
      };
    }
    const comparison = chunk.match(/^([\w.]+)\s*(=|>=|<=|>|<)\s*(.+)$/);
    if (comparison) {
      const raw = stripQuotes(comparison[3]!);
      const numeric = Number(raw);
      return {
        field: comparison[1]!,
        operator: comparison[2] as UgqlCondition['operator'],
        value: Number.isNaN(numeric) ? raw : numeric,
      };
    }
    return {
      field: chunk,
      operator: '=',
      value: 'true',
    };
  });
}

function parseOptions(input: string): UgqlOptions {
  if (!input) {
    return {};
  }
  const options: UgqlOptions = {};
  const limit = input.match(/\bLIMIT\s+(\d+)/i);
  if (limit) {
    options.limit = Number(limit[1]);
  }
  const orderBy = input.match(/\bORDER\s+BY\s+([\w.]+)(?:\s+(ASC|DESC))?/i);
  if (orderBy) {
    options.orderBy = {
      field: orderBy[1]!,
      direction: (orderBy[2]?.toUpperCase() === 'DESC' ? 'DESC' : 'ASC'),
    };
  }
  const groupBy = input.match(/\bGROUP\s+BY\s+([\w.]+)/i);
  if (groupBy) {
    options.groupBy = groupBy[1]!;
  }
  const include = input.match(/\bINCLUDE\s+(.+?)(?:\s+LIMIT|\s+ORDER|\s+GROUP|$)/i);
  if (include) {
    options.include = include[1]!
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean);
  }
  return options;
}

function getScopeObjects(scope: KnowledgeScope): KnowledgeObject[] {
  switch (scope) {
    case 'worlds':
      return [...seedStore.worlds];
    case 'docs':
      return seedStore.objects.filter((object) => object.kind === 'document');
    case 'metrics':
      return seedStore.objects.filter((object) => object.kind === 'metric');
    case 'mesh':
      return [...seedStore.worlds];
    case 'lineage':
      return [...seedStore.objects, ...seedStore.worlds];
    case 'objects':
    default:
      return [...seedStore.objects, ...seedStore.worlds];
  }
}

function buildSeedStore(): KnowledgeStore {
  const worlds: KnowledgeWorld[] = [
    {
      id: 'world:finance',
      kind: 'world',
      name: 'FinanceWorld',
      domain: 'finance',
      summary: 'Governed finance simulation for risk, exposure, and compliance.',
      tags: ['risk', 'exposure', 'regulation'],
      concepts: ['concept:risk', 'concept:governance', 'concept:evidence'],
      stabilityScore: 0.96,
      riskProfile: 'medium',
      lineage: ['world:finance-v1'],
      metadata: { branch: 'finance-core', timestamp: '2026-07-11T18:00:00.000Z' },
      constitutionRef: 'constitution:finance',
      rules: ['rule:finance-risk-limit', 'rule:finance-audit-trace'],
      agents: ['agent:trader-bot', 'agent:regulator'],
      arenas: ['arena:market'],
      state: 'stabilized',
      historyRef: 'history:finance',
    },
    {
      id: 'world:law',
      kind: 'world',
      name: 'LawWorld',
      domain: 'law',
      summary: 'Obligation, right, interpretation, and constitutional continuity.',
      tags: ['obligation', 'rights', 'precedent'],
      concepts: ['concept:governance', 'concept:lineage', 'concept:replay'],
      stabilityScore: 0.98,
      riskProfile: 'low',
      lineage: ['world:law-v1'],
      metadata: { branch: 'law-core', timestamp: '2026-07-11T18:00:00.000Z' },
      constitutionRef: 'constitution:law',
      rules: ['rule:law-obligation', 'rule:law-precedent'],
      agents: ['agent:clerk', 'agent:judge'],
      arenas: ['arena:court'],
      state: 'stable',
      historyRef: 'history:law',
    },
    {
      id: 'world:robotics',
      kind: 'world',
      name: 'RoboticsWorld',
      domain: 'robotics',
      summary: 'Safety envelopes, collision avoidance, and controlled autonomy.',
      tags: ['safety', 'collision-avoidance', 'redundancy'],
      concepts: ['concept:safety', 'concept:risk', 'concept:replay'],
      stabilityScore: 0.93,
      riskProfile: 'high',
      lineage: ['world:robotics-v1'],
      metadata: { branch: 'robotics-safety', timestamp: '2026-07-11T18:00:00.000Z' },
      constitutionRef: 'constitution:robotics',
      rules: ['rule:robotics-safety-envelope', 'rule:robotics-collision-avoidance'],
      agents: ['agent:robot-controller'],
      arenas: ['arena:navigation'],
      state: 'simulation-ready',
      historyRef: 'history:robotics',
    },
    {
      id: 'world:climate',
      kind: 'world',
      name: 'ClimateWorld',
      domain: 'climate',
      summary: 'Long-horizon resilience, adaptation, and scenario planning.',
      tags: ['resilience', 'scenario', 'mitigation'],
      concepts: ['concept:risk', 'concept:resilience', 'concept:lineage'],
      stabilityScore: 0.9,
      riskProfile: 'critical',
      lineage: ['world:climate-v1'],
      metadata: { branch: 'climate-planning', timestamp: '2026-07-11T18:00:00.000Z' },
      constitutionRef: 'constitution:climate',
      rules: ['rule:climate-scenario', 'rule:climate-adaptation'],
      agents: ['agent:planner'],
      arenas: ['arena:scenario'],
      state: 'advisory',
      historyRef: 'history:climate',
    },
    {
      id: 'world:project-infi',
      kind: 'world',
      name: 'Project Infi',
      domain: 'project-infi',
      summary: 'Umbrella constitutional workspace for nested repos, control planes, and replay surfaces.',
      tags: ['project-infi', 'ulx', 'sovereign-ide'],
      concepts: ['concept:governance', 'concept:lineage', 'concept:trust'],
      stabilityScore: 0.97,
      riskProfile: 'medium',
      lineage: ['world:project-infi-v1'],
      metadata: { branch: 'umbrella', timestamp: '2026-07-11T18:00:00.000Z' },
      constitutionRef: 'constitution:project-infi',
      rules: ['rule:workspace-adapter', 'rule:replay-persistence'],
      agents: ['agent:ulx-ide', 'agent:control-plane'],
      arenas: ['arena:cockpit', 'arena:replay'],
      state: 'integrated',
      historyRef: 'history:project-infi',
    },
  ];

  const objects: KnowledgeObject[] = [
    ...worlds,
    conceptObject('concept:risk', 'Risk', 'Cross-domain uncertainty management with domain-specific constraints.', ['finance', 'robotics', 'climate', 'law']),
    conceptObject('concept:safety', 'Safety', 'Protection against harm and unconstitutional state changes.', ['robotics', 'operations']),
    conceptObject('concept:governance', 'Governance', 'Constitutional control over change, evidence, and authority.', ['all']),
    conceptObject('concept:lineage', 'Lineage', 'Replayable history of artifacts, decisions, and change.', ['all']),
    conceptObject('concept:replay', 'Replay', 'Deterministic reconstruction of prior state.', ['all']),
    conceptObject('concept:evidence', 'Evidence', 'Artifacts that justify constitutional claims.', ['all']),
    conceptObject('concept:trust', 'Trust', 'Bounded, evidenced, and replayable confidence.', ['all']),
    {
      id: 'doc:finance-risk-guide',
      kind: 'document',
      name: 'Finance Risk Guide',
      domain: 'finance',
      summary: 'Models credit risk, exposure, and regulatory controls.',
      tags: ['risk', 'finance', 'regulation'],
      concepts: ['concept:risk'],
      stabilityScore: 0.95,
      riskProfile: 'medium',
      lineage: ['doc:finance-risk-guide-v1'],
      metadata: { source: 'memory', kind: 'specification' },
    },
    {
      id: 'doc:robotics-safety-pack',
      kind: 'document',
      name: 'Autonomous Robotics Safety Pack',
      domain: 'robotics',
      summary: 'UPL package for safety envelope and collision avoidance rules.',
      tags: ['upl', 'safety', 'robotics'],
      concepts: ['concept:safety', 'concept:risk'],
      stabilityScore: 0.92,
      riskProfile: 'high',
      lineage: ['doc:robotics-safety-pack-v1'],
      metadata: { package: 'RoboticsDomain', spec: 'UPL' },
    },
    {
      id: 'doc:lawworld-obligation-brief',
      kind: 'document',
      name: 'LawWorld Obligation Brief',
      domain: 'law',
      summary: 'Governed obligations, rights, and precedent notes.',
      tags: ['law', 'obligation', 'precedent'],
      concepts: ['concept:governance', 'concept:lineage'],
      stabilityScore: 0.97,
      riskProfile: 'low',
      lineage: ['doc:lawworld-obligation-brief-v1'],
      metadata: { source: 'constitutional-draft' },
    },
    {
      id: 'metric:finance-var',
      kind: 'metric',
      name: 'Finance Value at Risk',
      domain: 'finance',
      summary: 'Observed loss distribution over a governed horizon.',
      tags: ['risk', 'metric'],
      concepts: ['concept:risk'],
      stabilityScore: 0.93,
      riskProfile: 'medium',
      lineage: ['metric:finance-var-v1'],
      metadata: { value: 0.71, unit: 'probability' },
    },
    {
      id: 'metric:robotics-near-miss',
      kind: 'metric',
      name: 'Robotics Near Miss Rate',
      domain: 'robotics',
      summary: 'Count of near-misses detected in simulation and runtime.',
      tags: ['safety', 'metric'],
      concepts: ['concept:safety'],
      stabilityScore: 0.91,
      riskProfile: 'high',
      lineage: ['metric:robotics-near-miss-v1'],
      metadata: { value: 0.04, unit: 'rate' },
    },
    {
      id: 'metric:climate-resilience',
      kind: 'metric',
      name: 'Climate Resilience Index',
      domain: 'climate',
      summary: 'Long-horizon resilience scoring for scenarios and adaptation.',
      tags: ['resilience', 'metric'],
      concepts: ['concept:risk'],
      stabilityScore: 0.88,
      riskProfile: 'critical',
      lineage: ['metric:climate-resilience-v1'],
      metadata: { value: 0.82, unit: 'index' },
    },
    {
      id: 'profile:prod-critical-v3',
      kind: 'profile',
      name: 'Prod-Critical',
      domain: 'project-infi',
      summary: 'Critical profile with council authority, simulation, and validation required.',
      tags: ['profile', 'critical', 'routing'],
      concepts: ['concept:governance', 'concept:trust'],
      stabilityScore: 0.99,
      riskProfile: 'critical',
      lineage: ['profile:prod-critical-v1', 'profile:prod-critical-v2'],
      metadata: { version: 'v3', authorityMode: 'COUNCIL' },
    },
    {
      id: 'profile:dev-experimental-v1',
      kind: 'profile',
      name: 'Dev-Experimental',
      domain: 'project-infi',
      summary: 'Low-risk profile with lenient execution and validation.',
      tags: ['profile', 'experimental'],
      concepts: ['concept:governance'],
      stabilityScore: 0.92,
      riskProfile: 'low',
      lineage: ['profile:dev-experimental-v0'],
      metadata: { version: 'v1', authorityMode: 'SELF' },
    },
    {
      id: 'rule:robotics-safety-envelope',
      kind: 'rule',
      name: 'SafetyEnvelopeRule',
      domain: 'robotics',
      summary: 'Protects agents by enforcing a minimum safety envelope.',
      tags: ['upl', 'rule', 'safety'],
      concepts: ['concept:safety', 'concept:risk'],
      stabilityScore: 0.94,
      riskProfile: 'high',
      lineage: ['rule:robotics-safety-envelope-v1'],
      metadata: { evidencePolicy: 'RequireSimulationCoverage' },
    },
    {
      id: 'rule:finance-risk-limit',
      kind: 'rule',
      name: 'RiskLimitRule',
      domain: 'finance',
      summary: 'Constrains exposure under governance-defined thresholds.',
      tags: ['rule', 'finance'],
      concepts: ['concept:risk', 'concept:governance'],
      stabilityScore: 0.95,
      riskProfile: 'medium',
      lineage: ['rule:finance-risk-limit-v1'],
      metadata: { evidencePolicy: 'RequireAuditLog' },
    },
    {
      id: 'arena:market',
      kind: 'arena',
      name: 'MarketArena',
      domain: 'finance',
      summary: 'Governed market interaction space for finance simulations.',
      tags: ['arena', 'simulation'],
      concepts: ['concept:governance'],
      stabilityScore: 0.91,
      riskProfile: 'medium',
      lineage: ['arena:market-v1'],
      metadata: { participants: ['agent:trader-bot', 'agent:regulator'] },
    },
    {
      id: 'arena:navigation',
      kind: 'arena',
      name: 'NavigationArena',
      domain: 'robotics',
      summary: 'Safety-governed robot navigation arena.',
      tags: ['arena', 'robotics'],
      concepts: ['concept:safety'],
      stabilityScore: 0.92,
      riskProfile: 'high',
      lineage: ['arena:navigation-v1'],
      metadata: { participants: ['agent:robot-controller'] },
    },
    {
      id: 'agent:ulx-ide',
      kind: 'agent',
      name: 'ULX IDE',
      domain: 'project-infi',
      summary: 'Execution arena surface for governed replay and file operations.',
      tags: ['ulx', 'agent', 'desktop'],
      concepts: ['concept:replay', 'concept:lineage'],
      stabilityScore: 0.97,
      riskProfile: 'medium',
      lineage: ['agent:ulx-ide-v1'],
      metadata: { type: 'desktop-shell' },
    },
    {
      id: 'agent:control-plane',
      kind: 'agent',
      name: 'Sovereign Control Plane',
      domain: 'project-infi',
      summary: 'Backend control plane for governance, replay, and knowledge surfaces.',
      tags: ['control-plane', 'service'],
      concepts: ['concept:governance', 'concept:lineage'],
      stabilityScore: 0.98,
      riskProfile: 'medium',
      lineage: ['agent:control-plane-v1'],
      metadata: { type: 'service' },
    },
    {
      id: 'constitution:project-infi',
      kind: 'constitution',
      name: 'Project Infi Constitution',
      domain: 'project-infi',
      summary: 'Constitutional minimalism, authoritative homes, replayable change.',
      tags: ['constitution', 'governance'],
      concepts: ['concept:governance', 'concept:lineage'],
      stabilityScore: 0.99,
      riskProfile: 'low',
      lineage: ['constitution:project-infi-v1'],
      metadata: { principles: ['constitutional minimalism', 'one authoritative home'] },
    },
    {
      id: 'package:robotics-safety-pack',
      kind: 'package',
      name: 'Autonomous Robotics Safety Pack',
      domain: 'robotics',
      summary: 'UPL package with robotics domain, governance, rules, agents, and arenas.',
      tags: ['upl', 'package'],
      concepts: ['concept:safety', 'concept:governance'],
      stabilityScore: 0.94,
      riskProfile: 'high',
      lineage: ['package:robotics-safety-pack-v1'],
      metadata: { format: 'UPL', spec: 'autonomous robotics safety' },
    },
    {
      id: 'crf:prod-critical-incident',
      kind: 'crf',
      name: 'Prod-Critical Incident Replay File',
      domain: 'project-infi',
      summary: 'Portable constitutional artifact for replaying a governance tightening event.',
      tags: ['crf', 'replay', 'incident-123'],
      concepts: ['concept:replay', 'concept:lineage', 'concept:governance'],
      stabilityScore: 0.96,
      riskProfile: 'medium',
      lineage: ['crf:prod-critical-incident-v1'],
      metadata: { incidentRef: 'incident-123', profile: 'profile-prod-critical' },
    },
  ];

  const ledgerEntries: ConstitutionalChangeLedgerEntry[] = [
    createLedgerEntry({
      entryId: 'entry-021',
      timestamp: '2026-06-01T12:00:00.000Z',
      changeType: 'PROFILE_CREATED',
      artifactRef: 'profile:prod-critical-v1',
      domain: 'project-infi',
      subsystem: 'governance',
      tags: ['profile', 'bootstrap'],
      previousVersion: null,
      justificationEvidence: ['ev-profile-bootstrap-001'],
      relatedIncidents: [],
      councilVote: { for: 5, against: 0, abstain: 0 },
      beforeState: baselineGovernanceState(),
      afterState: {
        timestamp: '2026-06-01T12:00:00.000Z',
        profiles: ['profile:prod-critical-v1', 'profile:dev-experimental-v1'],
        rules: ['rule:finance-risk-limit', 'rule:robotics-safety-envelope'],
        stewardContracts: ['contract:steward-001'],
        constitutionClauses: ['clause-12', 'clause-19'],
        authorityModes: ['ROLE_BASED'],
        arenas: ['arena:market', 'arena:navigation'],
        intentChains: { 'intent-987': ['entry-021'] },
      },
      intentIds: ['intent-987'],
    }),
    createLedgerEntry({
      entryId: 'entry-033',
      timestamp: '2026-07-08T15:00:00.000Z',
      changeType: 'RULE_CREATED',
      artifactRef: 'rule:robotics-safety-envelope',
      domain: 'robotics',
      subsystem: 'runtime',
      tags: ['incident-123', 'safety'],
      previousVersion: 'entry-021',
      justificationEvidence: ['ev-incident-123', 'ev-simulation-coverage-001'],
      relatedIncidents: ['incident-123'],
      councilVote: { for: 4, against: 1, abstain: 0 },
      beforeState: {
        timestamp: '2026-07-08T14:59:59.000Z',
        profiles: ['profile:prod-critical-v1', 'profile:dev-experimental-v1'],
        rules: ['rule:finance-risk-limit'],
        stewardContracts: ['contract:steward-001'],
        constitutionClauses: ['clause-12', 'clause-19'],
        authorityModes: ['ROLE_BASED'],
        arenas: ['arena:market'],
        intentChains: { 'intent-987': ['entry-021'] },
      },
      afterState: {
        timestamp: '2026-07-08T15:00:00.000Z',
        profiles: ['profile:prod-critical-v2', 'profile:dev-experimental-v1'],
        rules: ['rule:finance-risk-limit', 'rule:robotics-safety-envelope'],
        stewardContracts: ['contract:steward-001'],
        constitutionClauses: ['clause-12', 'clause-19'],
        authorityModes: ['ROLE_BASED'],
        arenas: ['arena:market', 'arena:navigation'],
        intentChains: { 'intent-987': ['entry-021', 'entry-033'] },
      },
      intentIds: ['intent-987', 'intent-992'],
    }),
    createLedgerEntry({
      entryId: 'entry-044',
      timestamp: '2026-07-11T19:10:00.000Z',
      changeType: 'PROFILE_MODIFIED',
      artifactRef: 'profile:prod-critical-v3',
      domain: 'project-infi',
      subsystem: 'governance',
      tags: ['incident-123', 'routing', 'simulation'],
      previousVersion: 'entry-033',
      justificationEvidence: ['ev-profile-change-001', 'ev-incident-123', 'ev-replay-044'],
      relatedIncidents: ['incident-123'],
      councilVote: { for: 5, against: 1, abstain: 0 },
      beforeState: {
        timestamp: '2026-07-11T18:59:59.000Z',
        profiles: ['profile:prod-critical-v2', 'profile:dev-experimental-v1'],
        rules: ['rule:finance-risk-limit', 'rule:robotics-safety-envelope'],
        stewardContracts: ['contract:steward-001'],
        constitutionClauses: ['clause-12', 'clause-19'],
        authorityModes: ['ROLE_BASED'],
        arenas: ['arena:market', 'arena:navigation'],
        intentChains: { 'intent-987': ['entry-021', 'entry-033'] },
      },
      afterState: {
        timestamp: '2026-07-11T19:10:00.000Z',
        profiles: ['profile:prod-critical-v3', 'profile:dev-experimental-v1'],
        rules: ['rule:finance-risk-limit', 'rule:robotics-safety-envelope'],
        stewardContracts: ['contract:steward-001'],
        constitutionClauses: ['clause-12', 'clause-19'],
        authorityModes: ['COUNCIL'],
        arenas: ['arena:market', 'arena:navigation', 'arena:simulation', 'arena:validation'],
        intentChains: { 'intent-987': ['entry-021', 'entry-033', 'entry-044'] },
      },
      intentIds: ['intent-987'],
    }),
    createLedgerEntry({
      entryId: 'entry-055',
      timestamp: '2026-07-11T19:15:00.000Z',
      changeType: 'STEWARD_CONTRACT_UPDATED',
      artifactRef: 'contract:steward-001',
      domain: 'project-infi',
      subsystem: 'governance',
      tags: ['steward', 'contract'],
      previousVersion: 'entry-044',
      justificationEvidence: ['ev-contract-001'],
      relatedIncidents: ['incident-123'],
      councilVote: { for: 6, against: 0, abstain: 0 },
      beforeState: {
        timestamp: '2026-07-11T19:10:00.000Z',
        profiles: ['profile:prod-critical-v3', 'profile:dev-experimental-v1'],
        rules: ['rule:finance-risk-limit', 'rule:robotics-safety-envelope'],
        stewardContracts: ['contract:steward-001'],
        constitutionClauses: ['clause-12', 'clause-19'],
        authorityModes: ['COUNCIL'],
        arenas: ['arena:market', 'arena:navigation', 'arena:simulation', 'arena:validation'],
        intentChains: { 'intent-987': ['entry-021', 'entry-033', 'entry-044'] },
      },
      afterState: {
        timestamp: '2026-07-11T19:15:00.000Z',
        profiles: ['profile:prod-critical-v3', 'profile:dev-experimental-v1'],
        rules: ['rule:finance-risk-limit', 'rule:robotics-safety-envelope'],
        stewardContracts: ['contract:steward-001-v2'],
        constitutionClauses: ['clause-12', 'clause-19', 'clause-31'],
        authorityModes: ['COUNCIL'],
        arenas: ['arena:market', 'arena:navigation', 'arena:simulation', 'arena:validation'],
        intentChains: { 'intent-987': ['entry-021', 'entry-033', 'entry-044', 'entry-055'] },
      },
      intentIds: ['intent-987'],
    }),
  ];

  const crfArtifacts: CrfArtifact[] = [
    {
      id: 'crf:prod-critical-incident',
      profile: 'profile:prod-critical-v3',
      environment: 'project-infi',
      incidentRef: 'incident-123',
      hash: stableHash({
        id: 'crf:prod-critical-incident',
        profile: 'profile:prod-critical-v3',
        incidentRef: 'incident-123',
      }),
      signature: stableHash({
        kind: 'crf-signature',
        id: 'crf:prod-critical-incident',
      }),
      timeline: [
        { timestamp: '2026-07-11T18:59:59.000Z', event: 'pre-change-state', state: 'role-based routing' },
        { timestamp: '2026-07-11T19:10:00.000Z', event: 'profile-tightened', state: 'simulation-required' },
        { timestamp: '2026-07-11T19:15:00.000Z', event: 'ledger-committed', state: 'council-governed' },
      ],
      governanceState: cloneSnapshot(ledgerEntries[2]!.afterState),
      impact: {
        affectedProfiles: ['profile:prod-critical-v3'],
        affectedRules: ['rule:robotics-safety-envelope'],
        affectedArenas: ['arena:simulation', 'arena:validation'],
        affectedAuthorityModes: ['COUNCIL'],
        affectedIntents: ['intent-987'],
      },
      lineage: {
        previousVersion: 'crf:prod-critical-incident-v1',
        evidenceIds: ['ev-profile-change-001', 'ev-incident-123', 'ev-replay-044'],
        councilVote: { for: 5, against: 1, abstain: 0 },
      },
    },
  ];

  const meshLinks: KnowledgeMeshLink[] = [
    { fromWorldId: 'world:finance', toWorldId: 'world:law', similarity: 0.81, stability: 0.93, reason: 'regulation and audit lineage' },
    { fromWorldId: 'world:finance', toWorldId: 'world:project-infi', similarity: 0.74, stability: 0.95, reason: 'governed ledger and replay path' },
    { fromWorldId: 'world:robotics', toWorldId: 'world:project-infi', similarity: 0.77, stability: 0.92, reason: 'runtime control, evidence, and safety gates' },
    { fromWorldId: 'world:climate', toWorldId: 'world:project-infi', similarity: 0.7, stability: 0.9, reason: 'scenario planning and risk propagation' },
    { fromWorldId: 'world:robotics', toWorldId: 'world:finance', similarity: 0.68, stability: 0.88, reason: 'risk envelope and constraint enforcement' },
  ];

  const lineage: KnowledgeLineageNode[] = [
    {
      nodeId: 'node-concept-risk',
      refId: 'concept:risk',
      kind: 'concept-lineage',
      timestamp: '2026-07-11T18:00:00.000Z',
      links: [
        { relationType: 'SIMILAR_TO', targetNodeId: 'doc:finance-risk-guide' },
        { relationType: 'SIMILAR_TO', targetNodeId: 'doc:robotics-safety-pack' },
        { relationType: 'SIMILAR_TO', targetNodeId: 'metric:climate-resilience' },
      ],
    },
    {
      nodeId: 'node-profile-prod-critical-v3',
      refId: 'profile:prod-critical-v3',
      kind: 'profile',
      timestamp: '2026-07-11T19:10:00.000Z',
      links: [
        { relationType: 'SUPERSEDES', targetNodeId: 'profile:prod-critical-v2' },
        { relationType: 'JUSTIFIED_BY', targetNodeId: 'incident-123' },
      ],
    },
    {
      nodeId: 'node-entry-044',
      refId: 'entry-044',
      kind: 'change-ledger',
      timestamp: '2026-07-11T19:10:00.000Z',
      links: [
        { relationType: 'RESPONDS_TO', targetNodeId: 'incident-123' },
        { relationType: 'PRECEDES', targetNodeId: 'node-entry-055' },
      ],
    },
    {
      nodeId: 'incident-123',
      refId: 'incident-123',
      kind: 'incident',
      timestamp: '2026-07-11T18:58:00.000Z',
      links: [
        { relationType: 'RESPONDS_TO', targetNodeId: 'entry-033' },
      ],
    },
  ];

  return {
    worlds,
    objects,
    meshLinks,
    lineage,
    ledgerEntries,
    uplModules: [
      {
        id: 'upl:robotics-domain',
        name: 'RoboticsDomain',
        kind: 'domain',
        domain: 'robotics',
        summary: 'UPL domain module for robotics safety, collision avoidance, and risk control.',
        concepts: ['concept:safety', 'concept:risk', 'concept:trust'],
        rules: ['rule:robotics-safety-envelope'],
        worlds: ['world:robotics'],
        evidencePolicies: ['RequireSimulationCoverage', 'RequireIncidentLog'],
        authorityModes: ['steward', 'council'],
      },
      {
        id: 'upl:core-governance',
        name: 'CoreGovernance',
        kind: 'governance',
        domain: 'project-infi',
        summary: 'Governance module for replayable, evidence-backed change.',
        concepts: ['concept:governance', 'concept:lineage'],
        rules: ['rule:finance-risk-limit', 'rule:robotics-safety-envelope'],
        worlds: ['world:project-infi'],
        evidencePolicies: ['RequireAuditLog', 'RequireSimulationCoverage'],
        authorityModes: ['SELF', 'ROLE_BASED', 'COUNCIL'],
      },
      {
        id: 'upl:robotics-world-pack',
        name: 'RoboticsWorldPack',
        kind: 'world',
        domain: 'robotics',
        summary: 'World pack for the autonomous robotics safety scenario.',
        concepts: ['concept:safety', 'concept:risk'],
        rules: ['rule:robotics-safety-envelope'],
        worlds: ['world:robotics'],
        evidencePolicies: ['RequireSimulationCoverage'],
        authorityModes: ['steward'],
      },
    ],
    crfArtifacts,
  };
}

function conceptObject(id: string, name: string, summary: string, domains: string[]): KnowledgeObject {
  return {
    id,
    kind: 'concept',
    name,
    domain: domains[0] ?? 'global',
    summary,
    tags: [name.toLowerCase(), ...domains],
    concepts: [],
    stabilityScore: 0.99,
    riskProfile: 'low',
    lineage: [`${id}-v1`],
    metadata: { domains },
  };
}

function createLedgerEntry(input: ConstitutionalChangeLedgerSeed): ConstitutionalChangeLedgerEntry {
  return {
    ...input,
    lineage: {
      previousVersion: input.previousVersion,
      justificationEvidence: [...input.justificationEvidence],
      relatedIncidents: [...input.relatedIncidents],
      councilVote: { ...input.councilVote },
    },
    hash: stableHash({
      entryId: input.entryId,
      timestamp: input.timestamp,
      changeType: input.changeType,
      artifactRef: input.artifactRef,
      previousVersion: input.previousVersion,
    }),
    signature: stableHash({
      kind: 'ledger-signature',
      entryId: input.entryId,
      artifactRef: input.artifactRef,
    }),
  };
}

function baselineGovernanceState(): GovernanceStateSnapshot {
  return {
    timestamp: '2026-01-01T00:00:00.000Z',
    profiles: ['profile:dev-experimental-v1'],
    rules: ['rule:finance-risk-limit'],
    stewardContracts: ['contract:steward-001'],
    constitutionClauses: ['clause-12'],
    authorityModes: ['SELF'],
    arenas: ['arena:market'],
    intentChains: {},
  };
}

function cloneSnapshot(snapshot: GovernanceStateSnapshot): GovernanceStateSnapshot {
  return {
    timestamp: snapshot.timestamp,
    profiles: [...snapshot.profiles],
    rules: [...snapshot.rules],
    stewardContracts: [...snapshot.stewardContracts],
    constitutionClauses: [...snapshot.constitutionClauses],
    authorityModes: [...snapshot.authorityModes],
    arenas: [...snapshot.arenas],
    intentChains: Object.fromEntries(Object.entries(snapshot.intentChains).map(([key, value]) => [key, [...value]])),
  };
}

function timelineGraphFromLedgerEntry(entry: ConstitutionalChangeLedgerEntry): KnowledgeLineageNode[] {
  return [
    {
      nodeId: `${entry.entryId}-node`,
      refId: entry.entryId,
      kind: 'change-ledger',
      timestamp: entry.timestamp,
      links: [
        ...(entry.lineage.previousVersion ? [{ relationType: 'SUPERSEDES' as const, targetNodeId: `${entry.lineage.previousVersion}-node` }] : []),
        ...entry.lineage.relatedIncidents.map((incident) => ({
          relationType: 'RESPONDS_TO' as const,
          targetNodeId: incident,
        })),
      ],
    },
  ];
}

function diffNamedCollections(left: string[], right: string[], prefix: string): Array<Record<string, unknown>> {
  const leftSet = new Set(left);
  const rightSet = new Set(right);
  const names = new Set([...leftSet, ...rightSet]);
  return [...names].map((name) => ({
    [`${prefix}_id`]: name,
    changes: {
      state: {
        from: leftSet.has(name) ? 'present' : null,
        to: rightSet.has(name) ? 'present' : null,
      },
    },
  }));
}

function uniqueValues(values: string[]): string[] {
  return [...new Set(values)];
}

function compareValues(left: unknown, right: unknown, direction: 'ASC' | 'DESC'): number {
  const leftValue = normalizeComparable(left);
  const rightValue = normalizeComparable(right);
  if (leftValue < rightValue) {
    return direction === 'DESC' ? 1 : -1;
  }
  if (leftValue > rightValue) {
    return direction === 'DESC' ? -1 : 1;
  }
  return 0;
}

function normalizeComparable(value: unknown): string | number {
  if (typeof value === 'number') {
    return value;
  }
  return String(value ?? '').toLowerCase();
}

function serializeKnowledgeObject(object: KnowledgeObject, include: string[] | undefined = undefined): Record<string, unknown> {
  const serialized: Record<string, unknown> = {
    id: object.id,
    kind: object.kind,
    name: object.name,
    domain: object.domain,
    summary: object.summary,
    tags: [...object.tags],
    concepts: [...object.concepts],
    stabilityScore: object.stabilityScore,
    riskProfile: object.riskProfile,
  };
  if (!include || include.length === 0 || include.includes('lineage')) {
    serialized.lineage = [...object.lineage];
  }
  if (include?.includes('metadata') ?? true) {
    serialized.metadata = sortValue(object.metadata);
  }
  return serialized;
}

function normalizeString(value: unknown): string {
  return String(value ?? '').toLowerCase();
}

function stripQuotes(value: string): string {
  return value.trim().replace(/^['"]|['"]$/g, '');
}

function splitTopLevelAnd(input: string): string[] {
  const result: string[] = [];
  let current = '';
  let quote: string | null = null;
  for (let index = 0; index < input.length; index += 1) {
    const char = input[index]!;
    if ((char === '"' || char === '\'') && input[index - 1] !== '\\') {
      quote = quote === char ? null : quote ?? char;
      current += char;
      continue;
    }
    if (!quote && input.slice(index, index + 5).toUpperCase() === ' AND ') {
      result.push(current.trim());
      current = '';
      index += 4;
      continue;
    }
    current += char;
  }
  if (current.trim()) {
    result.push(current.trim());
  }
  return result;
}

function findWordIndex(text: string, word: string): number {
  const match = new RegExp(`\\b${word}\\b`, 'i').exec(text);
  return match?.index ?? -1;
}

function sortValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => sortValue(item));
  }
  if (!value || typeof value !== 'object') {
    return value;
  }
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>).sort()) {
    const next = (value as Record<string, unknown>)[key];
    if (next !== undefined) {
      sorted[key] = sortValue(next);
    }
  }
  return sorted;
}

function stableHash(value: unknown): string {
  return crypto.createHash('sha256').update(JSON.stringify(sortValue(value))).digest('hex');
}

function diffSet(from: string[], to: string[]): string[] {
  const set = new Set(to);
  return from.filter((item) => !set.has(item));
}

function round(value: number): number {
  return Number(value.toFixed(4));
}
