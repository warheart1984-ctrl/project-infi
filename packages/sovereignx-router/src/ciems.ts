import type {
  AgentBudgetSnapshot,
  CiemsDecision,
  CiemsIntentSpec,
  EvidenceRecord,
  GovernanceLimits,
  MeasurementHealth,
  RouteDecision,
  RouteTarget,
  RuntimeStats,
  WorkItem,
} from './types.js';

function clone<T>(value: T): T {
  return structuredClone(value);
}

function tooHot(runtime: RuntimeStats, limits: GovernanceLimits): boolean {
  return runtime.gpuTempC > limits.maxGpuTempC;
}

function tooMuchVram(runtime: RuntimeStats, limits: GovernanceLimits): boolean {
  return runtime.vramUsedBytes > limits.maxVramBytes;
}

function intentAllowsTarget(intent: CiemsIntentSpec | undefined, target: RouteTarget): boolean {
  return target === 'DELAY' || !intent || intent.allowedTargets.includes(target);
}

export class CiemsBrain {
  private readonly intents = new Map<string, CiemsIntentSpec>();
  private readonly evidence: EvidenceRecord[] = [];

  registerIntent(intent: CiemsIntentSpec): void {
    this.intents.set(intent.id, clone(intent));
  }

  submitEvidence(record: EvidenceRecord): void {
    this.evidence.push(clone(record));
  }

  listEvidence(): EvidenceRecord[] {
    return this.evidence.map((entry) => clone(entry));
  }

  getIntent(intentId: string): CiemsIntentSpec | undefined {
    const intent = this.intents.get(intentId);
    return intent ? clone(intent) : undefined;
  }

  evaluate(
    workItem: WorkItem,
    runtime: RuntimeStats,
    limits: GovernanceLimits,
    localDecision: RouteDecision,
    measurementHealth: MeasurementHealth,
    budget: AgentBudgetSnapshot,
  ): CiemsDecision[] {
    const decisions: CiemsDecision[] = [];
    const intent = this.intents.get(workItem.intentId);

    if (!intent) {
      decisions.push({
        workId: workItem.id,
        agentId: workItem.agentId,
        action: 'quarantine',
        reason: `intent ${workItem.intentId} is not registered`,
      });
      return decisions;
    }

    if (!intentAllowsTarget(intent, localDecision.target)) {
      decisions.push({
        workId: workItem.id,
        agentId: workItem.agentId,
        action: 'quarantine',
        reason: `intent ${intent.id} does not allow target ${localDecision.target}`,
      });
    }

    if (budget.tokensPerMin > (intent.maxTokensPerAgentPerMin ?? limits.maxTokensPerAgentPerMin)) {
      decisions.push({
        workId: workItem.id,
        agentId: workItem.agentId,
        action: 'throttle',
        reason: `agent ${workItem.agentId} exceeded token budget`,
      });
    }

    if (budget.flopsPerMin > (intent.maxFlopsPerAgentPerMin ?? limits.maxFlopsPerAgentPerMin)) {
      decisions.push({
        workId: workItem.id,
        agentId: workItem.agentId,
        action: 'throttle',
        reason: `agent ${workItem.agentId} exceeded flops budget`,
      });
    }

    if (!measurementHealth.trusted || measurementHealth.stale) {
      decisions.push({
        workId: workItem.id,
        agentId: workItem.agentId,
        action: 'quarantine',
        reason: 'measurement health is untrusted',
      });
    }

    if (tooHot(runtime, limits) || tooMuchVram(runtime, limits)) {
      decisions.push({
        workId: workItem.id,
        agentId: workItem.agentId,
        action: 'throttle',
        reason: 'runtime resource pressure requires conservative routing',
      });
    }

    if (runtime.activeGpuJobs > limits.maxGpuJobs || runtime.activeCpuJobs > limits.maxCpuJobs) {
      decisions.push({
        workId: workItem.id,
        agentId: workItem.agentId,
        action: 'throttle',
        reason: 'global concurrency budget exceeded',
      });
    }

    return decisions;
  }
}
