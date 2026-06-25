import { AAESPlan } from "./types.js"

export interface AAESDecision {
  decisionId: string
  rationale: string
  selectedPlan: AAESPlan
  rejectedPlans: AAESPlan[]
}
