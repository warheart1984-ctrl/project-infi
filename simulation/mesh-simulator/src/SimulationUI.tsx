import type { SimulationState } from './store/simStore.js';

export interface SimulationUIProps {
  state: SimulationState;
}

export function SimulationUI({ state }: SimulationUIProps) {
  return (
    <div>
      <h1>AAES-OS Simulation</h1>
      <p>Agents: {state.agents.length}</p>
      <p>Frozen: {String(state.governance.frozen)}</p>
    </div>
  );
}
