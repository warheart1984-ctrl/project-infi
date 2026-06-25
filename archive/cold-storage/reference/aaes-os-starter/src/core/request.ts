import { Scope, Constraint } from "./types.js"

export interface AAESRequest {
  id: string
  actorId: string
  timestamp: string
  channel: string
  payload: any
  scope: Scope
  constraints?: Constraint[]
}
