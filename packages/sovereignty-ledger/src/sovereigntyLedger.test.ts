import { describe, expect, it } from 'vitest';

import {
  appendSovereigntyEntry,
  createFileSovereigntyLedger,
  createSovereigntyLedger,
  verifySovereigntyChain,
} from './index.js';
import { mkdtempSync, rmSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

describe('sovereignty ledger', () => {
  it('hash chains enforcement and token events', () => {
    const ledger = createSovereigntyLedger();
    const first = appendSovereigntyEntry(ledger, {
      eventType: 'denied_transition',
      subjectId: 'transition:deny',
      payload: { reasonCode: 'INVARIANT_VIOLATION' },
      issuedAt: '2026-06-18T22:45:00.000Z',
    });
    const second = appendSovereigntyEntry(ledger, {
      eventType: 'authority_token_used',
      subjectId: 'vt-1',
      payload: { tokenType: 'VT' },
      issuedAt: '2026-06-18T22:45:01.000Z',
    });

    expect(first.previousHash).toBeNull();
    expect(second.previousHash).toBe(first.entryHash);
    expect(verifySovereigntyChain(ledger.entries())).toBe(true);
  });

  it('detects tampered entries', () => {
    const ledger = createSovereigntyLedger();
    appendSovereigntyEntry(ledger, {
      eventType: 'bypass_attempt',
      subjectId: 'transition:bypass',
      payload: { blocked: true },
      issuedAt: '2026-06-18T22:45:00.000Z',
    });
    const tampered = ledger.entries().map((entry) => ({ ...entry, subjectId: 'mutated' }));

    expect(verifySovereigntyChain(tampered)).toBe(false);
  });

  it('persists entries through a file-backed adapter', () => {
    const tempDir = mkdtempSync(path.join(os.tmpdir(), 'aaes-sovereignty-'));
    try {
      const filePath = path.join(tempDir, 'sovereignty.json');
      const firstLedger = createFileSovereigntyLedger(filePath);
      appendSovereigntyEntry(firstLedger, {
        eventType: 'freeze_decision',
        subjectId: 'transition:freeze',
        payload: { action: 'FREEZE' },
        issuedAt: '2026-06-18T22:45:00.000Z',
      });

      const secondLedger = createFileSovereigntyLedger(filePath);
      expect(secondLedger.entries()).toHaveLength(1);
      expect(secondLedger.entries()[0]?.subjectId).toBe('transition:freeze');
      expect(verifySovereigntyChain(secondLedger.entries())).toBe(true);
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  });
});
