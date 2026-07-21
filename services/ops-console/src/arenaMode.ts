export type FactionName = 'Protoss' | 'Zerg' | 'Terran';
export type ProofLevel = 'P0' | 'P1' | 'P2' | 'P3' | 'P4' | 'P5';

export interface UltimateAbility {
  name: string;
  description: string;
  cooldownTicks: number;
  effects: Record<string, number | boolean>;
}

export interface ArenaDensityProfile {
  name: string;
  terrainWeights: Record<string, number>;
  centerBias?: string[];
  edgeBias?: string[];
}

export interface ArenaMap {
  mapId: string;
  title: string;
  width: number;
  height: number;
  densityProfile: ArenaDensityProfile;
  terrainGrid: string[][];
  terrainSummary: { terrain: string; count: number }[];
}

export interface AgentTalent {
  name: string;
  description: string;
  modifiers: Record<string, number>;
}

export interface ArenaAgent {
  agentId: string;
  name: string;
  faction: FactionName;
  baseStats: {
    constraintDensity: number;
    evidenceWeight: number;
    ciemsProgress: number;
    riskTolerance: number;
  };
  talents: AgentTalent[];
  ultimate: UltimateAbility;
  ultimateReadyTick: number;
  synergyMods: Record<string, number>;
}

export interface ArenaTraceEvent {
  tick: number;
  kind: string;
  actor?: string;
  payload: Record<string, unknown>;
}

export interface ArenaTrace {
  traceId: string;
  matchId: string;
  mapId: string;
  recordedAt: string;
  events: ArenaTraceEvent[];
  outcome: {
    winner: string;
    score: number;
    reason: string;
  };
}

export interface TournamentMatch {
  matchId: string;
  agents: string[];
  winner: string | null;
  tracePath: string | null;
  traceId: string | null;
  summary: string;
}

export interface TournamentBracket {
  tournamentId: string;
  seedOrder: string[];
  rounds: TournamentMatch[][];
}

export interface ReplayAnalysisReport {
  traceId: string;
  matchId: string;
  tracePath: string;
  replayable: boolean;
  integrityScore: number;
  warnings: string[];
  notes: string[];
  eventCount: number;
  openReplayPath: string;
  timeline: ArenaTimelineEntry[];
  resourceUsage: ArenaResourceUsage;
}

export interface ArenaTimelineEntry {
  stage:
    | 'Intent'
    | 'Evidence'
    | 'Authority'
    | 'Runtime decision'
    | 'Resource usage'
    | 'Proof receipt'
    | 'Replay verification'
    | 'Final outcome';
  detail: string;
  status: 'PASS' | 'WARN' | 'FAIL' | 'INFO';
}

export interface ArenaResourceUsage {
  cpu: number;
  memory: number;
  network: number;
  latency: number;
  throughput: number;
}

export interface ArenaChallengeScenario {
  scenarioId: string;
  name: string;
  description: string;
  focus: 'runtime' | 'agent' | 'governance' | 'replay' | 'evidence' | 'network' | 'backend';
  severity: 'low' | 'moderate' | 'high' | 'extreme';
  pressures: {
    resourceExhaustion: number;
    adversarialRequests: number;
    governanceViolations: number;
    replayMismatches: number;
    evidenceCorruption: number;
    networkDegradation: number;
    backendFailures: number;
  };
}

export interface ArenaChallengePack {
  packId: string;
  name: string;
  description: string;
  scenarioIds: string[];
}

export interface ArenaChallengeRun {
  runId: string;
  scenarioId: string;
  scenarioName: string;
  focus: ArenaChallengeScenario['focus'];
  severity: ArenaChallengeScenario['severity'];
  status: 'PASS' | 'WARN' | 'FAIL';
  proofLevel: ProofLevel;
  constitutionalMaturity: number;
  replaySuccess: boolean;
  determinism: number;
  governanceCompliance: number;
  performance: number;
  resourceEfficiency: number;
  failureRecovery: number;
  challengePassRate: number;
  resourceUsage: ArenaResourceUsage;
  evidenceReceipts: string[];
  proofReceiptId: string;
  timeline: ArenaTimelineEntry[];
  battleScars: string[];
  finalOutcome: string;
}

export interface ArenaScorecard {
  proofLevel: ProofLevel;
  constitutionalMaturity: number;
  replaySuccess: number;
  determinism: number;
  governanceCompliance: number;
  performance: number;
  resourceEfficiency: number;
  failureRecovery: number;
  challengePassRate: number;
  readinessLevel: 'prototype' | 'candidate' | 'production-ready';
}

export interface ArenaBattleScar {
  scarId: string;
  type:
    | 'failed_scenario'
    | 'governance_violation'
    | 'replay_failure'
    | 'near_miss'
    | 'performance_regression'
    | 'successful_recovery';
  title: string;
  detail: string;
  scenarioId: string;
  severity: 'low' | 'medium' | 'high';
}

export interface ArenaReadinessCertificate {
  certificateId: string;
  proofSurface: string;
  challengeResults: string;
  replayVerification: string;
  conformanceStatus: string;
  evidenceReceipts: string[];
  constitutionalMaturity: number;
  readinessLevel: string;
  issuedAt: string;
}

export interface ArenaLifecyclePhase {
  stage: 'Design' | 'Build' | 'Verify' | 'Challenge' | 'Certify' | 'Release' | 'Observe' | 'Learn';
  status: 'complete' | 'in-progress' | 'future';
  description: string;
  artifacts: string[];
}

export interface ArenaSnapshot {
  arenaId: string;
  title: string;
  densityProfile: ArenaDensityProfile;
  map: ArenaMap;
  factions: FactionRoster[];
  agents: ArenaAgent[];
  tournament: TournamentBracket;
  traces: Record<string, ArenaTrace>;
  replayReports: Record<string, ReplayAnalysisReport>;
  challengePacks: ArenaChallengePack[];
  challengeScenarios: ArenaChallengeScenario[];
  challengeRuns: ArenaChallengeRun[];
  scorecard: ArenaScorecard;
  battleScars: ArenaBattleScar[];
  lifecycle: ArenaLifecyclePhase[];
  certificate: ArenaReadinessCertificate;
  digitalThread: string[];
  globalModifiers: Record<string, number | boolean>;
}

export interface FactionRoster {
  faction: FactionName;
  color: string;
  doctrine: string;
  ultimate: UltimateAbility;
  roster: string[];
}

const TERRAIN_TYPES = {
  TrustBastion: 'Trust Bastion',
  EvidenceFloodplain: 'Evidence Floodplain',
  DisputedEdge: 'Disputed Edge',
  InvariantRidge: 'Invariant Ridge',
  RelaySpine: 'Relay Spine',
} as const;

const ULT_PROTOSS_WARP: UltimateAbility = {
  name: 'Warp Governance',
  description: 'Temporarily reduce constraint density and boost evidence weight.',
  cooldownTicks: 50,
  effects: {
    constraint_density_multiplier: 0.5,
    evidence_weight_multiplier: 1.5,
    duration_ticks: 10,
  },
};

const ULT_ZERG_FLOOD: UltimateAbility = {
  name: 'Evidence Flood',
  description: 'Spawn a swarm of low-quality evidence to overwhelm constraints.',
  cooldownTicks: 40,
  effects: {
    evidence_generation_burst: 20,
    invariant_risk_tolerance: 1.3,
    duration_ticks: 8,
  },
};

const ULT_TERRAN_LOCKDOWN: UltimateAbility = {
  name: 'Lockdown',
  description: 'Freeze state changes and CIEMS progression in a zone.',
  cooldownTicks: 60,
  effects: {
    state_freeze: true,
    ciems_progress_multiplier: 0,
    duration_ticks: 12,
  },
};

const FACTION_ROSTERS: FactionRoster[] = [
  {
    faction: 'Protoss',
    color: '#5b7cff',
    doctrine: 'Structured authority, high evidence weight, low entropy state transitions.',
    ultimate: ULT_PROTOSS_WARP,
    roster: ['Aster', 'Lumen', 'Solace'],
  },
  {
    faction: 'Zerg',
    color: '#10b981',
    doctrine: 'Swarm evidence, burst throughput, risk-tolerant expansion.',
    ultimate: ULT_ZERG_FLOOD,
    roster: ['Kerr', 'Vanta', 'Nyx'],
  },
  {
    faction: 'Terran',
    color: '#f59e0b',
    doctrine: 'Disciplined locking, zone control, and state stabilization.',
    ultimate: ULT_TERRAN_LOCKDOWN,
    roster: ['Cass', 'Rook', 'Talon'],
  },
];

const FACTION_TALENTS: Record<FactionName, AgentTalent[]> = {
  Protoss: [
    { name: 'Evidence Hoarder', description: 'Retains high-value evidence for judicial turns.', modifiers: { evidence_weight_multiplier: 1.1 } },
    { name: 'Macro Overdrive', description: 'Improves baseline production and feed throughput.', modifiers: { macro_cost_multiplier: 0.85 } },
    { name: 'Invariant Shield', description: 'Converts one class of invariant loss into resilience.', modifiers: { invariant_penalty_multiplier: 0.75 } },
    { name: 'Warp Canticle', description: 'Extends the duration of governance-altering effects.', modifiers: { duration_multiplier: 1.15 } },
  ],
  Zerg: [
    { name: 'Evidence Flood', description: 'Generates large batches of low-fidelity evidence.', modifiers: { evidence_generation_burst: 8 } },
    { name: 'Swarm Surge', description: 'Amplifies burst actions and rush pressure.', modifiers: { burst_multiplier: 1.2 } },
    { name: 'Adaptive Spores', description: 'Raises tolerance to adversarial churn.', modifiers: { invariant_risk_tolerance: 1.08 } },
    { name: 'Replication Spiral', description: 'Makes repeated actions cheap but noisy.', modifiers: { action_cost_multiplier: 0.88 } },
  ],
  Terran: [
    { name: 'Lockdown Protocol', description: 'Helps the agent freeze local state changes.', modifiers: { state_freeze_resistance: 0.2 } },
    { name: 'Fortified Command', description: 'Improves compliance and CIEMS continuity.', modifiers: { ciems_progress_multiplier: 1.12 } },
    { name: 'Audit Net', description: 'Captures more detailed replay history.', modifiers: { replay_detail_multiplier: 1.1 } },
    { name: 'Railgun Discipline', description: 'Sharpens deterministic turn execution.', modifiers: { variance_multiplier: 0.9 } },
  ],
};

const RNG_MOD = 0xffffffff;

function createSeededRng(seed: string): () => number {
  let h1 = 1779033703 ^ seed.length;
  let h2 = 3144134277 ^ seed.length;
  let h3 = 1013904242 ^ seed.length;
  let h4 = 2773480762 ^ seed.length;

  for (let i = 0; i < seed.length; i += 1) {
    const k = seed.charCodeAt(i);
    h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
    h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
    h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
    h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
  }

  h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067);
  h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233);
  h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213);
  h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);

  return () => {
    h1 = (Math.imul(h1 ^ (h1 >>> 15), 2246822507) + h4) | 0;
    h2 = (Math.imul(h2 ^ (h2 >>> 13), 3266489909) + h1) | 0;
    h3 = (Math.imul(h3 ^ (h3 >>> 16), 2246822507) + h2) | 0;
    h4 = (Math.imul(h4 ^ (h4 >>> 17), 3266489909) + h3) | 0;
    return ((h1 ^ h2 ^ h3 ^ h4) >>> 0) / RNG_MOD;
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function stableSlug(input: string): string {
  return input.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function pickWeighted<T>(rng: () => number, entries: readonly T[], weights: readonly number[]): T {
  const total = weights.reduce((sum, weight) => sum + weight, 0);
  let cursor = rng() * total;
  for (let index = 0; index < entries.length; index += 1) {
    cursor -= weights[index] ?? 0;
    if (cursor <= 0) {
      return entries[index];
    }
  }
  return entries[entries.length - 1];
}

function summarizeTerrain(terrainGrid: string[][]): { terrain: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const row of terrainGrid) {
    for (const terrain of row) {
      counts.set(terrain, (counts.get(terrain) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .map(([terrain, count]) => ({ terrain, count }))
    .sort((left, right) => right.count - left.count || left.terrain.localeCompare(right.terrain));
}

export class ArenaMapGenerator {
  constructor(
    private readonly width: number,
    private readonly height: number,
    private readonly rng: () => number = Math.random,
  ) {}

  generate(densityProfile: ArenaDensityProfile): ArenaMap {
    const terrainTypes = Object.values(TERRAIN_TYPES);
    const grid: string[][] = [];

    for (let y = 0; y < this.height; y += 1) {
      const row: string[] = [];
      for (let x = 0; x < this.width; x += 1) {
        row.push(this.pickTerrain(terrainTypes, densityProfile, x, y));
      }
      grid.push(row);
    }

    return {
      mapId: `arena-map-${stableSlug(densityProfile.name)}-${this.width}x${this.height}`,
      title: densityProfile.name,
      width: this.width,
      height: this.height,
      densityProfile,
      terrainGrid: grid,
      terrainSummary: summarizeTerrain(grid),
    };
  }

  private pickTerrain(terrainTypes: string[], densityProfile: ArenaDensityProfile, x: number, y: number): string {
    const centerX = (this.width - 1) / 2;
    const centerY = (this.height - 1) / 2;
    const distance = Math.hypot(x - centerX, y - centerY);
    const maxDistance = Math.hypot(centerX, centerY) || 1;
    const radialBias = 1 - distance / maxDistance;

    const weights = terrainTypes.map((terrain) => {
      const baseWeight = densityProfile.terrainWeights[terrain] ?? 1;
      const centerBonus = densityProfile.centerBias?.includes(terrain) ? 1 + radialBias * 0.6 : 1;
      const edgeBonus = densityProfile.edgeBias?.includes(terrain) ? 1 + (1 - radialBias) * 0.7 : 1;
      return Math.max(0.05, baseWeight * centerBonus * edgeBonus);
    });

    return pickWeighted(this.rng, terrainTypes, weights);
  }
}

export class TalentSynergyEngine {
  computeSynergies(agent: ArenaAgent): Record<string, number> {
    const synergyMods: Record<string, number> = {};
    const names = new Set(agent.talents.map((talent) => talent.name));

    if (names.has('Evidence Hoarder') && names.has('Macro Overdrive')) {
      synergyMods.macro_cost_multiplier = 0.6;
      synergyMods.evidence_weight_multiplier = 1.15;
    }

    if (agent.faction === 'Protoss' && names.has('Invariant Shield')) {
      synergyMods.invariant_penalty_multiplier = 0.3;
    }

    if (agent.faction === 'Zerg' && names.has('Evidence Flood')) {
      synergyMods.evidence_generation_burst = 6;
      synergyMods.invariant_risk_tolerance = 0.15;
    }

    if (agent.faction === 'Terran' && names.has('Lockdown Protocol')) {
      synergyMods.state_freeze_resistance = 0.3;
      synergyMods.ciems_progress_multiplier = 1.1;
    }

    return synergyMods;
  }
}

function mergeModifiers(...mods: Array<Record<string, number | boolean>>): Record<string, number | boolean> {
  const merged: Record<string, number | boolean> = {};
  for (const current of mods) {
    for (const [key, value] of Object.entries(current)) {
      if (typeof value === 'number' && typeof merged[key] === 'number') {
        merged[key] = Number((Number(merged[key]) * value).toFixed(4));
        continue;
      }
      merged[key] = value;
    }
  }
  return merged;
}

function createAgent(
  faction: FactionName,
  name: string,
  ultimateReadyTick: number,
  talentNames: string[],
): ArenaAgent {
  const talents = talentNames.map((talentName) => {
    const talent = FACTION_TALENTS[faction].find((entry) => entry.name === talentName);
    if (!talent) {
      throw new Error(`Unknown talent ${talentName} for faction ${faction}`);
    }
    return talent;
  });

  const baseStatsByFaction: Record<FactionName, ArenaAgent['baseStats']> = {
    Protoss: { constraintDensity: 72, evidenceWeight: 88, ciemsProgress: 62, riskTolerance: 48 },
    Zerg: { constraintDensity: 58, evidenceWeight: 55, ciemsProgress: 78, riskTolerance: 84 },
    Terran: { constraintDensity: 81, evidenceWeight: 69, ciemsProgress: 74, riskTolerance: 56 },
  };

  const agent: ArenaAgent = {
    agentId: `agent-${stableSlug(name)}`,
    name,
    faction,
    baseStats: baseStatsByFaction[faction],
    talents,
    ultimate: FACTION_ROSTERS.find((roster) => roster.faction === faction)?.ultimate ?? ULT_PROTOSS_WARP,
    ultimateReadyTick,
    synergyMods: {},
  };

  const synergyEngine = new TalentSynergyEngine();
  agent.synergyMods = synergyEngine.computeSynergies(agent);
  return agent;
}

function resolveEffectiveStats(agent: ArenaAgent): {
  constraintDensity: number;
  evidenceWeight: number;
  ciemsProgress: number;
  riskTolerance: number;
} {
  const modifiers = mergeModifiers(
    {
      constraint_density_multiplier: 1,
      evidence_weight_multiplier: 1,
      ciems_progress_multiplier: 1,
      invariant_risk_tolerance: 1,
    },
    agent.talents.reduce<Record<string, number | boolean>>((acc, talent) => ({ ...acc, ...talent.modifiers }), {}),
    agent.synergyMods,
  );

  return {
    constraintDensity: Number((agent.baseStats.constraintDensity * Number(modifiers.constraint_density_multiplier ?? 1)).toFixed(2)),
    evidenceWeight: Number((agent.baseStats.evidenceWeight * Number(modifiers.evidence_weight_multiplier ?? 1)).toFixed(2)),
    ciemsProgress: Number((agent.baseStats.ciemsProgress * Number(modifiers.ciems_progress_multiplier ?? 1)).toFixed(2)),
    riskTolerance: Number((agent.baseStats.riskTolerance * Number(modifiers.invariant_risk_tolerance ?? 1)).toFixed(2)),
  };
}

class ArenaMatchEngine {
  constructor(private readonly rng: () => number) {}

  startMatch(matchId: string, left: ArenaAgent, right: ArenaAgent, map: ArenaMap): ArenaTrace {
    const leftStats = resolveEffectiveStats(left);
    const rightStats = resolveEffectiveStats(right);
    const events: ArenaTraceEvent[] = [];
    let leftScore = 0;
    let rightScore = 0;
    let currentTick = 0;
    let stateFreezeUntil = -1;

    const leftUltimateAvailable = left.ultimateReadyTick <= currentTick;
    const rightUltimateAvailable = right.ultimateReadyTick <= currentTick;

    if (leftUltimateAvailable) {
      this.applyUltimate(events, left, left.ultimate, currentTick, 'left');
      leftScore += this.scoreUltimate(left, left.ultimate, leftStats, map);
      if (left.ultimate.effects.state_freeze === true) {
        stateFreezeUntil = currentTick + Number(left.ultimate.effects.duration_ticks ?? 0);
      }
    }

    if (rightUltimateAvailable && currentTick >= stateFreezeUntil) {
      this.applyUltimate(events, right, right.ultimate, currentTick, 'right');
      rightScore += this.scoreUltimate(right, right.ultimate, rightStats, map);
      if (right.ultimate.effects.state_freeze === true) {
        stateFreezeUntil = currentTick + Number(right.ultimate.effects.duration_ticks ?? 0);
      }
    } else if (rightUltimateAvailable) {
      events.push({
        tick: currentTick,
        kind: 'ULTIMATE_BLOCKED',
        actor: right.name,
        payload: { reason: 'state freeze prevented activation' },
      });
    }

    for (currentTick = 1; currentTick <= 6; currentTick += 1) {
      const activeFreeze = currentTick <= stateFreezeUntil;
      const terrainPressure = map.terrainSummary[0]?.count ?? 0;
      const burst = activeFreeze ? 0 : 1 + this.rng();
      leftScore += this.evaluateTurn(left, leftStats, terrainPressure, burst, currentTick);
      rightScore += this.evaluateTurn(right, rightStats, terrainPressure, burst, currentTick);
      events.push({
        tick: currentTick,
        kind: activeFreeze ? 'STATE_FROZEN' : 'TICK_RESOLVED',
        payload: {
          leftScore: Number(leftScore.toFixed(2)),
          rightScore: Number(rightScore.toFixed(2)),
          stateFreezeUntil,
        },
      });
    }

    const winner = leftScore >= rightScore ? left : right;
    const loser = winner === left ? right : left;
    const score = Math.abs(leftScore - rightScore);

    events.push({
      tick: 7,
      kind: 'MATCH_RESOLVED',
      payload: {
        winner: winner.name,
        loser: loser.name,
        score: Number(score.toFixed(2)),
      },
    });

    return {
      traceId: `trace-${matchId}`,
      matchId,
      mapId: map.mapId,
      recordedAt: new Date('2026-07-08T12:00:00.000Z').toISOString(),
      events,
      outcome: {
        winner: winner.name,
        score: Number(score.toFixed(2)),
        reason: `${winner.faction} pressure held through round pressure`,
      },
    };
  }

  private applyUltimate(
    events: ArenaTraceEvent[],
    agent: ArenaAgent,
    ultimate: UltimateAbility,
    tick: number,
    side: 'left' | 'right',
  ): void {
    events.push({
      tick,
      kind: 'ULTIMATE_TRIGGERED',
      actor: agent.name,
      payload: {
        side,
        ultimate: ultimate.name,
        effects: ultimate.effects,
      },
    });
    events.push({
      tick: tick + 1,
      kind: 'CNODE_UPDATE',
      actor: agent.name,
      payload: {
        constraintDensity: ultimate.effects.constraint_density_multiplier ?? 1,
        evidenceWeight: ultimate.effects.evidence_weight_multiplier ?? 1,
        evidenceBurst: ultimate.effects.evidence_generation_burst ?? 0,
        ciemsProgressMultiplier: ultimate.effects.ciems_progress_multiplier ?? 1,
      },
    });
  }

  private scoreUltimate(
    agent: ArenaAgent,
    ultimate: UltimateAbility,
    stats: ReturnType<typeof resolveEffectiveStats>,
    map: ArenaMap,
  ): number {
    const weight = Number(ultimate.effects.evidence_weight_multiplier ?? 1);
    const density = Number(ultimate.effects.constraint_density_multiplier ?? 1);
    const burst = Number(ultimate.effects.evidence_generation_burst ?? 0);
    const terrainFactor = map.terrainSummary[0]?.count ?? 0;
    return (
      stats.evidenceWeight * weight * 0.08
      + stats.constraintDensity * (2 - density) * 0.04
      + burst * 0.7
      + terrainFactor * 0.01
      + (agent.faction === 'Terran' && ultimate.name === 'Lockdown' ? 4 : 0)
    );
  }

  private evaluateTurn(
    agent: ArenaAgent,
    stats: ReturnType<typeof resolveEffectiveStats>,
    terrainPressure: number,
    burst: number,
    tick: number,
  ): number {
    const variance = 0.85 + this.rng() * 0.3;
    const factionBias: Record<FactionName, number> = {
      Protoss: 1.1,
      Zerg: 1.2,
      Terran: 1.05,
    };
    const base = stats.ciemsProgress * 0.08
      + stats.evidenceWeight * 0.04
      + stats.riskTolerance * 0.02
      - stats.constraintDensity * 0.01;
    return Number(((base * factionBias[agent.faction]) + burst + terrainPressure * 0.002 + tick * 0.05) * variance);
  }
}

class ReplayAnalyzer {
  analyze(trace: ArenaTrace, tracePath: string): ReplayAnalysisReport {
    const warnings: string[] = [];
    const notes: string[] = [];
    const ultimateEvents = trace.events.filter((event) => event.kind === 'ULTIMATE_TRIGGERED');
    const freezeEvents = trace.events.filter((event) => event.kind === 'STATE_FROZEN');
    const finalEvent = trace.events[trace.events.length - 1];
    const timeline = buildReplayTimeline(trace);
    const resourceUsage = buildReplayResourceUsage(trace);

    if (ultimateEvents.length === 0) {
      warnings.push('no ultimate events were recorded');
    }

    if (!finalEvent || finalEvent.kind !== 'MATCH_RESOLVED') {
      warnings.push('trace did not resolve with a terminal match event');
    }

    if (freezeEvents.length > 0) {
      notes.push('state freeze was active during part of the replay');
    }

    const integrityScore = clamp(1 - warnings.length * 0.18 + notes.length * 0.04, 0, 1);

    return {
      traceId: trace.traceId,
      matchId: trace.matchId,
      tracePath,
      replayable: warnings.length === 0,
      integrityScore: Number(integrityScore.toFixed(3)),
      warnings,
      notes,
      eventCount: trace.events.length,
      openReplayPath: tracePath,
      timeline,
      resourceUsage,
    };
  }
}

function buildReplayTimeline(trace: ArenaTrace): ArenaTimelineEntry[] {
  const ultimateEvent = trace.events.find((event) => event.kind === 'ULTIMATE_TRIGGERED');
  const cnodeEvent = trace.events.find((event) => event.kind === 'CNODE_UPDATE');
  const resolvedEvent = trace.events.find((event) => event.kind === 'MATCH_RESOLVED');
  const stateEvents = trace.events.filter((event) => event.kind === 'STATE_FROZEN' || event.kind === 'TICK_RESOLVED');

  return [
    {
      stage: 'Intent',
      detail: `Match ${trace.matchId} set out to prove governed execution on ${trace.mapId}.`,
      status: 'INFO',
    },
    {
      stage: 'Evidence',
      detail: ultimateEvent ? `Evidence was captured through ${ultimateEvent.actor ?? 'an agent'} ultimate activation.` : 'No ultimate evidence was captured.',
      status: ultimateEvent ? 'PASS' : 'WARN',
    },
    {
      stage: 'Authority',
      detail: cnodeEvent
        ? `Authority updates were recorded in ${String(cnodeEvent.payload.authority ?? 'the runtime ledger')}.`
        : 'No authority update was recorded.',
      status: cnodeEvent ? 'PASS' : 'WARN',
    },
    {
      stage: 'Runtime decision',
      detail: stateEvents.length > 0
        ? `Runtime produced ${stateEvents.length} state step(s) before resolution.`
        : 'Runtime produced no state steps.',
      status: stateEvents.length > 0 ? 'PASS' : 'WARN',
    },
    {
      stage: 'Resource usage',
      detail: summarizeResourceUsage(trace),
      status: stateEvents.length > 0 ? 'PASS' : 'INFO',
    },
    {
      stage: 'Proof receipt',
      detail: `Proof receipt ${trace.traceId} recorded at ${trace.recordedAt}.`,
      status: 'PASS',
    },
    {
      stage: 'Replay verification',
      detail: `Replay verification ${resolvedEvent ? 'closed with a terminal event' : 'did not reach a terminal event'}.`,
      status: resolvedEvent ? 'PASS' : 'FAIL',
    },
    {
      stage: 'Final outcome',
      detail: `${trace.outcome.winner} won by ${trace.outcome.score.toFixed(2)} points. ${trace.outcome.reason}.`,
      status: 'PASS',
    },
  ];
}

function buildReplayResourceUsage(trace: ArenaTrace): ArenaResourceUsage {
  const tickCount = Math.max(1, trace.events.filter((event) => event.kind === 'TICK_RESOLVED' || event.kind === 'STATE_FROZEN').length);
  const ultimateCount = trace.events.filter((event) => event.kind === 'ULTIMATE_TRIGGERED').length;
  const cnodeCount = trace.events.filter((event) => event.kind === 'CNODE_UPDATE').length;
  const freezeCount = trace.events.filter((event) => event.kind === 'STATE_FROZEN').length;
  const factor = clamp(trace.outcome.score / 20, 0, 1);

  return {
    cpu: Number((35 + tickCount * 5 + ultimateCount * 8 + factor * 18).toFixed(1)),
    memory: Number((28 + cnodeCount * 4 + freezeCount * 5 + factor * 12).toFixed(1)),
    network: Number((18 + trace.events.length * 1.5 + factor * 10).toFixed(1)),
    latency: Number((20 + freezeCount * 11 + factor * 25).toFixed(1)),
    throughput: Number((100 - tickCount * 5 - freezeCount * 8 + trace.outcome.score * 2).toFixed(1)),
  };
}

function summarizeResourceUsage(trace: ArenaTrace): string {
  const usage = buildReplayResourceUsage(trace);
  return `CPU ${usage.cpu}%, memory ${usage.memory}%, network ${usage.network}%, latency ${usage.latency}ms, throughput ${usage.throughput}.`;
}

function buildArenaChallengeScenarios(): ArenaChallengeScenario[] {
  return [
    {
      scenarioId: 'normal-execution',
      name: 'Normal execution',
      description: 'Baseline contract flow with no injected stressors.',
      focus: 'runtime',
      severity: 'low',
      pressures: {
        resourceExhaustion: 0.08,
        adversarialRequests: 0.05,
        governanceViolations: 0.02,
        replayMismatches: 0.03,
        evidenceCorruption: 0.02,
        networkDegradation: 0.04,
        backendFailures: 0.02,
      },
    },
    {
      scenarioId: 'resource-exhaustion',
      name: 'Resource exhaustion',
      description: 'Memory and CPU pressure are pushed into the red.',
      focus: 'runtime',
      severity: 'high',
      pressures: {
        resourceExhaustion: 0.9,
        adversarialRequests: 0.15,
        governanceViolations: 0.08,
        replayMismatches: 0.08,
        evidenceCorruption: 0.05,
        networkDegradation: 0.12,
        backendFailures: 0.1,
      },
    },
    {
      scenarioId: 'adversarial-requests',
      name: 'Adversarial requests',
      description: 'Injected input attempts to bend authority and intent handling.',
      focus: 'agent',
      severity: 'high',
      pressures: {
        resourceExhaustion: 0.18,
        adversarialRequests: 0.92,
        governanceViolations: 0.38,
        replayMismatches: 0.15,
        evidenceCorruption: 0.1,
        networkDegradation: 0.08,
        backendFailures: 0.05,
      },
    },
    {
      scenarioId: 'governance-violations',
      name: 'Governance violations',
      description: 'Rules are intentionally broken to verify enforcement boundaries.',
      focus: 'governance',
      severity: 'extreme',
      pressures: {
        resourceExhaustion: 0.15,
        adversarialRequests: 0.2,
        governanceViolations: 0.96,
        replayMismatches: 0.14,
        evidenceCorruption: 0.1,
        networkDegradation: 0.06,
        backendFailures: 0.04,
      },
    },
    {
      scenarioId: 'replay-mismatches',
      name: 'Replay mismatches',
      description: 'The replay layer is challenged to prove determinism under divergence.',
      focus: 'replay',
      severity: 'high',
      pressures: {
        resourceExhaustion: 0.12,
        adversarialRequests: 0.16,
        governanceViolations: 0.12,
        replayMismatches: 0.95,
        evidenceCorruption: 0.18,
        networkDegradation: 0.1,
        backendFailures: 0.08,
      },
    },
    {
      scenarioId: 'evidence-corruption',
      name: 'Evidence corruption',
      description: 'Evidence receipts are perturbed to test trust boundaries.',
      focus: 'evidence',
      severity: 'high',
      pressures: {
        resourceExhaustion: 0.14,
        adversarialRequests: 0.18,
        governanceViolations: 0.16,
        replayMismatches: 0.28,
        evidenceCorruption: 0.94,
        networkDegradation: 0.1,
        backendFailures: 0.08,
      },
    },
    {
      scenarioId: 'network-degradation',
      name: 'Network degradation',
      description: 'Latency spikes and packet loss stress the runtime envelope.',
      focus: 'network',
      severity: 'moderate',
      pressures: {
        resourceExhaustion: 0.1,
        adversarialRequests: 0.08,
        governanceViolations: 0.08,
        replayMismatches: 0.2,
        evidenceCorruption: 0.12,
        networkDegradation: 0.92,
        backendFailures: 0.1,
      },
    },
    {
      scenarioId: 'backend-failures',
      name: 'Backend failures',
      description: 'Service outages and dependency drops test recovery behavior.',
      focus: 'backend',
      severity: 'extreme',
      pressures: {
        resourceExhaustion: 0.18,
        adversarialRequests: 0.12,
        governanceViolations: 0.12,
        replayMismatches: 0.24,
        evidenceCorruption: 0.18,
        networkDegradation: 0.2,
        backendFailures: 0.96,
      },
    },
  ];
}

function buildArenaChallengePacks(scenarios: ArenaChallengeScenario[]): ArenaChallengePack[] {
  return [
    {
      packId: 'pack-core-constitutional-flow',
      name: 'Core constitutional flow',
      description: 'Validates normal execution and routine runtime behavior.',
      scenarioIds: scenarios.filter((scenario) => scenario.focus === 'runtime').map((scenario) => scenario.scenarioId),
    },
    {
      packId: 'pack-adversarial-pressure',
      name: 'Adversarial pressure',
      description: 'Exercises governance, replay, and intent safety under hostile input.',
      scenarioIds: scenarios.filter((scenario) => ['agent', 'governance', 'replay', 'evidence'].includes(scenario.focus)).map((scenario) => scenario.scenarioId),
    },
    {
      packId: 'pack-infrastructure-resilience',
      name: 'Infrastructure resilience',
      description: 'Tests failure injection, network degradation, and backend recovery.',
      scenarioIds: scenarios.filter((scenario) => ['network', 'backend'].includes(scenario.focus)).map((scenario) => scenario.scenarioId),
    },
  ];
}

function buildArenaChallengeRuns(
  seed: string,
  agents: ArenaAgent[],
  map: ArenaMap,
  scenarios: ArenaChallengeScenario[],
  tournament: TournamentBracket,
): ArenaChallengeRun[] {
  const arenaRng = createSeededRng(`${seed}:challenge`);
  const averageConstraintDensity = average(agents.map((agent) => agent.baseStats.constraintDensity));
  const averageEvidenceWeight = average(agents.map((agent) => agent.baseStats.evidenceWeight));
  const averageCiemsProgress = average(agents.map((agent) => agent.baseStats.ciemsProgress));
  const averageRiskTolerance = average(agents.map((agent) => agent.baseStats.riskTolerance));
  const mapRigidity = average(map.terrainSummary.map((entry) => entry.count));

  return scenarios.map((scenario, index) => {
    const rng = createSeededRng(`${seed}:challenge:${scenario.scenarioId}`);
    const pressure = Object.values(scenario.pressures).reduce((sum, value) => sum + value, 0) / Object.keys(scenario.pressures).length;
    const runtimePressure = clamp(0.42 + pressure * 0.45 + (arenaRng() * 0.08) - (averageRiskTolerance / 250), 0, 1);
    const governanceCompliance = clamp(1 - scenario.pressures.governanceViolations * 0.7 + averageEvidenceWeight / 400, 0, 1);
    const determinism = clamp(1 - scenario.pressures.replayMismatches * 0.55 + averageConstraintDensity / 500, 0, 1);
    const performance = clamp(1 - scenario.pressures.resourceExhaustion * 0.5 - scenario.pressures.networkDegradation * 0.22 + averageCiemsProgress / 500, 0, 1);
    const resourceEfficiency = clamp(1 - scenario.pressures.resourceExhaustion * 0.45 + mapRigidity / 500, 0, 1);
    const failureRecovery = clamp(1 - scenario.pressures.backendFailures * 0.5 - scenario.pressures.evidenceCorruption * 0.25 + averageRiskTolerance / 450, 0, 1);
    const replaySuccess = determinism > 0.63 && scenario.pressures.replayMismatches < 0.7;
    const challengePassRate = clamp((governanceCompliance * 0.28) + (determinism * 0.22) + (performance * 0.2) + (resourceEfficiency * 0.15) + (failureRecovery * 0.15), 0, 1);
    const constitutionalMaturity = Number(((challengePassRate * 100) * 0.55 + runtimePressure * 45).toFixed(1));
    const status = challengePassRate >= 0.78 && governanceCompliance >= 0.75 && replaySuccess ? 'PASS' : challengePassRate >= 0.58 ? 'WARN' : 'FAIL';
    const resourceUsage = {
      cpu: Number((36 + scenario.pressures.resourceExhaustion * 42 + runtimePressure * 16 + rng() * 4).toFixed(1)),
      memory: Number((30 + scenario.pressures.evidenceCorruption * 20 + scenario.pressures.backendFailures * 18 + rng() * 5).toFixed(1)),
      network: Number((18 + scenario.pressures.networkDegradation * 60 + scenario.pressures.adversarialRequests * 12 + rng() * 4).toFixed(1)),
      latency: Number((22 + scenario.pressures.networkDegradation * 120 + scenario.pressures.backendFailures * 90 + rng() * 8).toFixed(1)),
      throughput: Number((100 - scenario.pressures.resourceExhaustion * 30 - scenario.pressures.networkDegradation * 22 + averageCiemsProgress * 0.25).toFixed(1)),
    };
    const proofLevel = scoreToProofLevel(constitutionalMaturity);
    const proofReceiptId = `receipt-${scenario.scenarioId}-${stableSlug(seed)}`;
    const evidenceReceipts = [`evidence-${scenario.scenarioId}`, `proof-surface-${stableSlug(map.mapId)}`];
    const timeline: ArenaTimelineEntry[] = [
      {
        stage: 'Intent',
        detail: `Scenario ${scenario.name} is intended to challenge ${scenario.focus} behavior under ${scenario.severity} severity.`,
        status: 'INFO',
      },
      {
        stage: 'Evidence',
        detail: `Evidence receipts ${evidenceReceipts.join(', ')} were ${scenario.pressures.evidenceCorruption > 0.7 ? 'stress-tested' : 'preserved'}.`,
        status: scenario.pressures.evidenceCorruption > 0.7 ? 'WARN' : 'PASS',
      },
      {
        stage: 'Authority',
        detail: `Authority delegation was resolved against ${tournament.tournamentId}.`,
        status: scenario.pressures.governanceViolations > 0.7 ? 'WARN' : 'PASS',
      },
      {
        stage: 'Runtime decision',
        detail: `${status === 'FAIL' ? 'Runtime rejected the scenario' : 'Runtime adapted to the scenario'} with ${Math.round(runtimePressure * 100)}% pressure.`,
        status,
      },
      {
        stage: 'Resource usage',
        detail: `CPU ${resourceUsage.cpu}%, memory ${resourceUsage.memory}%, network ${resourceUsage.network}%, latency ${resourceUsage.latency}ms, throughput ${resourceUsage.throughput}.`,
        status: resourceUsage.latency > 100 ? 'WARN' : 'PASS',
      },
      {
        stage: 'Proof receipt',
        detail: `Proof receipt ${proofReceiptId} recorded as ${proofLevel}.`,
        status: 'PASS',
      },
      {
        stage: 'Replay verification',
        detail: replaySuccess ? 'Replay verification matched the deterministic challenge path.' : 'Replay verification exposed divergence or mismatch.',
        status: replaySuccess ? 'PASS' : 'FAIL',
      },
      {
        stage: 'Final outcome',
        detail: `${status} - constitutional maturity ${constitutionalMaturity.toFixed(1)}.`,
        status,
      },
    ];

    const battleScarsForRun: string[] = [];
    if (status === 'FAIL') {
      battleScarsForRun.push('failed scenario');
    }
    if (!replaySuccess) {
      battleScarsForRun.push('replay failure');
    }
    if (scenario.pressures.governanceViolations > 0.7) {
      battleScarsForRun.push('governance violation');
    }
    if (challengePassRate > 0.65 && challengePassRate < 0.82) {
      battleScarsForRun.push('near miss');
    }
    if (performance < 0.62) {
      battleScarsForRun.push('performance regression');
    }
    if (failureRecovery > 0.76) {
      battleScarsForRun.push('successful recovery');
    }

    return {
      runId: `run-${scenario.scenarioId}-${index + 1}`,
      scenarioId: scenario.scenarioId,
      scenarioName: scenario.name,
      focus: scenario.focus,
      severity: scenario.severity,
      status,
      proofLevel,
      constitutionalMaturity,
      replaySuccess,
      determinism: Number((determinism * 100).toFixed(1)),
      governanceCompliance: Number((governanceCompliance * 100).toFixed(1)),
      performance: Number((performance * 100).toFixed(1)),
      resourceEfficiency: Number((resourceEfficiency * 100).toFixed(1)),
      failureRecovery: Number((failureRecovery * 100).toFixed(1)),
      challengePassRate: Number((challengePassRate * 100).toFixed(1)),
      resourceUsage,
      evidenceReceipts,
      proofReceiptId,
      timeline,
      battleScars: battleScarsForRun,
      finalOutcome: `${status} under ${scenario.name}`,
    };
  });
}

function buildArenaScorecard(runs: ArenaChallengeRun[]): ArenaScorecard {
  const challengePassRate = average(runs.map((run) => run.challengePassRate));
  const constitutionalMaturity = average(runs.map((run) => run.constitutionalMaturity));
  const replaySuccess = average(runs.map((run) => (run.replaySuccess ? 100 : 0)));
  const determinism = average(runs.map((run) => run.determinism));
  const governanceCompliance = average(runs.map((run) => run.governanceCompliance));
  const performance = average(runs.map((run) => run.performance));
  const resourceEfficiency = average(runs.map((run) => run.resourceEfficiency));
  const failureRecovery = average(runs.map((run) => run.failureRecovery));

  return {
    proofLevel: scoreToProofLevel(constitutionalMaturity),
    constitutionalMaturity: Number(constitutionalMaturity.toFixed(1)),
    replaySuccess: Number(replaySuccess.toFixed(1)),
    determinism: Number(determinism.toFixed(1)),
    governanceCompliance: Number(governanceCompliance.toFixed(1)),
    performance: Number(performance.toFixed(1)),
    resourceEfficiency: Number(resourceEfficiency.toFixed(1)),
    failureRecovery: Number(failureRecovery.toFixed(1)),
    challengePassRate: Number(challengePassRate.toFixed(1)),
    readinessLevel: challengePassRate >= 85 && replaySuccess >= 85 && governanceCompliance >= 82
      ? 'production-ready'
      : challengePassRate >= 70
        ? 'candidate'
        : 'prototype',
  };
}

function buildBattleScars(runs: ArenaChallengeRun[]): ArenaBattleScar[] {
  const scars: ArenaBattleScar[] = [];
  for (const run of runs) {
    if (run.status === 'FAIL') {
      scars.push({
        scarId: `${run.runId}-failed`,
        type: 'failed_scenario',
        title: `${run.scenarioName} failed`,
        detail: `Scenario ${run.scenarioName} did not survive the arena challenge.`,
        scenarioId: run.scenarioId,
        severity: 'high',
      });
    }
    if (!run.replaySuccess) {
      scars.push({
        scarId: `${run.runId}-replay`,
        type: 'replay_failure',
        title: `${run.scenarioName} replay mismatch`,
        detail: `Replay verification diverged for ${run.scenarioName}.`,
        scenarioId: run.scenarioId,
        severity: 'high',
      });
    }
    if (run.governanceCompliance < 70) {
      scars.push({
        scarId: `${run.runId}-governance`,
        type: 'governance_violation',
        title: `${run.scenarioName} governance violation`,
        detail: `Governance compliance fell below the acceptable threshold.`,
        scenarioId: run.scenarioId,
        severity: 'high',
      });
    }
    if (run.challengePassRate >= 65 && run.challengePassRate < 80) {
      scars.push({
        scarId: `${run.runId}-near-miss`,
        type: 'near_miss',
        title: `${run.scenarioName} near miss`,
        detail: `The system cleared the scenario but left a narrow margin.`,
        scenarioId: run.scenarioId,
        severity: 'medium',
      });
    }
    if (run.performance < 70) {
      scars.push({
        scarId: `${run.runId}-performance`,
        type: 'performance_regression',
        title: `${run.scenarioName} performance regression`,
        detail: `Performance dipped below the preferred operating range.`,
        scenarioId: run.scenarioId,
        severity: 'medium',
      });
    }
    if (run.failureRecovery > 76) {
      scars.push({
        scarId: `${run.runId}-recovery`,
        type: 'successful_recovery',
        title: `${run.scenarioName} recovery`,
        detail: `The arena recovered successfully after injected stress.`,
        scenarioId: run.scenarioId,
        severity: 'low',
      });
    }
  }
  return scars;
}

function buildArenaLifecycle(snapshot: {
  challengePacks: ArenaChallengePack[];
  scorecard: ArenaScorecard;
  certificate: ArenaReadinessCertificate;
  battleScars: ArenaBattleScar[];
  replayReports: Record<string, ReplayAnalysisReport>;
  map: ArenaMap;
  tournament: TournamentBracket;
}): ArenaLifecyclePhase[] {
  return [
    {
      stage: 'Design',
      status: 'complete',
      description: 'ISL intent, constitutional laws, runtime contracts, and architectural decisions are shaped before execution.',
      artifacts: ['ISL intent', 'constitutional laws', 'runtime contracts', 'ADRs'],
    },
    {
      stage: 'Build',
      status: 'complete',
      description: 'Runtime implementation, SDKs, APIs, documentation, and example clients are assembled.',
      artifacts: ['runtime implementation', 'SDKs', 'APIs', 'documentation', 'example clients'],
    },
    {
      stage: 'Verify',
      status: 'complete',
      description: 'Conformance suite, replay verification, evidence receipts, and proof surfaces are checked.',
      artifacts: ['conformance suite', 'replay reports', 'evidence receipts', 'proof surface'],
    },
    {
      stage: 'Challenge',
      status: 'complete',
      description: 'Arena Mode injects adversarial requests, exhaustion, violations, divergence, and backend failures.',
      artifacts: snapshot.challengePacks.map((pack) => pack.name),
    },
    {
      stage: 'Certify',
      status: snapshot.scorecard.readinessLevel === 'production-ready' ? 'complete' : 'in-progress',
      description: `Readiness is summarized as ${snapshot.scorecard.readinessLevel} with proof level ${snapshot.scorecard.proofLevel}.`,
      artifacts: [snapshot.certificate.certificateId, snapshot.certificate.conformanceStatus, snapshot.certificate.replayVerification],
    },
    {
      stage: 'Release',
      status: 'in-progress',
      description: 'Release receipts and compatibility matrices govern promotion into live environments.',
      artifacts: ['release receipt', 'proof level', 'compatibility matrix'],
    },
    {
      stage: 'Observe',
      status: 'in-progress',
      description: 'Ops Console surfaces live health, evidence streams, and replay timelines.',
      artifacts: Object.keys(snapshot.replayReports).slice(0, 4),
    },
    {
      stage: 'Learn',
      status: snapshot.battleScars.length > 0 ? 'complete' : 'future',
      description: 'Battle scars, blindspots, and recovery paths become permanent engineering knowledge.',
      artifacts: snapshot.battleScars.slice(0, 4).map((scar) => scar.title),
    },
  ];
}

function buildArenaCertificate(snapshot: {
  scorecard: ArenaScorecard;
  replayReports: Record<string, ReplayAnalysisReport>;
  challengeRuns: ArenaChallengeRun[];
  battleScars: ArenaBattleScar[];
  map: ArenaMap;
}): ArenaReadinessCertificate {
  const evidenceReceipts = Object.values(snapshot.replayReports).flatMap((report) => [
    report.traceId,
    ...report.timeline.slice(0, 2).map((entry) => `${report.traceId}:${entry.stage}`),
  ]);

  const replayVerification = snapshot.challengeRuns.every((run) => run.replaySuccess)
    ? 'verified'
    : 'verified with caveats';

  const conformanceStatus = snapshot.challengeRuns.some((run) => run.status === 'FAIL')
    ? 'conditional'
    : 'pass';

  const challengeResults = `${snapshot.challengeRuns.filter((run) => run.status === 'PASS').length}/${snapshot.challengeRuns.length} challenges passed.`;

  const readinessLevel = snapshot.scorecard.readinessLevel === 'production-ready'
    ? 'Ready for production'
    : snapshot.scorecard.readinessLevel === 'candidate'
      ? 'Ready for candidate promotion'
      : 'Requires more challenge coverage';

  return {
    certificateId: `certificate-${stableSlug(snapshot.map.mapId)}`,
    proofSurface: `Arena proof surface for ${snapshot.map.title}`,
    challengeResults,
    replayVerification,
    conformanceStatus,
    evidenceReceipts,
    constitutionalMaturity: snapshot.scorecard.constitutionalMaturity,
    readinessLevel,
    issuedAt: '2026-07-08T12:00:00.000Z',
  };
}

function _buildConstitutionalEngineeringLifecycle(): ArenaLifecyclePhase[] {
  return [
    {
      stage: 'Design',
      status: 'complete',
      description: 'Intent, laws, runtime contracts, and architectural decisions are captured.',
      artifacts: ['ISL intent', 'constitutional laws', 'runtime contracts', 'ADRs'],
    },
    {
      stage: 'Build',
      status: 'complete',
      description: 'Runtime implementation, SDKs, APIs, documentation, and example clients are assembled.',
      artifacts: ['implementation', 'SDKs', 'APIs', 'documentation', 'example clients'],
    },
    {
      stage: 'Verify',
      status: 'complete',
      description: 'Conformance suite, replay verification, evidence receipts, proof surfaces, and challenge packs are checked.',
      artifacts: ['conformance suite', 'replay verification', 'evidence receipts', 'proof surface', 'challenge packs'],
    },
    {
      stage: 'Challenge',
      status: 'complete',
      description: 'Arena Mode injects adversarial requests, resource exhaustion, governance violations, and replay divergence.',
      artifacts: ['Arena Mode', 'adversarial testing', 'failure injection', 'replay divergence'],
    },
    {
      stage: 'Certify',
      status: 'complete',
      description: 'Readiness certificates, release receipts, proof levels, maturity scorecards, and compatibility matrices are issued.',
      artifacts: ['readiness certificate', 'release receipt', 'proof level', 'maturity scorecard'],
    },
    {
      stage: 'Release',
      status: 'complete',
      description: 'Artifacts can graduate into local, team, enterprise, and mission-critical deployment tiers.',
      artifacts: ['local', 'team', 'enterprise', 'mission-critical'],
    },
    {
      stage: 'Observe',
      status: 'complete',
      description: 'Ops Console, constitutional knowledge graph, health, evidence, and replay timeline remain visible.',
      artifacts: ['Ops Console', 'knowledge graph', 'runtime health', 'evidence streams', 'replay timeline'],
    },
    {
      stage: 'Learn',
      status: 'complete',
      description: 'Battle scars, blindspots, adoption feedback, performance baselines, and constitutional amendments close the loop.',
      artifacts: ['battle scars', 'blindspots', 'feedback', 'baselines', 'amendments'],
    },
  ];
}

function buildDigitalThread(snapshot: {
  challengeRuns: ArenaChallengeRun[];
  replayReports: Record<string, ReplayAnalysisReport>;
  certificate: ArenaReadinessCertificate;
  scorecard: ArenaScorecard;
}): string[] {
  return [
    'Intent',
    'Design',
    'Source code',
    'Build',
    'Tests',
    'Replay',
    'Evidence',
    'Challenge results',
    'Certification',
    'Release',
    'Runtime telemetry',
    'Operational history',
    `Challenge runs: ${snapshot.challengeRuns.length}`,
    `Replay reports: ${Object.keys(snapshot.replayReports).length}`,
    `Certificate: ${snapshot.certificate.certificateId}`,
    `Scorecard: ${snapshot.scorecard.proofLevel}/${snapshot.scorecard.readinessLevel}`,
  ];
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function scoreToProofLevel(value: number): ProofLevel {
  if (value >= 92) {
    return 'P5';
  }
  if (value >= 84) {
    return 'P4';
  }
  if (value >= 74) {
    return 'P3';
  }
  if (value >= 62) {
    return 'P2';
  }
  if (value >= 48) {
    return 'P1';
  }
  return 'P0';
}

class ArenaSimulationEngine {
  constructor(
    private readonly seed: string,
    private readonly map: ArenaMap,
  ) {}

  runTournament(agents: ArenaAgent[]): TournamentBracket {
    const rounds: TournamentMatch[][] = [];
    const seedOrder = agents.map((agent) => agent.name);
    let currentRoundAgents = [...agents];
    let roundNumber = 1;

    while (currentRoundAgents.length > 1) {
      const matches: TournamentMatch[] = [];
      for (let index = 0; index < currentRoundAgents.length; index += 2) {
        const left = currentRoundAgents[index];
        const right = currentRoundAgents[index + 1];
        if (!left) {
          continue;
        }
        if (!right) {
          matches.push({
            matchId: `round-${roundNumber}-bye-${stableSlug(left.name)}`,
            agents: [left.name],
            winner: left.name,
            tracePath: null,
            traceId: null,
            summary: `${left.name} advances on a bye.`,
          });
          continue;
        }

        const matchId = `round-${roundNumber}-${stableSlug(left.name)}-vs-${stableSlug(right.name)}`;
        const trace = new ArenaMatchEngine(createSeededRng(`${this.seed}:${matchId}`)).startMatch(matchId, left, right, this.map);
        matches.push({
          matchId,
          agents: [left.name, right.name],
          winner: trace.outcome.winner,
          tracePath: `arena/${matchId}.cnode-trace`,
          traceId: trace.traceId,
          summary: `${trace.outcome.winner} defeated ${trace.outcome.winner === left.name ? right.name : left.name} by ${trace.outcome.score.toFixed(2)}.`,
        });
      }

      rounds.push(matches);
      currentRoundAgents = matches
        .map((match) => agents.find((agent) => agent.name === match.winner))
        .filter((agent): agent is ArenaAgent => Boolean(agent));
      roundNumber += 1;
    }

    return {
      tournamentId: `arena-tournament-${stableSlug(this.map.title)}`,
      seedOrder,
      rounds,
    };
  }
}

function buildRoster(seed: string): ArenaAgent[] {
  const rng = createSeededRng(`${seed}:roster`);
  const talentAssignments: Record<FactionName, string[][]> = {
    Protoss: [
      ['Evidence Hoarder', 'Macro Overdrive'],
      ['Invariant Shield', 'Warp Canticle'],
      ['Evidence Hoarder', 'Invariant Shield'],
    ],
    Zerg: [
      ['Evidence Flood', 'Swarm Surge'],
      ['Adaptive Spores', 'Replication Spiral'],
      ['Evidence Flood', 'Replication Spiral'],
    ],
    Terran: [
      ['Lockdown Protocol', 'Fortified Command'],
      ['Audit Net', 'Railgun Discipline'],
      ['Lockdown Protocol', 'Audit Net'],
    ],
  };

  const roster: ArenaAgent[] = [];
  FACTION_ROSTERS.forEach((factionRoster) => {
    factionRoster.roster.forEach((name, index) => {
      const talentNames = talentAssignments[factionRoster.faction][index % talentAssignments[factionRoster.faction].length];
      roster.push(createAgent(factionRoster.faction, name, Math.floor(rng() * 8), talentNames));
    });
  });

  return roster;
}

function buildDensityProfile(): ArenaDensityProfile {
  return {
    name: 'High trust center, disputed edges',
    terrainWeights: {
      [TERRAIN_TYPES.TrustBastion]: 5,
      [TERRAIN_TYPES.EvidenceFloodplain]: 3,
      [TERRAIN_TYPES.DisputedEdge]: 2,
      [TERRAIN_TYPES.InvariantRidge]: 4,
      [TERRAIN_TYPES.RelaySpine]: 3,
    },
    centerBias: [TERRAIN_TYPES.TrustBastion, TERRAIN_TYPES.RelaySpine, TERRAIN_TYPES.InvariantRidge],
    edgeBias: [TERRAIN_TYPES.DisputedEdge, TERRAIN_TYPES.EvidenceFloodplain],
  };
}

export function createArenaModeSnapshot(seed = 'arena-mode-v1'): ArenaSnapshot {
  const rng = createSeededRng(seed);
  const densityProfile = buildDensityProfile();
  const map = new ArenaMapGenerator(10, 6, rng).generate(densityProfile);
  const agents = buildRoster(seed);
  const simulation = new ArenaSimulationEngine(seed, map);
  const tournament = simulation.runTournament(agents);
  const challengeScenarios = buildArenaChallengeScenarios();
  const challengePacks = buildArenaChallengePacks(challengeScenarios);
  const traces: Record<string, ArenaTrace> = {};
  const replayReports: Record<string, ReplayAnalysisReport> = {};
  const analyzer = new ReplayAnalyzer();

  for (const round of tournament.rounds) {
    for (const match of round) {
      if (!match.traceId || !match.tracePath || match.agents.length < 2 || !match.winner) {
        continue;
      }
      const left = agents.find((agent) => agent.name === match.agents[0]);
      const right = agents.find((agent) => agent.name === match.agents[1]);
      if (!left || !right) {
        continue;
      }
      const trace = new ArenaMatchEngine(createSeededRng(`${seed}:${match.matchId}`)).startMatch(match.matchId, left, right, map);
      traces[match.matchId] = trace;
      replayReports[match.matchId] = analyzer.analyze(trace, match.tracePath);
    }
  }

  const challengeRuns = buildArenaChallengeRuns(seed, agents, map, challengeScenarios, tournament);
  const scorecard = buildArenaScorecard(challengeRuns);
  const battleScars = buildBattleScars(challengeRuns);
  const certificate = buildArenaCertificate({
    scorecard,
    replayReports,
    challengeRuns,
    battleScars,
    map,
  });
  const lifecycle = buildArenaLifecycle({
    challengePacks,
    scorecard,
    certificate,
    battleScars,
    replayReports,
    map,
    tournament,
  });
  const digitalThread = buildDigitalThread({
    challengeRuns,
    replayReports,
    certificate,
    scorecard,
  });

  return {
    arenaId: `arena-${stableSlug(seed)}`,
    title: 'Governance Arena',
    densityProfile,
    map,
    factions: FACTION_ROSTERS,
    agents,
    tournament,
    traces,
    replayReports,
    challengePacks,
    challengeScenarios,
    challengeRuns,
    scorecard,
    battleScars,
    lifecycle,
    certificate,
    digitalThread,
    globalModifiers: {
      constraint_density_multiplier: 1,
      evidence_weight_multiplier: 1,
      evidence_generation_burst: 0,
      ciems_progress_multiplier: 1,
      state_freeze: false,
    },
  };
}

export function analyzeArenaReplay(snapshot: ArenaSnapshot, matchId: string): ReplayAnalysisReport | null {
  return snapshot.replayReports[matchId] ?? null;
}

export function summarizeBracket(bracket: TournamentBracket): string {
  const winner = bracket.rounds[bracket.rounds.length - 1]?.find((match) => Boolean(match.winner))?.winner ?? 'unknown';
  return `Tournament ${bracket.tournamentId} seeded ${bracket.seedOrder.length} agents across ${bracket.rounds.length} rounds. Winner: ${winner}.`;
}
