import type { AgentAction } from './AgentActions.js';
import type { AgentSensorsSnapshot } from './AgentSensors.js';

export interface AgentBehavior {
  decideAction(sensors: AgentSensorsSnapshot): AgentAction;
}

export class DefaultAgentBehavior implements AgentBehavior {
  decideAction(sensors: AgentSensorsSnapshot): AgentAction {
    return {
      type: 'compute',
      agentId: sensors.self.id,
      payload: {
        neighbors: sensors.neighbors.length,
        governanceFrozen: sensors.governance.frozen,
      },
    };
  }
}
