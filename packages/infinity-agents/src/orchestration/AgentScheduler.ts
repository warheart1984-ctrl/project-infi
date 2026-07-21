import { randomUUID } from 'node:crypto';

import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

import type { OrchestrationPlan, OrchestrationTask } from './OrchestrationPlan.js';

export interface ScheduledTaskResult {
  task: OrchestrationTask;
  message: TriCoreMessage;
}

export class AgentScheduler {
  constructor(private readonly bus: TriCoreBus = new TriCoreBus()) {}

  schedule(plan: OrchestrationPlan): OrchestrationTask[] {
    return [...plan.tasks].sort((left, right) => left.id.localeCompare(right.id));
  }

  dispatchTask(task: OrchestrationTask): TriCoreMessage | null {
    return this.bus.send({
      id: randomUUID(),
      from: 'governance',
      to: 'agent',
      type: 'AGENT_ACT',
      payload: task,
      timestamp: Date.now(),
      correlationId: task.id,
    });
  }

  handleAgentResponse(message: TriCoreMessage): boolean {
    return message.to === 'governance' || message.to === 'runtime';
  }
}
