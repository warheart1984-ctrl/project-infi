import type { AAESAction, AAESContext, DanielModule } from "../types.js";
import { notImplemented } from "../error.js";

export class DanielModuleStub implements DanielModule {
  readonly module_id = "daniel.cinematic.v1";

  plan(_context: AAESContext) {
    return notImplemented<Record<string, unknown>>("DanielModule.plan");
  }

  execute(_action: AAESAction, _context: AAESContext) {
    return notImplemented<Record<string, unknown>>("DanielModule.execute");
  }
}
