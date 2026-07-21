export interface MissionState {
  missionId: string;
  currentStep: number;
  completed: boolean;
  history: unknown[];
}
