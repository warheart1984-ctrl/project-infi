import { agentRegistry } from "./agent-registry";
import { clusterView } from "../../crk2";

export const clusterManager = {
  getClusterState() {
    return {
      agents: agentRegistry.list(),
      constitutional: clusterView(),
    };
  },

  ensureDefaultAgents(ids: string[] = ["agent-alpha", "agent-beta"]): void {
    for (const id of ids) {
      if (!agentRegistry.get(id)) agentRegistry.register(id);
    }
  },
};
