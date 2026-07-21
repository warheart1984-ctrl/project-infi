import { AgentSandbox } from './sandbox/AgentSandbox.js';
import type { CapabilityModel } from './capabilities/CapabilityModel.js';

export interface InfinityAgent {
  id: string;
  sandbox: AgentSandbox;
}

export function createInfinityAgent(id: string, capabilityModel: CapabilityModel): InfinityAgent {
  return {
    id,
    sandbox: new AgentSandbox(capabilityModel),
  };
}
