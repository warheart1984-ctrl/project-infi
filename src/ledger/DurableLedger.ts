import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { type LedgerRecord, type LedgerWriteResult, type LedgerReadResult } from './Ledger.types.js'

export class DurableLedger {
  private file: string

  constructor(directory: string) {
    this.file = path.join(directory, 'ledger.jsonl')

    if (!fs.existsSync(directory)) {
      fs.mkdirSync(directory, { recursive: true })
    }

    if (!fs.existsSync(this.file)) {
      fs.writeFileSync(this.file, '')
    }
  }

  write(envelope: any): LedgerWriteResult {
    const id = crypto.randomUUID()

    const record: LedgerRecord = {
      id,
      timestamp: new Date().toISOString(),
      envelopeHash: envelope.proposalHash,
      envelope,
    }

    fs.appendFileSync(this.file, JSON.stringify(record) + '\n')

    return { ok: true, id }
  }

  writeReceipt(receipt: any): LedgerWriteResult {
    const id = crypto.randomUUID()

    const record: LedgerRecord = {
      id,
      timestamp: new Date().toISOString(),
      envelopeHash: '',
      envelope: null,
      receipt,
    }

    fs.appendFileSync(this.file, JSON.stringify(record) + '\n')

    return { ok: true, id }
  }

  readAll(): LedgerReadResult {
    const content = fs.readFileSync(this.file, 'utf-8')
    const lines = content.split('\n').filter(Boolean)
    const records = lines.map((line) => JSON.parse(line))

    return { ok: true, records }
  }
}
