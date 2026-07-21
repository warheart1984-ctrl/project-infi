import { TriCoreBus } from '@aaes-os/tri-core-protocol';

import { AgentSandbox } from './sandbox/AgentSandbox.js';
import type { CapabilityModel } from './capabilities/CapabilityModel.js';
import { createInfinityAgent, type InfinityAgent } from './InfinityAgent.js';
import { OrchestrationEngine } from './orchestration/OrchestrationEngine.js';
import type { OrchestrationPlan } from './orchestration/OrchestrationPlan.js';

export class InfinityAgentManager {
  private readonly agents = new Map<string, InfinityAgent>();
  private readonly bus: TriCoreBus;
  private readonly orchestrationEngine: OrchestrationEngine;

  constructor(bus: TriCoreBus = new TriCoreBus()) {
    this.bus = bus;
    this.orchestrationEngine = new OrchestrationEngine(this.bus);
  }

  registerAgent(id: string, capabilityModel: CapabilityModel): InfinityAgent {
    const agent = createInfinityAgent(id, capabilityModel);
    this.agents.set(id, agent);
    return agent;
  }

  wrapAgent(id: string): AgentSandbox | undefined {
    return this.agents.get(id)?.sandbox;
  }

  loadPlan(plan: OrchestrationPlan): void {
    this.orchestrationEngine.loadPlan(plan);
  }

  executePlan(): void {
    this.orchestrationEngine.executePlan();
  }

  getOrchestrationEngine(): OrchestrationEngine {
    return this.orchestrationEngine;
  }
}
