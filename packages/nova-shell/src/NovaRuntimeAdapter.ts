import { randomUUID } from 'node:crypto';

import { TriCoreBus } from '@aaes-os/tri-core-protocol';
import { RuntimeCore, type RuntimeCoreResult } from '@aaes-os/ucr-runtime';

import type { Mission } from './missions/Mission.js';
import { MissionEngine } from './missions/MissionEngine.js';

export interface NovaRuntimeAdapterOptions {
  bus?: TriCoreBus;
}

export class NovaRuntimeAdapter {
  private readonly bus: TriCoreBus;
  private readonly runtimeCore: RuntimeCore;
  private readonly missionEngine: MissionEngine;

  constructor(options: NovaRuntimeAdapterOptions = {}) {
    this.bus = options.bus ?? new TriCoreBus({ allowWhileFrozen: (message) => message.type === 'SUBSTRATE_SIGNAL' });
    this.runtimeCore = new RuntimeCore({ bus: this.bus });
    this.missionEngine = new MissionEngine({ bus: this.bus });
  }

  sendULX(source: string): RuntimeCoreResult {
    return this.runtimeCore.executeUlx(source, { adapterId: randomUUID() });
  }

  forwardRuntimeOp(op: string, payload: unknown = {}): RuntimeCoreResult {
    return this.runtimeCore.forwardToGovernance(op, payload);
  }

  runMission(missionId: string): Mission {
    const mission = this.missionEngine.getMission(missionId);
    if (!mission) {
      throw new Error(`Unknown mission: ${missionId}`);
    }
    this.missionEngine.loadMission(mission);
    while (!this.missionEngine.getState().completed) {
      this.missionEngine.executeNextStep();
      if (this.missionEngine.getState().currentStep >= mission.steps.length) {
        break;
      }
    }
    return mission;
  }

  getMissionEngine(): MissionEngine {
    return this.missionEngine;
  }
}
