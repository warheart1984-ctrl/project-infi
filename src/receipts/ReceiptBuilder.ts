import crypto from 'crypto'
import { type Receipt } from './Receipt.types.js'
import { ReceiptSigner } from './ReceiptSigner.js'

export class ReceiptBuilder {
  constructor(private signer: ReceiptSigner) {}

  build(envelope: any): Receipt {
    const signature = this.signer.sign(envelope.proposalHash)

    return {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      envelopeHash: envelope.proposalHash,
      signature,
      publicKey: this.signer.getPublicKey(),
    }
  }
}
