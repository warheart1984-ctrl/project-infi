import type { JsonValue } from '../common/models.js';
export interface SimulationCluster { clusterId:string; twins:string[]; rootRealityId:string; assumptions:JsonValue; governanceProfile:string }
export interface SimulationRun { simulationId:string; clusterId:string; intentId:string; status:'pending'|'running'|'completed' }
