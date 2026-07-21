import { type SafetyRule, type SafetyRuleContext } from '../SafetyRule.js'

export class EmptyContentRule implements SafetyRule {
  id = 'empty-content'
  description = 'Insert/update operations must have non-empty content'

  check(ctx: SafetyRuleContext) {
    const violations: string[] = []

    for (const op of ctx.patchSet.applied) {
      if ((op.type === 'insert' || op.type === 'update') && !op.content) {
        violations.push(`Empty content for ${op.path ?? op.file ?? 'unknown file'} on ${op.type}`)
      }
    }

    return { ok: violations.length === 0, violations }
  }
}
