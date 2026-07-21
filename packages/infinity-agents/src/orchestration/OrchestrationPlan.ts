export interface OrchestrationTask {
  id: string;
  agentId: string;
  action: unknown;
}

export interface OrchestrationPlan {
  id: string;
  agents: string[];
  tasks: OrchestrationTask[];
}
