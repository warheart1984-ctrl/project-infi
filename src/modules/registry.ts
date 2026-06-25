/**
 * Mythic: Module constellation
 * Engineering: ModuleRegistry
 */

import type { AAESAction, ActionResult } from "../types.js";
import type { ExecutionModule } from "./daniel/module.js";

export class ModuleRegistry {
  private readonly modules = new Map<string, ExecutionModule>();

  register(module: ExecutionModule): void {
    this.modules.set(module.moduleId, module);
  }

  list(): ExecutionModule[] {
    return [...this.modules.values()];
  }

  findHandler(action: AAESAction): ExecutionModule | undefined {
    return this.list().find((m) => m.canHandle(action));
  }

  async execute(action: AAESAction): Promise<ActionResult> {
    const module = this.findHandler(action);
    if (!module) {
      return {
        actionId: action.actionId,
        target: `${action.target}.${action.operation}`,
        status: "skipped",
        error: `no registered module for ${action.target}.${action.operation}`,
      };
    }
    return module.execute(action);
  }
}
