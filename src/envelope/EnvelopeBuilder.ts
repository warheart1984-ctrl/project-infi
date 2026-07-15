import crypto from 'crypto'
import type { Envelope } from './Envelope.js'

export class EnvelopeBuilder {
  build(proposal: any, ucr: any, ala: any, safety: any, applied: any): Envelope {
    const proposalHash = crypto
      .createHash('sha256')
      .update(JSON.stringify(proposal))
      .digest('hex')

    return {
      proposalHash,
      proposal,
      ucrDecision: ucr,
      alaPlan: ala,
      safetyDecision: safety,
      applied,
      timestamp: new Date().toISOString(),
    }
  }
}
