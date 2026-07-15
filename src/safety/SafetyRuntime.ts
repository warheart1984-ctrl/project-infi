import { DefaultSafetyRules } from './SafetyRules.js'
import { SafetyEngine } from './SafetyEngine.js'

export class SafetyRuntime {
  private engine = new SafetyEngine(DefaultSafetyRules)

  check(patchSet: any, proposal: any, contract: any) {
    return this.engine.check({ patchSet, proposal, contract })
  }
}
