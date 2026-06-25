import { clusterManager } from "../control-tower/orchestrator/cluster-manager";
import { replayCluster } from "../control-tower/replay/cluster-replay";
import { simulateDrift } from "../control-tower/drift/drift-simulator";

export const controlTowerService = {
  getClusterState: () => clusterManager.getClusterState(),
  replayCluster,
  simulateDrift,
  ensureDefaultCluster: () => clusterManager.ensureDefaultAgents(),
};
