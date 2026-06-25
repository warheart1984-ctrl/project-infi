import { AAESAction } from "../core/action.js"
import { AAESContext } from "../core/context.js"
import { ActionResult } from "../core/types.js"

export interface ExecutionModule {
  name: string
  canHandle(action: AAESAction): boolean
  execute(action: AAESAction, ctx: AAESContext): Promise<ActionResult>
}
