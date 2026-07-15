import type { JsonValue } from '../common/models.js';
export interface TwinIdentity { twinId:string; displayName:string; principal:string; roles:string[]; sovereigntyScopes:string[]; modelProvenance:string; runtime:string; goalContext:string }
export interface TwinPersonalityProfile { twinId:string; traits:{name:string;weight:number}[]; style:{tone:'formal'|'casual'|'technical';riskTolerance:'low'|'medium'|'high';explorationBias:'conservative'|'balanced'|'aggressive'}; updatedAt:string }
export interface TwinRoleContract { roleName:string; allowedIntentTypes:string[]; allowedGraphs:string[]; maxRisk:'low'|'medium'|'high' }
export interface SovereigntyScope { scopeName:string; graphs:string[]; capabilities:string[] }
export interface MissionAssignment { missionId:string; twinId:string; role:string }
export interface MissionOrchestrationFlow { missionId:string; assignments:MissionAssignment[]; consensusRule:ConsensusRule; roleWeights?:Record<string,number> }
export type TwinMessageType='PROPOSE_INTENT'|'COUNTER_PROPOSAL'|'AGREE'|'REJECT';
export interface TwinMessage { id:string; fromTwinId:string; toTwinId:string; type:TwinMessageType; intentId?:string; payload:JsonValue; timestamp:string }
export type ConsensusRule='UNANIMOUS'|'MAJORITY'|'WEIGHTED_ROLES';
export interface TwinVote { proposalId:string; twinId:string; decision:'ACCEPT'|'REJECT'|'AMEND'; payload?:JsonValue; timestamp:string }
export interface ConsensusConfig { proposalId:string; participants:string[]; rule:ConsensusRule; weights?:Record<string,number> }
