import { type SafetyRule, type SafetyRuleContext } from '../SafetyRule.js'

export class ForbiddenDeleteRule implements SafetyRule {
  id = 'forbidden-delete'
  description = 'Delete operations must be explicitly allowed'

  check(ctx: SafetyRuleContext) {
    const violations: string[] = []

    for (const op of ctx.patchSet.applied) {
      if (op.type === 'delete' && !ctx.contract.allowedOps.includes('delete')) {
        violations.push(`Delete not allowed: ${op.path ?? op.file ?? 'unknown file'}`)
      }
    }

    return { ok: violations.length === 0, violations }
  }
}
