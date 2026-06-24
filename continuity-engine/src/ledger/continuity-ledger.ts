import {
  annotateCorrigibility,
  assessCorrigibility,
  type CorrigibilityStatus,
  type JudgmentCycle,
} from "../judgment/cycle";
import { rollupLineageCorrigibility } from "../judgment/cycle-ledger";
import type { RealityVetoReceipt } from "../rpa1/reality-veto";
import type {
  ContinuityHealth,
  ContinuityHealthReport,
  ConstitutionalFailureMode,
  RecalibrationView,
  ThresholdView,
} from "./types";

/** Continuity Ledger v2 — cycles, Reality Veto receipts, and lineage views. */
export interface ContinuityLedger {
  appendCycle(cycle: JudgmentCycle): Promise<void>;
  getCycle(id: string): Promise<JudgmentCycle | null>;
  getCyclesByObserver(observerId: string): Promise<JudgmentCycle[]>;

  appendRealityVeto(veto: RealityVetoReceipt): Promise<void>;
  getRealityVetoes(): Promise<RealityVetoReceipt[]>;

  getThresholdViews(): Promise<ThresholdView[]>;
  getRecalibrationViews(thresholdId: string): Promise<RecalibrationView[]>;

  getLineageCorrigibility(observerId: string): Promise<CorrigibilityStatus>;
  getFailedLineages(): Promise<string[]>;
  getContinuityHealth(): Promise<ContinuityHealthReport>;
}

export class InMemoryContinuityLedger implements ContinuityLedger {
  private cycles = new Map<string, JudgmentCycle>();
  private cyclesByObserver = new Map<string, string[]>();
  private vetoes: RealityVetoReceipt[] = [];

  async appendCycle(cycle: JudgmentCycle): Promise<void> {
    const annotated = annotateCorrigibility(cycle);
    this.cycles.set(annotated.id, annotated);
    const ids = this.cyclesByObserver.get(annotated.observerId) ?? [];
    if (!ids.includes(annotated.id)) {
      this.cyclesByObserver.set(annotated.observerId, [...ids, annotated.id]);
    }
  }

  async getCycle(id: string): Promise<JudgmentCycle | null> {
    return this.cycles.get(id) ?? null;
  }

  async getCyclesByObserver(observerId: string): Promise<JudgmentCycle[]> {
    const ids = this.cyclesByObserver.get(observerId) ?? [];
    return ids.map((id) => this.cycles.get(id)!).filter(Boolean);
  }

  async appendRealityVeto(veto: RealityVetoReceipt): Promise<void> {
    this.vetoes.push(veto);
  }

  async getRealityVetoes(): Promise<RealityVetoReceipt[]> {
    return [...this.vetoes];
  }

  async getThresholdViews(): Promise<ThresholdView[]> {
    const byThreshold = new Map<string, ThresholdView>();

    for (const cycle of this.cycles.values()) {
      for (const thresholdId of cycle.relatedThresholdIds ?? []) {
        const existing = byThreshold.get(thresholdId) ?? {
          thresholdId,
          cycleCount: 0,
          lastCorrigibility: "at-risk" as CorrigibilityStatus,
          relatedVetoCount: 0,
          observerIds: [],
        };
        existing.cycleCount += 1;
        existing.lastCorrigibility = cycle.corrigibilityStatus ?? assessCorrigibility(cycle).status;
        if (!existing.observerIds.includes(cycle.observerId)) {
          existing.observerIds.push(cycle.observerId);
        }
        byThreshold.set(thresholdId, existing);
      }
    }

    for (const veto of this.vetoes) {
      const exp = veto.violatedExpectation;
      if (typeof exp === "object" && exp !== null && "thresholdId" in exp) {
        const thresholdId = String((exp as { thresholdId: string }).thresholdId);
        const view = byThreshold.get(thresholdId) ?? {
          thresholdId,
          cycleCount: 0,
          lastCorrigibility: "at-risk" as CorrigibilityStatus,
          relatedVetoCount: 0,
          observerIds: [],
        };
        view.relatedVetoCount += 1;
        byThreshold.set(thresholdId, view);
      }
    }

    return [...byThreshold.values()];
  }

  async getRecalibrationViews(thresholdId: string): Promise<RecalibrationView[]> {
    const matching = [...this.cycles.values()].filter((c) =>
      c.relatedThresholdIds?.includes(thresholdId),
    );
    if (matching.length === 0) return [];

    const deltaIds = [
      ...new Set(matching.flatMap((c) => c.relatedDeltaIds ?? [])),
    ];
    return [
      {
        thresholdId,
        deltaIds,
        cycles: matching,
        corrigibility: rollupLineageCorrigibility(
          matching.map((c) => c.corrigibilityStatus ?? assessCorrigibility(c).status),
        ),
      },
    ];
  }

  async getLineageCorrigibility(observerId: string): Promise<CorrigibilityStatus> {
    const cycles = await this.getCyclesByObserver(observerId);
    if (cycles.length === 0) return "at-risk";
    return rollupLineageCorrigibility(
      cycles.map((c) => c.corrigibilityStatus ?? assessCorrigibility(c).status),
    );
  }

  async getFailedLineages(): Promise<string[]> {
    const failed: string[] = [];
    for (const observerId of this.cyclesByObserver.keys()) {
      if ((await this.getLineageCorrigibility(observerId)) === "failed") {
        failed.push(observerId);
      }
    }
    return failed;
  }

  async getContinuityHealth(): Promise<ContinuityHealthReport> {
    const observerIds = [...this.cyclesByObserver.keys()];
    const statuses = await Promise.all(
      observerIds.map((id) => this.getLineageCorrigibility(id)),
    );
    const soundLineageCount = statuses.filter((s) => s === "sound").length;
    const failedLineageCount = statuses.filter((s) => s === "failed").length;
    const lineageCorrigibility = rollupLineageCorrigibility(
      statuses.length ? statuses : ["at-risk"],
    );
    const vetoes = await this.getRealityVetoes();
    const suppressedVetoes = vetoes.filter((v) => v.suppressed);

    const failureModes: ConstitutionalFailureMode[] = [];
    const detachedObservation = [...this.cycles.values()].some((c) => c.observation == null);
    if (detachedObservation) failureModes.push("F-1");

    const repeatedContradiction =
      vetoes.length > 0 && failedLineageCount > 0 && soundLineageCount === 0;
    if (repeatedContradiction) failureModes.push("F-2");

    const allLineagesFailed =
      observerIds.length > 0 && failedLineageCount === observerIds.length;
    const realityDisempowered = suppressedVetoes.length > 0 || (allLineagesFailed && vetoes.length === 0);
    if (realityDisempowered) failureModes.push("F-3");

    let health: ContinuityHealth = "healthy";
    if (failureModes.includes("F-3")) {
      health = "collapsed";
    } else if (failureModes.length > 0 || lineageCorrigibility !== "sound") {
      health = "at-risk";
    }

    return {
      health,
      failureModes,
      lineageCorrigibility,
      soundLineageCount,
      failedLineageCount,
      pendingVetoCount: vetoes.length,
    };
  }
}
