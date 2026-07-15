import type { AgentEntity } from '../AgentEntity.js';
import type { AgentAction } from '../AgentActions.js';

export interface SimulationState {
  agents: AgentEntity[];
  actions: AgentAction[];
  governance: {
    frozen: boolean;
    approvals: number;
    denials: number;
  };
}

const state: SimulationState = {
  agents: [],
  actions: [],
  governance: {
    frozen: false,
    approvals: 0,
    denials: 0,
  },
};

const listeners = new Set<(state: SimulationState) => void>();

export const simStore = {
  getState(): SimulationState {
    return structuredClone(state);
  },
  setState(patch: Partial<SimulationState>): void {
    Object.assign(state, patch);
    listeners.forEach((listener) => listener(simStore.getState()));
  },
  subscribe(listener: (state: SimulationState) => void): () => void {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};
