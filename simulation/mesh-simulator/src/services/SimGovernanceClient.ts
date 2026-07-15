import type { SimulationState } from '../store/simStore.js';

export class SimGovernanceClient {
  constructor(private readonly getState: () => SimulationState) {}

  readGovernanceState(): SimulationState['governance'] {
    return this.getState().governance;
  }
}
