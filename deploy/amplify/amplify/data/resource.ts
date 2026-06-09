import { type ClientSchema, a, defineData } from '@aws-amplify/backend';

/**
 * Query projections only — JSONL operator receipts remain write authority
 * (same law as deploy/firebase-data-connect and deploy/appwrite spikes).
 */
const schema = a.schema({
  TrustBundleProjection: a
    .model({
      bundleId: a.id().required(),
      tenantId: a.string().required(),
      sessionId: a.string(),
      claimLabel: a.enum(['asserted', 'proven', 'rejected']),
      summary: a.string().required(),
      proofLink: a.url(),
      sourceLedgerHash: a.string().required(),
      recordedAt: a.datetime().required(),
    })
    .authorization((allow) => [
      allow.groups(['operator']).to(['create', 'read', 'update']),
      allow.groups(['observer']).to(['read']),
    ]),

  GovernanceDeltaReceipt: a
    .model({
      deltaId: a.id().required(),
      tenantId: a.string().required(),
      humanOverride: a.boolean().default(false),
      aiProposal: a.string(),
      humanDecision: a.string(),
      debtTicketId: a.string(),
      recordedAt: a.datetime().required(),
    })
    .authorization((allow) => [
      allow.groups(['operator']).to(['create', 'read']),
      allow.groups(['observer']).to(['read']),
    ]),
});

export type Schema = ClientSchema<typeof schema>;
export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'userPool',
  },
});
