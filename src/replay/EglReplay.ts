import { UcrEngine } from '../ucr/UcrContract.js'
import { AlaRuntime } from '../ala/AlaRuntime.js'
import { SafetyRuntime } from '../safety/SafetyRuntime.js'

export class EglReplay {
  replay(envelope: any, contract: any) {
    const ucr = new UcrEngine().evaluate(envelope.proposal, contract)
    const alaRuntime = new AlaRuntime()
    const ala = alaRuntime.plan(envelope.proposal)
    const applied = alaRuntime.apply(ala)
    const safety = new SafetyRuntime().check(applied, envelope.proposal, contract)

    const ok =
      ucr.ok &&
      safety.ok &&
      JSON.stringify(applied.applied) === JSON.stringify(envelope.applied.applied)

    return { ok, envelope }
  }
}
