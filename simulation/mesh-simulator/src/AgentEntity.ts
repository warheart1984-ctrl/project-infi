export interface AgentPosition {
  x: number;
  y: number;
}

export interface AgentCapability {
  id: string;
  name: string;
}

export interface AgentEntity {
  id: string;
  position: AgentPosition;
  capabilities: AgentCapability[];
  sensors: string[];
  behavior: string;
}
