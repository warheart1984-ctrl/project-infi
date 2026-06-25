import { createHash, randomUUID } from "crypto";

export interface LineageRecord {
  root_id: string;
  entry_id: string;
  parent_id: string | null;
  operator_id: string;
  call_id: string;
  append_hash: string;
  timestamp: number;
}

let genesisRootId: string | null = null;
let lastEntryId: string | null = null;
const lineageLog: LineageRecord[] = [];

export function resetLineageForTests(): void {
  genesisRootId = null;
  lastEntryId = null;
  lineageLog.length = 0;
}

export function appendLineage(params: {
  operator_id: string;
  call_id: string;
  payload: string;
}): LineageRecord {
  const entry_id = randomUUID();
  if (!genesisRootId) {
    genesisRootId = entry_id;
  }
  const parent_id = lastEntryId;
  const append_hash = createHash("sha256")
    .update(JSON.stringify({ parent_id, payload: params.payload, call_id: params.call_id }))
    .digest("hex");

  const record: LineageRecord = {
    root_id: genesisRootId,
    entry_id,
    parent_id,
    operator_id: params.operator_id,
    call_id: params.call_id,
    append_hash,
    timestamp: Date.now(),
  };

  lineageLog.push(record);
  lastEntryId = entry_id;
  return record;
}

export function getLineageLog(): readonly LineageRecord[] {
  return lineageLog;
}
