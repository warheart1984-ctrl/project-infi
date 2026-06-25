import { Stage } from "./types.js"

export interface AAESStep {
  stepId: string
  stage: Stage
  input: any
  output: any
  metadata?: Record<string, any>
}
