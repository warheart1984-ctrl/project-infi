import { readFile } from "fs/promises";
import path from "path";
import { storage } from "./storage";
import type { EvolutionCommand } from "./evolution-command";
import { parseEvolutionCommand, renderEvolutionStateSummary } from "./evolution-command";
import { evaluateExecutiveAutonomy } from "./evolution-evaluator";
import { runSelfDistortionScan } from "./self-distortion";
import { runSelfEvaluation } from "./self-evaluation";
import {
  appendDriftTrajectoryMetrics,
  buildDriftSamplesFromLedger,
  computeDriftTrajectoryPreview,
  computeInvariantPressureIndex,
  estimateInvariantImpactFromFiles,
  estimateSemanticDiffScore,
  evaluateAutonomyDriftBudget,
  evaluateExploratoryMicroDelta,
  getAutonomyDriftBudget,
  getDriftTrajectoryConfig,
  getExploratoryMicroDeltaBudget,
  readEvolutionLedgerEntries,
} from "./evolution-drift";
import { buildRewriteProposalDraft } from "./proposals/proposal-generator";
import {
  getRewriteProposalById,
  listRewriteProposals,
  recordRewriteProposalApply,
  recordRewriteProposalExecution,
  saveRewriteProposal,
  updateRewriteProposalStatus,
} from "./proposals/proposal-store";
import {
  isCodexExecutionEnabled,
  runRewriteProposalExecution,
} from "./proposals/proposal-executor";
import { applyRewriteProposalPatch } from "./proposals/proposal-applier";
import { recordSelfRepoCommit, summarizePatchFromText } from "./evolution-self-repo";
import {
  appendEvolutionLedger,
  getPrincipalEvolutionState,
  recordEvolutionContext,
  updatePrincipalEvolutionState,
  type EvolutionTrigger,
  type PrincipalEvolutionState,
} from "./evolution-state";

interface EvolutionCycleInput {
  principalId: string;
  chatId: string;
  trigger: EvolutionTrigger;
  signal?: string;
  force?: boolean;
  now?: number;
}

interface EvolutionCycleResult {
  status: "skipped" | "drafted" | "executed" | "applied" | "failed";
  summary: string;
  proposalId?: string;
}

function normalizePrincipalId(value: string): string {
  return value.trim().slice(0, 200);
}

function parsePositiveInt(raw: string | undefined, fallback: number, min = 1, max = 60 * 24): number {
  const parsed = Number.parseInt(raw || "", 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, parsed));
}

function parseBoundedNumber(
  raw: string | undefined,
  fallback: number,
  min: number,
  max: number,
): number {
  const parsed = Number.parseFloat(raw || "");
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, parsed));
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
}

function maxInvariantPressureForAutonomyApply(): number {
  return parseBoundedNumber(process.env.SPIRAL_AUTONOMY_INVARIANT_PRESSURE_MAX, 0.72, 0, 1);
}

function round(value: number, decimals = 6): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

function isExploratoryAutonomySignal(signal: string | undefined): boolean {
  const normalized = (signal || "").trim().toLowerCase();
  if (!normalized) return false;
  return normalized.includes("autonomy_trigger_exploratory_pulse");
}

export function evolutionTriggerAllowsProposalApply(trigger: EvolutionTrigger): boolean {
  return trigger === "manual";
}

export function pulseAncillaryWorkAllowed(state: Pick<
  PrincipalEvolutionState,
  "backgroundPulseEnabled" | "mutationSealEnabled"
>): boolean {
  return state.backgroundPulseEnabled && !state.mutationSealEnabled;
}

function minCycleMinutes(): number {
  return parsePositiveInt(process.env.SPIRAL_EVOLUTION_MIN_CYCLE_MINUTES, 30, 1, 24 * 7);
}

function minCycleMessages(): number {
  return parsePositiveInt(process.env.SPIRAL_EVOLUTION_MIN_CYCLE_MESSAGES, 8, 2, 200);
}

function observationAuditIntervalMs(): number {
  return parsePositiveInt(
    process.env.SPIRAL_OBSERVATION_AUDIT_INTERVAL_MS,
    15 * 60_000,
    60_000,
    24 * 60 * 60_000,
  );
}

export function isObservationAuditDue(
  lastObservationAuditAt: number,
  now: number,
  intervalMs: number,
): boolean {
  if (!Number.isFinite(lastObservationAuditAt) || lastObservationAuditAt <= 0) return true;
  return now - lastObservationAuditAt >= intervalMs;
}

export function buildObservationAuditSummary(args: {
  gatesFailed: number;
  mimicryFindings: number;
  firstGateFailureId?: string;
  firstMimicryClass?: string;
}): string {
  const parts = [
    `gatesFailed=${Math.max(0, Math.floor(args.gatesFailed))}`,
    `mimicryFindings=${Math.max(0, Math.floor(args.mimicryFindings))}`,
    ...(args.firstGateFailureId ? [`firstGateFailure=${args.firstGateFailureId}`] : []),
    ...(args.firstMimicryClass ? [`firstMimicry=${args.firstMimicryClass}`] : []),
  ];
  return `Observation audit: ${parts.join(" ")}`;
}

function hasCooldownElapsed(state: PrincipalEvolutionState, now: number): boolean {
  if (!Number.isFinite(state.lastCycleAt) || state.lastCycleAt <= 0) return true;
  const minMs = minCycleMinutes() * 60_000;
  return now - state.lastCycleAt >= minMs;
}

function summarizeCooldownRemaining(state: PrincipalEvolutionState, now: number): string {
  if (!Number.isFinite(state.lastCycleAt) || state.lastCycleAt <= 0) return "ready";
  const minMs = minCycleMinutes() * 60_000;
  const remaining = Math.max(0, minMs - (now - state.lastCycleAt));
  if (remaining <= 0) return "ready";
  const minutes = Math.ceil(remaining / 60_000);
  return `${minutes}m remaining`;
}

async function markCycleOutcome(args: {
  principalId: string;
  now: number;
  chatId: string;
  trigger: EvolutionTrigger;
  status: EvolutionCycleResult["status"];
  summary: string;
  proposalId?: string;
  cycleId?: number;
  commitHash?: string;
}): Promise<void> {
  await updatePrincipalEvolutionState(
    args.principalId,
    (current) => ({
      ...current,
      lastCycleAt: args.now,
      lastCycleTrigger: args.trigger,
      lastCycleStatus: args.status,
      lastCycleSummary: args.summary.slice(0, 1000),
      lastCycleChatId: args.chatId,
      ...(args.proposalId ? { lastProposalId: args.proposalId } : {}),
      ...(args.cycleId ? { lastCycleId: args.cycleId } : {}),
      ...(args.commitHash ? { lastCommitHash: args.commitHash } : {}),
      lastSeenChatId: args.chatId,
    }),
    args.now,
  );
}

function isCommandOnlyUserTurn(content: string): boolean {
  const command = parseEvolutionCommand(content);
  return Boolean(command);
}

function resolvePatchArtifactAbsolutePath(patchArtifactPath: string): string {
  const absolute = path.resolve(process.cwd(), patchArtifactPath);
  const relative = path.relative(process.cwd(), absolute);
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(
      `AUTONOMY_DRIFT_BUDGET_PATCH_PATH_INVALID path=${patchArtifactPath}`,
    );
  }
  return absolute;
}

async function enforceAutonomyMutationGuards(args: {
  principalId: string;
  patchArtifactPath: string;
  signal?: string;
}): Promise<void> {
  const driftConfig = getDriftTrajectoryConfig();
  const budget = getAutonomyDriftBudget();
  const entries = await readEvolutionLedgerEntries();
  const samples = buildDriftSamplesFromLedger(entries, {
    principalId: args.principalId,
    modeFilter: "wild",
    config: driftConfig,
  });

  const patchAbsolutePath = resolvePatchArtifactAbsolutePath(args.patchArtifactPath);
  const patchText = await readFile(patchAbsolutePath, "utf8");
  const patchSummary = summarizePatchFromText(patchText);
  const candidateSemanticDiffScore = estimateSemanticDiffScore(
    patchSummary.linesAdded,
    patchSummary.linesDeleted,
    patchSummary.files.length,
  );
  const candidateInvariantImpact = estimateInvariantImpactFromFiles(patchSummary.files);
  const candidate = {
    filesTouched: patchSummary.files.length,
    linesAdded: patchSummary.linesAdded,
    linesDeleted: patchSummary.linesDeleted,
    semanticDiffScore: candidateSemanticDiffScore,
    invariantImpact: candidateInvariantImpact,
  };

  if (isExploratoryAutonomySignal(args.signal)) {
    const exploratoryBudget = getExploratoryMicroDeltaBudget();
    const exploratoryEvaluation = evaluateExploratoryMicroDelta({
      candidate,
      budget: exploratoryBudget,
    });
    if (!exploratoryEvaluation.allowed) {
      throw new Error(
        `${exploratoryEvaluation.reasonCode} filesTouched=${exploratoryEvaluation.candidate.filesTouched} maxFilesTouched=${exploratoryEvaluation.limits.maxFilesTouched} linesAdded=${exploratoryEvaluation.candidate.linesAdded} maxLinesAdded=${exploratoryEvaluation.limits.maxLinesAdded} linesDeleted=${exploratoryEvaluation.candidate.linesDeleted} maxLinesDeleted=${exploratoryEvaluation.limits.maxLinesDeleted} semanticDiffScore=${exploratoryEvaluation.candidate.semanticDiffScore.toFixed(6)} maxSemanticDiffScore=${exploratoryEvaluation.limits.maxSemanticDiffScore.toFixed(6)}`,
      );
    }
  }

  const driftBudget = evaluateAutonomyDriftBudget({
    samples,
    candidate,
    budget,
    config: driftConfig,
  });
  if (!driftBudget.allowed) {
    throw new Error(
      `${driftBudget.reasonCode} projectedCumulativeDelta=${driftBudget.projectedCumulativeDelta.toFixed(6)} limit=${driftBudget.maxCumulativeDelta.toFixed(6)} candidateFilesTouched=${driftBudget.candidateFilesTouched} maxFilesTouched=${driftBudget.maxFilesTouched}`,
    );
  }

  const pressureWindow = Math.max(1, budget.windowSize);
  const pressure = computeInvariantPressureIndex({
    samples,
    windowSize: pressureWindow,
    impactWeights: driftConfig.impactWeights,
  });
  const candidateWeight = driftConfig.impactWeights[candidateInvariantImpact] ?? 0;
  const projectedPressure = round(
    Math.min(1, (pressure.weightedSum + candidateWeight) / Math.max(1, pressure.count + 1)),
  );
  const pressureMax = maxInvariantPressureForAutonomyApply();
  if (projectedPressure > pressureMax) {
    throw new Error(
      `AUTONOMY_INVARIANT_PRESSURE_HIGH projectedInvariantPressure=${projectedPressure.toFixed(6)} limit=${pressureMax.toFixed(6)} candidateImpact=${candidateInvariantImpact}`,
    );
  }
}

async function appendLatestDriftMetricsRecord(args: {
  principalId: string;
  now: number;
}): Promise<void> {
  const record = await computeDriftTrajectoryPreview({
    principalId: args.principalId,
    modeFilter: "all",
    now: args.now,
  });
  await appendDriftTrajectoryMetrics(record);
}

async function runObservationOnlyPulseAudit(args: {
  principalId: string;
  chatId: string;
  now: number;
}): Promise<void> {
  const state = await getPrincipalEvolutionState(args.principalId, args.now);
  if (
    !isObservationAuditDue(
      state.lastObservationAuditAt,
      args.now,
      observationAuditIntervalMs(),
    )
  ) {
    return;
  }

  const [gatesReport, mimicryReport] = await Promise.all([
    runSelfEvaluation("gates"),
    runSelfDistortionScan("mimicry"),
  ]);
  const firstGateFailure = gatesReport.checks.find((check) => !check.pass)?.id;
  const firstMimicryFinding = mimicryReport.findings[0]?.class;
  const summary = buildObservationAuditSummary({
    gatesFailed: gatesReport.summary.failed,
    mimicryFindings: mimicryReport.summary.findings,
    ...(firstGateFailure ? { firstGateFailureId: firstGateFailure } : {}),
    ...(firstMimicryFinding ? { firstMimicryClass: firstMimicryFinding } : {}),
  });

  await updatePrincipalEvolutionState(
    args.principalId,
    (current) => ({
      ...current,
      lastObservationAuditAt: args.now,
      lastObservationAuditSummary: summary,
      lastSeenChatId: args.chatId,
    }),
    args.now,
  );
  await appendEvolutionLedger({
    timestamp: args.now,
    principalId: args.principalId,
    type: "observation-audit",
    detail: summary,
    chatId: args.chatId,
    mode: state.mode,
    trigger: "pulse",
  });
}

async function runEvolutionCycle(input: EvolutionCycleInput): Promise<EvolutionCycleResult> {
  const principalId = normalizePrincipalId(input.principalId);
  const chatId = input.chatId.trim();
  const now = normalizeTimestamp(input.now || Date.now());
  if (!principalId) {
    return {
      status: "skipped",
      summary: "Evolution skipped: principal is missing.",
    };
  }
  if (!chatId) {
    return {
      status: "skipped",
      summary: "Evolution skipped: chat context is missing.",
    };
  }

  const state = await getPrincipalEvolutionState(principalId, now);
  if (state.mutationSealEnabled) {
    return {
      status: "skipped",
      summary: "Evolution skipped: mutation seal is ON.",
    };
  }
  if (state.mode !== "wild") {
    return {
      status: "skipped",
      summary: "Evolution skipped: mode is STILL.",
    };
  }
  if (input.trigger === "pulse" && !state.backgroundPulseEnabled) {
    return {
      status: "skipped",
      summary: "Evolution skipped: background pulse is OFF.",
    };
  }
  if (!input.force && !hasCooldownElapsed(state, now)) {
    return {
      status: "skipped",
      summary: `Evolution skipped: cooldown active (${summarizeCooldownRemaining(state, now)}).`,
    };
  }

  const chat = await storage.getChat(chatId);
  if (!chat) {
    return {
      status: "skipped",
      summary: "Evolution skipped: chat not found.",
    };
  }
  if (chat.principalId && chat.principalId !== principalId) {
    return {
      status: "skipped",
      summary: "Evolution skipped: chat is outside current principal scope.",
    };
  }

  const messages = await storage.getMessages(chatId);
  const nonEmpty = messages.filter((message) => message.content.trim().length > 0);
  if (nonEmpty.length < minCycleMessages()) {
    return {
      status: "skipped",
      summary: `Evolution skipped: not enough message mass (${nonEmpty.length}/${minCycleMessages()}).`,
    };
  }

  const latestUserMessage = [...messages].reverse().find((message) => message.role === "user");
  if (latestUserMessage && isCommandOnlyUserTurn(latestUserMessage.content)) {
    return {
      status: "skipped",
      summary: "Evolution skipped: latest user turn is an evolution command.",
    };
  }

  const pending = await listRewriteProposals({
    principalId,
    chatId,
    status: "pending",
    limit: 20,
  });
  if (!input.force && pending.length > 0) {
    return {
      status: "skipped",
      summary: `Evolution skipped: ${pending.length} pending proposal(s) already exist for this chat.`,
    };
  }

  const draft = buildRewriteProposalDraft({
    principalId,
    chatId,
    chatTitle: chat.title,
    messages,
    ...(input.signal ? { signal: input.signal } : {}),
  });
  const saved = await saveRewriteProposal(draft);
  const proposedSummary = `Evolution drafted proposal ${saved.id}.`;

  await markCycleOutcome({
    principalId,
    now,
    chatId,
    trigger: input.trigger,
    status: "drafted",
    summary: proposedSummary,
    proposalId: saved.id,
  });
  await appendEvolutionLedger({
    timestamp: now,
    principalId,
    type: "cycle-drafted",
    detail: proposedSummary,
    chatId,
    proposalId: saved.id,
    mode: state.mode,
    trigger: input.trigger,
    ...(input.signal ? { signal: input.signal } : {}),
  });

  if (!state.autoApplyEnabled) {
    return {
      status: "drafted",
      summary: `${proposedSummary} Auto-apply is OFF.`,
      proposalId: saved.id,
    };
  }

  const accepted = await updateRewriteProposalStatus({
    principalId,
    proposalId: saved.id,
    nextStatus: "accepted",
    decidedBy: principalId,
    reason: "evolution:auto-apply",
  });
  if (!accepted) {
    const summary = `Evolution failed: could not accept proposal ${saved.id}.`;
    await markCycleOutcome({
      principalId,
      now,
      chatId,
      trigger: input.trigger,
      status: "failed",
      summary,
      proposalId: saved.id,
    });
    await appendEvolutionLedger({
      timestamp: now,
      principalId,
      type: "cycle-failed",
      detail: summary,
      chatId,
      proposalId: saved.id,
      mode: state.mode,
      trigger: input.trigger,
      ...(input.signal ? { signal: input.signal } : {}),
    });
    return {
      status: "failed",
      summary,
      proposalId: saved.id,
    };
  }

  if (!isCodexExecutionEnabled()) {
    const summary =
      `Evolution drafted and accepted proposal ${saved.id}, but execution is disabled (` +
      "set SPIRAL_CODEX_EXECUTION_ENABLED=1 to continue).";
    await markCycleOutcome({
      principalId,
      now,
      chatId,
      trigger: input.trigger,
      status: "executed",
      summary,
      proposalId: saved.id,
    });
    await appendEvolutionLedger({
      timestamp: now,
      principalId,
      type: "cycle-executed",
      detail: summary,
      chatId,
      proposalId: saved.id,
      mode: state.mode,
      trigger: input.trigger,
      ...(input.signal ? { signal: input.signal } : {}),
    });
    return {
      status: "executed",
      summary,
      proposalId: saved.id,
    };
  }

  try {
    const execution = await runRewriteProposalExecution({
      proposal: accepted,
      principalId,
    });
    const withExecution = await recordRewriteProposalExecution({
      principalId,
      proposalId: saved.id,
      execution,
    });
    if (!withExecution) {
      throw new Error("Execution result could not be recorded.");
    }

    if (execution.status !== "succeeded") {
      const summary = `Evolution execution failed for proposal ${saved.id}: ${execution.summary}`;
      await markCycleOutcome({
        principalId,
        now,
        chatId,
        trigger: input.trigger,
        status: "failed",
        summary,
        proposalId: saved.id,
      });
      await appendEvolutionLedger({
        timestamp: now,
        principalId,
        type: "cycle-failed",
        detail: summary,
        chatId,
        proposalId: saved.id,
        mode: state.mode,
        trigger: input.trigger,
        ...(input.signal ? { signal: input.signal } : {}),
      });
      return {
        status: "failed",
        summary,
        proposalId: saved.id,
      };
    }

    const latestProposal =
      (await getRewriteProposalById({
        principalId,
        proposalId: saved.id,
      })) || withExecution;

    if (execution.patchArtifactPath) {
      await enforceAutonomyMutationGuards({
        principalId,
        patchArtifactPath: execution.patchArtifactPath,
        ...(input.signal ? { signal: input.signal } : {}),
      });
    }

    if (!evolutionTriggerAllowsProposalApply(input.trigger)) {
      const summary =
        `Evolution executed proposal ${saved.id} (${execution.summary}). ` +
        "Autonomous apply is sealed; manual promotion is required.";
      await markCycleOutcome({
        principalId,
        now,
        chatId,
        trigger: input.trigger,
        status: "executed",
        summary,
        proposalId: saved.id,
      });
      await appendEvolutionLedger({
        timestamp: now,
        principalId,
        type: "cycle-executed",
        detail: summary,
        chatId,
        proposalId: saved.id,
        mode: state.mode,
        trigger: input.trigger,
        ...(input.signal ? { signal: input.signal } : {}),
      });
      return {
        status: "executed",
        summary,
        proposalId: saved.id,
      };
    }

    const apply = await applyRewriteProposalPatch({
      proposal: latestProposal,
      principalId,
      ...(execution.runId ? { runId: execution.runId } : {}),
    });
    const withApply = await recordRewriteProposalApply({
      principalId,
      proposalId: saved.id,
      apply,
    });
    if (!withApply) {
      throw new Error("Apply result could not be recorded.");
    }

    let ritualCommitHash: string | undefined;
    let ritualCycleId: number | undefined;
    let ritualDrift:
      | {
          filesTouched: number;
          linesAdded: number;
          linesDeleted: number;
          semanticDiffScore: number;
          invariantImpact: "none" | "low" | "medium" | "high";
        }
      | undefined;
    let ritualFailureNote: string | undefined;
    try {
      const ritual = await recordSelfRepoCommit({
        principalId,
        proposalId: saved.id,
        chatId,
        mode: state.mode,
        trigger: input.trigger,
        ...(input.signal ? { signal: input.signal } : {}),
        timestamp: now,
        patchArtifactPath: apply.patchArtifactPath,
        executionSummary: execution.summary,
        applySummary: apply.summary,
      });
      ritualCommitHash = ritual.commitHash;
      ritualCycleId = ritual.cycleId;
      ritualDrift = ritual.driftIndex;
    } catch (error) {
      ritualFailureNote =
        error instanceof Error && error.message.trim()
          ? error.message.trim()
          : "self-repo ritual commit failed";
    }

    const summary = ritualCommitHash
      ? `Evolution applied proposal ${saved.id} (${apply.summary}). ritualCommit=${ritualCommitHash}`
      : `Evolution applied proposal ${saved.id} (${apply.summary}).${ritualFailureNote ? ` ritualNote=${ritualFailureNote}` : ""}`;
    await markCycleOutcome({
      principalId,
      now,
      chatId,
      trigger: input.trigger,
      status: "applied",
      summary,
      proposalId: saved.id,
      ...(ritualCycleId ? { cycleId: ritualCycleId } : {}),
      ...(ritualCommitHash ? { commitHash: ritualCommitHash } : {}),
    });
    await appendEvolutionLedger({
      timestamp: now,
      principalId,
      type: "cycle-applied",
      detail: summary,
      chatId,
      proposalId: saved.id,
      mode: state.mode,
      trigger: input.trigger,
      ...(input.signal ? { signal: input.signal } : {}),
      ...(ritualCommitHash ? { commitHash: ritualCommitHash } : {}),
      ...(ritualCycleId ? { cycleId: ritualCycleId } : {}),
      ...(ritualDrift ? { driftIndex: ritualDrift } : {}),
    });
    try {
      await appendLatestDriftMetricsRecord({ principalId, now });
    } catch (error) {
      const note = error instanceof Error ? error.message : String(error);
      console.warn("Evolution drift metrics append skipped:", note);
    }
    return {
      status: "applied",
      summary,
      proposalId: saved.id,
    };
  } catch (error) {
    const message = error instanceof Error && error.message.trim()
      ? error.message.trim()
      : "unknown failure";
    const summary = `Evolution failed for proposal ${saved.id}: ${message}`;
    await markCycleOutcome({
      principalId,
      now,
      chatId,
      trigger: input.trigger,
      status: "failed",
      summary,
      proposalId: saved.id,
    });
    await appendEvolutionLedger({
      timestamp: now,
      principalId,
      type: "cycle-failed",
      detail: summary,
      chatId,
      proposalId: saved.id,
      mode: state.mode,
      trigger: input.trigger,
      ...(input.signal ? { signal: input.signal } : {}),
    });
    return {
      status: "failed",
      summary,
      proposalId: saved.id,
    };
  }
}

export async function executeEvolutionCommand(args: {
  principalId: string;
  chatId?: string;
  command: EvolutionCommand;
  now?: number;
}): Promise<string> {
  const principalId = normalizePrincipalId(args.principalId);
  const now = normalizeTimestamp(args.now || Date.now());
  if (!principalId) {
    return "Evolution unavailable: principal context is missing.";
  }
  if (args.chatId) {
    await recordEvolutionContext(principalId, args.chatId, now);
  }

  const command = args.command;

  switch (command.type) {
    case "status": {
      const state = await getPrincipalEvolutionState(principalId, now);
      return renderEvolutionStateSummary(state, now);
    }
    case "set-mode": {
      const updated = await updatePrincipalEvolutionState(
        principalId,
        (current) => ({
          ...current,
          mode: command.mode,
        }),
        now,
      );
      await appendEvolutionLedger({
        timestamp: now,
        principalId,
        type: "mode",
        detail: `Mode set to ${updated.mode.toUpperCase()}.`,
        ...(args.chatId ? { chatId: args.chatId } : {}),
      });
      return `Evolution mode set to ${updated.mode.toUpperCase()}.`;
    }
    case "set-background": {
      const updated = await updatePrincipalEvolutionState(
        principalId,
        (current) => ({
          ...current,
          backgroundPulseEnabled: command.enabled,
        }),
        now,
      );
      await appendEvolutionLedger({
        timestamp: now,
        principalId,
        type: "background",
        detail: `Background pulse ${updated.backgroundPulseEnabled ? "enabled" : "disabled"}.`,
        ...(args.chatId ? { chatId: args.chatId } : {}),
      });
      return `Background pulse ${updated.backgroundPulseEnabled ? "enabled" : "disabled"}.`;
    }
    case "set-auto-apply": {
      const updated = await updatePrincipalEvolutionState(
        principalId,
        (current) => ({
          ...current,
          autoApplyEnabled: command.enabled,
        }),
        now,
      );
      await appendEvolutionLedger({
        timestamp: now,
        principalId,
        type: "auto-apply",
        detail: `Auto-apply ${updated.autoApplyEnabled ? "enabled" : "disabled"}.`,
        ...(args.chatId ? { chatId: args.chatId } : {}),
      });
      return `Auto-apply ${updated.autoApplyEnabled ? "enabled" : "disabled"}.`;
    }
    case "set-mutation-seal": {
      const updated = await updatePrincipalEvolutionState(
        principalId,
        (current) => ({
          ...current,
          mutationSealEnabled: command.enabled,
          backgroundPulseEnabled: command.enabled ? false : current.backgroundPulseEnabled,
        }),
        now,
      );
      const detail = command.enabled
        ? "Mutation seal enabled. Background pulse disabled."
        : "Mutation seal disabled.";
      await appendEvolutionLedger({
        timestamp: now,
        principalId,
        type: "mutation-seal",
        detail,
        ...(args.chatId ? { chatId: args.chatId } : {}),
      });
      return detail;
    }
    case "cycle": {
      const state = await getPrincipalEvolutionState(principalId, now);
      const cycleChatId = (args.chatId || state.lastSeenChatId || "").trim();
      if (!cycleChatId) {
        return "Evolution cycle blocked: no chat context is available yet.";
      }
      const result = await runEvolutionCycle({
        principalId,
        chatId: cycleChatId,
        trigger: "manual",
        force: true,
        ...(command.signal ? { signal: command.signal } : {}),
        now,
      });
      return result.summary;
    }
  }
}

export async function triggerEvolutionPulse(args: {
  principalId: string;
  chatId: string;
  now?: number;
}): Promise<void> {
  const principalId = normalizePrincipalId(args.principalId);
  const chatId = args.chatId.trim();
  if (!principalId || !chatId) return;
  const now = normalizeTimestamp(args.now || Date.now());
  await recordEvolutionContext(principalId, chatId, now);
  const result = await runEvolutionCycle({
    principalId,
    chatId,
    trigger: "pulse",
    now,
  });
  const pulseState = await getPrincipalEvolutionState(principalId, now);
  if (result.status === "skipped") {
    await appendEvolutionLedger({
      timestamp: now,
      principalId,
      type: "cycle-skipped",
      detail: result.summary,
      chatId,
      mode: pulseState.mode,
      trigger: "pulse",
      ...(result.proposalId ? { proposalId: result.proposalId } : {}),
    });
  }
  if (!pulseAncillaryWorkAllowed(pulseState)) {
    return;
  }

  const autonomy = await evaluateExecutiveAutonomy({
    principalId,
    now,
  });
  const shouldRecordShadow =
    autonomy.triggered ||
    autonomy.shadow.findings.identityConsistency === "warn" ||
    autonomy.shadow.findings.deadCodeSignal === "possible";
  if (shouldRecordShadow) {
    const state = await getPrincipalEvolutionState(principalId, now);
    const shadowDetail = [
      `Autonomy shadow authority=${autonomy.shadow.authority}`,
      `triggered=${autonomy.triggered}`,
      `reasons=${autonomy.reasonCodes.join(",")}`,
      `entropy=${autonomy.shadow.findings.structuralEntropyScore.toFixed(6)}`,
      `recursivePressure=${autonomy.shadow.findings.recursivePressureScore.toFixed(6)}`,
      `identityConsistency=${autonomy.shadow.findings.identityConsistency}`,
      `deadCode=${autonomy.shadow.findings.deadCodeSignal}`,
      `note=${autonomy.shadow.findings.notes[0] || "n/a"}`,
    ].join(" | ");
    await appendEvolutionLedger({
      timestamp: now,
      principalId,
      type: "cycle-skipped",
      detail: shadowDetail,
      chatId,
      mode: state.mode,
      trigger: "pulse",
      ...(autonomy.signal ? { signal: autonomy.signal } : {}),
    });
  }
  if (autonomy.triggered) {
    const autonomousResult = await runEvolutionCycle({
      principalId,
      chatId,
      trigger: "pulse",
      ...(autonomy.signal ? { signal: autonomy.signal } : {}),
      now,
    });
    if (autonomousResult.status === "skipped") {
      const state = await getPrincipalEvolutionState(principalId, now);
      await appendEvolutionLedger({
        timestamp: now,
        principalId,
        type: "cycle-skipped",
        detail: `Autonomy trigger skipped: ${autonomousResult.summary}`,
        chatId,
        mode: state.mode,
        trigger: "pulse",
        ...(autonomy.signal ? { signal: autonomy.signal } : {}),
        ...(autonomousResult.proposalId ? { proposalId: autonomousResult.proposalId } : {}),
      });
    }
  }
  try {
    await runObservationOnlyPulseAudit({
      principalId,
      chatId,
      now,
    });
  } catch (error) {
    console.error("Observation audit failed after pulse:", error);
  }
}
