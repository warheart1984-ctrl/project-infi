import type { AgentAction } from './AgentActions.js';
import type { AgentEntity, AgentPosition } from './AgentEntity.js';

export interface SimulationGovernanceState {
  frozen: boolean;
  authority: string;
}

export class SimulationWorld {
  readonly governance: SimulationGovernanceState = {
    frozen: false,
    authority: 'AAES governance',
  };

  private readonly agents = new Map<string, AgentEntity>();

  constructor(
    public readonly width = 8,
    public readonly height = 8,
  ) {}

  addAgent(agent: AgentEntity): void {
    this.agents.set(agent.id, structuredClone(agent));
  }

  getAgentAt(x: number, y: number): AgentEntity | undefined {
    for (const agent of this.agents.values()) {
      if (agent.position.x === x && agent.position.y === y) {
        return structuredClone(agent);
      }
    }
    return undefined;
  }

  getAgents(): AgentEntity[] {
    return [...this.agents.values()].map((agent) => structuredClone(agent));
  }

  getNeighbors(x: number, y: number): AgentPosition[] {
    return [
      { x: x - 1, y },
      { x: x + 1, y },
      { x, y: y - 1 },
      { x, y: y + 1 },
    ].filter((position) => this.isInBounds(position.x, position.y));
  }

  updateWorld(): void {
    for (const agent of this.agents.values()) {
      if (agent.position.x < 0) agent.position.x = 0;
      if (agent.position.y < 0) agent.position.y = 0;
      if (agent.position.x >= this.width) agent.position.x = this.width - 1;
      if (agent.position.y >= this.height) agent.position.y = this.height - 1;
    }
  }

  applyAgentActions(actions: AgentAction[]): void {
    for (const action of actions) {
      const agent = this.agents.get(action.agentId);
      if (!agent) {
        continue;
      }
      if (action.type === 'move') {
        const payload = action.payload as { x?: number; y?: number };
        if (typeof payload.x === 'number') {
          agent.position.x = this.clamp(payload.x, 0, this.width - 1);
        }
        if (typeof payload.y === 'number') {
          agent.position.y = this.clamp(payload.y, 0, this.height - 1);
        }
      }
    }
  }

  private isInBounds(x: number, y: number): boolean {
    return x >= 0 && y >= 0 && x < this.width && y < this.height;
  }

  private clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
  }
}
