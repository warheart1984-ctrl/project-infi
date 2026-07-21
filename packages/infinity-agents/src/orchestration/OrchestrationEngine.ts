import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

import type { OrchestrationPlan } from './OrchestrationPlan.js';
import { AgentScheduler } from './AgentScheduler.js';
import { orchestrationInvariants, type OrchestrationInvariantResult } from './OrchestrationInvariant.js';

export interface OrchestrationState {
  planId: string;
  completedTasks: string[];
  frozen: boolean;
}

export class OrchestrationEngine {
  private plan?: OrchestrationPlan;
  private state: OrchestrationState = { planId: '', completedTasks: [], frozen: false };

  constructor(
    private readonly bus: TriCoreBus = new TriCoreBus(),
    private readonly scheduler: AgentScheduler = new AgentScheduler(bus),
  ) {}

  loadPlan(plan: OrchestrationPlan): OrchestrationState {
    this.plan = plan;
    this.state = { planId: plan.id, completedTasks: [], frozen: false };
    return this.getState();
  }

  validatePlan(): OrchestrationInvariantResult[] {
    if (!this.plan) {
      throw new Error('No plan loaded');
    }
    return orchestrationInvariants.map((invariant) => invariant.check(this.plan!, this.state.frozen));
  }

  executePlan(): TriCoreMessage[] {
    if (!this.plan) {
      throw new Error('No plan loaded');
    }
    const results: TriCoreMessage[] = [];
    for (const task of this.scheduler.schedule(this.plan)) {
      const message = this.scheduler.dispatchTask(task);
      if (message) {
        results.push(message);
        this.state.completedTasks.push(task.id);
      }
    }
    return results;
  }

  receiveResult(message: TriCoreMessage): boolean {
    return this.scheduler.handleAgentResponse(message);
  }

  getState(): OrchestrationState {
    return structuredClone(this.state);
  }
}
