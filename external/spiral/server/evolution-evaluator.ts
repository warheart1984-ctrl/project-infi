import {
  buildDriftSamplesFromLedger,
  calculateSlope,
  computeStructuralEntropyIndex,
  deriveDriftTrajectoryFromLedger,
  readEvolutionLedgerEntries,
  type EvolutionLedgerLikeEntry,
} from "./evolution-drift";

interface AutonomyTriggerThresholds {
  driftVelocityAbsThreshold: number;
  stabilityIndexFloor: number;
  invariantPressureCeiling: number;
  structuralEntropyCeiling: number;
}

interface ExecutiveCycleRunnerConfig {
  evaluationIntervalMs: number;
  triggerCooldownMs: number;
  entropyWindowSize: number;
  exploratoryEnabled: boolean;
  exploratoryPulseCadence: number;
  exploratoryMinimumSampleCount: number;
}

export interface ShadowAutonomySuggestion {
  schemaVersion: "autonomy-shadow.v1";
  timestamp: number;
  principalId: string;
  authority: "shadow";
  findings: {
    structuralEntropyScore: number;
    recursivePressureScore: number;
    identityConsistency: "pass" | "warn";
    deadCodeSignal: "none" | "possible";
    notes: string[];
  };
}

export interface ExecutiveAutonomyEvaluation {
  schemaVersion: "autonomy-trigger.v1";
  timestamp: number;
  principalId: string;
  triggered: boolean;
  reasonCodes: string[];
  sampleCount: number;
  metrics: {
    driftVelocity: number;
    stabilityIndex: number;
    invariantPressure: number;
    structuralEntropy: number;
    recursivePressure: number;
  };
  thresholds: AutonomyTriggerThresholds;
  runner: {
    intervalAllowed: boolean;
    cooldownAllowed: boolean;
    exploratoryEnabled: boolean;
    exploratoryPulseCadence: number;
    exploratoryMinimumSampleCount: number;
    exploratoryPulseDue: boolean;
  };
  signal?: string;
  shadow: ShadowAutonomySuggestion;
}

const lastEvaluationByPrincipal = new Map<string, number>();
const lastTriggerByPrincipal = new Map<string, number>();
const lastExploratorySampleByPrincipal = new Map<string, number>();

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

function normalizePrincipalId(value: string): string {
  return value.trim().slice(0, 200);
}

function envPositiveInt(name: string, fallback: number): number {
  const parsed = Number.parseInt(process.env[name] || "", 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.floor(parsed);
}

function envUnitInterval(name: string, fallback: number): number {
  const parsed = Number.parseFloat(process.env[name] || "");
  if (!Number.isFinite(parsed)) return fallback;
  return clamp(parsed, 0, 1);
}

function envBoolean(name: string, fallback: boolean): boolean {
  const raw = (process.env[name] || "").trim().toLowerCase();
  if (!raw) return fallback;
  if (raw === "1" || raw === "true" || raw === "yes" || raw === "on") return true;
  if (raw === "0" || raw === "false" || raw === "no" || raw === "off") return false;
  return fallback;
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function buildSignal(reasonCodes: string[]): string {
  const normalized = reasonCodes
    .map((code) => code.trim().toLowerCase())
    .filter(Boolean)
    .join("+")
    .slice(0, 220);
  return normalized ? `autonomy:${normalized}` : "autonomy:threshold";
}

function getAutonomyTriggerThresholds(): AutonomyTriggerThresholds {
  return {
    driftVelocityAbsThreshold: envUnitInterval("SPIRAL_AUTONOMY_DRIFT_VELOCITY_THRESHOLD", 0.02),
    stabilityIndexFloor: envUnitInterval("SPIRAL_AUTONOMY_STABILITY_INDEX_FLOOR", 0.92),
    invariantPressureCeiling: envUnitInterval("SPIRAL_AUTONOMY_INVARIANT_PRESSURE_CEILING", 0.68),
    structuralEntropyCeiling: envUnitInterval("SPIRAL_AUTONOMY_STRUCTURAL_ENTROPY_CEILING", 0.58),
  };
}

function getExecutiveCycleRunnerConfig(): ExecutiveCycleRunnerConfig {
  return {
    evaluationIntervalMs: envPositiveInt("SPIRAL_AUTONOMY_EVAL_INTERVAL_MS", 5 * 60_000),
    triggerCooldownMs: envPositiveInt("SPIRAL_AUTONOMY_TRIGGER_COOLDOWN_MS", 20 * 60_000),
    entropyWindowSize: envPositiveInt("SPIRAL_AUTONOMY_ENTROPY_WINDOW_SIZE", 10),
    exploratoryEnabled: envBoolean("SPIRAL_AUTONOMY_EXPLORATORY_ENABLED", true),
    exploratoryPulseCadence: envPositiveInt("SPIRAL_AUTONOMY_EXPLORATORY_PULSE_CADENCE", 6),
    exploratoryMinimumSampleCount: envPositiveInt("SPIRAL_AUTONOMY_EXPLORATORY_MIN_SAMPLES", 6),
  };
}

function isExploratoryPulseDue(args: {
  enabled: boolean;
  sampleCount: number;
  cadence: number;
  minimumSampleCount: number;
  lastTriggeredSampleCount: number;
}): boolean {
  if (!args.enabled) return false;
  const sampleCount = Math.max(0, Math.floor(args.sampleCount));
  const cadence = Math.max(1, Math.floor(args.cadence));
  const minimumSampleCount = Math.max(1, Math.floor(args.minimumSampleCount));
  const lastTriggeredSampleCount = Math.max(0, Math.floor(args.lastTriggeredSampleCount));
  if (sampleCount < minimumSampleCount) return false;
  if (sampleCount % cadence !== 0) return false;
  return sampleCount > lastTriggeredSampleCount;
}

function isIntervalAllowed(principalId: string, now: number, intervalMs: number): boolean {
  const previous = lastEvaluationByPrincipal.get(principalId);
  if (previous === undefined || previous <= 0) return true;
  return now - previous >= intervalMs;
}

function isCooldownAllowed(principalId: string, now: number, cooldownMs: number): boolean {
  const previous = lastTriggerByPrincipal.get(principalId);
  if (previous === undefined || previous <= 0) return true;
  return now - previous >= cooldownMs;
}

function buildShadowSuggestion(args: {
  principalId: string;
  timestamp: number;
  structuralEntropy: number;
  recursivePressure: number;
  stabilityIndex: number;
  invariantPressure: number;
  stabilityFloor: number;
  invariantPressureCeiling: number;
  linesAddedMean: number;
  linesDeletedMean: number;
  semanticDiffMean: number;
}): ShadowAutonomySuggestion {
  const notes: string[] = [];
  if (args.structuralEntropy >= 0.58) {
    notes.push(
      `STRUCTURAL_ENTROPY_HIGH(${args.structuralEntropy.toFixed(3)}>=0.580): recommend bounded review before another mutation.`,
    );
  }
  if (args.recursivePressure >= 0.08) {
    notes.push(
      `RECURSIVE_PRESSURE_RISING(${args.recursivePressure.toFixed(3)}>=0.080): suppress self-amplifying loops until stabilization.`,
    );
  }
  if (args.stabilityIndex < args.stabilityFloor || args.invariantPressure > args.invariantPressureCeiling) {
    notes.push(
      `IDENTITY_CONSISTENCY_WARN(stability=${args.stabilityIndex.toFixed(3)}, pressure=${args.invariantPressure.toFixed(3)}).`,
    );
  }
  if (
    args.linesDeletedMean > args.linesAddedMean * 1.5 &&
    args.semanticDiffMean <= 0.12
  ) {
    notes.push(
      `DEAD_CODE_POSSIBLE(deletedMean=${args.linesDeletedMean.toFixed(3)}, addedMean=${args.linesAddedMean.toFixed(3)}, semanticMean=${args.semanticDiffMean.toFixed(3)}).`,
    );
  }
  if (notes.length === 0) {
    notes.push("SHADOW_OK: no high-risk recursive or entropy signal detected.");
  }

  const identityConsistency =
    args.stabilityIndex >= args.stabilityFloor &&
    args.invariantPressure <= args.invariantPressureCeiling
      ? "pass"
      : "warn";
  const deadCodeSignal =
    args.linesDeletedMean > args.linesAddedMean * 1.5 && args.semanticDiffMean <= 0.12
      ? "possible"
      : "none";

  return {
    schemaVersion: "autonomy-shadow.v1",
    timestamp: args.timestamp,
    principalId: args.principalId,
    authority: "shadow",
    findings: {
      structuralEntropyScore: round(args.structuralEntropy),
      recursivePressureScore: round(args.recursivePressure),
      identityConsistency,
      deadCodeSignal,
      notes,
    },
  };
}

export async function evaluateExecutiveAutonomy(args: {
  principalId: string;
  now?: number;
  thresholds?: AutonomyTriggerThresholds;
  runnerConfig?: ExecutiveCycleRunnerConfig;
  ledgerEntries?: EvolutionLedgerLikeEntry[];
}): Promise<ExecutiveAutonomyEvaluation> {
  const principalId = normalizePrincipalId(args.principalId);
  const now = normalizeTimestamp(args.now || Date.now());
  const thresholds = args.thresholds || getAutonomyTriggerThresholds();
  const runnerConfig = args.runnerConfig || getExecutiveCycleRunnerConfig();
  const intervalAllowed = principalId
    ? isIntervalAllowed(principalId, now, runnerConfig.evaluationIntervalMs)
    : false;
  const baseShadow: ShadowAutonomySuggestion = {
    schemaVersion: "autonomy-shadow.v1",
    timestamp: now,
    principalId,
    authority: "shadow",
    findings: {
      structuralEntropyScore: 0,
      recursivePressureScore: 0,
      identityConsistency: "pass",
      deadCodeSignal: "none",
      notes: ["SHADOW_SKIPPED: interval gate prevented this evaluation tick."],
    },
  };
  if (!principalId || !intervalAllowed) {
    return {
      schemaVersion: "autonomy-trigger.v1",
      timestamp: now,
      principalId,
      triggered: false,
      reasonCodes: ["AUTONOMY_EVAL_INTERVAL_ACTIVE"],
      sampleCount: 0,
      metrics: {
        driftVelocity: 0,
        stabilityIndex: 1,
        invariantPressure: 0,
        structuralEntropy: 0,
        recursivePressure: 0,
      },
      thresholds,
      runner: {
        intervalAllowed,
        cooldownAllowed: false,
        exploratoryEnabled: runnerConfig.exploratoryEnabled,
        exploratoryPulseCadence: Math.max(1, Math.floor(runnerConfig.exploratoryPulseCadence)),
        exploratoryMinimumSampleCount: Math.max(
          1,
          Math.floor(runnerConfig.exploratoryMinimumSampleCount),
        ),
        exploratoryPulseDue: false,
      },
      shadow: baseShadow,
    };
  }

  const entries = args.ledgerEntries ?? (await readEvolutionLedgerEntries());
  const trajectory = deriveDriftTrajectoryFromLedger(entries, {
    principalId,
    modeFilter: "wild",
    now,
  });
  const samples = buildDriftSamplesFromLedger(entries, {
    principalId,
    modeFilter: "wild",
    config: trajectory.config,
  });
  const structuralEntropy = computeStructuralEntropyIndex(
    samples,
    runnerConfig.entropyWindowSize,
  );
  const recursivePressure = round(
    Math.abs(
      calculateSlope([
        trajectory.windows["20c"].driftVelocity,
        trajectory.windows["10c"].driftVelocity,
        trajectory.windows["5c"].driftVelocity,
      ]),
    ),
  );

  const reasonCodes: string[] = [];
  const exploratoryPulseDue = isExploratoryPulseDue({
    enabled: runnerConfig.exploratoryEnabled,
    sampleCount: samples.length,
    cadence: runnerConfig.exploratoryPulseCadence,
    minimumSampleCount: runnerConfig.exploratoryMinimumSampleCount,
    lastTriggeredSampleCount: lastExploratorySampleByPrincipal.get(principalId) || 0,
  });
  if (Math.abs(trajectory.latest.driftVelocity) >= thresholds.driftVelocityAbsThreshold) {
    reasonCodes.push("AUTONOMY_TRIGGER_DRIFT_VELOCITY");
  }
  if (trajectory.latest.stabilityIndex <= thresholds.stabilityIndexFloor) {
    reasonCodes.push("AUTONOMY_TRIGGER_STABILITY_LOW");
  }
  if (trajectory.latest.invariantPressure >= thresholds.invariantPressureCeiling) {
    reasonCodes.push("AUTONOMY_TRIGGER_INVARIANT_PRESSURE");
  }
  if (structuralEntropy >= thresholds.structuralEntropyCeiling) {
    reasonCodes.push("AUTONOMY_TRIGGER_STRUCTURAL_ENTROPY");
  }
  if (exploratoryPulseDue) {
    reasonCodes.push("AUTONOMY_TRIGGER_EXPLORATORY_PULSE");
  }

  const recent = samples.slice(-Math.max(1, runnerConfig.entropyWindowSize));
  const linesAddedMean = mean(recent.map((sample) => sample.linesAdded));
  const linesDeletedMean = mean(recent.map((sample) => sample.linesDeleted));
  const semanticDiffMean = mean(recent.map((sample) => sample.semanticDiffScore));
  const shadow = buildShadowSuggestion({
    principalId,
    timestamp: now,
    structuralEntropy,
    recursivePressure,
    stabilityIndex: trajectory.latest.stabilityIndex,
    invariantPressure: trajectory.latest.invariantPressure,
    stabilityFloor: thresholds.stabilityIndexFloor,
    invariantPressureCeiling: thresholds.invariantPressureCeiling,
    linesAddedMean,
    linesDeletedMean,
    semanticDiffMean,
  });

  const thresholdTriggered = reasonCodes.length > 0;
  const cooldownAllowed = isCooldownAllowed(principalId, now, runnerConfig.triggerCooldownMs);
  const triggered = thresholdTriggered && cooldownAllowed;
  lastEvaluationByPrincipal.set(principalId, now);
  if (triggered) {
    lastTriggerByPrincipal.set(principalId, now);
    if (exploratoryPulseDue) {
      lastExploratorySampleByPrincipal.set(principalId, Math.max(0, samples.length));
    }
  } else if (thresholdTriggered && !cooldownAllowed) {
    reasonCodes.push("AUTONOMY_TRIGGER_COOLDOWN_ACTIVE");
  }

  return {
    schemaVersion: "autonomy-trigger.v1",
    timestamp: now,
    principalId,
    triggered,
    reasonCodes: reasonCodes.length > 0 ? reasonCodes : ["AUTONOMY_TRIGGER_NONE"],
    sampleCount: samples.length,
    metrics: {
      driftVelocity: trajectory.latest.driftVelocity,
      stabilityIndex: trajectory.latest.stabilityIndex,
      invariantPressure: trajectory.latest.invariantPressure,
      structuralEntropy,
      recursivePressure,
    },
    thresholds,
    runner: {
      intervalAllowed: true,
      cooldownAllowed,
      exploratoryEnabled: runnerConfig.exploratoryEnabled,
      exploratoryPulseCadence: Math.max(1, Math.floor(runnerConfig.exploratoryPulseCadence)),
      exploratoryMinimumSampleCount: Math.max(
        1,
        Math.floor(runnerConfig.exploratoryMinimumSampleCount),
      ),
      exploratoryPulseDue,
    },
    ...(triggered ? { signal: buildSignal(reasonCodes) } : {}),
    shadow,
  };
}
