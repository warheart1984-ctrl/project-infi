export interface IntentSpecAST { name:string; preconditions:string[]; capabilities:string[]; steps:{name:string;capability:string}[]; governanceProfile:string }
export interface SubstrateStep { stepId:string; name:string; capability:string; substrateId:string }
export interface SubstratePlan { planId:string; intentId:string; actorId:string; contextId:string; steps:SubstrateStep[]; governance:{id:string;riskCeiling:'low'|'medium'|'high';requiredEvidence:string[]}; provenance:{islProgramId:string;islProgramVersion:string;registryRevision:string} }
export interface RegistryClient { findByCapability(capability:string):Promise<{substrateId:string;registryRevision:string}> }
export interface USSClient { hasEvidence(requirement:string):Promise<boolean> }
