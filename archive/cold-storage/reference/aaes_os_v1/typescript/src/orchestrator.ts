import type { AAESContext, AAESRequest, CognitiveOrchestrator } from "./types.js";
import { notImplemented } from "./error.js";

export class CognitiveOrchestratorStub implements CognitiveOrchestrator {
  execute(_request: AAESRequest) {
    return notImplemented<AAESContext>("CognitiveOrchestrator.execute");
  }
}
