import { type SafetyRule, type SafetyRuleContext } from '../SafetyRule.js'

export class UnauthorizedFileRule implements SafetyRule {
  id = 'unauthorized-file'
  description = 'Operations must target authorized files only'

  check(ctx: SafetyRuleContext) {
    const violations: string[] = []

    for (const op of ctx.patchSet.applied) {
      if (!ctx.contract.authorizedFiles.includes(op.file)) {
        violations.push(`Unauthorized file access: ${op.file}`)
      }
    }

    return { ok: violations.length === 0, violations }
  }
}
