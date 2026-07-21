import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { OpsConsoleShell } from './App.js';
import { createArenaModeSnapshot } from './arenaMode.js';
import type { ProofSurfaceSummary } from '@aaes-os/aaes-governance';

function buildProofSurfaceSummary(overrides: Partial<ProofSurfaceSummary> = {}): ProofSurfaceSummary {
  return {
    identity: {
      id: '@aaes-os/aaes-governance',
      name: 'AAES Governance Package',
      type: 'repository',
    },
    domain: 'Governance',
    healthIndicator: 'Verified',
    proofLevel: 'P2',
    maturity: 'Verified Prototype',
    verificationStatus: 'Test Verified',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The package does not certify external production systems.',
    constitutionalLimits: 'Does not replace consumer-specific adapters or deployment pipelines.',
    dependencies: ['runledger'],
    inputs: ['gov-impl-evidence'],
    outputs: ['The package implements proof-surface types, validation, and registry helpers.', 'gov-impl'],
    evidenceReceipts: ['gov-impl-evidence'],
    currentEvidence: [
      {
        id: 'gov-impl-evidence',
        statement: 'Source files define ProofSurface, ProofSurfaceRegistry, and JSON helpers.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'src/proofSurface.ts',
      },
    ],
    replayPath: 'Replay from registry documents and validation output.',
    verificationPath: 'Build, test, and schema serialization checks.',
    whatItProves: 'Govern proof-surface claims across the stack.',
    whatItDoesNotProve: 'The package does not certify external production systems.',
    blindspots: ['Independent verification is still limited to the local workspace.'],
    knownLimitations: ['Does not replace consumer-specific adapters or deployment pipelines.'],
    adversarialClaims: ['A scorecard can be mistaken for a verified artifact.'],
    battleScars: ['Readiness language used to outpace machine-readable evidence.'],
    relatedProofSurfaces: ['@aaes-os/sovereignx-router'],
    currentMaturity: 'Verified Prototype',
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Governance teams and tool builders',
      primaryUseCase: 'Machine-readable proof-surface publication',
      valueProposition: 'A standard claim/evidence contract for dashboards and product tiers.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Independent consumer integration'],
    ...overrides,
  };
}

describe('OpsConsoleView', () => {
  it('renders the knowledge graph and constitutional profile for proof surfaces', () => {
    const html = renderToString(
      <OpsConsoleShell
        telemetry={{
          drift: { score: 0.2, totalFaults: 2, uniquePatterns: 1, topPatterns: [] },
          topPatterns: [],
          lastFaults: [],
          patchTimeline: [],
          aais: {
            connected: true,
            baseUrl: 'http://127.0.0.1:8000',
            service: 'AAIS',
            activeModelMode: 'mock',
            aiStatus: 'initialized',
            aiBootstrapStatus: 'initialized',
            mockModeActive: true,
            legacyApiLoaded: true,
          },
        }}
        mriV2={{
          state_vector: { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
          delta_state: { continuity: 0.08, governance: -0.04, memory: 0.11, coordination: -0.02, confidence: 0.06 },
          trajectory_vector: { continuity: 0.06, governance: -0.03, memory: 0.08, coordination: -0.01, magnitude: 0.1, confidenceWeightedMagnitude: 0.08, confidence_weighted_magnitude: 0.08 },
          benchmarks: {
            industryAverage: { continuity: 61, governance: 59, memory: 64, coordination: 57, confidence: 70 },
            topQuartile: { continuity: 78, governance: 74, memory: 82, coordination: 71, confidence: 85 },
            previousMeasurement: { continuity: 64, governance: 72, memory: 64, coordination: 65, confidence: 74 },
            summary: '+11 above industry',
            deltas: [],
            bar_markers: {
              continuity: { current: 72, previous: 64, industry: 61, topQuartile: 78 },
              governance: { current: 68, previous: 72, industry: 59, topQuartile: 74 },
              memory: { current: 75, previous: 64, industry: 64, topQuartile: 82 },
              coordination: { current: 63, previous: 65, industry: 57, topQuartile: 71 },
              confidence: { current: 81, previous: 74, industry: 70, topQuartile: 85 },
            },
          },
          trajectory_signatures: ['stable_continuity_declining_governance'],
          trajectory_breakdown: [],
          projection: [],
          risks: [],
          interventions: [],
          evidence: { beforeConfidence: 74, afterConfidence: 81, meanConfidence: 0.8, confidenceTensor: { observationCompleteness: 0.8, dataQuality: 0.8, sourceReliability: 0.8, temporalFreshness: 0.8, crossEvidenceConsistency: 0.8 } },
          before_after: {
            before: { continuity: 64, governance: 72, memory: 64, coordination: 65, confidence: 74 },
            after: { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
          },
        }}
        enforcement={{ events: [{ receiptId: 'cen:1', verdict: 'DENY', reasonCode: 'INVARIANT_VIOLATION' }], status: 'ACTIVE' }}
        meta={{ podId: 'meta_constitutional_collapse', generativeCoreId: 'CML-15', metaInvariantCount: 4 }}
        customers={{
          customers: [
            {
              id: 'cust-1',
              email: 'customer@example.com',
              planId: 'pro',
              planName: 'Pro',
              entitlements: {
                routingTier: 'pro',
                codexPacketHandoff: true,
                usageLedger: true,
                marginDashboard: true,
                auditScope: 'personal',
              },
              createdAt: '2026-07-11T00:00:00.000Z',
            },
          ],
          customerCount: 1,
          planCounts: { pro: 1 },
        }}
        organizations={{
          organizations: [
            {
              id: 'org-1',
              name: 'Customer One Org',
              ownerCustomerId: 'cust-1',
              billingContactEmail: 'billing@example.com',
              domain: 'example.com',
              members: [{ customerId: 'cust-1', role: 'owner', joinedAt: '2026-07-11T00:00:00.000Z' }],
              createdAt: '2026-07-11T00:00:00.000Z',
              updatedAt: '2026-07-11T00:00:00.000Z',
            },
          ],
          organizationCount: 1,
          roleCounts: { owner: 1, admin: 0, analyst: 0, developer: 0, auditor: 0 },
        }}
        quota={{
          customer: {
            id: 'cust-1',
            email: 'customer@example.com',
            planName: 'Pro',
            organizationId: 'org-1',
            organizationRole: 'owner',
            entitlements: {
              routingTier: 'pro',
              codexPacketHandoff: true,
              usageLedger: true,
              marginDashboard: true,
              auditScope: 'personal',
            },
          },
          quota: {
            requestLimit: 1000,
            requestCount: 12,
            requestOverage: 0,
            tokenLimit: 100000,
            tokenCount: 1200,
            tokenOverage: 0,
            overageBillingUsd: 0,
            overageBillingEnabled: true,
            enforcement: {
              status: 'within_limit',
              allowed: true,
              reason: 'Within entitlement limits',
            },
          },
          usageRecords: [
            { operation: 'billing:pricing-evaluate', units: 12, timestamp: '2026-07-11T00:00:00.000Z' },
          ],
        }}
        cepArtifacts={{
          storePath: 'E:/project-infi/services/ops-console/.runtime/cep-artifacts.jsonl',
          entryCount: 3,
          countsByKind: {
            'promotion-request': 1,
            'replay-job': 1,
            decision: 1,
          },
          records: [
            {
              id: 'cep-promo-1',
              kind: 'promotion-request',
              title: 'Promotion Request',
              source: 'test',
              recordedAt: '2026-07-11T00:00:00.000Z',
              payload: { type: 'PromotionRequest' },
            },
            {
              id: 'cep-replay-1',
              kind: 'replay-job',
              title: 'Replay Job',
              source: 'test',
              relatedArtifactId: 'cep-promo-1',
              recordedAt: '2026-07-11T00:01:00.000Z',
              payload: { type: 'ReplayJob' },
            },
            {
              id: 'cep-decision-1',
              kind: 'decision',
              title: 'Decision',
              source: 'test',
              relatedArtifactId: 'cep-replay-1',
              recordedAt: '2026-07-11T00:02:00.000Z',
              payload: { type: 'PromotionDecision' },
            },
          ],
          recentRecords: [],
          viewState: {
            selectedKind: 'promotion-request',
            selectedArtifactId: 'cep-promo-1',
            updatedAt: '2026-07-11T00:02:00.000Z',
            source: 'local',
          },
        }}
        treasurySchedule={{
          schedule: {
            scheduledAt: '2026-07-11T00:00:00.000Z',
            source: 'ledger',
            customerId: 'cust-1',
            ownerId: 'owner-1',
            governanceProfile: 'balanced',
            instructions: {
              openAI: { destination: 'OpenAI', channel: 'openai-org-billing', amountUsd: 42, notes: 'Pay OpenAI' },
              tax: { destination: 'IRS', channel: 'irs-direct-pay', amountUsd: 18, notes: 'IRS Direct Pay instructions' },
              ownerProfit: { destination: 'PayPal', channel: 'paypal-payouts', amountUsd: 72, notes: 'Send owner profit through PayPal Payouts' },
            },
            sourcePlan: {
              grossInvoiceUsd: 250,
              openAiUsageCostUsd: 42,
              taxReserveUsd: 18,
              platformReserveUsd: 20,
              ownerProfitUsd: 72,
              totalReserveUsd: 80,
              netAfterReservesUsd: 170,
              providerNotes: {
                customerCollection: 'Collect customer payment through checkout, then record settlement in the treasury ledger.',
                openAI: 'OpenAI costs are separate vendor spend. Keep the treasury reserve aligned with your OpenAI billing cycle.',
                tax: 'IRS remittance should be scheduled through IRS-approved payment channels, not via PayPal.',
                profit: 'Profit can be distributed to the owner through PayPal Payouts after reserves are held.',
              },
              adapters: {
                paypalCheckout: {
                  enabled: true,
                  environment: 'sandbox',
                  apiBaseUrl: 'https://api-m.sandbox.paypal.com',
                  createOrderPath: '/v2/checkout/orders',
                  captureOrderPath: '/v2/checkout/orders/:orderId/capture',
                  orderRequest: {
                    intent: 'CAPTURE',
                    application_context: {
                      brand_name: 'Sovereign Router X',
                      landing_page: 'NO_PREFERENCE',
                      user_action: 'PAY_NOW',
                      return_url: 'http://localhost:4000/treasury/paypal/return',
                      cancel_url: 'http://localhost:4000/treasury/paypal/cancel',
                    },
                    purchase_units: [
                      {
                        reference_id: 'cust-1',
                        description: 'Customer treasury collection for cust-1',
                        custom_id: 'cust-1:owner-1',
                        amount: { currency_code: 'USD', value: '250.00' },
                      },
                    ],
                  },
                },
                paypalPayout: {
                  enabled: true,
                  environment: 'sandbox',
                  apiBaseUrl: 'https://api-m.sandbox.paypal.com',
                  createBatchPath: '/v1/payments/payouts',
                  batchRequest: {
                    sender_batch_header: {
                      sender_batch_id: 'owner-1-batch',
                      email_subject: 'Sovereign Router X owner payout',
                      email_message: 'Your owner-profit payout has been scheduled from the treasury ledger.',
                    },
                    items: [
                      {
                        recipient_type: 'EMAIL',
                        amount: { currency: 'USD', value: '72.00' },
                        receiver: 'owner@example.com',
                        note: 'Owner-profit distribution for owner-1',
                        sender_item_id: 'cust-1:owner-1:owner-profit',
                      },
                    ],
                  },
                },
              },
            },
          },
        }}
        governanceEvolution={{
          timelineId: 'governance-evolution-timeline',
          summary: {
            entryCount: 2,
            continuityReports: 2,
            governanceDiffs: 1,
            replayReports: 1,
            validatedAmendments: 1,
          },
          entries: [
            {
              eventId: 'evo-1',
              stage: 'governance',
              artifactId: 'inv-1',
              createdAt: '2026-07-11T00:00:00.000Z',
              summary: 'Governance amendment proposed after review.',
              outcome: 'proposed',
              continuityReport: {
                reportId: 'continuity-1',
                createdAt: '2026-07-11T00:00:00.000Z',
                valid: true,
                lineageValid: true,
                replayValid: true,
                receiptId: 'receipt-1',
                notes: ['Lineage preserved.'],
                chain: [
                  {
                    sequence: 1,
                    entryType: 'collapse_record',
                    subjectId: 'CML-15',
                    issuedAt: '2026-06-18T22:02:00.000Z',
                    entryHash: 'sha3-256:abc',
                    previousHash: null,
                  },
                ],
              },
              governanceDiff: {
                diffId: 'diff-1',
                createdAt: '2026-07-11T00:00:00.000Z',
                currentConfigVersion: 'v1.0.0',
                targetConfigVersion: 'v1.1.0',
                domain: 'governance',
                tier: 'constitutional',
                changes: [
                  {
                    path: 'thresholds.minTrustScore',
                    before: 0.7,
                    after: 0.78,
                    rationale: 'Raise the trust floor.',
                  },
                ],
                replayReportIds: ['receipt-1'],
                trustReportIds: ['receipt-2'],
              },
              replayReport: null,
            },
            {
              eventId: 'evo-2',
              stage: 'renewal',
              artifactId: 'inv-1-approved',
              createdAt: '2026-07-11T00:01:00.000Z',
              summary: 'Amendment outcome validated and archived.',
              outcome: 'validated',
              continuityReport: {
                reportId: 'continuity-2',
                createdAt: '2026-07-11T00:01:00.000Z',
                valid: true,
                lineageValid: true,
                replayValid: true,
                receiptId: 'receipt-2',
                notes: ['Replay passed.'],
                chain: [
                  {
                    sequence: 1,
                    entryType: 'collapse_record',
                    subjectId: 'CML-15',
                    issuedAt: '2026-06-18T22:02:00.000Z',
                    entryHash: 'sha3-256:abc',
                    previousHash: null,
                  },
                ],
              },
              governanceDiff: {
                diffId: 'diff-1-approved',
                createdAt: '2026-07-11T00:01:00.000Z',
                currentConfigVersion: 'v1.1.0',
                targetConfigVersion: 'v1.1.1',
                domain: 'governance',
                tier: 'constitutional',
                changes: [],
                replayReportIds: ['receipt-2'],
                trustReportIds: ['receipt-1'],
              },
              replayReport: {
                replayId: 'replay-1',
                mode: 'Resonance',
                decision: 'promote',
                stage: 'constitutional',
                summary: 'Replay validated the amendment path.',
                receiptId: 'receipt-2',
                lawOfLawsEntryId: 'entry-1',
              },
            },
          ],
        }}
        arenaMode={createArenaModeSnapshot('ops-console-test-seed')}
        proofSurfaceCatalog={{
          status: 'loaded',
          catalogUrl: 'http://127.0.0.1:4000/proof-surfaces',
          proofSurfaces: [
            buildProofSurfaceSummary(),
            buildProofSurfaceSummary({
              identity: {
                id: '@aaes-os/sovereignx-router',
                name: 'SovereignX Execution Surface',
                type: 'runtime',
              },
              domain: 'Execution',
              healthIndicator: 'Experimental',
              proofLevel: 'P2',
              maturity: 'Verified Prototype',
              verificationStatus: 'Test Verified',
              whatItProves: 'Governed execution receipts and replayable operator evidence.',
              whatItDoesNotProve: 'It does not prove production cluster orchestration.',
              relatedProofSurfaces: ['@aaes-os/aaes-governance'],
            }),
          ],
        }}
        catalogUrlInput="http://127.0.0.1:4000/proof-surfaces"
        selectedProofSurfaceId="@aaes-os/sovereignx-router"
        selectedGovernanceEvolutionId="evo-2"
        onCatalogUrlInputChange={() => undefined}
        onCatalogSubmit={(event) => event.preventDefault()}
        onResetCatalogUrl={() => undefined}
        onUseQueryCatalogUrl={() => undefined}
        onSelectedProofSurfaceChange={() => undefined}
        onSelectedGovernanceEvolutionIdChange={() => undefined}
      />
    );

    expect(html).toContain('Constitutional Knowledge Graph');
    expect(html).toContain('Governance');
    expect(html).toContain('Execution');
    expect(html).toContain('Arena Mode');
    expect(html).toContain('Challenge');
    expect(html).toContain('Tournament');
    expect(html).toContain('Replay Timeline');
    expect(html).toContain('What it proves');
    expect(html).toContain('What it does not prove');
    expect(html).toContain('Related proof surfaces');
    expect(html).toContain('SovereignX Execution Surface');
  });
});
