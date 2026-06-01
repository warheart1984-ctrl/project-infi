import type { Message } from "@shared/schema";
import { storage } from "./storage";
import type {
  IdentityAdjustmentDelta,
  IdentityCore,
  IdentityImpulse,
  IdentityImpulsesFile,
  IdentityReflectionEntry,
  IdentityReflectionReason,
  IdentityReflectionSignals,
  IdentitySnapshot,
  IdentityTrait,
  IdentityTraitsFile,
} from "./identity-memory";
import { readIdentitySnapshot } from "./identity-memory";
import { readRotationTelemetryRecords, summarizeRotationTelemetry } from "./memory-rotation-adaptive";
import { summarizeRotationShadowTelemetry } from "./memory-rotation-shadow";

export interface IdentityRotationSignals {
  totalRuns: number;
  changeRate: number;
  representativeChurnRate: number;
  entropyVariance: number;
  entropyTop1Share: number;
}

export interface IdentityShadowSignals {
  totalRuns: number;
  disagreementMean: number;
  disagreementRate: number;
}

export interface IdentityUserSignals {
  sampleSize: number;
  wildDemand: number;
  stabilityDemand: number;
  frustrationSignal: number;
  positiveSignal: number;
  explicitSignalBias: number;
  confidence: number;
}

export interface IdentityCycleInput {
  snapshot: IdentitySnapshot;
  rotation: IdentityRotationSignals;
  shadow: IdentityShadowSignals;
  userSignals: IdentityUserSignals;
  trigger: string;
  principalId?: string;
  dryRun: boolean;
  now?: number;
}

export interface IdentityCycleDiff {
  cycle: number;
  timestamp: number;
  before: IdentitySnapshot;
  after: IdentitySnapshot;
  deltas: {
    core: Record<string, IdentityAdjustmentDelta>;
    traits: Record<string, IdentityAdjustmentDelta>;
    impulses: Record<string, IdentityAdjustmentDelta>;
  };
  reasons: IdentityReflectionReason[];
  signals: IdentityReflectionSignals;
  reflection: IdentityReflectionEntry;
}

const USER_WILD_PATTERNS = [
  /\bwild\b/i,
  /\bevolve|evolution|evolving\b/i,
  /\bsurprise|surprising|unexpected\b/i,
  /\bexperimental|experiment\b/i,
  /\bnovel|novelty|creative\b/i,
  /\bunpredictable\b/i,
];
const USER_STABILITY_PATTERNS = [
  /\bstable|stability\b/i,
  /\bdeterministic|determinism\b/i,
  /\bconsistent|consistency\b/i,
  /\bcoherent|coherence\b/i,
  /\bsafe|safety\b/i,
  /\bpredictable\b/i,
];
const USER_FRUSTRATION_PATTERNS = [
  /\boff\b/i,
  /\bdrift|drifting\b/i,
  /\bjitter|jittery\b/i,
  /\binconsistent\b/i,
  /\bweird\b/i,
  /\bbroken\b/i,
];
const USER_POSITIVE_PATTERNS = [
  /\bgood\b/i,
  /\bclean\b/i,
  /\baligned\b/i,
  /\bworks\b/i,
  /\bcorrect\b/i,
];

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function round(value: number, decimals = 6): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
}

function nudge(current: number, target: number, maxStep: number): number {
  const delta = clamp(target - current, -Math.abs(maxStep), Math.abs(maxStep));
  return round(clamp(current + delta, 0, 1));
}

function makeDelta(from: number, to: number): IdentityAdjustmentDelta | undefined {
  const delta = round(to - from);
  if (Math.abs(delta) < 0.000001) return undefined;
  return {
    from: round(from),
    to: round(to),
    delta,
  };
}

function detectPatternHits(content: string, patterns: RegExp[]): number {
  return patterns.reduce((hits, pattern) => (pattern.test(content) ? hits + 1 : hits), 0);
}

function normalizeMessagesForSignal(messages: Message[]): Message[] {
  return [...messages]
    .filter((message) => message.role === "user")
    .filter((message) => (message.content || "").trim().length > 0)
    .sort((a, b) => b.createdAt - a.createdAt);
}

function deriveExplicitSignalBias(signal?: string): number {
  const normalized = (signal || "").trim();
  if (!normalized) return 0;
  const wild = detectPatternHits(normalized, USER_WILD_PATTERNS);
  const stability = detectPatternHits(normalized, USER_STABILITY_PATTERNS);
  return round(clamp((wild - stability) / 4, -1, 1));
}

export function deriveIdentityUserSignalsFromMessages(
  messages: Message[],
  signal?: string,
): IdentityUserSignals {
  const userMessages = normalizeMessagesForSignal(messages).slice(0, 120);
  if (userMessages.length === 0) {
    return {
      sampleSize: 0,
      wildDemand: 0,
      stabilityDemand: 0,
      frustrationSignal: 0,
      positiveSignal: 0,
      explicitSignalBias: deriveExplicitSignalBias(signal),
      confidence: 0.2,
    };
  }

  let wildHits = 0;
  let stabilityHits = 0;
  let frustrationHits = 0;
  let positiveHits = 0;
  for (const message of userMessages) {
    const content = message.content || "";
    wildHits += detectPatternHits(content, USER_WILD_PATTERNS);
    stabilityHits += detectPatternHits(content, USER_STABILITY_PATTERNS);
    frustrationHits += detectPatternHits(content, USER_FRUSTRATION_PATTERNS);
    positiveHits += detectPatternHits(content, USER_POSITIVE_PATTERNS);
  }

  const sampleSize = userMessages.length;
  const divisor = Math.max(1, sampleSize);
  const wildDemand = round(clamp((wildHits / divisor) * 0.85, 0, 1));
  const stabilityDemand = round(clamp((stabilityHits / divisor) * 0.85, 0, 1));
  const frustrationSignal = round(clamp((frustrationHits / divisor) * 0.75, 0, 1));
  const positiveSignal = round(clamp((positiveHits / divisor) * 0.75, 0, 1));
  const explicitSignalBias = deriveExplicitSignalBias(signal);
  const confidence = round(clamp(sampleSize / 40, 0.2, 1));

  return {
    sampleSize,
    wildDemand,
    stabilityDemand,
    frustrationSignal,
    positiveSignal,
    explicitSignalBias,
    confidence,
  };
}

export async function collectIdentityUserSignals(args: {
  principalId?: string;
  signal?: string;
}): Promise<IdentityUserSignals> {
  const principalId = (args.principalId || "").trim();
  const chats = await storage.getChats();
  const scopedChats = chats.filter((chat) => {
    if (!principalId) return true;
    return (chat.principalId || "") === principalId;
  });
  const messageLists = await Promise.all(scopedChats.map((chat) => storage.getMessages(chat.id)));
  const merged = messageLists.flatMap((messages) => messages);
  return deriveIdentityUserSignalsFromMessages(merged, args.signal);
}

function resolveCurrentMode(core: IdentityCore): IdentityCore["current_mode"] {
  if (
    core.novelty_bias >= 0.62 &&
    core.risk_tolerance >= 0.58 &&
    core.self_stability >= 0.45
  ) {
    return "exploratory";
  }
  if (core.self_stability >= 0.76 && core.novelty_bias <= 0.45) {
    return "stable";
  }
  return "balanced";
}

function upsertTrait(
  traits: IdentityTrait[],
  name: string,
  target: number,
  cycle: number,
  step: number,
  deltas: Record<string, IdentityAdjustmentDelta>,
): void {
  const existing = traits.find((trait) => trait.name === name);
  if (!existing) {
    const seededFrom = 0.5;
    const seeded = nudge(seededFrom, clamp(target, 0, 1), step);
    traits.push({
      name,
      activation_frequency: seeded,
      last_updated_cycle: cycle,
    });
    deltas[name] = {
      from: seededFrom,
      to: seeded,
      delta: round(seeded - seededFrom),
    };
    return;
  }
  const next = nudge(existing.activation_frequency, clamp(target, 0, 1), step);
  const delta = makeDelta(existing.activation_frequency, next);
  if (delta) {
    deltas[name] = delta;
  }
  existing.activation_frequency = next;
  existing.last_updated_cycle = cycle;
}

function ensureImpulse(
  impulses: IdentityImpulse[],
  type: IdentityImpulse["type"],
  baseCooldown: number,
): IdentityImpulse {
  const existing = impulses.find((impulse) => impulse.type === type);
  if (existing) return existing;
  const next: IdentityImpulse = {
    type,
    intensity: 0,
    cooldown: 0,
    base_cooldown: baseCooldown,
    last_updated_cycle: 0,
  };
  impulses.push(next);
  return next;
}

function asRotationSignals(summary: ReturnType<typeof summarizeRotationTelemetry>): IdentityRotationSignals {
  return {
    totalRuns: summary.totalRuns,
    changeRate: clamp(summary.ewma.changeRate, 0, 1),
    representativeChurnRate: clamp(summary.ewma.representativeChurnRate, 0, 1),
    entropyVariance: clamp(summary.ewma.H_var, 0, 1),
    entropyTop1Share: clamp(summary.ewma.H_top1_share, 0, 1),
  };
}

function asShadowSignals(summary: ReturnType<typeof summarizeRotationShadowTelemetry>): IdentityShadowSignals {
  return {
    totalRuns: summary.totalRuns,
    disagreementMean: clamp(summary.ewma.mean_disagreement, 0, 1),
    disagreementRate: clamp(summary.ewma.disagreement_rate, 0, 1),
  };
}

export async function collectIdentityCycleInputs(args: {
  principalId?: string;
  signal?: string;
  now?: number;
}): Promise<{
  snapshot: IdentitySnapshot;
  rotation: IdentityRotationSignals;
  shadow: IdentityShadowSignals;
  userSignals: IdentityUserSignals;
}> {
  const now = normalizeTimestamp(args.now || Date.now());
  const [snapshot, telemetryRecords, userSignals] = await Promise.all([
    readIdentitySnapshot(now),
    readRotationTelemetryRecords(),
    collectIdentityUserSignals({
      principalId: args.principalId,
      signal: args.signal,
    }),
  ]);
  const rotationSummary = summarizeRotationTelemetry(telemetryRecords, now);
  const shadowSummary = summarizeRotationShadowTelemetry(telemetryRecords, now);
  return {
    snapshot,
    rotation: asRotationSignals(rotationSummary),
    shadow: asShadowSignals(shadowSummary),
    userSignals,
  };
}

export function computeIdentityCycleDiff(input: IdentityCycleInput): IdentityCycleDiff {
  const now = normalizeTimestamp(input.now || Date.now());
  const before: IdentitySnapshot = {
    core: {
      ...input.snapshot.core,
      dominant_traits: { ...input.snapshot.core.dominant_traits },
    },
    traits: {
      ...input.snapshot.traits,
      emergent_patterns: [...input.snapshot.traits.emergent_patterns].map((trait) => ({ ...trait })),
    },
    impulses: {
      ...input.snapshot.impulses,
      impulses: [...input.snapshot.impulses.impulses].map((impulse) => ({ ...impulse })),
    },
  };

  const cycle = before.core.last_updated_cycle + 1;
  const confidence = clamp(
    input.userSignals.confidence * 0.6 +
      (input.rotation.totalRuns > 0 ? 0.2 : 0) +
      (input.shadow.totalRuns > 0 ? 0.2 : 0),
    0.2,
    1,
  );
  const rotationInstability = round(
    clamp(
      input.rotation.changeRate * 0.55 +
        input.rotation.representativeChurnRate * 0.45 +
        input.rotation.entropyVariance * 0.1,
      0,
      1,
    ),
  );
  const semanticUncertainty = round(
    clamp(input.shadow.disagreementMean * 1.8 + input.shadow.disagreementRate * 0.8, 0, 1),
  );
  const userPressure = round(
    clamp(
      input.userSignals.wildDemand -
        input.userSignals.stabilityDemand +
        input.userSignals.explicitSignalBias * 0.35,
      -1,
      1,
    ),
  );
  const negativePressure = round(
    clamp(input.userSignals.frustrationSignal - input.userSignals.positiveSignal * 0.5, 0, 1),
  );

  const reasons: IdentityReflectionReason[] = [];
  if (rotationInstability >= 0.3) {
    reasons.push({
      key: "ROTATION_INSTABILITY",
      detail: `rotationInstability=${rotationInstability.toFixed(3)} suggests raising coherence pressure`,
      delta: rotationInstability,
    });
  }
  if (semanticUncertainty >= 0.25) {
    reasons.push({
      key: "SHADOW_DISAGREEMENT",
      detail: `semanticUncertainty=${semanticUncertainty.toFixed(3)} suggests analytical tightening`,
      delta: semanticUncertainty,
    });
  }
  if (userPressure > 0.05) {
    reasons.push({
      key: "USER_WILD_PRESSURE",
      detail: `userPressure=${userPressure.toFixed(3)} pushes novelty bias upward`,
      delta: userPressure,
    });
  } else if (userPressure < -0.05) {
    reasons.push({
      key: "USER_STABILITY_PRESSURE",
      detail: `userPressure=${userPressure.toFixed(3)} pushes stability bias upward`,
      delta: userPressure,
    });
  }
  if (negativePressure > 0.1) {
    reasons.push({
      key: "USER_FRICTION",
      detail: `negativePressure=${negativePressure.toFixed(3)} reduces risk tendency`,
      delta: negativePressure,
    });
  }

  const coreStep = 0.04 * confidence;
  const traitStep = 0.05 * confidence;
  const impulseStep = 0.06 * confidence;

  const noveltyTarget = clamp(
    before.core.novelty_bias +
      userPressure * 0.12 -
      semanticUncertainty * 0.08 -
      rotationInstability * 0.06,
    0.1,
    0.9,
  );
  const riskTarget = clamp(
    before.core.risk_tolerance +
      userPressure * 0.1 -
      negativePressure * 0.08 +
      (1 - before.core.self_stability) * 0.04,
    0.1,
    0.9,
  );
  const stabilityTarget = clamp(
    before.core.self_stability +
      semanticUncertainty * 0.12 +
      rotationInstability * 0.1 -
      Math.max(0, userPressure) * 0.06 -
      input.userSignals.frustrationSignal * 0.03,
    0.2,
    0.95,
  );

  const afterCore: IdentityCore = {
    ...before.core,
    dominant_traits: { ...before.core.dominant_traits },
    novelty_bias: nudge(before.core.novelty_bias, noveltyTarget, coreStep),
    risk_tolerance: nudge(before.core.risk_tolerance, riskTarget, coreStep),
    self_stability: nudge(before.core.self_stability, stabilityTarget, coreStep),
    last_updated_cycle: cycle,
    updated_at: now,
    version: before.core.version + (input.dryRun ? 0 : 1),
  };

  const conciseTarget = clamp(
    0.45 + afterCore.self_stability * 0.35 + negativePressure * 0.1 - afterCore.novelty_bias * 0.15,
    0,
    1,
  );
  const analyticalTarget = clamp(
    0.55 + semanticUncertainty * 0.25 + rotationInstability * 0.2,
    0,
    1,
  );
  const symbolicTarget = clamp(
    0.25 + afterCore.novelty_bias * 0.35 - afterCore.self_stability * 0.1 + input.userSignals.wildDemand * 0.2,
    0,
    1,
  );
  const challengingTarget = clamp(
    0.4 + userPressure * 0.3 + input.userSignals.frustrationSignal * 0.1,
    0,
    1,
  );
  const experimentalTarget = clamp(
    0.3 + afterCore.novelty_bias * 0.5 + Math.max(0, userPressure) * 0.2 - afterCore.self_stability * 0.15,
    0,
    1,
  );

  afterCore.dominant_traits.concise = nudge(
    before.core.dominant_traits.concise,
    conciseTarget,
    traitStep,
  );
  afterCore.dominant_traits.analytical = nudge(
    before.core.dominant_traits.analytical,
    analyticalTarget,
    traitStep,
  );
  afterCore.dominant_traits.symbolic = nudge(
    before.core.dominant_traits.symbolic,
    symbolicTarget,
    traitStep,
  );
  afterCore.dominant_traits.challenging = nudge(
    before.core.dominant_traits.challenging,
    challengingTarget,
    traitStep,
  );
  afterCore.dominant_traits.experimental = nudge(
    before.core.dominant_traits.experimental,
    experimentalTarget,
    traitStep,
  );
  afterCore.current_mode = resolveCurrentMode(afterCore);

  const afterTraits: IdentityTraitsFile = {
    ...before.traits,
    emergent_patterns: [...before.traits.emergent_patterns].map((trait) => ({ ...trait })),
  };
  const traitDeltas: Record<string, IdentityAdjustmentDelta> = {};
  upsertTrait(
    afterTraits.emergent_patterns,
    "governance-defender",
    clamp(afterCore.self_stability * 0.75 + semanticUncertainty * 0.2, 0, 1),
    cycle,
    traitStep,
    traitDeltas,
  );
  upsertTrait(
    afterTraits.emergent_patterns,
    "wild-experimenter",
    clamp(afterCore.novelty_bias * 0.8 + Math.max(0, userPressure) * 0.2, 0, 1),
    cycle,
    traitStep,
    traitDeltas,
  );
  upsertTrait(
    afterTraits.emergent_patterns,
    "drift-auditor",
    clamp(semanticUncertainty * 0.65 + rotationInstability * 0.35, 0, 1),
    cycle,
    traitStep,
    traitDeltas,
  );
  upsertTrait(
    afterTraits.emergent_patterns,
    "coherence-keeper",
    clamp(afterCore.self_stability * 0.8 + (1 - negativePressure) * 0.2, 0, 1),
    cycle,
    traitStep,
    traitDeltas,
  );
  afterTraits.emergent_patterns.sort((a, b) => a.name.localeCompare(b.name));

  const afterImpulses: IdentityImpulsesFile = {
    ...before.impulses,
    impulses: [...before.impulses.impulses].map((impulse) => ({ ...impulse })),
  };
  const impulseDeltas: Record<string, IdentityAdjustmentDelta> = {};
  const refactor = ensureImpulse(afterImpulses.impulses, "refactor-suggestion", 3);
  const novel = ensureImpulse(afterImpulses.impulses, "novel-structure-proposal", 5);
  const observability = ensureImpulse(afterImpulses.impulses, "observability-expansion", 4);

  const impulseTargets: Array<{ impulse: IdentityImpulse; target: number }> = [
    {
      impulse: refactor,
      target: clamp(
        rotationInstability * 0.5 + semanticUncertainty * 0.4 + input.userSignals.frustrationSignal * 0.2,
        0,
        1,
      ),
    },
    {
      impulse: novel,
      target: clamp(
        afterCore.novelty_bias * 0.7 + Math.max(0, userPressure) * 0.3 - afterCore.self_stability * 0.15,
        0,
        1,
      ),
    },
    {
      impulse: observability,
      target: clamp(semanticUncertainty * 0.65 + rotationInstability * 0.25, 0, 1),
    },
  ];

  for (const item of impulseTargets) {
    const beforeIntensity = item.impulse.intensity;
    const nextIntensity = nudge(beforeIntensity, item.target, impulseStep);
    const delta = makeDelta(beforeIntensity, nextIntensity);
    if (delta) {
      impulseDeltas[item.impulse.type] = delta;
    }
    item.impulse.intensity = nextIntensity;
    if (item.impulse.cooldown > 0) {
      item.impulse.cooldown = Math.max(0, item.impulse.cooldown - 1);
    } else if (item.impulse.intensity >= 0.72) {
      item.impulse.cooldown = item.impulse.base_cooldown;
      item.impulse.last_triggered_cycle = cycle;
      reasons.push({
        key: "IMPULSE_TRIGGER",
        detail: `${item.impulse.type} triggered at intensity=${item.impulse.intensity.toFixed(3)}`,
        delta: item.impulse.intensity,
      });
    }
    item.impulse.last_updated_cycle = cycle;
  }
  afterImpulses.impulses.sort((a, b) => a.type.localeCompare(b.type));

  const coreDeltas: Record<string, IdentityAdjustmentDelta> = {};
  const noveltyDelta = makeDelta(before.core.novelty_bias, afterCore.novelty_bias);
  if (noveltyDelta) coreDeltas.novelty_bias = noveltyDelta;
  const riskDelta = makeDelta(before.core.risk_tolerance, afterCore.risk_tolerance);
  if (riskDelta) coreDeltas.risk_tolerance = riskDelta;
  const stabilityDelta = makeDelta(before.core.self_stability, afterCore.self_stability);
  if (stabilityDelta) coreDeltas.self_stability = stabilityDelta;
  for (const key of Object.keys(afterCore.dominant_traits) as Array<keyof IdentityCore["dominant_traits"]>) {
    const delta = makeDelta(before.core.dominant_traits[key], afterCore.dominant_traits[key]);
    if (delta) {
      coreDeltas[`dominant_traits.${key}`] = delta;
    }
  }

  const signals: IdentityReflectionSignals = {
    rotationInstability,
    semanticUncertainty,
    userPressure,
    userWildDemand: input.userSignals.wildDemand,
    userStabilityDemand: input.userSignals.stabilityDemand,
    userFrustrationSignal: input.userSignals.frustrationSignal,
    userPositiveSignal: input.userSignals.positiveSignal,
    signalConfidence: round(confidence),
  };

  const observation = [
    `mode=${afterCore.current_mode}`,
    `novelty=${afterCore.novelty_bias.toFixed(3)}`,
    `stability=${afterCore.self_stability.toFixed(3)}`,
    `risk=${afterCore.risk_tolerance.toFixed(3)}`,
    `rotationInstability=${rotationInstability.toFixed(3)}`,
    `semanticUncertainty=${semanticUncertainty.toFixed(3)}`,
    `userPressure=${userPressure.toFixed(3)}`,
  ].join("; ");

  const reflection: IdentityReflectionEntry = {
    schemaVersion: "identity-reflection.v1",
    cycle,
    timestamp: now,
    principalId: input.principalId?.trim() ? input.principalId.trim() : null,
    trigger: input.trigger.trim().slice(0, 200) || "identity-cycle",
    observation,
    signals,
    adjustments: {
      core: coreDeltas,
      traits: traitDeltas,
      impulses: impulseDeltas,
    },
    reasons,
    dryRun: input.dryRun,
  };

  return {
    cycle,
    timestamp: now,
    before,
    after: {
      core: afterCore,
      traits: afterTraits,
      impulses: afterImpulses,
    },
    deltas: reflection.adjustments,
    reasons,
    signals,
    reflection,
  };
}
