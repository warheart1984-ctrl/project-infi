import { randomUUID } from 'node:crypto';

import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

import type { Mission, MissionStep } from './Mission.js';
import type { MissionState } from './MissionState.js';

export interface MissionEngineOptions {
  bus?: TriCoreBus;
  missions?: Mission[];
}

export class MissionEngine {
  private readonly missions = new Map<string, Mission>();
  private readonly bus: TriCoreBus;
  private state: MissionState = {
    missionId: '',
    currentStep: 0,
    completed: false,
    history: [],
  };

  constructor(options: MissionEngineOptions = {}) {
    this.bus = options.bus ?? new TriCoreBus();
    for (const mission of options.missions ?? []) {
      this.missions.set(mission.id, mission);
    }
  }

  loadMission(mission: Mission): MissionState {
    this.missions.set(mission.id, mission);
    this.state = {
      missionId: mission.id,
      currentStep: 0,
      completed: mission.steps.length === 0,
      history: [],
    };
    return this.getState();
  }

  getMission(missionId: string): Mission | undefined {
    return this.missions.get(missionId);
  }

  getState(): MissionState {
    return structuredClone(this.state);
  }

  executeNextStep(): TriCoreMessage | null {
    const mission = this.missions.get(this.state.missionId);
    if (!mission || this.state.completed) {
      return null;
    }

    const step = mission.steps[this.state.currentStep];
    if (!step) {
      this.state.completed = true;
      return null;
    }

    const message = this.bus.send({
      id: randomUUID(),
      from: 'agent',
      to: 'runtime',
      type: 'AGENT_ACT',
      payload: {
        missionId: mission.id,
        stepId: step.id,
        description: step.description,
        action: step.action,
      },
      timestamp: Date.now(),
      correlationId: mission.id,
    });

    this.recordStepResult({
      step,
      approved: true,
      message,
    });

    return message;
  }

  recordStepResult(result: { step: MissionStep; approved: boolean; message?: TriCoreMessage | null }): MissionState {
    this.state.history.push({
      stepId: result.step.id,
      approved: result.approved,
      messageId: result.message?.id,
    });
    if (result.approved) {
      this.state.currentStep += 1;
    }

    const mission = this.missions.get(this.state.missionId);
    if (mission && this.state.currentStep >= mission.steps.length) {
      this.state.completed = true;
    }
    return this.getState();
  }

  receiveGovernanceDecision(message: TriCoreMessage): MissionState {
    if (message.to !== 'agent' && message.to !== 'runtime') {
      return this.getState();
    }
    if (message.type === 'GOVERNANCE_DENY') {
      this.state.history.push({ decision: 'denied', messageId: message.id });
      this.state.completed = true;
      return this.getState();
    }
    if (message.type === 'GOVERNANCE_APPROVE') {
      this.state.history.push({ decision: 'approved', messageId: message.id });
      return this.getState();
    }
    return this.getState();
  }
}
