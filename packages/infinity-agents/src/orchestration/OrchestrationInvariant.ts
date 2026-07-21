import type { OrchestrationPlan } from './OrchestrationPlan.js';

export interface OrchestrationInvariantResult {
  passed: boolean;
  severity: 'info' | 'warn' | 'error' | 'fatal';
  message?: string;
}

export interface OrchestrationInvariant {
  id: string;
  description: string;
  check(plan: OrchestrationPlan, freezeActive: boolean): OrchestrationInvariantResult;
}

export const orchestrationInvariants: OrchestrationInvariant[] = [
  {
    id: 'I-ORCH-001',
    description: 'No agent may execute tasks outside its capability model',
    check(plan) {
      const passed = plan.tasks.every((task) => plan.agents.includes(task.agentId));
      return {
        passed,
        severity: passed ? 'info' : 'error',
        message: passed ? 'Capability boundary respected' : 'Task outside capability model',
      };
    },
  },
  {
    id: 'I-ORCH-002',
    description: 'Orchestration tasks must be ledgered',
    check(plan) {
      const passed = plan.tasks.length > 0;
      return {
        passed,
        severity: passed ? 'info' : 'error',
        message: passed ? 'Tasks present for ledgering' : 'No tasks to ledger',
      };
    },
  },
  {
    id: 'I-ORCH-003',
    description: 'Orchestration must halt if constitutional freeze is active',
    check(_plan, freezeActive) {
      return {
        passed: !freezeActive,
        severity: freezeActive ? 'fatal' : 'info',
        message: freezeActive ? 'Freeze active' : 'Orchestration allowed',
      };
    },
  },
];
