import type { JudgmentCycle } from "../judgment/types.js";
import { deriveRecalibrationViews, deriveThresholdViews } from "./views.js";
import type { ContinuityLedger, RecalibrationView, ThresholdView } from "./types.js";

export class InMemoryContinuityLedger implements ContinuityLedger {
  private readonly cycles = new Map<string, JudgmentCycle>();

  constructor(initial: JudgmentCycle[] = []) {
    for (const cycle of initial) {
      this.cycles.set(cycle.id, cycle);
    }
  }

  async appendCycle(cycle: JudgmentCycle): Promise<void> {
    this.cycles.set(cycle.id, cycle);
  }

  async getCycle(id: string): Promise<JudgmentCycle | null> {
    return this.cycles.get(id) ?? null;
  }

  async getCyclesByObserver(observerId: string): Promise<JudgmentCycle[]> {
    return [...this.cycles.values()].filter((c) => c.observerId === observerId);
  }

  async getAllCycles(): Promise<JudgmentCycle[]> {
    return [...this.cycles.values()];
  }

  async getThresholdViews(): Promise<ThresholdView[]> {
    return deriveThresholdViews(await this.getAllCycles());
  }

  async getRecalibrationViews(thresholdId: string): Promise<RecalibrationView[]> {
    return deriveRecalibrationViews(await this.getAllCycles(), thresholdId);
  }

  toArray(): JudgmentCycle[] {
    return [...this.cycles.values()];
  }

  static fromArray(cycles: JudgmentCycle[]): InMemoryContinuityLedger {
    return new InMemoryContinuityLedger(cycles);
  }
}

export function appendLedgerCycle(
  cycles: JudgmentCycle[],
  cycle: JudgmentCycle,
): JudgmentCycle[] {
  const idx = cycles.findIndex((c) => c.id === cycle.id);
  if (idx >= 0) {
    const next = [...cycles];
    next[idx] = cycle;
    return next;
  }
  return [...cycles, cycle];
}
