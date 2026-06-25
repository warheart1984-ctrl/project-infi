export interface Scope {
  name: string
  resources?: Record<string, any>
  ttlMs?: number
}

export interface Constraint {
  key: string
  value: any
}

export interface PolicySet {
  name: string
  rules: any[]
}

export type Stage =
  | "perception"
  | "deliberation"
  | "planning"
  | "action"
  | "check"

export interface InvariantResult {
  status: "allow" | "warn" | "block" | "review"
  messages?: string[]
}

export interface PolicyResult {
  status: "allow" | "deny" | "warn"
  messages?: string[]
}

export interface AAESPlan {
  id: string
  description: string
  steps: any[]
}

export interface ActionResult {
  actionId: string
  status: "success" | "failed"
  details?: any
}
