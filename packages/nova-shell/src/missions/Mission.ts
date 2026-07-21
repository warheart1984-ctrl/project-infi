export interface MissionStep {
  id: string;
  description: string;
  action: unknown;
}

export interface Mission {
  id: string;
  name: string;
  steps: MissionStep[];
}
