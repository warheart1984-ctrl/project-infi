/** Observer Verification Handbook — independent verification procedure. */

import type { AmendmentReceiptV2, BaseReceiptV2, TransitionReceiptV2 } from './receipts_v2.js';
import { isReceiptV2Complete } from './receipts_v2.js';
import type { AmendmentState } from './amendments.js';
import { replayAmendment } from './amendments.js';
import type { StateObject } from './constitutional_state.js';
import { replayState } from './constitutional_state.js';
import type { ConstitutionalTransitionLedger } from './transition_ledger.js';
import type {
  ObserverVerificationPayloadV2,
  ObserverVerificationReceiptV2,
  ObserverDivergenceReceiptV2,
  ObserverRemediationRequestReceiptV2,
  ObserverClosureReceiptV2,
} from './receipts_v2.js';

export interface ObserverVerificationContext {
  target_id: string;
  receipts?: BaseReceiptV2[];
  transition_receipts?: TransitionReceiptV2[];
  amendment_receipts?: AmendmentReceiptV2[];
  canonical_state?: StateObject | null;
  amendment_state?: AmendmentState | null;
  trigger_receipt_id?: string | null;
  ledger?: ConstitutionalTransitionLedger | null;
  responsible_parties?: string[];
}

export interface ObserverVerificationReport {
  verification: ObserverVerificationPayloadV2;
  failures: string[];
  verification_receipt?: ObserverVerificationReceiptV2 | null;
  divergence_receipt?: ObserverDivergenceReceiptV2 | null;
  remediation_request_receipt?: ObserverRemediationRequestReceiptV2 | null;
  closure_receipt?: ObserverClosureReceiptV2 | null;
}

export function runObserverVerification(ctx: ObserverVerificationContext): ObserverVerificationReport {
  const failures: string[] = [];
  const receipts = ctx.receipts ?? [];
  const transitionReceipts = ctx.transition_receipts ?? [];

  if (!receipts.length && !transitionReceipts.length) {
    failures.push('no receipts supplied');
  }

  for (const receipt of receipts) {
    if (!isReceiptV2Complete(receipt)) {
      failures.push(`incomplete receipt: ${receipt.receipt_id}`);
    }
  }

  let stateReconstructed = false;
  let stateReplayed = false;
  let divergenceDetected = false;

  if (ctx.ledger) {
    for (const lf of ctx.ledger.detectFailures()) {
      failures.push(`${lf.code}: ${lf.message}`);
    }
    divergenceDetected = ctx.ledger.detectFailures().some((f) =>
      ['illegal_transition', 'broken_lineage'].includes(f.code),
    );
  }

  if (ctx.canonical_state && transitionReceipts.length) {
    const replay = replayState(transitionReceipts, ctx.canonical_state);
    stateReconstructed = true;
    stateReplayed = true;
    if (replay.diverged) {
      divergenceDetected = true;
      failures.push('state replay diverged');
    }
  }

  const remediationValid =
    !divergenceDetected ||
    receipts.some((r) => r.lifecycle?.stage === 'closure');

  let amendmentsValid = true;
  if (ctx.amendment_receipts?.length && ctx.trigger_receipt_id && ctx.amendment_state) {
    const replay = replayAmendment(
      ctx.trigger_receipt_id,
      ctx.amendment_receipts,
      ctx.amendment_state,
    );
    if (replay.diverged) {
      amendmentsValid = false;
      failures.push('amendment replay diverged');
    }
  }

  const verification: ObserverVerificationPayloadV2 = {
    state_reconstructed: stateReconstructed,
    state_replayed: stateReplayed,
    divergence_detected: divergenceDetected,
    remediation_valid: remediationValid,
    amendments_valid: amendmentsValid,
    target_id: ctx.target_id,
  };

  return { verification, failures };
}
