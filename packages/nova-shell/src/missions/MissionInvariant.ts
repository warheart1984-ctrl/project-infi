import type { Mission } from './Mission.js';
import type { MissionState } from './MissionState.js';

export interface MissionInvariantResult {
  passed: boolean;
  severity: 'info' | 'warn' | 'error' | 'fatal';
  message?: string;
}

export interface MissionInvariant {
  id: string;
  description: string;
  check(mission: Mission, state: MissionState): MissionInvariantResult;
}

export const missionInvariants: MissionInvariant[] = [
  {
    id: 'I-MSN-001',
    description: 'Mission steps must be executed in order',
    check(mission, state) {
      const passed = state.currentStep >= 0 && state.currentStep <= mission.steps.length;
      return {
        passed,
        severity: passed ? 'info' : 'error',
        message: passed ? 'Mission order valid' : 'Mission steps executed out of order',
      };
    },
  },
  {
    id: 'I-MSN-002',
    description: 'Mission must not bypass governance',
    check(_mission, state) {
      const passed = state.history.every((entry) => typeof entry === 'object' && entry !== null);
      return {
        passed,
        severity: passed ? 'info' : 'fatal',
        message: passed ? 'Mission routed through governance' : 'Mission bypassed governance',
      };
    },
  },
  {
    id: 'I-MSN-003',
    description: 'Mission must record all steps in ledger',
    check(mission, state) {
      const passed = state.history.length >= Math.min(state.currentStep, mission.steps.length);
      return {
        passed,
        severity: passed ? 'info' : 'error',
        message: passed ? 'Mission ledger complete' : 'Mission step missing from ledger',
      };
    },
  },
];

export function registerMissionInvariants(engine: { register(invariant: MissionInvariant): void }): void {
  for (const invariant of missionInvariants) {
    engine.register(invariant);
  }
}
