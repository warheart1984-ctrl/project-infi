import { create } from "zustand";

export interface AgentSnapshotCell {
  id: string;
  state: "ok" | "drift" | "error";
  hash?: string;
}

export interface AgentReceipt {
  receiptId: string;
  actionId: string;
  invariantsChecked: string[];
  pitBand: number;
  continuityHash: string;
}

export interface ClusterAgent {
  id: string;
  status: "online" | "offline" | "drift" | "error";
  kernelStatus?: "ok" | "warn" | "error" | string;
  pitBand?: number;
  snapshots: AgentSnapshotCell[];
  receipts: AgentReceipt[];
}

export interface ClusterEvent {
  id: string;
  type: string;
  agentId?: string;
  timestamp: number;
  payload?: Record<string, unknown>;
}

export interface DriftEventPayload {
  driftId: string;
  agents: string[];
  snapshotId: string;
  driftType: string;
}

interface ClusterStoreState {
  agents: Record<string, ClusterAgent>;
  selectedAgent: string | null;
  clusterEvents: ClusterEvent[];
  replayWindow: { from?: string; to?: string } | null;
  actions: {
    updateAgentStatus(id: string, patch: Partial<ClusterAgent>): void;
    updateAgentKernelStatus(
      id: string,
      patch: { kernelStatus: "ok" | "warn" | "error"; pitBand: number }
    ): void;
    addAgentReceipt(agentId: string, receipt: AgentReceipt): void;
    addAgentSnapshot(
      agentId: string,
      snapshot: { snapshotId: string; hash: string; partial: boolean }
    ): void;
    setClusterHeartbeat(
      agents: Record<string, { kernelStatus: "ok" | "warn" | "error"; pitBand: number }>
    ): void;
    addDriftEvent(payload: DriftEventPayload): void;
    addClusterEvent(event: Omit<ClusterEvent, "id"> & { id?: string }): void;
    selectAgent(id: string | null): void;
    setReplayWindow(window: { from?: string; to?: string } | null): void;
    seedDemoAgents(): void;
  };
}

function emptyAgent(id: string, patch: Partial<ClusterAgent> = {}): ClusterAgent {
  return {
    id,
    status: "online",
    snapshots: [],
    receipts: [],
    ...patch,
  };
}

export const useClusterStore = create<ClusterStoreState>((set) => ({
  agents: {},
  selectedAgent: null,
  clusterEvents: [],
  replayWindow: null,
  actions: {
    updateAgentStatus: (id, patch) =>
      set((state) => ({
        agents: {
          ...state.agents,
          [id]: { ...emptyAgent(id, state.agents[id]), ...patch },
        },
      })),
    updateAgentKernelStatus: (id, patch) =>
      set((state) => ({
        agents: {
          ...state.agents,
          [id]: {
            ...emptyAgent(id, state.agents[id]),
            kernelStatus: patch.kernelStatus,
            pitBand: patch.pitBand,
            status:
              patch.kernelStatus === "error"
                ? "error"
                : patch.kernelStatus === "warn"
                  ? "drift"
                  : "online",
          },
        },
      })),
    addAgentReceipt: (agentId, receipt) =>
      set((state) => {
        const agent = emptyAgent(agentId, state.agents[agentId]);
        return {
          agents: {
            ...state.agents,
            [agentId]: { ...agent, receipts: [receipt, ...agent.receipts] },
          },
        };
      }),
    addAgentSnapshot: (agentId, snapshot) =>
      set((state) => {
        const agent = emptyAgent(agentId, state.agents[agentId]);
        return {
          agents: {
            ...state.agents,
            [agentId]: {
              ...agent,
              snapshots: [
                ...agent.snapshots,
                {
                  id: snapshot.snapshotId,
                  hash: snapshot.hash,
                  state: "ok" as const,
                },
              ],
            },
          },
        };
      }),
    setClusterHeartbeat: (agents) =>
      set((state) => {
        const next = { ...state.agents };
        for (const [id, hb] of Object.entries(agents)) {
          next[id] = {
            ...emptyAgent(id, next[id]),
            kernelStatus: hb.kernelStatus,
            pitBand: hb.pitBand,
            status: hb.kernelStatus === "error" ? "error" : "online",
          };
        }
        return { agents: next };
      }),
    addDriftEvent: (payload) =>
      set((state) => ({
        clusterEvents: [
          {
            id: payload.driftId,
            type: "cluster.driftDetected",
            timestamp: Date.now(),
            payload: payload as unknown as Record<string, unknown>,
          },
          ...state.clusterEvents,
        ],
      })),
    addClusterEvent: (event) =>
      set((state) => ({
        clusterEvents: [
          { ...event, id: event.id ?? crypto.randomUUID() },
          ...state.clusterEvents,
        ],
      })),
    selectAgent: (selectedAgent) => set({ selectedAgent }),
    setReplayWindow: (replayWindow) => set({ replayWindow }),
    seedDemoAgents: () =>
      set({
        agents: {
          "agent-alpha": emptyAgent("agent-alpha", {
            kernelStatus: "ok",
            pitBand: 2,
            snapshots: [
              { id: "s1", state: "ok" },
              { id: "s2", state: "ok" },
            ],
          }),
          "agent-beta": emptyAgent("agent-beta", {
            kernelStatus: "warn",
            pitBand: 3,
            snapshots: [
              { id: "s1", state: "ok" },
              { id: "s2", state: "drift" },
            ],
          }),
        },
      }),
  },
}));
