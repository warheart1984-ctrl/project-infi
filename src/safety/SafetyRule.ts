export interface SafetyRuleContext {
  patchSet: any
  proposal: any
  contract: any
}

export interface SafetyRuleResult {
  ok: boolean
  violations: string[]
}

export interface SafetyRule {
  id: string
  description: string
  check(ctx: SafetyRuleContext): SafetyRuleResult
}
