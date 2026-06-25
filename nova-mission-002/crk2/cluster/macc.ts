import { createHash } from "crypto";
import { listReceipts } from "../ledger/ledger-v2";
import { listSnapshots } from "../continuity/substrate";

export interface ClusterState {
  kernelVersion: "CRK-2";
  invariantSetHash: string;
  constraintSetHash: string;
  ledgerPrefixHash: string;
  continuityAnchorHash: string;
  pitDefinitionHash: string;
}

function hashPayload(payload: unknown): string {
  return createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}

export function clusterView(): ClusterState {
  const receipts = listReceipts();
  const snapshots = listSnapshots();
  return {
    kernelVersion: "CRK-2",
    invariantSetHash: hashPayload({ version: "crk2-invariants-v1" }),
    constraintSetHash: hashPayload({ version: "crk2-constraints-v1" }),
    ledgerPrefixHash: hashPayload(receipts.slice(0, 10)),
    continuityAnchorHash: hashPayload(snapshots[snapshots.length - 1] ?? "none"),
    pitDefinitionHash: hashPayload({ bands: [1, 2, 3, 4, 5] }),
  };
}
