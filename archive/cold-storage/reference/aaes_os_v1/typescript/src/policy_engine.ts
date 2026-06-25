import type { AAESContext, AAESDecision, AAESRequest, PolicyEngine } from "./types.js";
import { notImplemented } from "./error.js";

export class PolicyEngineStub implements PolicyEngine {
  evaluate(_request: AAESRequest, _context: AAESContext) {
    return notImplemented<AAESDecision>("PolicyEngine.evaluate");
  }
}
