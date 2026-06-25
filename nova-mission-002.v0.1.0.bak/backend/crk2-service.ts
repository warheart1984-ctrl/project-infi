import { dLAP, takeSnapshot, replay, generateCRP, clusterView } from "../crk2";
import { listReceipts, appendReceipt } from "../crk2/ledger/ledger-v2";
import { listSnapshots } from "../crk2/continuity/substrate";

export const crk2Service = {
  evaluateAction: dLAP,
  takeSnapshot,
  replay,
  generateCRP,
  getClusterView: clusterView,
  listReceipts,
  appendReceipt,
  listSnapshots,
};
