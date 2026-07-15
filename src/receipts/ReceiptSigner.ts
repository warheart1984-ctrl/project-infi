import crypto from 'crypto'

export class ReceiptSigner {
  private privateKey: crypto.KeyObject
  private publicKey: crypto.KeyObject

  constructor() {
    const { privateKey, publicKey } = crypto.generateKeyPairSync('ed25519')
    this.privateKey = privateKey
    this.publicKey = publicKey
  }

  sign(envelopeHash: string) {
    const signature = crypto.sign(null, Buffer.from(envelopeHash, 'utf-8'), this.privateKey)
    return signature.toString('base64')
  }

  getPublicKey(): string {
    return this.publicKey.export({ type: 'spki', format: 'pem' }) as string
  }

  verify(envelopeHash: string, signature: string) {
    return crypto.verify(
      null,
      Buffer.from(envelopeHash, 'utf-8'),
      this.publicKey,
      Buffer.from(signature, 'base64')
    )
  }
}
