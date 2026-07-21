export interface CapabilityModel {
  agentId: string;
  allowedActions: string[];
  maxPayloadSize?: number;
}

export function allowsCapability(model: CapabilityModel, action: string): boolean {
  return model.allowedActions.includes(action);
}
