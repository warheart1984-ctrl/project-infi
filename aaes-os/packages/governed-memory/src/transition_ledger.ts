/** Constitutional Transition Ledger — durable record of state transitions. */

import type { StateObject } from './constitutional_state.js';
import { reconstructState, replayState, validateTransition } from './constitutional_state.js';
import type { TransitionReceiptV2 } from './receipts_v2.js';
import { isReceiptV2Complete } from './receipts_v2.js';

export interface LedgerEntry {
  transition_id: string;
  state_object_id: string;
  from_state: string;
  to_state: string;
  receipt_id: string;
  timestamp: string;
  runtime: string;
  legal_basis: string;
  accountable_party: string;
  lineage_hash: string;
}

export interface LedgerFailure {
  code: string;
  message: string;
  receipt_id?: string | null;
  transition_id?: string | null;
}

export interface LedgerReplayResult {
  entries_processed: number;
  failures: LedgerFailure[];
  state_replay_diverged: boolean;
  ledger_hash: string;
}

export class ConstitutionalTransitionLedger {
  private entries: LedgerEntry[] = [];
  private receiptIndex = new Map<string, LedgerEntry>();

  getEntries(): LedgerEntry[] {
    return [...this.entries];
  }

  appendFromTransitionReceipt(
    receipt: TransitionReceiptV2,
    opts: { stateObjectId: string; accountableParty: string },
  ): LedgerEntry {
    if (!isReceiptV2Complete(receipt)) {
      throw new Error(`incomplete transition receipt: ${receipt.receipt_id}`);
    }
    validateTransition(receipt.transition.from_state, receipt.transition.to_state);
    if (this.receiptIndex.has(receipt.receipt_id)) {
      throw new Error(`duplicate receipt_id in ledger: ${receipt.receipt_id}`);
    }
    const entry: LedgerEntry = {
      transition_id: receipt.receipt_id,
      state_object_id: opts.stateObjectId,
      from_state: receipt.transition.from_state,
      to_state: receipt.transition.to_state,
      receipt_id: receipt.receipt_id,
      timestamp: receipt.timestamp,
      runtime: receipt.runtime,
      legal_basis: receipt.transition.legal_basis,
      accountable_party: opts.accountableParty,
      lineage_hash: receipt.continuity.lineage_hash,
    };
    this.entries.push(entry);
    this.receiptIndex.set(receipt.receipt_id, entry);
    return entry;
  }

  detectFailures(): LedgerFailure[] {
    const failures: LedgerFailure[] = [];
    const seenReceipts = new Set<string>();
    const priorByState = new Map<string, string>();

    for (const entry of this.entries) {
      if (seenReceipts.has(entry.receipt_id)) {
        failures.push({
          code: 'duplicate_receipt',
          message: 'duplicate receipt_id in ledger',
          receipt_id: entry.receipt_id,
          transition_id: entry.transition_id,
        });
      }
      seenReceipts.add(entry.receipt_id);

      if (!entry.legal_basis) {
        failures.push({ code: 'missing_legal_basis', message: 'missing legal_basis', receipt_id: entry.receipt_id });
      }
      if (!entry.accountable_party) {
        failures.push({
          code: 'unaccountable_action',
          message: 'missing accountable_party',
          receipt_id: entry.receipt_id,
        });
      }

      try {
        validateTransition(entry.from_state, entry.to_state);
      } catch (err) {
        failures.push({
          code: 'illegal_transition',
          message: err instanceof Error ? err.message : String(err),
          transition_id: entry.transition_id,
        });
      }

      const expectedFrom = priorByState.get(entry.state_object_id) ?? 'Proposed';
      if (entry.from_state !== expectedFrom) {
        failures.push({
          code: 'broken_lineage',
          message: `expected from_state ${expectedFrom}, got ${entry.from_state}`,
          transition_id: entry.transition_id,
        });
      }
      priorByState.set(entry.state_object_id, entry.to_state);
    }

    return failures;
  }

  replay(receipts: TransitionReceiptV2[], canonicalState: StateObject): LedgerReplayResult {
    const failures = this.detectFailures();
    const stateResult = replayState(receipts, canonicalState);
    if (stateResult.diverged) {
      failures.push({
        code: 'irreproducible_transition',
        message: 'state replay diverged from canonical state',
      });
    }
    return {
      entries_processed: this.entries.length,
      failures,
      state_replay_diverged: stateResult.diverged,
      ledger_hash: `sha256:${JSON.stringify(this.entries)}`,
    };
  }
}

export function reconstructStateForObject(
  stateObjectId: string,
  receipts: TransitionReceiptV2[],
  seed: StateObject,
): StateObject {
  const scoped = receipts.filter(
    (r) => !r.transition.state_id || r.transition.state_id === stateObjectId,
  );
  return reconstructState(scoped, seed);
}
