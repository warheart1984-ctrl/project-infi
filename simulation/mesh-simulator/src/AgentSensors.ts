import type { AgentEntity } from './AgentEntity.js';
import type { SimulationWorld } from './SimulationWorld.js';

export interface GovernanceSnapshot {
  frozen: boolean;
  authority: string;
}

export interface AgentSensorsSnapshot {
  self: AgentEntity;
  neighbors: AgentEntity[];
  governance: GovernanceSnapshot;
}

export function senseEnvironment(world: SimulationWorld, agent: AgentEntity): AgentSensorsSnapshot {
  return {
    self: agent,
    neighbors: senseAgents(world, agent),
    governance: senseGovernanceState(world),
  };
}

export function senseAgents(world: SimulationWorld, agent: AgentEntity): AgentEntity[] {
  return world.getNeighbors(agent.position.x, agent.position.y)
    .map((position) => world.getAgentAt(position.x, position.y))
    .filter((candidate): candidate is AgentEntity => candidate !== undefined && candidate.id !== agent.id);
}

export function senseGovernanceState(world: SimulationWorld): GovernanceSnapshot {
  return {
    frozen: world.governance.frozen,
    authority: world.governance.authority,
  };
}
