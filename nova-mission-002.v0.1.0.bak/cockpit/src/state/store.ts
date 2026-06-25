import { create } from "zustand";
import type {
  CenterMode,
  AgentLogEntry,
  ContinuityNode,
  SelectedDiff,
  UiSignals,
  Plan,
  GovernanceReceipt,
  InvariantViolation,
  KernelStatus,
  Invariant,
} from "../types";

interface CockpitState {
  ui: { centerMode: CenterMode; selectedAgents: string[] };
  uiSignals: UiSignals;
  agent: {
    currentGoal: string | null;
    currentPlan: Plan | null;
    log: AgentLogEntry[];
  };
  governance: {
    invariants: Invariant[];
    receipts: GovernanceReceipt[];
    violations: InvariantViolation[];
    selectedReceiptId: string | null;
  };
  continuity: {
    timeline: ContinuityNode[];
    selectedSnapshotId: string | null;
  };
  workspace: {
    selectedDiff: SelectedDiff | null;
  };
  kernel: { status: KernelStatus };
  actions: {
    setCenterMode(mode: CenterMode): void;
    setGoal(goal: string): void;
    setPlan(plan: Plan): void;
    setInvariants(invariants: Invariant[]): void;
    appendLog(entry: Omit<AgentLogEntry, "id"> & { id?: string }): void;
    addReceipt(r: GovernanceReceipt): void;
    addViolation(v: InvariantViolation): void;
    updateKernelStatus(status: KernelStatus): void;
    updateContinuity(snapshot: { id: string; timestamp: number; stateHash: string }): void;
    selectSnapshot(id: string): void;
    selectReceipt(id: string): void;
    selectDiff(diff: SelectedDiff): void;
    signalViolation(id: string): void;
    signalReceipt(id: string): void;
    signalPlan(id: string): void;
    clearSignal(key: keyof UiSignals): void;
    setSelectedAgents(agentIds: string[]): void;
    addViolationFromGateway(v: {
      agentId: string;
      invariantId: string;
      message: string;
      actionId: string;
      severity: "error" | "warn";
    }): void;
    addReceiptFromGateway(r: {
      agentId: string;
      receiptId: string;
      actionId: string;
      invariantsChecked: string[];
      pitBand: number;
      continuityHash: string;
    }): void;
    addSnapshotFromGateway(s: {
      agentId: string;
      snapshotId: string;
      hash: string;
      partial: boolean;
    }): void;
    setPlanForAgent(
      agentId: string,
      payload: { planId: string; steps: { id: string; description: string }[] }
    ): void;
    addActionLog(entry: {
      agentId: string;
      actionId: string;
      stepId: string;
      description: string;
    }): void;
  };
}

const defaultKernel: KernelStatus = {
  invariantEngine: "ok",
  ledger: "ok",
  continuity: "ok",
  violationsLastMinute: 0,
  receiptCount: 0,
  snapshotCount: 0,
  activeInvariants: 0,
};

export const useCockpitState = create<CockpitState>((set) => ({
  ui: { centerMode: "plan", selectedAgents: ["agent-alpha", "agent-beta"] },
  uiSignals: {},
  agent: { currentGoal: null, currentPlan: null, log: [] },
  governance: { invariants: [], receipts: [], violations: [], selectedReceiptId: null },
  continuity: { timeline: [], selectedSnapshotId: null },
  workspace: { selectedDiff: null },
  kernel: { status: defaultKernel },

  actions: {
    setCenterMode: (mode) => set((s) => ({ ui: { ...s.ui, centerMode: mode } })),
    setGoal: (goal) => set((s) => ({ agent: { ...s.agent, currentGoal: goal } })),
    setPlan: (plan) => set((s) => ({ agent: { ...s.agent, currentPlan: plan } })),
    setInvariants: (invariants) =>
      set((s) => ({ governance: { ...s.governance, invariants } })),
    appendLog: (entry) =>
      set((s) => ({
        agent: {
          ...s.agent,
          log: [
            ...s.agent.log,
            { ...entry, id: entry.id ?? crypto.randomUUID() },
          ],
        },
      })),
    addReceipt: (r) =>
      set((s) => ({
        governance: {
          ...s.governance,
          receipts: [r, ...s.governance.receipts],
        },
        continuity: {
          ...s.continuity,
          timeline: [
            ...s.continuity.timeline,
            {
              id: r.id,
              timestamp: r.timestamp,
              stateHash: r.continuityHash,
              type: "receipt" as const,
              label: r.action.type,
            },
          ],
        },
      })),
    addViolation: (v) =>
      set((s) => ({
        governance: {
          ...s.governance,
          violations: [v, ...s.governance.violations],
        },
        continuity: {
          ...s.continuity,
          timeline: [
            ...s.continuity.timeline,
            {
              id: v.id,
              timestamp: Date.now(),
              stateHash: v.invariantId,
              type: "violation" as const,
              label: v.invariantId,
            },
          ],
        },
      })),
    updateKernelStatus: (status) => set({ kernel: { status } }),
    updateContinuity: (snapshot) =>
      set((s) => ({
        continuity: {
          ...s.continuity,
          timeline: [
            ...s.continuity.timeline,
            {
              id: snapshot.id,
              timestamp: snapshot.timestamp,
              stateHash: snapshot.stateHash,
              type: "snapshot" as const,
            },
          ],
        },
      })),
    selectSnapshot: (id) =>
      set((s) => ({ continuity: { ...s.continuity, selectedSnapshotId: id } })),
    selectReceipt: (id) =>
      set((s) => ({
        governance: { ...s.governance, selectedReceiptId: id },
        ui: { ...s.ui, centerMode: "receipts" },
      })),
    selectDiff: (diff) =>
      set((s) => ({
        workspace: { ...s.workspace, selectedDiff: diff },
        ui: { ...s.ui, centerMode: "diff" },
      })),
    signalViolation: (id) =>
      set((s) => ({ uiSignals: { ...s.uiSignals, lastViolationId: id } })),
    signalReceipt: (id) =>
      set((s) => ({ uiSignals: { ...s.uiSignals, lastReceiptId: id } })),
    signalPlan: (id) =>
      set((s) => ({ uiSignals: { ...s.uiSignals, lastPlanId: id } })),
    clearSignal: (key) =>
      set((s) => {
        const next = { ...s.uiSignals };
        delete next[key];
        return { uiSignals: next };
      }),
    setSelectedAgents: (selectedAgents) =>
      set((s) => ({ ui: { ...s.ui, selectedAgents } })),
    addViolationFromGateway: (v) =>
      set((s) => ({
        governance: {
          ...s.governance,
          violations: [
            {
              id: crypto.randomUUID(),
              invariantId: v.invariantId,
              description: v.message,
              message: v.message,
              severity: v.severity,
              action: { type: "generate", payload: { actionId: v.actionId, agentId: v.agentId } },
            },
            ...s.governance.violations,
          ],
        },
      })),
    addReceiptFromGateway: (r) =>
      set((s) => ({
        governance: {
          ...s.governance,
          receipts: [
            {
              id: r.receiptId,
              timestamp: Date.now(),
              action: { type: "generate", payload: { actionId: r.actionId, agentId: r.agentId } },
              invariantsChecked: r.invariantsChecked,
              continuityHash: r.continuityHash,
              ledgerHash: "",
            },
            ...s.governance.receipts,
          ],
        },
      })),
    addSnapshotFromGateway: (snap) =>
      set((s) => ({
        continuity: {
          ...s.continuity,
          timeline: [
            ...s.continuity.timeline,
            {
              id: snap.snapshotId,
              timestamp: Date.now(),
              stateHash: snap.hash,
              type: "snapshot" as const,
              label: snap.agentId,
            },
          ],
        },
      })),
    setPlanForAgent: (agentId, payload) =>
      set((s) => ({
        agent: {
          ...s.agent,
          currentPlan: {
            id: payload.planId,
            justification: `Plan for ${agentId}`,
            receipts: [],
            steps: payload.steps.map((step) => ({
              id: step.id,
              description: step.description,
              action: { type: "plan" as const, payload: { stepId: step.id } },
            })),
          },
        },
        uiSignals: { ...s.uiSignals, lastPlanId: payload.planId },
      })),
    addActionLog: (entry) =>
      set((s) => ({
        agent: {
          ...s.agent,
          log: [
            ...s.agent.log,
            {
              id: crypto.randomUUID(),
              type: "action",
              timestamp: Date.now(),
              message: `[${entry.agentId}] ${entry.description}`,
            },
          ],
        },
      })),
  },
}));
