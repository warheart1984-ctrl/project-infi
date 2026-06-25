import { create } from "zustand";
import type { AgentSnapshotCell } from "./clusterStore";

export interface DriftAgentColumn {
  id: string;
  snapshots: AgentSnapshotCell[];
}

export interface DivergenceEvent {
  id: string;
  type: string;
  snapshotId?: string;
  agents: string[];
}

interface DriftStoreState {
  agents: DriftAgentColumn[];
  divergences: DivergenceEvent[];
  actions: {
    setAgents(agents: DriftAgentColumn[]): void;
    setDivergences(divergences: DivergenceEvent[]): void;
    appendDivergence(event: Omit<DivergenceEvent, "id"> & { id?: string }): void;
    syncFromCluster(agents: Record<string, { id: string; snapshots: AgentSnapshotCell[] }>): void;
  };
}

export const useDriftStore = create<DriftStoreState>((set) => ({
  agents: [],
  divergences: [],
  actions: {
    setAgents: (agents) => set({ agents }),
    setDivergences: (divergences) => set({ divergences }),
    appendDivergence: (event) =>
      set((state) => ({
        divergences: [
          { ...event, id: event.id ?? crypto.randomUUID() },
          ...state.divergences,
        ],
      })),
    syncFromCluster: (agents) =>
      set({
        agents: Object.values(agents).map((a) => ({
          id: a.id,
          snapshots: a.snapshots,
        })),
      }),
  },
}));
