import { createHash } from 'node:crypto';

import { PatternLedger } from '@aaes-os/aaes-governance';
import { AuthorityLevel, SovrenAuthority, type AuthToken } from '@aaes-os/sovren';

export interface FederationContract {
  federation_id: string;
  initiating_node: string;
  receiving_node: string;
  federation_law_hash: string;
  authority_scope: string[];
  initiated_at: string;
  initiator_signature: string;
  receiver_signature?: string;
  status: 'PENDING' | 'ACTIVE' | 'REVOKED';
}

export class FederationManager {
  constructor(
    private readonly nodeId: string,
    private readonly lawHash: string,
    private readonly sovren: SovrenAuthority,
    private readonly ledger: PatternLedger,
  ) {}

  initiate(
    targetNodeId: string,
    scope: string[],
    sovereignRootToken: AuthToken,
  ): FederationContract {
    this.sovren.authorize(sovereignRootToken, AuthorityLevel.SOVEREIGN_ROOT);

    const federation_id = `fed_${Date.now()}`;
    const contract: FederationContract = {
      federation_id,
      initiating_node: this.nodeId,
      receiving_node: targetNodeId,
      federation_law_hash: this.lawHash,
      authority_scope: scope,
      initiated_at: new Date().toISOString(),
      initiator_signature: this.sovren.signEnvelope({
        federation_id,
        initiating_node: this.nodeId,
        receiving_node: targetNodeId,
        federation_law_hash: this.lawHash,
      }),
      status: 'PENDING',
    };

    this.ledger.append({
      envelope_id: federation_id,
      trace_id: federation_id,
      delta_hash: createHash('sha256').update(JSON.stringify(contract)).digest('hex'),
      action: 'FEDERATE_INITIATE',
      actor_id: this.nodeId,
      verdict_class: 'IRREVERSIBLE',
    });

    return contract;
  }

  accept(contract: FederationContract, sovereignRootToken: AuthToken): FederationContract {
    this.sovren.authorize(sovereignRootToken, AuthorityLevel.SOVEREIGN_ROOT);

    if (contract.federation_law_hash !== this.lawHash) {
      throw new Error(
        `FEDERATION: law hash mismatch — initiator: ${contract.federation_law_hash}, receiver: ${this.lawHash}`,
      );
    }

    const active: FederationContract = {
      ...contract,
      receiver_signature: this.sovren.signEnvelope({
        federation_id: contract.federation_id,
        receiving_node: this.nodeId,
        federation_law_hash: this.lawHash,
      }),
      status: 'ACTIVE',
    };

    this.ledger.append({
      envelope_id: contract.federation_id,
      trace_id: contract.federation_id,
      delta_hash: createHash('sha256').update(JSON.stringify(active)).digest('hex'),
      action: 'FEDERATE_ACCEPT',
      actor_id: this.nodeId,
      verdict_class: 'IRREVERSIBLE',
    });

    return active;
  }

  revoke(contract: FederationContract, sovereignRootToken: AuthToken, reason: string): void {
    this.sovren.authorize(sovereignRootToken, AuthorityLevel.SOVEREIGN_ROOT);

    this.ledger.append({
      envelope_id: contract.federation_id,
      trace_id: contract.federation_id,
      delta_hash: createHash('sha256').update(reason).digest('hex'),
      action: 'REVOKE_FEDERATION',
      actor_id: this.nodeId,
      verdict_class: 'IRREVERSIBLE',
      meta: { reason, revoked_at: new Date().toISOString() },
    });
  }
}
