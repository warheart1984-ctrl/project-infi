import { type SafetyRule } from './SafetyRule.js'
import { EmptyContentRule } from './rules/EmptyContentRule.js'
import { UnauthorizedFileRule } from './rules/UnauthorizedFileRule.js'
import { ForbiddenDeleteRule } from './rules/ForbiddenDeleteRule.js'

export const DefaultSafetyRules: SafetyRule[] = [
  new EmptyContentRule(),
  new UnauthorizedFileRule(),
  new ForbiddenDeleteRule(),
]
