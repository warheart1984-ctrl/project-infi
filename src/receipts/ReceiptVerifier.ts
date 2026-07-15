import { type Receipt } from './Receipt.types.js'
import { ReceiptSigner } from './ReceiptSigner.js'

export class ReceiptVerifier {
  constructor(private signer: ReceiptSigner) {}

  verify(receipt: Receipt) {
    return this.signer.verify(receipt.envelopeHash, receipt.signature)
  }
}
