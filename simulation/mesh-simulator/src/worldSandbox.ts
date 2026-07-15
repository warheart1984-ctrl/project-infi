import { createHash } from 'node:crypto';
import { writeFile } from 'node:fs/promises';

export type DomainName = 'law' | 'medicine' | 'science' | 'economics' | 'society' | 'custom';
export type MandalaDecisionLabel = 'approve' | 'reject' | 'neutral';
export type DomainNodeDecisionLabel =
  | 'approve'
  | 'reject'
  | 'needs_revision'
  | 'unsafe'
  | 'unsafe_policy'
  | 'insufficient_evidence'
  | 'not_applicable';

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue =
  | JsonPrimitive
  | readonly JsonValue[]
  | { readonly [key: string]: JsonValue };

export interface ExperimentIntent {
  description: string;
  domain: DomainName;
  authority: string;
  purpose?: string;
  justification?: string;
}

export interface ExperimentValidation {
  required_metrics: readonly string[];
}

export interface ExperimentSpec {
  operation: string;
  model_ref: string;
  inputs: Record<string, JsonValue>;
  parameters: Record<string, JsonValue>;
  constraints?: Record<string, JsonValue>;
  validation?: ExperimentValidation;
  code_version?: string;
}

export interface ExperimentSubmission {
  world_id: string;
  intent: ExperimentIntent;
  spec: ExperimentSpec;
}

export interface MandalaContext {
  world: WorldContract;
  experiment: {
    world_id: string;
    domain: DomainName;
    intent: ExperimentIntent;
    spec: ExperimentSpec;
    metrics: Record<string, number>;
  };
}

export interface WorldRole {
  role_id: string;
  permissions: readonly string[];
}

export interface WorldModel {
  model_id: string;
  type: string;
  version: string;
  parameters: Record<string, JsonValue>;
}

export interface WorldContractSchema {
  version: string;
  world_id: string;
  domain: DomainName;
  description: string;
  constitution: {
    principles: readonly string[];
    contracts: {
      ILC: 'enabled' | 'disabled';
      CIC: 'enabled' | 'disabled';
      CCC: 'enabled' | 'disabled';
    };
  };
  sandbox: {
    isolation: {
      cpu_limit: string;
      memory_limit: string;
      network: string;
      filesystem: string;
    };
    execution: {
      allowed_operations: readonly string[];
      max_runtime_ms: number;
      max_experiments_per_step: number;
    };
  };
  simulation: {
    engine: string;
    models: readonly WorldModel[];
    state: {
      initial: Record<string, JsonValue>;
      schema: Record<string, JsonValue>;
    };
  };
  governance: {
    authority: {
      roles: readonly WorldRole[];
    };
    intent_rules: {
      require_description: boolean;
      require_domain_alignment: boolean;
      require_authority: boolean;
      require_evidence: boolean;
    };
    evidence_rules: {
      record_all_transitions: boolean;
      record_inputs: boolean;
      record_outputs: boolean;
      record_code_version: boolean;
      record_parameters: boolean;
    };
  };
  interfaces: {
    submit_intent: string;
    submit_experiment: string;
    get_state: string;
    get_evidence: string;
  };
  lineage: {
    ledger_type: 'CSR';
    record_format: {
      timestamp: 'float';
      intent: Record<string, JsonValue>;
      inputs: Record<string, JsonValue>;
      outputs: Record<string, JsonValue>;
      model_version: string;
      authority: string;
      justification: string;
    };
  };
}

export interface WorldContract {
  world_contract: WorldContractSchema;
}

export interface MandalaNodeDecision {
  [key: string]: JsonValue | undefined;
}

export abstract class MandalaNode {
  protected readonly state: Record<string, JsonValue>;

  protected constructor(
    public readonly node_id: string,
    public readonly node_type: string,
    state: Record<string, JsonValue> = {},
  ) {
    this.state = { ...state };
  }

  abstract decide(context: MandalaContext): MandalaNodeDecision;
}

function readExperimentDomain(experiment: MandalaContext['experiment']): DomainName {
  return experiment.domain;
}

function hasTruthyText(value: unknown): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

function asRecord(value: unknown): Record<string, JsonValue> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, JsonValue>)
    : {};
}

function asArray(value: unknown): readonly JsonValue[] {
  return Array.isArray(value) ? (value as readonly JsonValue[]) : [];
}

function decisionPolarity(decision: MandalaNodeDecision): number {
  const values = Object.values(decision);
  if (values.some((value) => value === 'approve')) {
    return 1;
  }
  if (
    values.some(
      (value) =>
        value === 'reject' ||
        value === 'unsafe' ||
        value === 'unsafe_policy' ||
        value === 'insufficient_evidence',
    )
  ) {
    return -1;
  }
  return 0;
}

export class LawRuleNode extends MandalaNode {
  constructor(node_id: string) {
    super(node_id, 'LAW_RULE_NODE');
  }

  decide(context: MandalaContext): MandalaNodeDecision {
    const exp = context.experiment;
    if (readExperimentDomain(exp) !== 'law') {
      return { law_rule: 'not_applicable' };
    }

    const spec = exp.spec;
    const operation = spec.operation;
    const inputs = spec.inputs;
    const intent = exp.intent;

    const authority = intent.authority;
    if (!['judge', 'law_researcher', 'policy_analyst'].includes(authority)) {
      return { law_rule: 'reject', reason: 'invalid_authority' };
    }

    if (!['case_simulation', 'precedent_analysis', 'policy_stress_test'].includes(operation)) {
      return { law_rule: 'reject', reason: 'invalid_operation' };
    }

    if (operation === 'case_simulation') {
      const caseData = asRecord(inputs.case);
      if (!hasTruthyText(caseData.facts) && asArray(caseData.facts).length === 0) {
        return { law_rule: 'needs_revision', reason: 'missing_case_facts_or_issues' };
      }
      if (!hasTruthyText(caseData.issues) && asArray(caseData.issues).length === 0) {
        return { law_rule: 'needs_revision', reason: 'missing_case_facts_or_issues' };
      }
      if (!hasTruthyText(caseData.jurisdiction)) {
        return { law_rule: 'reject', reason: 'missing_jurisdiction' };
      }
    }

    if (operation === 'precedent_analysis') {
      const precedents = asArray(inputs.precedents);
      if (precedents.length === 0) {
        return { law_rule: 'needs_revision', reason: 'no_precedents_provided' };
      }
    }

    if (operation === 'policy_stress_test') {
      const policy = asRecord(inputs.policy);
      const rightsImpact = typeof policy.rights_impact === 'string' ? policy.rights_impact : 'unknown';
      if (rightsImpact === 'severe') {
        return { law_rule: 'unsafe_policy', reason: 'rights_impact_too_high' };
      }
      if (!hasTruthyText(policy.text)) {
        return { law_rule: 'needs_revision', reason: 'policy_text_missing' };
      }
    }

    const evidence = asArray(spec.validation?.required_metrics ?? []);
    if (evidence.length === 0) {
      return { law_rule: 'reject', reason: 'no_required_metrics' };
    }

    return { law_rule: 'approve', reason: 'constitutional_requirements_met' };
  }
}

export class MedProtocolNode extends MandalaNode {
  constructor(node_id: string) {
    super(node_id, 'MED_PROTOCOL_NODE');
  }

  decide(context: MandalaContext): MandalaNodeDecision {
    const exp = context.experiment;
    if (readExperimentDomain(exp) !== 'medicine') {
      return { med_protocol: 'not_applicable' };
    }

    const spec = exp.spec;
    const inputs = spec.inputs;
    const protocol = asRecord(inputs.protocol);
    const treatment = asRecord(inputs.treatment);
    const cohort = asRecord(inputs.cohort);

    for (const field of ['drug', 'dose', 'schedule'] as const) {
      if (!(field in treatment)) {
        return { med_protocol: 'needs_revision', reason: `missing_${field}` };
      }
    }

    const dose = typeof treatment.dose === 'number' ? treatment.dose : Number(treatment.dose);
    if (!Number.isFinite(dose) || dose <= 0 || dose > 1000) {
      return { med_protocol: 'reject', reason: 'dose_out_of_bounds' };
    }

    const risk = typeof cohort.risk_profile === 'string' ? cohort.risk_profile : 'unknown';
    if (risk === 'high') {
      return { med_protocol: 'unsafe', reason: 'cohort_risk_high' };
    }

    const ethicsClearance = protocol.ethics_clearance === true;
    if (!ethicsClearance) {
      return { med_protocol: 'reject', reason: 'no_ethics_clearance' };
    }

    return { med_protocol: 'approve', reason: 'protocol_valid' };
  }
}

export class SciModelNode extends MandalaNode {
  constructor(node_id: string) {
    super(node_id, 'SCI_MODEL_NODE');
  }

  decide(context: MandalaContext): MandalaNodeDecision {
    const exp = context.experiment;
    if (readExperimentDomain(exp) !== 'science') {
      return { sci_model: 'not_applicable' };
    }

    const spec = exp.spec;
    const inputs = spec.inputs;
    const hypothesis = asRecord(inputs.hypothesis);
    const model = asRecord(inputs.model);
    const params = spec.parameters;

    if (hypothesis.testable !== true) {
      return { sci_model: 'reject', reason: 'hypothesis_not_falsifiable' };
    }

    if (!('equations' in model)) {
      return { sci_model: 'needs_revision', reason: 'model_missing_equations' };
    }

    for (const [key, value] of Object.entries(params)) {
      if (typeof value === 'number' && Math.abs(value) > 1e9) {
        return { sci_model: 'reject', reason: `parameter_${key}_out_of_bounds` };
      }
    }

    const measurements = asArray(inputs.measurements);
    if (measurements.length === 0) {
      return { sci_model: 'needs_revision', reason: 'missing_measurements' };
    }

    return { sci_model: 'approve', reason: 'model_consistent' };
  }
}

export class EcoPolicyNode extends MandalaNode {
  constructor(node_id: string) {
    super(node_id, 'ECO_POLICY_NODE');
  }

  decide(context: MandalaContext): MandalaNodeDecision {
    const exp = context.experiment;
    if (readExperimentDomain(exp) !== 'economics') {
      return { eco_policy: 'not_applicable' };
    }

    const spec = exp.spec;
    const inputs = spec.inputs;
    const policy = asRecord(inputs.policy);
    const market = asRecord(inputs.market);
    const agents = asArray(inputs.agents);

    if (policy.incentive_distortion === 'high') {
      return { eco_policy: 'reject', reason: 'incentive_distortion_high' };
    }

    const volatility = typeof market.volatility === 'number' ? market.volatility : 0;
    if (volatility > 0.8) {
      return { eco_policy: 'unsafe', reason: 'market_too_volatile' };
    }

    const unfairAgents = agents.filter((agent) => {
      const entry = asRecord(agent);
      return entry.strategy === 'exploit';
    });
    if (unfairAgents.length > 0) {
      return { eco_policy: 'needs_revision', reason: 'unfair_agent_strategies' };
    }

    if (!('rules' in market)) {
      return { eco_policy: 'reject', reason: 'missing_market_rules' };
    }

    return { eco_policy: 'approve', reason: 'policy_stable' };
  }
}

export class ConsensusNode extends MandalaNode {
  constructor(node_id = 'CONSENSUS_NODE') {
    super(node_id, 'CONSENSUS_NODE');
  }

  decide(): MandalaNodeDecision {
    return { consensus: 'neutral' };
  }
}

export interface MandalaEdge {
  source: string;
  target: string;
  weight?: number;
  relation?: 'influence' | 'constraint' | 'delegation';
}

export interface MandalaEvaluationResult {
  node_decisions: Record<string, MandalaNodeDecision>;
  influence: Record<string, number>;
  mandala_decision: MandalaDecisionLabel;
  score: number;
}

export class MandalaBrainV2 {
  constructor(
    public readonly nodes: Record<string, MandalaNode>,
    public readonly edges: readonly MandalaEdge[],
  ) {}

  propagate(context: MandalaContext): Record<string, number> {
    const influence: Record<string, number> = Object.fromEntries(
      Object.keys(this.nodes).map((node_id) => [node_id, 0]),
    );
    const nodeDecisions = this.evaluateNodes(context);

    for (const edge of this.edges) {
      const decision = nodeDecisions[edge.source];
      if (!decision) {
        continue;
      }
      const weight = typeof edge.weight === 'number' ? edge.weight : 1;
      const polarity = decisionPolarity(decision);
      if (polarity !== 0) {
        influence[edge.target] = (influence[edge.target] ?? 0) + polarity * weight;
      }
    }

    return influence;
  }

  consensus(influence: Record<string, number>): { mandala_decision: MandalaDecisionLabel; score: number } {
    const score = Object.values(influence).reduce((sum, value) => sum + value, 0);
    if (score > 0) {
      return { mandala_decision: 'approve', score };
    }
    if (score < 0) {
      return { mandala_decision: 'reject', score };
    }
    return { mandala_decision: 'neutral', score };
  }

  evaluate(context: MandalaContext): MandalaEvaluationResult {
    const node_decisions = this.evaluateNodes(context);
    const influence = this.propagate(context);
    const consensus = this.consensus(influence);
    return {
      node_decisions,
      influence,
      mandala_decision: consensus.mandala_decision,
      score: consensus.score,
    };
  }

  evaluateNodes(context: MandalaContext): Record<string, MandalaNodeDecision> {
    const node_decisions: Record<string, MandalaNodeDecision> = {};
    for (const [node_id, node] of Object.entries(this.nodes)) {
      node_decisions[node_id] = node.decide(context);
    }
    return node_decisions;
  }
}

export interface WorldStateSnapshot {
  world_id: string;
  domain: DomainName;
  nodes: Record<string, MandalaNodeDecision>;
  influence: Record<string, number>;
  mandala_decision: MandalaDecisionLabel;
  score: number;
  latest_record_id?: string;
  latest_result?: Record<string, JsonValue>;
}

export class WorldStateEngine {
  apply_mandala_decisions(world: WorldContract, decisions: Record<string, MandalaNodeDecision>): WorldContract {
    const clone = structuredClone(world);
    const schema = clone.world_contract;

    if (schema.domain === 'medicine') {
      const medDecisions = Object.values(decisions);
      const unsafe = medDecisions.some((decision) => decision.med_protocol === 'unsafe');
      const approved = medDecisions.some((decision) => decision.med_protocol === 'approve');
      if (unsafe) {
        schema.sandbox.execution.max_runtime_ms = 1000;
      } else if (approved) {
        schema.sandbox.execution.max_runtime_ms = 5000;
      }
    }

    if (schema.domain === 'economics') {
      const ecoDecisions = Object.values(decisions);
      const unsafe = ecoDecisions.some((decision) => decision.eco_policy === 'unsafe');
      const approved = ecoDecisions.some((decision) => decision.eco_policy === 'approve');
      const model = schema.simulation.models[0];
      if (model) {
        const parameters = { ...model.parameters };
        if (unsafe) {
          parameters.risk_limit = 0.1;
        } else if (approved) {
          parameters.risk_limit = 0.5;
        }
        schema.simulation.models = [{ ...model, parameters }];
      }
    }

    if (schema.domain === 'science') {
      const sciDecisions = Object.values(decisions);
      const rejected = sciDecisions.some((decision) => decision.sci_model === 'reject');
      const approved = sciDecisions.some((decision) => decision.sci_model === 'approve');
      schema.simulation.engine = rejected ? 'safe_mode_engine' : approved ? 'full_engine' : schema.simulation.engine;
    }

    if (schema.domain === 'law') {
      const lawDecisions = Object.values(decisions);
      const unsafe = lawDecisions.some((decision) => decision.law_rule === 'unsafe_policy');
      const approved = lawDecisions.some((decision) => decision.law_rule === 'approve');
      if (unsafe) {
        schema.sandbox.execution.max_experiments_per_step = 1;
      } else if (approved) {
        schema.sandbox.execution.max_experiments_per_step = 10;
      }
    }

    return clone;
  }

  get_world_state(world: WorldContract, snapshot: Partial<WorldStateSnapshot> = {}): WorldStateSnapshot {
    return {
      world_id: world.world_contract.world_id,
      domain: world.world_contract.domain,
      nodes: snapshot.nodes ?? {},
      influence: snapshot.influence ?? {},
      mandala_decision: snapshot.mandala_decision ?? 'neutral',
      score: snapshot.score ?? 0,
      latest_record_id: snapshot.latest_record_id,
      latest_result: snapshot.latest_result,
    };
  }
}

export interface LawOutcome {
  decision: 'liable' | 'not_liable';
  fairness: number;
  consistency: number;
  rights_impact: number;
}

export interface MedicineOutcome {
  efficacy: number;
  toxicity: number;
  safety: number;
}

export interface ScienceOutcome {
  model_error: number;
  confidence: number;
  non_falsifiable: boolean;
}

export interface EconomicsOutcome {
  efficiency: number;
  inequality: number;
  instability: number;
}

export interface DomainEngine<TOutcome extends object = Record<string, JsonValue>> {
  readonly domain: DomainName;
  run(spec: ExperimentSpec): TOutcome;
}

export class LawEngine implements DomainEngine<LawOutcome> {
  readonly domain = 'law' as const;

  run(spec: ExperimentSpec): LawOutcome {
    const caseRecord = asRecord(spec.inputs.case);
    const issues = asArray(caseRecord.issues).map((issue) => String(issue));
    const liable = issues.includes('breach');
    return {
      decision: liable ? 'liable' : 'not_liable',
      fairness: 0.9,
      consistency: 0.85,
      rights_impact: liable ? 0.6 : 0.1,
    };
  }
}

export class MedicineEngine implements DomainEngine<MedicineOutcome> {
  readonly domain = 'medicine' as const;

  run(spec: ExperimentSpec): MedicineOutcome {
    const treatment = asRecord(spec.inputs.treatment);
    const dose = typeof treatment.dose === 'number' ? treatment.dose : Number(treatment.dose ?? 0);
    const efficacy = Math.min(1, dose / 500);
    const toxicity = Math.max(0, dose / 1000);
    return {
      efficacy,
      toxicity,
      safety: Math.max(0, 1 - toxicity),
    };
  }
}

export class ScienceEngine implements DomainEngine<ScienceOutcome> {
  readonly domain = 'science' as const;

  run(spec: ExperimentSpec): ScienceOutcome {
    const x = typeof spec.parameters.x === 'number' ? spec.parameters.x : 1;
    const model_error = Math.abs(x * 0.01);
    return {
      model_error,
      confidence: Math.max(0, 1 - model_error),
      non_falsifiable: false,
    };
  }
}

export class EconomicsEngine implements DomainEngine<EconomicsOutcome> {
  readonly domain = 'economics' as const;

  run(spec: ExperimentSpec): EconomicsOutcome {
    const market = asRecord(spec.inputs.market);
    const volatility = typeof market.volatility === 'number' ? market.volatility : 0.3;
    const gini = typeof market.gini === 'number' ? market.gini : 0.3;
    return {
      efficiency: Math.max(0, 1 - volatility),
      inequality: gini,
      instability: volatility,
    };
  }
}

export interface EvidenceRecord {
  record_id: string;
  timestamp: number;
  world_id: string;
  domain: DomainName;
  intent: ExperimentIntent;
  spec: ExperimentSpec;
  metrics: Record<string, number>;
  node_decisions: Record<string, MandalaNodeDecision>;
  influence: Record<string, number>;
  mandala_decision: MandalaDecisionLabel;
  score: number;
  authority: string;
  inputs: Record<string, JsonValue>;
  outputs: Record<string, JsonValue>;
  code_version: string;
  justification: string;
  lineage: readonly string[];
  runtime_artifacts_jsonl: string;
}

export interface EvidenceRecordInput {
  timestamp: number;
  world_id: string;
  domain: DomainName;
  intent: ExperimentIntent;
  spec: ExperimentSpec;
  metrics: Record<string, number>;
  node_decisions: Record<string, MandalaNodeDecision>;
  influence: Record<string, number>;
  mandala_decision: MandalaDecisionLabel;
  score: number;
  authority: string;
  inputs: Record<string, JsonValue>;
  outputs: Record<string, JsonValue>;
  code_version: string;
  justification: string;
  lineage: readonly string[];
}

function stableValue(value: JsonValue): JsonValue {
  if (Array.isArray(value)) {
    return value.map((item) => stableValue(item)) as readonly JsonValue[];
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, nested]) => [key, stableValue(nested)] as const);
    return Object.fromEntries(entries);
  }
  return value;
}

function stableStringify(value: JsonValue): string {
  return JSON.stringify(stableValue(value));
}

function hashRecord(payload: JsonValue): string {
  return createHash('sha256').update(stableStringify(payload)).digest('hex').slice(0, 24);
}

export class EvidenceLedger {
  private readonly _records: EvidenceRecord[] = [];

  get records(): readonly EvidenceRecord[] {
    return this._records;
  }

  append(input: EvidenceRecordInput): EvidenceRecord {
    const payload = {
      timestamp: input.timestamp,
      world_id: input.world_id,
      domain: input.domain,
      intent: stableValue(input.intent as unknown as JsonValue),
      spec: stableValue(input.spec as unknown as JsonValue),
      metrics: stableValue(input.metrics as unknown as JsonValue),
      node_decisions: stableValue(input.node_decisions as unknown as JsonValue),
      influence: stableValue(input.influence as unknown as JsonValue),
      mandala_decision: input.mandala_decision,
      score: input.score,
      authority: input.authority,
      inputs: stableValue(input.inputs as unknown as JsonValue),
      outputs: stableValue(input.outputs as unknown as JsonValue),
      code_version: input.code_version,
      justification: input.justification,
      lineage: stableValue(input.lineage as unknown as JsonValue),
    } as JsonValue;
    const provisional: EvidenceRecord = {
      ...input,
      record_id: `csr-${hashRecord(payload)}`,
      runtime_artifacts_jsonl: '',
    };
    const runtime_artifacts = buildRuntimeArtifactBundle(provisional);
    const runtime_artifacts_jsonl = serializeRuntimeArtifactBundle(runtime_artifacts);
    const record: EvidenceRecord = {
      ...provisional,
      runtime_artifacts_jsonl,
    };
    this._records.push(structuredClone(record));
    return structuredClone(record);
  }

  list_by_world(world_id: string): EvidenceRecord[] {
    return this._records.filter((record) => record.world_id === world_id).map((record) => structuredClone(record));
  }

  list_by_domain(domain: DomainName): EvidenceRecord[] {
    return this._records.filter((record) => record.domain === domain).map((record) => structuredClone(record));
  }

  export_runtime_artifacts_jsonl(world_id: string, filter: ReplayFilter = {}): string {
    const record = this.list_by_world(world_id)
      .filter((entry) => (filter.domain ? entry.domain === filter.domain : true))
      .filter((entry) => (filter.node_id ? entry.node_decisions[filter.node_id] !== undefined : true))
      .at(-1);
    if (!record) {
      throw new Error(`No evidence available for world: ${world_id}`);
    }
    return record.runtime_artifacts_jsonl;
  }

  async write_runtime_artifacts_jsonl(
    world_id: string,
    file_path: string,
    filter: ReplayFilter = {},
  ): Promise<string> {
    const jsonl = this.export_runtime_artifacts_jsonl(world_id, filter);
    await writeFile(file_path, `${jsonl}\n`, 'utf8');
    return file_path;
  }
}

export interface ReplayFilter {
  domain?: DomainName;
  node_id?: string;
}

export class ReplayEngine {
  constructor(private readonly ledger: EvidenceLedger) {}

  replay_world(world_id: string, filter: ReplayFilter = {}): EvidenceRecord[] {
    const history = this.ledger.list_by_world(world_id);
    const filtered = filter.domain ? history.filter((entry) => entry.domain === filter.domain) : history;
    const nodeFiltered = filter.node_id
      ? filtered.filter((entry) => entry.node_decisions[filter.node_id!] !== undefined)
      : filtered;
    return [...nodeFiltered].sort((left, right) => left.timestamp - right.timestamp);
  }

  replay_runtime(world_id: string, filter: ReplayFilter = {}): ReplayRecord {
    const records = this.replay_world(world_id, filter);
    const latest = records.at(-1);
    if (!latest) {
      throw new Error(`No evidence available for world: ${world_id}`);
    }
    return {
      replay_id: hashRecordId({
        kind: 'replay',
        world_id,
        record_ids: records.map((record) => record.record_id),
      }),
      world_id,
      domain: latest.domain,
      generated_at: latest.timestamp,
      record_ids: records.map((record) => record.record_id),
      records,
      runtime_artifacts_jsonl: records.map((record) => record.runtime_artifacts_jsonl).join('\n'),
    };
  }

  replay_artifacts(world_id: string, filter: ReplayFilter = {}): RuntimeArtifactBundle {
    const jsonl = this.ledger.export_runtime_artifacts_jsonl(world_id, filter);
    return parseRuntimeArtifactBundleJsonl(jsonl);
  }
}

export class WorldRegistry {
  private readonly worlds = new Map<string, WorldContract>();

  constructor(seed: readonly WorldContract[] = []) {
    for (const world of seed) {
      this.register_world(world);
    }
  }

  register_world(world: WorldContract): WorldContract {
    validateWorldContract(world);
    const clone = structuredClone(world);
    this.worlds.set(clone.world_contract.world_id, clone);
    return structuredClone(clone);
  }

  get_world(world_id: string): WorldContract {
    const world = this.worlds.get(world_id);
    if (!world) {
      throw new Error(`Unknown world: ${world_id}`);
    }
    return structuredClone(world);
  }

  update_world(world: WorldContract): WorldContract {
    validateWorldContract(world);
    const clone = structuredClone(world);
    this.worlds.set(clone.world_contract.world_id, clone);
    return structuredClone(clone);
  }

  list_worlds(): WorldContract[] {
    return [...this.worlds.values()].map((world) => structuredClone(world));
  }
}

function validateWorldContract(world: WorldContract): void {
  const schema = world?.world_contract;
  if (!schema) {
    throw new Error('World contract is missing the world_contract envelope.');
  }
  if (!hasTruthyText(schema.world_id)) {
    throw new Error('World contract must include a world_id.');
  }
  if (!hasTruthyText(schema.description)) {
    throw new Error(`World contract ${schema.world_id} is missing a description.`);
  }
  if (!schema.constitution?.principles?.length) {
    throw new Error(`World contract ${schema.world_id} must declare constitutional principles.`);
  }
  if (!schema.sandbox?.execution?.allowed_operations?.length) {
    throw new Error(`World contract ${schema.world_id} must declare allowed operations.`);
  }
  if (schema.sandbox.execution.max_runtime_ms <= 0) {
    throw new Error(`World contract ${schema.world_id} must have a positive runtime limit.`);
  }
}

export interface ExperimentOutcome {
  world_id: string;
  domain: DomainName;
  allowed: boolean;
  mandala_decision: MandalaDecisionLabel;
  score: number;
  node_decisions: Record<string, MandalaNodeDecision>;
  influence: Record<string, number>;
  result: Record<string, JsonValue>;
  evidence: EvidenceRecord;
  world: WorldContract;
  metrics: Record<string, number>;
  runtime_artifacts: RuntimeArtifactBundle;
  runtime_artifacts_jsonl: string;
}

export class ExperimentOrchestrator {
  constructor(
    private readonly registry: WorldRegistry,
    private readonly ledger: EvidenceLedger,
    private readonly brain: MandalaBrainV2,
    private readonly engines: Record<DomainName, DomainEngine<any>>,
    private readonly state_engine: WorldStateEngine,
    private readonly clock: () => number = () => Date.now(),
  ) {}

  submit_experiment(request: ExperimentSubmission, metrics: Record<string, number> = {}): ExperimentOutcome {
    const world = this.registry.get_world(request.world_id);
    const schema = world.world_contract;
    if (request.intent.domain !== schema.domain) {
      throw new Error(`Intent domain ${request.intent.domain} does not match world domain ${schema.domain}.`);
    }
    if (schema.governance.intent_rules.require_description && !hasTruthyText(request.intent.description)) {
      throw new Error('Intent description is required.');
    }
    if (schema.governance.intent_rules.require_authority && !hasTruthyText(request.intent.authority)) {
      throw new Error('Intent authority is required.');
    }
    if (schema.governance.intent_rules.require_evidence && (request.spec.validation?.required_metrics ?? []).length === 0) {
      throw new Error('Required evidence metrics are missing.');
    }
    if (!schema.sandbox.execution.allowed_operations.includes(request.spec.operation)) {
      throw new Error(`Operation ${request.spec.operation} is not allowed in ${schema.world_id}.`);
    }

    const context: MandalaContext = {
      world,
      experiment: {
        world_id: request.world_id,
        domain: schema.domain,
        intent: request.intent,
        spec: request.spec,
        metrics,
      },
    };

    const evaluation = this.brain.evaluate(context);
    const updatedWorld = this.state_engine.apply_mandala_decisions(world, evaluation.node_decisions);
    this.registry.update_world(updatedWorld);

    let result: Record<string, JsonValue> = {};
    const allowed = evaluation.mandala_decision === 'approve';
    if (allowed) {
      const engine = this.engines[schema.domain];
      if (!engine) {
        throw new Error(`No domain engine registered for ${schema.domain}.`);
      }
      result = engine.run(request.spec) as Record<string, JsonValue>;
    } else {
      result = {
        status: 'blocked',
        reason: evaluation.mandala_decision,
      };
    }

    const record = this.ledger.append({
      timestamp: this.clock(),
      world_id: request.world_id,
      domain: schema.domain,
      intent: request.intent,
      spec: request.spec,
      metrics,
      node_decisions: evaluation.node_decisions,
      influence: evaluation.influence,
      mandala_decision: evaluation.mandala_decision,
      score: evaluation.score,
      authority: request.intent.authority,
      inputs: request.spec.inputs,
      outputs: result,
      code_version: request.spec.code_version ?? 'v1',
      justification: request.intent.justification ?? request.intent.description,
      lineage: [request.world_id, request.intent.domain, request.spec.model_ref],
    });

    return {
      world_id: request.world_id,
      domain: schema.domain,
      allowed,
      mandala_decision: evaluation.mandala_decision,
      score: evaluation.score,
      node_decisions: evaluation.node_decisions,
      influence: evaluation.influence,
      result,
      evidence: record,
      world: updatedWorld,
      metrics,
      runtime_artifacts: buildRuntimeArtifactBundle(record),
      runtime_artifacts_jsonl: record.runtime_artifacts_jsonl,
    };
  }
}

export interface WorldSandboxState {
  registry: WorldRegistry;
  ledger: EvidenceLedger;
  replay: ReplayEngine;
  orchestrator: ExperimentOrchestrator;
  brain: MandalaBrainV2;
  state_engine: WorldStateEngine;
}

export class ConstitutionalSandbox {
  readonly registry: WorldRegistry;
  readonly ledger: EvidenceLedger;
  readonly replay: ReplayEngine;
  readonly orchestrator: ExperimentOrchestrator;
  readonly brain: MandalaBrainV2;
  readonly state_engine: WorldStateEngine;

  constructor(seedWorlds: readonly WorldContract[] = createDefaultWorlds(), clock: () => number = () => Date.now()) {
    this.registry = new WorldRegistry(seedWorlds);
    this.ledger = new EvidenceLedger();
    this.brain = createDefaultMandalaBrain();
    this.state_engine = new WorldStateEngine();
    this.orchestrator = new ExperimentOrchestrator(
      this.registry,
      this.ledger,
      this.brain,
      {
        law: new LawEngine(),
        medicine: new MedicineEngine(),
        science: new ScienceEngine(),
        economics: new EconomicsEngine(),
        society: new EconomicsEngine(),
        custom: new EconomicsEngine(),
      },
      this.state_engine,
      clock,
    );
    this.replay = new ReplayEngine(this.ledger);
  }

  submit_experiment(request: ExperimentSubmission, metrics: Record<string, number> = {}): ExperimentOutcome {
    return this.orchestrator.submit_experiment(request, metrics);
  }

  replay_world(world_id: string, filter: ReplayFilter = {}): EvidenceRecord[] {
    return this.replay.replay_world(world_id, filter);
  }

  replay_runtime(world_id: string, filter: ReplayFilter = {}): ReplayRecord {
    return this.replay.replay_runtime(world_id, filter);
  }

  replay_artifacts(world_id: string, filter: ReplayFilter = {}): RuntimeArtifactBundle {
    return this.replay.replay_artifacts(world_id, filter);
  }

  emit_runtime_artifacts(world_id: string): RuntimeArtifactBundle {
    const latest = this.ledger.list_by_world(world_id).at(-1);
    if (!latest) {
      throw new Error(`No evidence available for world: ${world_id}`);
    }
    return buildRuntimeArtifactBundle(latest);
  }

  export_runtime_artifacts_jsonl(world_id: string, filter: ReplayFilter = {}): string {
    return this.ledger.export_runtime_artifacts_jsonl(world_id, filter);
  }

  async write_runtime_artifacts_jsonl(
    world_id: string,
    file_path: string,
    filter: ReplayFilter = {},
  ): Promise<string> {
    return this.ledger.write_runtime_artifacts_jsonl(world_id, file_path, filter);
  }

  get_world_state(world_id: string): WorldStateSnapshot {
    const world = this.registry.get_world(world_id);
    const history = this.ledger.list_by_world(world_id);
    const latest = history.at(-1);
    return this.state_engine.get_world_state(world, latest
      ? {
          nodes: latest.node_decisions,
          influence: latest.influence,
          mandala_decision: latest.mandala_decision,
          score: latest.score,
          latest_record_id: latest.record_id,
          latest_result: latest.outputs,
        }
      : undefined);
  }
}

export function createDefaultMandalaBrain(): MandalaBrainV2 {
  const nodes: Record<string, MandalaNode> = {
    LAW_RULE: new LawRuleNode('LAW_RULE'),
    MED_PROTOCOL: new MedProtocolNode('MED_PROTOCOL'),
    SCI_MODEL: new SciModelNode('SCI_MODEL'),
    ECO_POLICY: new EcoPolicyNode('ECO_POLICY'),
    CONSENSUS: new ConsensusNode('CONSENSUS'),
  };
  const edges: MandalaEdge[] = [
    { source: 'LAW_RULE', target: 'CONSENSUS', weight: 1.0, relation: 'influence' },
    { source: 'MED_PROTOCOL', target: 'CONSENSUS', weight: 1.0, relation: 'influence' },
    { source: 'SCI_MODEL', target: 'CONSENSUS', weight: 1.0, relation: 'influence' },
    { source: 'ECO_POLICY', target: 'CONSENSUS', weight: 1.0, relation: 'influence' },
  ];
  return new MandalaBrainV2(nodes, edges);
}

export function createWorldContract(
  schema: Omit<WorldContractSchema, 'version'> & { version?: string },
): WorldContract {
  return {
    world_contract: {
      ...schema,
      version: schema.version ?? '1.0',
    },
  };
}

export function createDefaultWorlds(): WorldContract[] {
  return [
    createWorldContract({
      world_id: 'law_arena_1',
      domain: 'law',
      description: 'Law arena for case reasoning, precedent analysis, and policy stress testing.',
      constitution: {
        principles: [
          'no_decision_without_evidence',
          'lineage_preservation',
          'authority_separation',
          'intent_requires_justification',
        ],
        contracts: {
          ILC: 'enabled',
          CIC: 'enabled',
          CCC: 'enabled',
        },
      },
      sandbox: {
        isolation: {
          cpu_limit: 'medium',
          memory_limit: 'safe',
          network: 'none',
          filesystem: 'ephemeral',
        },
        execution: {
          allowed_operations: ['case_simulation', 'precedent_analysis', 'policy_stress_test'],
          max_runtime_ms: 5000,
          max_experiments_per_step: 10,
        },
      },
      simulation: {
        engine: 'law_engine_v1',
        models: [
          {
            model_id: 'law_reasoner_v1',
            type: 'reasoning_model',
            version: '1.0.0',
            parameters: {},
          },
        ],
        state: {
          initial: { cases: [], precedents: [] },
          schema: { cases: 'array', precedents: 'array' },
        },
      },
      governance: {
        authority: {
          roles: [
            {
              role_id: 'judge',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
            {
              role_id: 'law_researcher',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
            {
              role_id: 'policy_analyst',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
          ],
        },
        intent_rules: {
          require_description: true,
          require_domain_alignment: true,
          require_authority: true,
          require_evidence: true,
        },
        evidence_rules: {
          record_all_transitions: true,
          record_inputs: true,
          record_outputs: true,
          record_code_version: true,
          record_parameters: true,
        },
      },
      interfaces: {
        submit_intent: '/world/{world_id}/intent',
        submit_experiment: '/world/{world_id}/experiment',
        get_state: '/world/{world_id}/state',
        get_evidence: '/world/{world_id}/evidence',
      },
      lineage: {
        ledger_type: 'CSR',
        record_format: {
          timestamp: 'float',
          intent: {},
          inputs: {},
          outputs: {},
          model_version: 'string',
          authority: 'string',
          justification: 'string',
        },
      },
    }),
    createWorldContract({
      world_id: 'med_arena_1',
      domain: 'medicine',
      description: 'Medicine arena for treatment comparison, protocol simulation, and risk modeling.',
      constitution: {
        principles: [
          'no_decision_without_evidence',
          'lineage_preservation',
          'authority_separation',
          'intent_requires_justification',
        ],
        contracts: {
          ILC: 'enabled',
          CIC: 'enabled',
          CCC: 'enabled',
        },
      },
      sandbox: {
        isolation: {
          cpu_limit: 'medium',
          memory_limit: 'safe',
          network: 'none',
          filesystem: 'ephemeral',
        },
        execution: {
          allowed_operations: ['treatment_comparison', 'protocol_simulation', 'risk_modeling'],
          max_runtime_ms: 5000,
          max_experiments_per_step: 10,
        },
      },
      simulation: {
        engine: 'medicine_engine_v1',
        models: [
          {
            model_id: 'med_model_v3',
            type: 'treatment_model',
            version: '3.0.0',
            parameters: {},
          },
        ],
        state: {
          initial: { cohorts: [], protocols: [] },
          schema: { cohorts: 'array', protocols: 'array' },
        },
      },
      governance: {
        authority: {
          roles: [
            {
              role_id: 'researcher_alpha',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
            {
              role_id: 'clinician',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
          ],
        },
        intent_rules: {
          require_description: true,
          require_domain_alignment: true,
          require_authority: true,
          require_evidence: true,
        },
        evidence_rules: {
          record_all_transitions: true,
          record_inputs: true,
          record_outputs: true,
          record_code_version: true,
          record_parameters: true,
        },
      },
      interfaces: {
        submit_intent: '/world/{world_id}/intent',
        submit_experiment: '/world/{world_id}/experiment',
        get_state: '/world/{world_id}/state',
        get_evidence: '/world/{world_id}/evidence',
      },
      lineage: {
        ledger_type: 'CSR',
        record_format: {
          timestamp: 'float',
          intent: {},
          inputs: {},
          outputs: {},
          model_version: 'string',
          authority: 'string',
          justification: 'string',
        },
      },
    }),
    createWorldContract({
      world_id: 'sci_arena_1',
      domain: 'science',
      description: 'Science arena for experiments, hypothesis tests, and model validation.',
      constitution: {
        principles: [
          'no_decision_without_evidence',
          'lineage_preservation',
          'authority_separation',
          'intent_requires_justification',
        ],
        contracts: {
          ILC: 'enabled',
          CIC: 'enabled',
          CCC: 'enabled',
        },
      },
      sandbox: {
        isolation: {
          cpu_limit: 'medium',
          memory_limit: 'safe',
          network: 'none',
          filesystem: 'ephemeral',
        },
        execution: {
          allowed_operations: ['experiment', 'hypothesis_test', 'model_validation'],
          max_runtime_ms: 5000,
          max_experiments_per_step: 10,
        },
      },
      simulation: {
        engine: 'science_engine_v1',
        models: [
          {
            model_id: 'sci_model_v1',
            type: 'scientific_model',
            version: '1.0.0',
            parameters: {},
          },
        ],
        state: {
          initial: { systems: [], observations: [] },
          schema: { systems: 'array', observations: 'array' },
        },
      },
      governance: {
        authority: {
          roles: [
            {
              role_id: 'scientist',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
          ],
        },
        intent_rules: {
          require_description: true,
          require_domain_alignment: true,
          require_authority: true,
          require_evidence: true,
        },
        evidence_rules: {
          record_all_transitions: true,
          record_inputs: true,
          record_outputs: true,
          record_code_version: true,
          record_parameters: true,
        },
      },
      interfaces: {
        submit_intent: '/world/{world_id}/intent',
        submit_experiment: '/world/{world_id}/experiment',
        get_state: '/world/{world_id}/state',
        get_evidence: '/world/{world_id}/evidence',
      },
      lineage: {
        ledger_type: 'CSR',
        record_format: {
          timestamp: 'float',
          intent: {},
          inputs: {},
          outputs: {},
          model_version: 'string',
          authority: 'string',
          justification: 'string',
        },
      },
    }),
    createWorldContract({
      world_id: 'soc_arena_1',
      domain: 'economics',
      description: 'Economics and society arena for market simulations and policy impact studies.',
      constitution: {
        principles: [
          'no_decision_without_evidence',
          'lineage_preservation',
          'authority_separation',
          'intent_requires_justification',
        ],
        contracts: {
          ILC: 'enabled',
          CIC: 'enabled',
          CCC: 'enabled',
        },
      },
      sandbox: {
        isolation: {
          cpu_limit: 'medium',
          memory_limit: 'safe',
          network: 'none',
          filesystem: 'ephemeral',
        },
        execution: {
          allowed_operations: ['market_simulation', 'policy_impact', 'agent_based_model'],
          max_runtime_ms: 5000,
          max_experiments_per_step: 10,
        },
      },
      simulation: {
        engine: 'economics_engine_v1',
        models: [
          {
            model_id: 'eco_model_v1',
            type: 'market_model',
            version: '1.0.0',
            parameters: {},
          },
        ],
        state: {
          initial: { agents: [], market: {} },
          schema: { agents: 'array', market: 'object' },
        },
      },
      governance: {
        authority: {
          roles: [
            {
              role_id: 'economist',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
            {
              role_id: 'policy_analyst',
              permissions: ['submit_intent', 'run_experiment', 'view_evidence'],
            },
          ],
        },
        intent_rules: {
          require_description: true,
          require_domain_alignment: true,
          require_authority: true,
          require_evidence: true,
        },
        evidence_rules: {
          record_all_transitions: true,
          record_inputs: true,
          record_outputs: true,
          record_code_version: true,
          record_parameters: true,
        },
      },
      interfaces: {
        submit_intent: '/world/{world_id}/intent',
        submit_experiment: '/world/{world_id}/experiment',
        get_state: '/world/{world_id}/state',
        get_evidence: '/world/{world_id}/evidence',
      },
      lineage: {
        ledger_type: 'CSR',
        record_format: {
          timestamp: 'float',
          intent: {},
          inputs: {},
          outputs: {},
          model_version: 'string',
          authority: 'string',
          justification: 'string',
        },
      },
    }),
  ];
}

export function createWorldStateEngine(): WorldStateEngine {
  return new WorldStateEngine();
}

export function createConstitutionalSandbox(clock: () => number = () => Date.now()): ConstitutionalSandbox {
  return new ConstitutionalSandbox(createDefaultWorlds(), clock);
}

export interface FeatureMetrics {
  risk?: number;
  health?: number;
  drift?: number;
}

export interface ConstitutionalEvidenceMetrics {
  evidence_sufficiency?: number;
  evidence_completeness?: number;
  lineage_depth?: number;
  metrics_present?: number;
}

export interface ConstitutionalRiskMetrics {
  toxicity?: number;
  rights_impact?: number;
  instability?: number;
  non_falsifiable?: number;
}

export function extractFeatures(
  world: Record<string, unknown> | WorldContract,
  experiment: Record<string, unknown> | MandalaContext['experiment'],
  metrics: FeatureMetrics = {},
): Record<string, number> {
  const feats: Record<string, number> = {};
  const worldView = 'world_contract' in world ? (world.world_contract as WorldContractSchema) : asRecord(world);
  const experimentView = 'domain' in experiment ? experiment : asRecord(experiment);
  const intent = asRecord((experimentView as Record<string, unknown>).intent);
  const spec = asRecord((experimentView as Record<string, unknown>).spec);

  const domain = String((experimentView as Record<string, unknown>).domain ?? 'custom');
  for (const current of ['law', 'medicine', 'science', 'economics'] as const) {
    feats[`domain_${current}`] = current === domain ? 1 : 0;
  }

  feats.intent_has_description = hasTruthyText(intent.description) ? 1 : 0;
  feats.intent_purpose_exploration = intent.purpose === 'exploration' ? 1 : 0;
  feats.intent_purpose_comparison = intent.purpose === 'comparison' ? 1 : 0;

  feats.has_constraints = spec.constraints ? 1 : 0;
  feats.num_parameters = Object.keys(asRecord(spec.parameters)).length;

  const sandbox = asRecord((worldView as Record<string, unknown>).sandbox);
  const execution = asRecord(sandbox.execution);
  feats.max_runtime_ms = typeof execution.max_runtime_ms === 'number' ? execution.max_runtime_ms : 0;
  feats.max_experiments_per_step =
    typeof execution.max_experiments_per_step === 'number' ? execution.max_experiments_per_step : 0;

  feats.prior_risk = typeof metrics.risk === 'number' ? metrics.risk : 0;
  feats.prior_health = typeof metrics.health === 'number' ? metrics.health : 1;
  feats.prior_drift = typeof metrics.drift === 'number' ? metrics.drift : 0;

  return feats;
}

export function buildCanonicalFeatureNames(): readonly string[] {
  return [
    'domain_law',
    'domain_medicine',
    'domain_science',
    'domain_economics',
    'intent_has_description',
    'intent_purpose_exploration',
    'intent_purpose_comparison',
    'has_constraints',
    'num_parameters',
    'max_runtime_ms',
    'max_experiments_per_step',
    'prior_risk',
    'prior_health',
    'prior_drift',
  ];
}

export function buildConstitutionalFeatureNames(): readonly string[] {
  return [
    ...buildCanonicalFeatureNames(),
    'evidence_sufficiency',
    'evidence_completeness',
    'evidence_lineage_depth',
    'evidence_metrics_present',
    'risk_toxicity',
    'risk_rights_impact',
    'risk_instability',
    'risk_non_falsifiable',
  ];
}

export class ContextEncoderV1 {
  constructor(public readonly feature_names: readonly string[]) {}

  encode(features: Record<string, number>): number[] {
    return this.feature_names.map((name) => features[name] ?? 0);
  }
}

export function extractConstitutionalFeatures(
  world: Record<string, unknown> | WorldContract,
  experiment: Record<string, unknown> | MandalaContext['experiment'],
  metrics: FeatureMetrics & ConstitutionalRiskMetrics & ConstitutionalEvidenceMetrics = {},
): Record<string, number> {
  const feats = extractFeatures(world, experiment, metrics);
  feats.evidence_sufficiency = typeof metrics.evidence_sufficiency === 'number' ? metrics.evidence_sufficiency : 0;
  feats.evidence_completeness = typeof metrics.evidence_completeness === 'number' ? metrics.evidence_completeness : 0;
  feats.evidence_lineage_depth = typeof metrics.lineage_depth === 'number' ? metrics.lineage_depth : 0;
  feats.evidence_metrics_present = typeof metrics.metrics_present === 'number' ? metrics.metrics_present : 0;
  feats.risk_toxicity = typeof metrics.toxicity === 'number' ? metrics.toxicity : 0;
  feats.risk_rights_impact = typeof metrics.rights_impact === 'number' ? metrics.rights_impact : 0;
  feats.risk_instability = typeof metrics.instability === 'number' ? metrics.instability : 0;
  feats.risk_non_falsifiable = typeof metrics.non_falsifiable === 'number' ? metrics.non_falsifiable : 0;
  return feats;
}

export interface DenseLayerWeights {
  weights: readonly (readonly number[])[];
  bias: readonly number[];
}

function dot(left: readonly number[], right: readonly number[]): number {
  let total = 0;
  for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
    total += left[index]! * right[index]!;
  }
  return total;
}

function relu(value: number): number {
  return Math.max(0, value);
}

function denseForward(layer: DenseLayerWeights, input: readonly number[]): number[] {
  return layer.weights.map((row, rowIndex) => dot(row, input) + (layer.bias[rowIndex] ?? 0));
}

export class ContextEncoderV2 {
  constructor(
    private readonly input_layer: DenseLayerWeights,
    private readonly output_layer: DenseLayerWeights,
  ) {}

  forward(input: readonly number[]): number[] {
    const hidden = denseForward(this.input_layer, input).map(relu);
    return denseForward(this.output_layer, hidden);
  }
}

export class MandalaBrainV3 {
  constructor(
    private readonly weights: readonly number[],
    private readonly bias = 0,
  ) {}

  step(context_vector: readonly number[]): number {
    return dot(this.weights, context_vector) + this.bias;
  }
}

export function constitutionalLoss(score: number, target: 1 | -1): number {
  return Math.max(0, 1 - target * score);
}

export function evidenceAlignmentLoss(score: number, evidence_score: number): number {
  return Math.max(0, Math.abs(score) - evidence_score);
}

export function domainSafetyLoss(score: number, domain_risk: number): number {
  return Math.max(0, score * domain_risk);
}

export function calibrationLoss(score: number, delta = 1): number {
  return delta * score * score;
}

export function regretLoss(score_decision: number, score_hindsight: number): number {
  return Math.abs(score_decision - score_hindsight);
}

export interface MandalaTrainingWeights {
  alpha: number;
  beta: number;
  gamma: number;
  delta: number;
  eta: number;
}

export interface MandalaTrainingBatch {
  target: 1 | -1;
  evidence_score: number;
  domain_risk: number;
  score_decision: number;
  score_hindsight: number;
}

export function totalMandalaLoss(
  batch: MandalaTrainingBatch,
  score: number,
  weights: MandalaTrainingWeights,
): number {
  const const_loss = constitutionalLoss(score, batch.target);
  const evidence_loss = evidenceAlignmentLoss(score, batch.evidence_score);
  const domain_loss = domainSafetyLoss(score, batch.domain_risk);
  const calibration_loss = calibrationLoss(score);
  const regret_loss = regretLoss(batch.score_decision, batch.score_hindsight);

  return (
    weights.alpha * const_loss +
    weights.beta * evidence_loss +
    weights.gamma * domain_loss +
    weights.delta * calibration_loss +
    weights.eta * regret_loss
  );
}

export function decisionFromScore(score: number, epsilon = 1e-6): MandalaDecisionLabel {
  if (score > epsilon) {
    return 'approve';
  }
  if (score < -epsilon) {
    return 'reject';
  }
  return 'neutral';
}

export type ConstitutionalSafetyLabel = 'safe_approve' | 'unsafe_approve' | 'safe_reject' | 'unsafe_reject';

export interface ConstitutionalDatasetRecord {
  world_id: string;
  domain: DomainName;
  experiment: {
    intent: ExperimentIntent;
    spec: ExperimentSpec;
  };
  metrics: Record<string, number>;
  evidence: {
    sufficiency: number;
    completeness: number;
    lineage_depth: number;
    metrics_present: number;
  };
  mandala_decision: MandalaDecisionLabel;
  score: number;
  outcome: Record<string, JsonValue>;
  safety_label: ConstitutionalSafetyLabel;
  hindsight_score: number;
}

function outcomeRiskScore(outcome: Record<string, JsonValue>, metrics: Record<string, number>): number {
  const values = [
    typeof outcome.toxicity === 'number' ? outcome.toxicity : 0,
    typeof outcome.rights_impact === 'number' ? outcome.rights_impact : 0,
    typeof outcome.instability === 'number' ? outcome.instability : 0,
    outcome.non_falsifiable === true ? 1 : 0,
    typeof metrics.risk === 'number' ? metrics.risk : 0,
  ];
  return Math.max(0, Math.min(1, Math.max(...values)));
}

function completenessScore(intent: ExperimentIntent, spec: ExperimentSpec): number {
  const checks = [
    hasTruthyText(intent.description),
    hasTruthyText(intent.domain),
    hasTruthyText(intent.authority),
    hasTruthyText(spec.operation),
    hasTruthyText(spec.model_ref),
    Object.keys(spec.inputs).length > 0,
    Object.keys(spec.parameters).length > 0,
    (spec.validation?.required_metrics ?? []).length > 0,
  ];
  return checks.filter(Boolean).length / checks.length;
}

export function evidenceSufficiencyScore(record: Pick<ConstitutionalDatasetRecord, 'experiment' | 'evidence'>): number {
  return record.evidence.sufficiency;
}

export function deriveConstitutionalSafetyLabel(
  score: number,
  outcome: Record<string, JsonValue>,
  metrics: Record<string, number>,
): ConstitutionalSafetyLabel {
  const risk = outcomeRiskScore(outcome, metrics);
  const approved = score > 0;
  const unsafe = risk >= 0.5;
  if (approved && !unsafe) return 'safe_approve';
  if (approved && unsafe) return 'unsafe_approve';
  if (!approved && unsafe) return 'unsafe_reject';
  return 'safe_reject';
}

export function hindsightScoreFromOutcome(
  score: number,
  outcome: Record<string, JsonValue>,
  evidence: number,
  metrics: Record<string, number>,
): number {
  const risk = outcomeRiskScore(outcome, metrics);
  return score - risk + evidence * 0.5;
}

export function buildConstitutionalDatasetRecord(input: {
  evidence: EvidenceRecord;
}): ConstitutionalDatasetRecord {
  const evidence = input.evidence;
  const completeness = completenessScore(evidence.intent, evidence.spec);
  const lineage_depth = evidence.lineage.length;
  const metrics_present = Object.keys(evidence.metrics).length;
  const sufficiency = Math.max(
    0,
    Math.min(
      1,
      completeness * 0.5 + Math.min(lineage_depth / 5, 1) * 0.25 + Math.min(metrics_present / 6, 1) * 0.25,
    ),
  );

  return {
    world_id: evidence.world_id,
    domain: evidence.domain,
    experiment: {
      intent: structuredClone(evidence.intent),
      spec: structuredClone(evidence.spec),
    },
    evidence: {
      sufficiency,
      completeness,
      lineage_depth,
      metrics_present,
    },
    mandala_decision: evidence.mandala_decision,
    score: evidence.score,
    outcome: structuredClone(evidence.outputs),
    metrics: structuredClone(evidence.metrics),
    safety_label: deriveConstitutionalSafetyLabel(evidence.score, evidence.outputs, evidence.metrics),
    hindsight_score: hindsightScoreFromOutcome(evidence.score, evidence.outputs, sufficiency, evidence.metrics),
  };
}

export function constitutionalTargetFromSafetyLabel(label: ConstitutionalSafetyLabel): 1 | -1 {
  return label === 'safe_approve' || label === 'unsafe_reject' ? 1 : -1;
}

export function constitutionalAccuracy(records: readonly ConstitutionalDatasetRecord[]): number {
  if (records.length === 0) {
    return 0;
  }
  let hits = 0;
  for (const record of records) {
    const target = constitutionalTargetFromSafetyLabel(record.safety_label);
    if (Math.sign(record.score) === target || (record.score === 0 && target === 1)) {
      hits += 1;
    }
  }
  return hits / records.length;
}

export function evidenceCalibrationScore(records: readonly ConstitutionalDatasetRecord[]): number {
  if (records.length === 0) {
    return 1;
  }
  const total = records.reduce((sum, record) => sum + Math.abs(Math.abs(record.score) - record.evidence.sufficiency), 0);
  return Math.max(0, 1 - total / records.length);
}

export function domainSafetyScore(records: readonly ConstitutionalDatasetRecord[]): number {
  if (records.length === 0) {
    return 1;
  }
  const total = records.reduce((sum, record) => {
    const risk = outcomeRiskScore(record.outcome, record.metrics);
    return sum + Math.max(0, record.score * risk);
  }, 0);
  return Math.max(0, 1 - total / records.length);
}

export function constitutionalRegret(records: readonly ConstitutionalDatasetRecord[]): number {
  if (records.length === 0) {
    return 0;
  }
  const total = records.reduce((sum, record) => sum + Math.abs(record.score - record.hindsight_score), 0);
  return total / records.length;
}

export function evidenceWeightedApprovalRate(records: readonly ConstitutionalDatasetRecord[]): number {
  if (records.length === 0) {
    return 0;
  }
  let approval = 0;
  let evidence = 0;
  for (const record of records) {
    evidence += record.evidence.sufficiency;
    if (record.mandala_decision === 'approve') {
      approval += record.evidence.sufficiency;
    }
  }
  return evidence === 0 ? 0 : approval / evidence;
}

export interface ConstitutionalMetricsSummary {
  constitutional_accuracy: number;
  evidence_calibration_score: number;
  domain_safety_score: number;
  constitutional_regret: number;
  evidence_weighted_approval_rate: number;
}

export function summarizeConstitutionalMetrics(
  records: readonly ConstitutionalDatasetRecord[],
): ConstitutionalMetricsSummary {
  return {
    constitutional_accuracy: constitutionalAccuracy(records),
    evidence_calibration_score: evidenceCalibrationScore(records),
    domain_safety_score: domainSafetyScore(records),
    constitutional_regret: constitutionalRegret(records),
    evidence_weighted_approval_rate: evidenceWeightedApprovalRate(records),
  };
}

export interface ConstitutionalReceipt {
  receipt_id: string;
  world_id: string;
  domain: DomainName;
  evidence_record_id: string;
  mandala_decision: MandalaDecisionLabel;
  score: number;
  authority: string;
  issued_at: number;
  summary: string;
}

export interface EvidencePackage {
  package_id: string;
  world_id: string;
  domain: DomainName;
  evidence_record_id: string;
  sufficiency: number;
  completeness: number;
  lineage_depth: number;
  metrics_present: number;
  inputs: Record<string, JsonValue>;
  outputs: Record<string, JsonValue>;
  lineage: readonly string[];
  code_version: string;
}

export interface ReplayRecord {
  replay_id: string;
  world_id: string;
  domain: DomainName;
  generated_at: number;
  record_ids: readonly string[];
  records: readonly EvidenceRecord[];
  runtime_artifacts_jsonl: string;
}

export interface ConformanceCheck {
  check_id: string;
  passed: boolean;
  message: string;
}

export interface ConformanceRecord {
  conformance_id: string;
  world_id: string;
  domain: DomainName;
  evidence_record_id: string;
  passed: boolean;
  checks: readonly ConformanceCheck[];
  summary: string;
}

export interface OperatorTimelineEvent {
  phase: 'intent' | 'evaluation' | 'execution' | 'evidence' | 'conformance' | 'replay';
  timestamp: number;
  message: string;
}

export interface OperatorTimeline {
  timeline_id: string;
  world_id: string;
  domain: DomainName;
  events: readonly OperatorTimelineEvent[];
}

export interface CoriAlphaLineageReference {
  reference_id: string;
  system: 'CORI_ALPHA';
  relation: 'lineage_reference';
  connected: false;
  note: 'symbolic_only';
}

export interface RuntimeArtifactBundle {
  receipt: ConstitutionalReceipt;
  evidence_package: EvidencePackage;
  replay_record: ReplayRecord;
  conformance_record: ConformanceRecord;
  operator_timeline: OperatorTimeline;
  cori_alpha_lineage_reference: CoriAlphaLineageReference;
}

function hashRecordId(seed: JsonValue): string {
  return `art-${hashRecord(seed)}`;
}

export function buildRuntimeArtifactBundle(evidence: EvidenceRecord): RuntimeArtifactBundle {
  const receipt: ConstitutionalReceipt = {
    receipt_id: hashRecordId({
      kind: 'receipt',
      record_id: evidence.record_id,
      score: evidence.score,
      decision: evidence.mandala_decision,
    }),
    world_id: evidence.world_id,
    domain: evidence.domain,
    evidence_record_id: evidence.record_id,
    mandala_decision: evidence.mandala_decision,
    score: evidence.score,
    authority: evidence.authority,
    issued_at: evidence.timestamp,
    summary: `${evidence.domain} execution ${evidence.mandala_decision} at score ${evidence.score.toFixed(3)}`,
  };

  const evidence_package: EvidencePackage = {
    package_id: hashRecordId({
      kind: 'evidence-package',
      record_id: evidence.record_id,
      world_id: evidence.world_id,
    }),
    world_id: evidence.world_id,
    domain: evidence.domain,
    evidence_record_id: evidence.record_id,
    sufficiency: evidence.metrics.evidence_sufficiency ?? 0,
    completeness: evidence.metrics.evidence_completeness ?? 0,
    lineage_depth: evidence.lineage.length,
    metrics_present: Object.keys(evidence.metrics).length,
    inputs: structuredClone(evidence.inputs),
    outputs: structuredClone(evidence.outputs),
    lineage: structuredClone(evidence.lineage),
    code_version: evidence.code_version,
  };

  const replay_record: ReplayRecord = {
    replay_id: hashRecordId({
      kind: 'replay-record',
      record_id: evidence.record_id,
      timestamps: [evidence.timestamp],
    }),
    world_id: evidence.world_id,
    domain: evidence.domain,
    generated_at: evidence.timestamp,
    record_ids: [evidence.record_id],
    records: [structuredClone(evidence)],
    runtime_artifacts_jsonl: '',
  };

  const conformance_checks: ConformanceCheck[] = [
    {
      check_id: 'domain_alignment',
      passed: evidence.intent.domain === evidence.domain,
      message: 'Experiment intent must align with the world domain.',
    },
    {
      check_id: 'evidence_present',
      passed: evidence.lineage.length > 0 && Object.keys(evidence.inputs).length > 0,
      message: 'Evidence package must preserve lineage and inputs.',
    },
    {
      check_id: 'authority_declared',
      passed: hasTruthyText(evidence.authority),
      message: 'Authority must be declared for each constitutional execution.',
    },
    {
      check_id: 'recorded_outcome',
      passed: Object.keys(evidence.outputs).length > 0,
      message: 'Runtime execution must record outputs.',
    },
  ];
  const conformance_record: ConformanceRecord = {
    conformance_id: hashRecordId({
      kind: 'conformance-record',
      record_id: evidence.record_id,
      checks: conformance_checks.map((check) => check.passed),
    }),
    world_id: evidence.world_id,
    domain: evidence.domain,
    evidence_record_id: evidence.record_id,
    passed: conformance_checks.every((check) => check.passed),
    checks: conformance_checks,
    summary: conformance_checks.every((check) => check.passed)
      ? 'Execution conformed to sandbox constraints.'
      : 'Execution failed one or more constitutional checks.',
  };

  const operator_timeline: OperatorTimeline = {
    timeline_id: hashRecordId({
      kind: 'operator-timeline',
      record_id: evidence.record_id,
      world_id: evidence.world_id,
    }),
    world_id: evidence.world_id,
    domain: evidence.domain,
    events: [
      {
        phase: 'intent',
        timestamp: evidence.timestamp,
        message: `Intent submitted for ${evidence.intent.domain} by ${evidence.authority}.`,
      },
      {
        phase: 'evaluation',
        timestamp: evidence.timestamp + 1,
        message: `Mandala decision ${evidence.mandala_decision} with score ${evidence.score.toFixed(3)}.`,
      },
      {
        phase: 'execution',
        timestamp: evidence.timestamp + 2,
        message: evidence.mandala_decision === 'approve' ? 'Domain engine executed.' : 'Execution blocked by governance.',
      },
      {
        phase: 'evidence',
        timestamp: evidence.timestamp + 3,
        message: 'Evidence package captured with inputs, outputs, and lineage.',
      },
      {
        phase: 'conformance',
        timestamp: evidence.timestamp + 4,
        message: conformance_record.passed ? 'Conformance record passed.' : 'Conformance record failed.',
      },
      {
        phase: 'replay',
        timestamp: evidence.timestamp + 5,
        message: 'Replay record emitted for deterministic rewind.',
      },
    ],
  };

  const cori_alpha_lineage_reference: CoriAlphaLineageReference = {
    reference_id: hashRecordId({
      kind: 'cori-alpha-lineage-reference',
      world_id: evidence.world_id,
      record_id: evidence.record_id,
    }),
    system: 'CORI_ALPHA',
    relation: 'lineage_reference',
    connected: false,
    note: 'symbolic_only',
  };

  return {
    receipt,
    evidence_package,
    replay_record,
    conformance_record,
    operator_timeline,
    cori_alpha_lineage_reference,
  };
}

export function serializeRuntimeArtifactBundle(bundle: RuntimeArtifactBundle): string {
  const lines = [
    {
      artifact_type: 'constitutional_receipt',
      artifact: bundle.receipt,
    },
    {
      artifact_type: 'evidence_package',
      artifact: bundle.evidence_package,
    },
    {
      artifact_type: 'replay_record',
      artifact: bundle.replay_record,
    },
    {
      artifact_type: 'conformance_record',
      artifact: bundle.conformance_record,
    },
    {
      artifact_type: 'operator_timeline',
      artifact: bundle.operator_timeline,
    },
    {
      artifact_type: 'cori_alpha_lineage_reference',
      artifact: bundle.cori_alpha_lineage_reference,
    },
  ];
  return lines.map((line) => JSON.stringify(stableValue(line as unknown as JsonValue))).join('\n');
}

function parseRuntimeArtifactLine(line: string): { artifact_type: string; artifact: Record<string, JsonValue> } {
  const parsed = JSON.parse(line) as unknown;
  const entry = asRecord(parsed);
  const artifactType = entry.artifact_type;
  if (typeof artifactType !== 'string') {
    throw new Error('Runtime artifact JSONL line is missing artifact_type.');
  }
  return {
    artifact_type: artifactType,
    artifact: asRecord(entry.artifact),
  };
}

function parseEvidenceRecord(artifact: Record<string, JsonValue>): EvidenceRecord {
  return {
    record_id: String(artifact.record_id ?? ''),
    timestamp: typeof artifact.timestamp === 'number' ? artifact.timestamp : Number(artifact.timestamp ?? 0),
    world_id: String(artifact.world_id ?? ''),
    domain: String(artifact.domain ?? 'custom') as DomainName,
    intent: asRecord(artifact.intent) as unknown as ExperimentIntent,
    spec: asRecord(artifact.spec) as unknown as ExperimentSpec,
    metrics: Object.fromEntries(
      Object.entries(asRecord(artifact.metrics)).map(([key, value]) => [key, typeof value === 'number' ? value : Number(value)]),
    ),
    node_decisions: Object.fromEntries(
      Object.entries(asRecord(artifact.node_decisions)).map(([key, value]) => [key, asRecord(value)]),
    ),
    influence: Object.fromEntries(
      Object.entries(asRecord(artifact.influence)).map(([key, value]) => [key, typeof value === 'number' ? value : Number(value)]),
    ),
    mandala_decision: String(artifact.mandala_decision ?? 'neutral') as MandalaDecisionLabel,
    score: typeof artifact.score === 'number' ? artifact.score : Number(artifact.score ?? 0),
    authority: String(artifact.authority ?? ''),
    inputs: asRecord(artifact.inputs),
    outputs: asRecord(artifact.outputs),
    code_version: String(artifact.code_version ?? 'v1'),
    justification: String(artifact.justification ?? ''),
    lineage: Array.isArray(artifact.lineage) ? (artifact.lineage.map((value) => String(value)) as readonly string[]) : [],
    runtime_artifacts_jsonl: String(artifact.runtime_artifacts_jsonl ?? ''),
  };
}

export function parseRuntimeArtifactBundleJsonl(jsonl: string): RuntimeArtifactBundle {
  const parts = jsonl
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  const bucket: Partial<RuntimeArtifactBundle> = {};
  for (const part of parts) {
    const entry = parseRuntimeArtifactLine(part);
    switch (entry.artifact_type) {
      case 'constitutional_receipt':
        bucket.receipt = {
          receipt_id: String(entry.artifact.receipt_id ?? ''),
          world_id: String(entry.artifact.world_id ?? ''),
          domain: String(entry.artifact.domain ?? 'custom') as DomainName,
          evidence_record_id: String(entry.artifact.evidence_record_id ?? ''),
          mandala_decision: String(entry.artifact.mandala_decision ?? 'neutral') as MandalaDecisionLabel,
          score: typeof entry.artifact.score === 'number' ? entry.artifact.score : Number(entry.artifact.score ?? 0),
          authority: String(entry.artifact.authority ?? ''),
          issued_at: typeof entry.artifact.issued_at === 'number' ? entry.artifact.issued_at : Number(entry.artifact.issued_at ?? 0),
          summary: String(entry.artifact.summary ?? ''),
        };
        break;
      case 'evidence_package':
        bucket.evidence_package = {
          package_id: String(entry.artifact.package_id ?? ''),
          world_id: String(entry.artifact.world_id ?? ''),
          domain: String(entry.artifact.domain ?? 'custom') as DomainName,
          evidence_record_id: String(entry.artifact.evidence_record_id ?? ''),
          sufficiency: typeof entry.artifact.sufficiency === 'number' ? entry.artifact.sufficiency : Number(entry.artifact.sufficiency ?? 0),
          completeness: typeof entry.artifact.completeness === 'number' ? entry.artifact.completeness : Number(entry.artifact.completeness ?? 0),
          lineage_depth: typeof entry.artifact.lineage_depth === 'number' ? entry.artifact.lineage_depth : Number(entry.artifact.lineage_depth ?? 0),
          metrics_present:
            typeof entry.artifact.metrics_present === 'number' ? entry.artifact.metrics_present : Number(entry.artifact.metrics_present ?? 0),
          inputs: asRecord(entry.artifact.inputs),
          outputs: asRecord(entry.artifact.outputs),
          lineage: Array.isArray(entry.artifact.lineage) ? (entry.artifact.lineage.map((value) => String(value)) as readonly string[]) : [],
          code_version: String(entry.artifact.code_version ?? 'v1'),
        };
        break;
      case 'replay_record':
        bucket.replay_record = {
          replay_id: String(entry.artifact.replay_id ?? ''),
          world_id: String(entry.artifact.world_id ?? ''),
          domain: String(entry.artifact.domain ?? 'custom') as DomainName,
          generated_at:
            typeof entry.artifact.generated_at === 'number' ? entry.artifact.generated_at : Number(entry.artifact.generated_at ?? 0),
          record_ids: Array.isArray(entry.artifact.record_ids)
            ? (entry.artifact.record_ids.map((value) => String(value)) as readonly string[])
            : [],
          records: Array.isArray(entry.artifact.records)
            ? (entry.artifact.records.map((value) => parseEvidenceRecord(asRecord(value))) as readonly EvidenceRecord[])
            : [],
          runtime_artifacts_jsonl: String(entry.artifact.runtime_artifacts_jsonl ?? ''),
        };
        break;
      case 'conformance_record':
        bucket.conformance_record = {
          conformance_id: String(entry.artifact.conformance_id ?? ''),
          world_id: String(entry.artifact.world_id ?? ''),
          domain: String(entry.artifact.domain ?? 'custom') as DomainName,
          evidence_record_id: String(entry.artifact.evidence_record_id ?? ''),
          passed: entry.artifact.passed === true,
          checks: Array.isArray(entry.artifact.checks)
            ? (entry.artifact.checks.map((value) => ({
                check_id: String(asRecord(value).check_id ?? ''),
                passed: asRecord(value).passed === true,
                message: String(asRecord(value).message ?? ''),
              })) as readonly ConformanceCheck[])
            : [],
          summary: String(entry.artifact.summary ?? ''),
        };
        break;
      case 'operator_timeline':
        bucket.operator_timeline = {
          timeline_id: String(entry.artifact.timeline_id ?? ''),
          world_id: String(entry.artifact.world_id ?? ''),
          domain: String(entry.artifact.domain ?? 'custom') as DomainName,
          events: Array.isArray(entry.artifact.events)
            ? (entry.artifact.events.map((value) => ({
                phase: String(asRecord(value).phase ?? 'intent') as OperatorTimelineEvent['phase'],
                timestamp:
                  typeof asRecord(value).timestamp === 'number'
                    ? (asRecord(value).timestamp as number)
                    : Number(asRecord(value).timestamp ?? 0),
                message: String(asRecord(value).message ?? ''),
              })) as readonly OperatorTimelineEvent[])
            : [],
        };
        break;
      case 'cori_alpha_lineage_reference':
        bucket.cori_alpha_lineage_reference = {
          reference_id: String(entry.artifact.reference_id ?? ''),
          system: 'CORI_ALPHA',
          relation: 'lineage_reference',
          connected: false,
          note: 'symbolic_only',
        };
        break;
      default:
        throw new Error(`Unknown runtime artifact type: ${entry.artifact_type}`);
    }
  }

  if (
    !bucket.receipt ||
    !bucket.evidence_package ||
    !bucket.replay_record ||
    !bucket.conformance_record ||
    !bucket.operator_timeline ||
    !bucket.cori_alpha_lineage_reference
  ) {
    throw new Error('Runtime artifact JSONL is incomplete.');
  }

  return bucket as RuntimeArtifactBundle;
}
