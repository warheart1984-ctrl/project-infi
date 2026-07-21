import type { CapabilityModel } from '../capabilities/CapabilityModel.js';

export interface SandboxedAgentAction {
  agentId: string;
  action: string;
  payload?: unknown;
}

export class AgentSandbox {
  constructor(private readonly capabilityModel: CapabilityModel) {}

  allow(action: SandboxedAgentAction): boolean {
    return this.capabilityModel.agentId === action.agentId && this.capabilityModel.allowedActions.includes(action.action);
  }

  enforce(action: SandboxedAgentAction): SandboxedAgentAction {
    if (!this.allow(action)) {
      throw new Error(`Unauthorized action: ${action.action}`);
    }
    return action;
  }
}
