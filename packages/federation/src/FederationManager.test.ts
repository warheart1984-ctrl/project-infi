import { describe, expect, it } from 'vitest';

import { PatternLedger } from '@aaes-os/aaes-governance';
import { AuthorityLevel, SovrenAuthority } from '@aaes-os/sovren';

import { FederationManager } from './FederationManager.js';

const LAW_KEY = 'federation-test-law-key';
const LAW_HASH = 'law-hash-v1';

describe('FederationManager', () => {
  it('initiate() requires Sovereign Root authority level 5', () => {
    const sovren = new SovrenAuthority(LAW_KEY);
    const ledger = new PatternLedger();
    const manager = new FederationManager('node-a', LAW_HASH, sovren, ledger);
    const operatorToken = sovren.issue('actor-1', AuthorityLevel.OPERATOR);

    expect(() => manager.initiate('node-b', ['read'], operatorToken)).toThrow(/requires level 5/);
  });

  it('accept() rejects if law hashes do not match', () => {
    const sovren = new SovrenAuthority(LAW_KEY);
    const nodeA = new FederationManager('node-a', LAW_HASH, sovren, new PatternLedger());
    const nodeB = new FederationManager('node-b', 'different-law-hash', sovren, new PatternLedger());
    const rootToken = sovren.issue('root', AuthorityLevel.SOVEREIGN_ROOT);

    const contract = nodeA.initiate('node-b', ['sync'], rootToken);

    expect(() => nodeB.accept(contract, rootToken)).toThrow(/law hash mismatch/);
  });

  it('accept() produces ACTIVE contract with both signatures', () => {
    const sovren = new SovrenAuthority(LAW_KEY);
    const nodeA = new FederationManager('node-a', LAW_HASH, sovren, new PatternLedger());
    const nodeB = new FederationManager('node-b', LAW_HASH, sovren, new PatternLedger());
    const rootToken = sovren.issue('root', AuthorityLevel.SOVEREIGN_ROOT);

    const pending = nodeA.initiate('node-b', ['sync'], rootToken);
    const active = nodeB.accept(pending, rootToken);

    expect(active.status).toBe('ACTIVE');
    expect(active.initiator_signature).toBeTruthy();
    expect(active.receiver_signature).toBeTruthy();
  });

  it('revoke() writes IRREVERSIBLE entry to PatternLedger', () => {
    const sovren = new SovrenAuthority(LAW_KEY);
    const ledger = new PatternLedger();
    const manager = new FederationManager('node-a', LAW_HASH, sovren, ledger);
    const rootToken = sovren.issue('root', AuthorityLevel.SOVEREIGN_ROOT);

    const contract = manager.initiate('node-b', ['sync'], rootToken);
    manager.revoke(contract, rootToken, 'policy drift');

    const entries = ledger.getEntries();
    expect(entries.some((entry) => entry.action === 'REVOKE_FEDERATION')).toBe(true);
    expect(entries.find((entry) => entry.action === 'REVOKE_FEDERATION')?.verdict_class).toBe(
      'IRREVERSIBLE',
    );
  });

  it('ledger.verify() passes after full federation + revocation sequence', () => {
    const sovren = new SovrenAuthority(LAW_KEY);
    const nodeALedger = new PatternLedger();
    const nodeBLedger = new PatternLedger();
    const nodeA = new FederationManager('node-a', LAW_HASH, sovren, nodeALedger);
    const nodeB = new FederationManager('node-b', LAW_HASH, sovren, nodeBLedger);
    const rootToken = sovren.issue('root', AuthorityLevel.SOVEREIGN_ROOT);

    const pending = nodeA.initiate('node-b', ['sync'], rootToken);
    const active = nodeB.accept(pending, rootToken);
    nodeA.revoke(active, rootToken, 'test revocation');

    expect(nodeALedger.verify()).toEqual({ valid: true });
    expect(nodeBLedger.verify()).toEqual({ valid: true });
  });
});
