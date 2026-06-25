/** Article XVI — Constitutional Amendment Process. */

import type {
  AmendmentReceiptV2,
  AmendmentStage,
  BaseReceiptV2,
} from './receipts_v2.js';
import {
  isReceiptV2Complete,
  validateAmendmentTransition,
  validateImmutableAmendment,
} from './receipts_v2.js';

export interface AmendmentState {
  amendment_id: string;
  article: string;
  current_stage: AmendmentStage;
  trigger_receipt_id: string;
  version: number;
  receipt_ids: string[];
}

export interface AmendmentReplayResult {
  amendment_id: string;
  final_stage: AmendmentStage;
  diverged: boolean;
  canonical_stage: AmendmentStage;
  replay_hash: string;
}

export function applyAmendmentReceipt(state: AmendmentState, receipt: AmendmentReceiptV2): AmendmentState {
  if (!isReceiptV2Complete(receipt)) {
    throw new Error(`incomplete amendment receipt: ${receipt.receipt_id}`);
  }
  const stage = receipt.amendment.amendment_stage;
  if (state.version === 0 && stage !== 'proposed') {
    throw new Error('amendment must begin with proposed stage');
  }
  if (state.version > 0) {
    validateAmendmentTransition(state.current_stage, stage);
  }
  validateImmutableAmendment(receipt.amendment);
  return {
    ...state,
    current_stage: stage,
    version: state.version + 1,
    receipt_ids: [...state.receipt_ids, receipt.receipt_id],
  };
}

export function processAmendmentReceipts(
  triggerReceiptId: string,
  receipts: AmendmentReceiptV2[],
): AmendmentState {
  if (!receipts.length) {
    throw new Error('amendment requires at least a proposal receipt');
  }
  const first = receipts[0];
  if (first.amendment.trigger_receipt_id !== triggerReceiptId) {
    throw new Error('proposal must reference trigger_receipt_id');
  }
  let state: AmendmentState = {
    amendment_id: first.receipt_id,
    article: first.amendment.article,
    current_stage: 'proposed',
    trigger_receipt_id: triggerReceiptId,
    version: 0,
    receipt_ids: [],
  };
  for (const receipt of receipts) {
    state = applyAmendmentReceipt(state, receipt);
  }
  return state;
}

export function replayAmendment(
  triggerReceiptId: string,
  receipts: AmendmentReceiptV2[],
  canonical: AmendmentState,
): AmendmentReplayResult {
  const replayed = processAmendmentReceipts(triggerReceiptId, receipts);
  const diverged =
    replayed.current_stage !== canonical.current_stage ||
    replayed.version !== canonical.version ||
    replayed.receipt_ids.join(',') !== canonical.receipt_ids.join(',');
  return {
    amendment_id: canonical.amendment_id,
    final_stage: replayed.current_stage,
    diverged,
    canonical_stage: canonical.current_stage,
    replay_hash: `sha256:${JSON.stringify({ replayed, canonical })}`,
  };
}
