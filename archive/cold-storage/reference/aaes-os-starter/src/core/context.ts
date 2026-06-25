import { AAESRequest } from "./request.js"
import { PolicySet } from "./types.js"

export interface AAESContext {
  request: AAESRequest
  traceId: string
  session: Record<string, any>
  policies: PolicySet
}
