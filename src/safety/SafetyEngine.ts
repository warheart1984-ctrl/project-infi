import { type SafetyRule, type SafetyRuleContext } from './SafetyRule.js'

export class SafetyEngine {
  constructor(private rules: SafetyRule[]) {}

  check(ctx: SafetyRuleContext) {
    const violations: string[] = []

    for (const rule of this.rules) {
      const result = rule.check(ctx)
      if (!result.ok) {
        violations.push(...result.violations)
      }
    }

    return {
      ok: violations.length === 0,
      violations,
    }
  }
}
