import { type Envelope } from '../envelope/Envelope.js'
import { EnvelopeValidator } from '../envelope/EnvelopeValidator.js'
import { type DriftReport } from './ReplayDriftDetector.types.js'

export class ReplayDriftDetector {
  constructor(private validator: EnvelopeValidator) {}

  detect(envelope: Envelope, contract: any): DriftReport {
    const result = this.validator.validate(envelope, contract)

    if (!result.ok) {
      return {
        ok: false,
        drift: true,
        reasons: result.violations,
      }
    }

    return {
      ok: true,
      drift: false,
      reasons: [],
    }
  }
}
