import crypto from 'crypto'
import { type Envelope } from './Envelope.js'
import { type EnvelopeValidationResult, type EnvelopeValidatorDeps } from './EnvelopeValidator.types.js'

export class EnvelopeValidator {
  constructor(private deps: EnvelopeValidatorDeps) {}

  validate(envelope: Envelope, contract: any): EnvelopeValidationResult {
    const violations: string[] = []

    const recomputedHash = crypto
      .createHash('sha256')
      .update(JSON.stringify(envelope.proposal))
      .digest('hex')

    if (recomputedHash !== envelope.proposalHash) {
      violations.push('Proposal hash mismatch')
    }

    const ucrDecision = this.deps.ucr.evaluate(envelope.proposal, contract)
    if (ucrDecision.ok !== envelope.ucrDecision.ok) {
      violations.push('UCR decision drift')
    }

    const alaPlan = this.deps.ala.plan(envelope.proposal)
    const applied = this.deps.ala.apply(alaPlan)

    if (JSON.stringify(applied.applied) !== JSON.stringify(envelope.applied.applied)) {
      violations.push('ALA applied patch set drift')
    }

    const safetyDecision = this.deps.safety.check(applied, envelope.proposal, contract)
    if (safetyDecision.ok !== envelope.safetyDecision.ok) {
      violations.push('Safety decision drift')
    }

    const ts = Date.parse(envelope.timestamp)
    if (isNaN(ts)) {
      violations.push('Invalid timestamp')
    } else {
      const now = Date.now()
      if (ts > now + 5000) {
        violations.push('Timestamp is in the future')
      }
    }

    const supportedVersions = ['1']
    if (!supportedVersions.includes(envelope.proposal.schemaVersion)) {
      violations.push('Unsupported schema version')
    }

    return {
      ok: violations.length === 0,
      violations,
    }
  }
}
