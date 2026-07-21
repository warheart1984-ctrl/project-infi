import { TriCoreBus } from '@aaes-os/tri-core-protocol';

import { createComputeAction, sendAgentAction, type AgentAction } from './AgentActions.js';
import type { AgentBehavior } from './AgentBehavior.js';
import { DefaultAgentBehavior } from './AgentBehavior.js';
import type { AgentEntity } from './AgentEntity.js';
import { senseEnvironment } from './AgentSensors.js';
import { SimulationWorld } from './SimulationWorld.js';
import { simStore } from './store/simStore.js';

export interface SimulationEngineOptions {
  bus?: TriCoreBus;
}

export class SimulationEngine {
  private readonly bus: TriCoreBus;
  private readonly world: SimulationWorld = new SimulationWorld();
  private readonly behaviors = new Map<string, AgentBehavior>();

  constructor(options: SimulationEngineOptions = {}) {
    this.bus = options.bus ?? new TriCoreBus();
  }

  loadAgents(agents: AgentEntity[]): void {
    for (const agent of agents) {
      this.world.addAgent(agent);
      this.behaviors.set(agent.id, new DefaultAgentBehavior());
    }
    simStore.setState({ agents: this.world.getAgents() });
  }

  tick(): AgentAction[] {
    const actions: AgentAction[] = [];
    for (const agent of this.world.getAgents()) {
      const behavior = this.behaviors.get(agent.id) ?? new DefaultAgentBehavior();
      const sensors = senseEnvironment(this.world, agent);
      const action = behavior.decideAction(sensors);
      actions.push(action);
      sendAgentAction(this.bus, action);
    }

    this.world.applyAgentActions(actions);
    this.world.updateWorld();
    simStore.setState({
      agents: this.world.getAgents(),
      actions,
    });
    return actions;
  }

  getWorld(): SimulationWorld {
    return this.world;
  }

  seedDefaultAgents(count = 3): void {
    const agents: AgentEntity[] = Array.from({ length: count }, (_, index) => ({
      id: `agent-${index}`,
      position: { x: index, y: index },
      capabilities: [{ id: `cap-${index}`, name: `Capability ${index}` }],
      sensors: ['environment', 'governance'],
      behavior: 'default',
    }));
    this.loadAgents(agents);
  }

  createComputeBurst(job = 'governed-compute'): void {
    const actions: AgentAction[] = this.world.getAgents().map((agent) => createComputeAction(agent, job));
    this.world.applyAgentActions(actions);
    simStore.setState({ actions });
  }
}
