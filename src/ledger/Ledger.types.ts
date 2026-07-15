export interface LedgerRecord {
  id: string
  timestamp: string
  envelopeHash: string
  envelope: any
  receipt?: any
}

export interface LedgerWriteResult {
  ok: boolean
  id: string
}

export interface LedgerReadResult {
  ok: boolean
  records: LedgerRecord[]
}
