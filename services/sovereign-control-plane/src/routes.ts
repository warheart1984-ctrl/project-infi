import type { Express, Request, Response, NextFunction } from 'express';
import { dirname } from 'node:path';

import {
  buildRouteDecisionArtifact,
  type TrustBand,
  type TrustDomain,
  type TrustReplayMode,
  type TrustReplayScope,
} from '../../../packages/sovereignx-router/dist/index.js';
import {
  getCoriAlphaGraph,
  getCoriAlphaLineage,
  getCoriAlphaStats,
  getCoriAlphaUpload,
  listCoriAlphaUploads,
  runCoriAlphaUpload,
  syncCoriAlphaSummary,
  validateCoriAlphaStore,
} from './coriAlpha.js';

import {
  createGovernanceProposal,
  debugTrustArtifact,
  evaluateGovernanceAction,
  getAuthorityFlows,
  getAuthorityMap,
  getClauseHeatmap,
  getClauses,
  getContinuityOverview,
  getCurrentGovernanceConfig,
  getGovernanceConfigSnapshot,
  getGovernanceDecision,
  getGovernanceSummary,
  getMemoryEpisode,
  getMemoryEvents,
  getMemoryNarratives,
  getMeshLinks,
  getMeshNodes,
  getNodeHealth,
  getReplayReport,
  getReplaySession,
  getReplaySnapshot,
  getReplayTimeline,
  getSovereignControlPlaneState,
  getRouteDecision,
  getTrustArtifact,
  getTrustFabric,
  getTrustGovernanceView,
  getTrustRelationship,
  getTrustReceipts,
  getDriftSummary,
  getEffectivePolicies,
  listGovernanceTimeline,
  listPolicies,
  listTrustRelationships,
  recordGovernanceDecision,
  recordRouteDecision,
  reviewGovernanceProposal,
  startReplaySession,
  listRouteDecisions,
} from './state.js';
import {
  type ChangeType,
  diffGovernanceStates,
  getChangeLedgerEntries,
  getChangeLedgerEntry,
  getChangeTimeline,
  getCrfArtifacts,
  getGovernanceImpactMap,
  getGovernanceHistory,
  getKnowledgeLineage,
  getKnowledgeObject,
  getKnowledgeWorld,
  getLineageGraph,
  getMeshNeighbors,
  getUplModules,
  queryKnowledge,
  replayChange,
  replayGovernanceState,
  searchKnowledge,
  validateCrfArtifact,
} from './knowledge.js';

function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<void>,
) {
  return (req: Request, res: Response, next: NextFunction) => {
    void fn(req, res, next).catch(next);
  };
}

function normalizeTrustBand(value: unknown): TrustBand | null {
  return value === 'low' || value === 'medium' || value === 'high' ? value : null;
}

function normalizeReplayMode(value: unknown): TrustReplayMode {
  return value === 'historical' ? 'historical' : 'counterfactual';
}

function normalizeReplayScope(value: unknown): TrustReplayScope {
  return value === 'relationship' || value === 'domain' ? value : 'global';
}

function normalizeTrustDomain(value: unknown): TrustDomain | null {
  return value === 'ops' || value === 'safety' || value === 'finance' || value === 'compliance' || value === 'global'
    ? value
    : null;
}

function normalizeDropboxPath(value: unknown): string | undefined {
  if (typeof value !== 'string') {
    return undefined;
  }
  const normalized = value.replace(/\\/g, '/').replace(/^\/+/, '').replace(/\/+$/, '');
  return normalized.length > 0 ? normalized : undefined;
}

function normalizeChangeType(value: unknown): ChangeType | null {
  return value === 'PROFILE_CREATED'
    || value === 'PROFILE_MODIFIED'
    || value === 'PROFILE_DELETED'
    || value === 'RULE_CREATED'
    || value === 'RULE_MODIFIED'
    || value === 'RULE_DELETED'
    || value === 'STEWARD_CONTRACT_UPDATED'
    || value === 'CONSTITUTIONAL_CLAUSE_ADDED'
    || value === 'CONSTITUTIONAL_CLAUSE_REVISED'
    ? value
    : null;
}

function deriveDropboxRoot(dropboxPath: string | undefined): string | undefined {
  if (!dropboxPath) {
    return undefined;
  }
  const parent = dirname(dropboxPath);
  if (!parent || parent === '.' || parent === '/') {
    return dropboxPath;
  }
  return parent.replace(/\\/g, '/');
}

export function mountRoutes(app: Express): void {
  app.get('/health', (_req, res) => {
    res.json({
      status: 'ok',
      service: 'sovereign-control-plane',
      planes: ['governance', 'knowledge', 'execution', 'control'],
    });
  });

  app.post('/upload', asyncHandler(async (req, res) => {
    const repoPath = typeof req.body?.repo_path === 'string' ? req.body.repo_path : typeof req.body?.repoPath === 'string' ? req.body.repoPath : undefined;
    const developerId = typeof req.body?.developer_id === 'string' ? req.body.developer_id : typeof req.body?.developerId === 'string' ? req.body.developerId : undefined;
    const commit = typeof req.body?.commit === 'string' ? req.body.commit : undefined;
    const dropboxPath = normalizeDropboxPath(req.body?.dropbox_path ?? req.body?.dropboxPath);
    const dropboxRoot = deriveDropboxRoot(dropboxPath);
    const result = await runCoriAlphaUpload({
      repoPath,
      developerId,
      commit,
      tag: typeof req.body?.tag === 'string' ? req.body.tag : null,
      mode: req.body?.mode === 'tag' || req.body?.mode === 'manual' ? req.body.mode : 'push',
      publishToDropbox: typeof req.body?.publishToDropbox === 'boolean' ? req.body.publishToDropbox : undefined,
      dropboxRoot: typeof req.body?.dropboxRoot === 'string' ? req.body.dropboxRoot : dropboxRoot,
    });
    res.status(201).json({
      status: result.upload.decision.result,
      decision_id: result.upload.decision.decisionId,
      receipt_id: result.upload.decision.receiptId,
      ledger_entry_id: result.upload.ledgerEntryId,
      dropbox_file: result.upload.artifact.dropboxPath ?? null,
      upload: result.upload,
      validation: result.validation,
      dropboxTransfers: result.dropboxTransfers,
    });
  }));

  app.get('/uploads', (_req, res) => {
    const uploads = listCoriAlphaUploads();
    res.json({
      uploads,
      summary: getCoriAlphaStats(),
    });
  });

  app.get('/upload/:commit', (req, res) => {
    const upload = getCoriAlphaUpload(String(req.params.commit));
    if (!upload) {
      res.status(404).json({ error: 'cori alpha upload not found' });
      return;
    }
    res.json(upload);
  });

  app.get('/graph', (_req, res) => {
    res.json(getCoriAlphaGraph());
  });

  app.get('/lineage/:commit', (req, res) => {
    const lineage = getCoriAlphaLineage(String(req.params.commit));
    if (lineage.length === 0) {
      res.status(404).json({ error: 'cori alpha lineage not found' });
      return;
    }
    res.json({
      commit: String(req.params.commit),
      lineage,
    });
  });

  app.get('/stats', (_req, res) => {
    res.json(getCoriAlphaStats());
  });

  app.get('/events', (_req, res) => {
    res.json({ events: getMemoryEvents(), summary: getGovernanceSummary() });
  });

  app.get('/governance/summary', (_req, res) => {
    res.json(getGovernanceSummary());
  });

  app.get('/governance/decision/:commit', (req, res) => {
    const decision = getGovernanceDecision(String(req.params.commit));
    if (!decision) {
      res.status(404).json({ error: 'governance decision not found' });
      return;
    }
    res.json(decision);
  });

  app.get('/clauses', (_req, res) => {
    res.json({ clauses: getClauses() });
  });

  app.get('/clauses-heatmap', (_req, res) => {
    res.json(getClauseHeatmap());
  });

  app.get('/policies', (_req, res) => {
    res.json({ policies: listPolicies() });
  });

  app.get('/policies/effective', (req, res) => {
    const target = typeof req.query.target === 'string' ? req.query.target : '';
    res.json(getEffectivePolicies(target));
  });

  app.get('/drift', (_req, res) => {
    res.json(getDriftSummary());
  });

  app.get('/governance/change-ledger', (req, res) => {
    const changeTypes = Array.isArray(req.query.change_type)
      ? req.query.change_type.map(normalizeChangeType).filter((entry): entry is ChangeType => entry !== null)
      : normalizeChangeType(req.query.change_type);
    res.json({
      entries: getChangeLedgerEntries({
        changeType: Array.isArray(changeTypes) ? changeTypes : changeTypes ? [changeTypes] : null,
        domain: typeof req.query.domain === 'string' ? req.query.domain : null,
        subsystem: typeof req.query.subsystem === 'string' ? req.query.subsystem : null,
        dateRange: {
          from: typeof req.query.from === 'string' ? req.query.from : null,
          to: typeof req.query.to === 'string' ? req.query.to : null,
        },
        tags: Array.isArray(req.query.tags)
          ? req.query.tags.filter((entry): entry is string => typeof entry === 'string')
          : typeof req.query.tags === 'string'
            ? [req.query.tags]
            : null,
      }),
    });
  });

  app.get('/governance/change-ledger/:entryId', (req, res) => {
    const entry = getChangeLedgerEntry(String(req.params.entryId));
    if (!entry) {
      res.status(404).json({ error: 'change ledger entry not found' });
      return;
    }
    res.json(entry);
  });

  app.get('/governance/history/:intentId', (req, res) => {
    res.json(getGovernanceHistory(String(req.params.intentId)));
  });

  app.get('/governance/replay-state', (req, res) => {
    const timestamp = typeof req.query.timestamp === 'string' ? req.query.timestamp : new Date().toISOString();
    res.json(replayGovernanceState(timestamp));
  });

  app.get('/governance/replay-change/:entryId', (req, res) => {
    const replay = replayChange(String(req.params.entryId));
    if (!replay) {
      res.status(404).json({ error: 'governance replay change not found' });
      return;
    }
    res.json(replay);
  });

  app.get('/governance/diff', (req, res) => {
    const from = typeof req.query.from === 'string' ? req.query.from : '2026-01-01T00:00:00.000Z';
    const to = typeof req.query.to === 'string' ? req.query.to : new Date().toISOString();
    res.json(diffGovernanceStates(from, to));
  });

  app.get('/governance/timeline', (req, res) => {
    const changeTypes = Array.isArray(req.query.change_type)
      ? req.query.change_type.map(normalizeChangeType).filter((entry): entry is ChangeType => entry !== null)
      : normalizeChangeType(req.query.change_type);
    res.json(getChangeTimeline({
      changeType: Array.isArray(changeTypes) ? changeTypes : changeTypes ? [changeTypes] : null,
      domain: typeof req.query.domain === 'string' ? req.query.domain : null,
      tags: Array.isArray(req.query.tags)
        ? req.query.tags.filter((entry): entry is string => typeof entry === 'string')
        : typeof req.query.tags === 'string'
          ? [req.query.tags]
          : null,
    }));
  });

  app.get('/governance/impact/:entryId', (req, res) => {
    const impact = getGovernanceImpactMap(String(req.params.entryId));
    if (!impact) {
      res.status(404).json({ error: 'governance impact not found' });
      return;
    }
    res.json(impact);
  });

  app.get('/governance/lineage/:subjectId', (req, res) => {
    res.json(getLineageGraph(String(req.params.subjectId)));
  });

  app.get('/knowledge/world/:worldId', (req, res) => {
    const world = getKnowledgeWorld(String(req.params.worldId));
    if (!world) {
      res.status(404).json({ error: 'knowledge world not found' });
      return;
    }
    res.json(world);
  });

  app.get('/knowledge/object/:objectId', (req, res) => {
    const object = getKnowledgeObject(String(req.params.objectId));
    if (!object) {
      res.status(404).json({ error: 'knowledge object not found' });
      return;
    }
    res.json(object);
  });

  app.get('/knowledge/lineage/:subjectId', (req, res) => {
    res.json({ nodes: getKnowledgeLineage(String(req.params.subjectId)) });
  });

  app.get('/knowledge/mesh/neighbors', (req, res) => {
    const worldId = typeof req.query.world_id === 'string' ? req.query.world_id : '';
    const mesh = getMeshNeighbors(worldId);
    if (!mesh.world) {
      res.status(404).json({ error: 'knowledge world not found' });
      return;
    }
    res.json(mesh);
  });

  app.get('/knowledge/search', (req, res) => {
    const text = typeof req.query.text === 'string' ? req.query.text : '';
    const domain = typeof req.query.domain === 'string' ? req.query.domain : null;
    res.json({ results: searchKnowledge(text, domain) });
  });

  app.get('/upl/modules', (_req, res) => {
    res.json({ modules: getUplModules() });
  });

  app.get('/crf/artifacts', (_req, res) => {
    res.json({ artifacts: getCrfArtifacts() });
  });

  app.get('/crf/artifacts/:artifactId', (req, res) => {
    const artifact = getCrfArtifacts().find((entry) => entry.id === String(req.params.artifactId));
    if (!artifact) {
      res.status(404).json({ error: 'crf artifact not found' });
      return;
    }
    res.json({ artifact, validation: validateCrfArtifact(artifact) });
  });

  app.post('/ugr/query', asyncHandler(async (req, res) => {
    const ugql = typeof req.body?.ugql === 'string' ? req.body.ugql : '';
    if (!ugql.trim()) {
      res.status(400).json({ error: 'ugql is required' });
      return;
    }
    res.json(queryKnowledge(ugql));
  }));

  app.get('/ugr/query', (req, res) => {
    const ugql = typeof req.query.ugql === 'string' ? req.query.ugql : '';
    if (!ugql.trim()) {
      res.status(400).json({ error: 'ugql is required' });
      return;
    }
    res.json(queryKnowledge(ugql));
  });

  app.get('/trust-fabric', (_req, res) => {
    res.json(getTrustFabric());
  });

  app.get('/nodes-health', (_req, res) => {
    res.json(getNodeHealth());
  });

  app.get('/mesh/nodes', (_req, res) => {
    res.json(getMeshNodes());
  });

  app.get('/mesh/links', (_req, res) => {
    res.json(getMeshLinks());
  });

  app.get('/authority-map', (_req, res) => {
    res.json(getAuthorityMap());
  });

  app.get('/authority/flows', (req, res) => {
    res.json(getAuthorityFlows({
      actor: typeof req.query.actor === 'string' ? req.query.actor : null,
      resource: typeof req.query.resource === 'string' ? req.query.resource : null,
    }));
  });

  app.get('/memory/events', (req, res) => {
    res.json({ events: getMemoryEvents({
      commit: typeof req.query.commit === 'string' ? req.query.commit : null,
      topic: typeof req.query.topic === 'string' ? req.query.topic : null,
    }) });
  });

  app.get('/memory/episode/:id', (req, res) => {
    const episode = getMemoryEpisode(String(req.params.id));
    if (!episode) {
      res.status(404).json({ error: 'memory episode not found' });
      return;
    }
    res.json(episode);
  });

  app.get('/memory/narratives', (req, res) => {
    res.json({ narratives: getMemoryNarratives({ topic: typeof req.query.topic === 'string' ? req.query.topic : null }) });
  });

  app.get('/validate', (_req, res) => {
    const validation = validateCoriAlphaStore();
    const summary = syncCoriAlphaSummary();
    res.json({
      validation,
      summary,
    });
  });

  app.post('/dropbox/validate', (_req, res) => {
    const validation = validateCoriAlphaStore();
    const summary = syncCoriAlphaSummary();
    res.json({
      status: validation.valid ? 'pass' : 'fail',
      validation,
      summary,
    });
  });

  app.get('/trust/relationships', (req, res) => {
    const relationships = listTrustRelationships({
      domain: typeof req.query.domain === 'string' ? req.query.domain : null,
      tier: typeof req.query.tier === 'string' ? req.query.tier : null,
      trustBand: normalizeTrustBand(req.query.trustBand),
    });
    const trustScoreTotal = relationships.reduce((sum, relationship) => sum + relationship.trustResult.score, 0);
    res.json({
      relationships,
      summary: {
        count: relationships.length,
        highTrustCount: relationships.filter((relationship) => relationship.trustResult.band === 'high').length,
        averageTrustScore: relationships.length > 0 ? Number((trustScoreTotal / relationships.length).toFixed(4)) : null,
      },
    });
  });

  app.get('/trust/relationships/:relationshipId/timeline', (req, res) => {
    const relationship = getTrustRelationship(String(req.params.relationshipId));
    if (!relationship) {
      res.status(404).json({ error: 'trust relationship not found' });
      return;
    }

    res.json({
      relationshipId: relationship.relationshipId,
      trustPacket: relationship.trustPacket,
      revisions: relationship.revisions,
      receipts: relationship.receipts,
    });
  });

  app.get('/trust/artifacts/:artifactId', (req, res) => {
    const artifact = getTrustArtifact(String(req.params.artifactId));
    if (!artifact) {
      res.status(404).json({ error: 'trust artifact not found' });
      return;
    }

    res.json({
      artifact,
      continuity: getContinuityOverview(),
    });
  });

  app.get('/trust/artifacts/:artifactId/receipts', (req, res) => {
    const receipts = getTrustReceipts(String(req.params.artifactId));
    if (receipts.length === 0) {
      res.status(404).json({ error: 'trust receipts not found' });
      return;
    }
    res.json({ receipts });
  });

  app.get('/trust/governance/:relationshipId', (req, res) => {
    const view = getTrustGovernanceView(String(req.params.relationshipId));
    if (!view) {
      res.status(404).json({ error: 'trust governance view not found' });
      return;
    }
    res.json(view);
  });

  app.post('/trust/debug/:artifactId', asyncHandler(async (req, res) => {
    const report = debugTrustArtifact(String(req.params.artifactId), {
      confidence: typeof req.body?.confidence === 'number' ? req.body.confidence : undefined,
      authorityLevel: typeof req.body?.authorityLevel === 'number' ? req.body.authorityLevel : undefined,
      evidenceStrength: typeof req.body?.evidenceStrength === 'number' ? req.body.evidenceStrength : undefined,
      evidenceIds: Array.isArray(req.body?.evidenceIds) ? req.body.evidenceIds.filter((entry: unknown): entry is string => typeof entry === 'string') : undefined,
      authorityChain: Array.isArray(req.body?.authorityChain) ? req.body.authorityChain.filter((entry: unknown): entry is string => typeof entry === 'string') : undefined,
    });
    if (!report) {
      res.status(404).json({ error: 'trust artifact not found' });
      return;
    }
    res.json({ report, continuity: getContinuityOverview() });
  }));

  app.get('/governance/config', (req, res) => {
    const config = getGovernanceConfigSnapshot({
      domain: typeof req.query.domain === 'string' ? req.query.domain : null,
      tier: typeof req.query.tier === 'string' ? req.query.tier : null,
      version: typeof req.query.version === 'string' ? req.query.version : null,
    }) ?? getCurrentGovernanceConfig();

    res.json({
      configVersion: config.configVersion,
      domain: config.domain,
      tier: config.tier,
      thresholds: config.thresholds,
      algebraWeights: config.algebraWeights,
      delegationRules: config.delegationRules,
      trustPolicy: config.trustPolicy,
    });
  });

  app.post('/governance/evaluate', (req, res) => {
    const trustPacket = req.body?.trustPacket;
    if (!trustPacket || typeof trustPacket !== 'object') {
      res.status(400).json({ error: 'trustPacket is required' });
      return;
    }

    const result = evaluateGovernanceAction({
      actionId: String(req.body?.actionId ?? 'action-unknown'),
      actionType: req.body?.actionType === 'promotion' || req.body?.actionType === 'delegation' || req.body?.actionType === 'deployment' || req.body?.actionType === 'audit'
        ? req.body.actionType
        : 'routing',
      actorId: String(req.body?.actorId ?? 'steward-unknown'),
      relationshipId: typeof req.body?.relationshipId === 'string' ? req.body.relationshipId : null,
      domain: req.body?.domain === 'ops' || req.body?.domain === 'safety' || req.body?.domain === 'finance' || req.body?.domain === 'compliance' || req.body?.domain === 'global'
        ? req.body.domain
        : 'global',
      trustPacket,
      context: typeof req.body?.context === 'object' && req.body.context ? req.body.context : {},
    });

    res.json(result);
  });

  app.post('/governance/decision', (req, res) => {
    const trustPacket = req.body?.trustPacket;
    if (!trustPacket || typeof trustPacket !== 'object') {
      res.status(400).json({ error: 'trustPacket is required' });
      return;
    }

    const record = recordGovernanceDecision({
      decisionId: String(req.body?.decisionId ?? `decision-${Date.now().toString(36)}`),
      actionId: String(req.body?.actionId ?? 'action-unknown'),
      actionType: req.body?.actionType === 'promotion' || req.body?.actionType === 'delegation' || req.body?.actionType === 'deployment' || req.body?.actionType === 'audit'
        ? req.body.actionType
        : 'routing',
      result: req.body?.result === 'warning' ? 'warning' : req.body?.result === 'blocked' ? 'blocked' : 'allowed',
      tier: String(req.body?.tier ?? 'core'),
      domain: req.body?.domain === 'ops' || req.body?.domain === 'safety' || req.body?.domain === 'finance' || req.body?.domain === 'compliance' || req.body?.domain === 'global'
        ? req.body.domain
        : 'global',
      trustPacket,
      reason: String(req.body?.reason ?? 'decision recorded by sovereign control plane'),
      constraintsApplied: Array.isArray(req.body?.constraintsApplied) ? req.body.constraintsApplied.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
      decidedBy: String(req.body?.decidedBy ?? 'kernel-1'),
      decidedAt: typeof req.body?.decidedAt === 'string' ? req.body.decidedAt : new Date().toISOString(),
    });

    res.json({
      ledgerEntryId: record.ledgerEntryId,
      hash: record.hash,
      signature: record.signature,
      decision: record,
    });
  });

  app.post('/router/evaluate', (req, res) => {
    const trustPacket = req.body?.trustPacket;
    const routeEvaluation = req.body?.routeEvaluation ?? req.body?.evaluation?.routing?.routeEvaluation;
    if (!trustPacket || typeof trustPacket !== 'object') {
      res.status(400).json({ error: 'trustPacket is required' });
      return;
    }
    if (!routeEvaluation || typeof routeEvaluation !== 'object') {
      res.status(400).json({ error: 'routeEvaluation is required' });
      return;
    }

    try {
      const domain = normalizeTrustDomain(req.body?.domain) ?? 'global';
      const governanceConfig = getGovernanceConfigSnapshot({
        domain,
        tier: typeof req.body?.tier === 'string' ? req.body.tier : null,
        version: typeof req.body?.configVersion === 'string' ? req.body.configVersion : null,
      }) ?? getCurrentGovernanceConfig();
      const governanceKernelResult = evaluateGovernanceAction({
        actionId: String(req.body?.actionId ?? req.body?.requestId ?? `route-${Date.now().toString(36)}`),
        actionType: 'routing',
        actorId: String(req.body?.actorId ?? 'router-x'),
        relationshipId: typeof req.body?.relationshipId === 'string' ? req.body.relationshipId : null,
        domain,
        trustPacket,
        context: typeof req.body?.context === 'object' && req.body.context ? req.body.context : {},
      });

      const routeDecisionArtifact = buildRouteDecisionArtifact({
        artifactId: String(req.body?.artifactId ?? req.body?.requestId ?? `route-${Date.now().toString(36)}`),
        requestId: String(req.body?.requestId ?? routeEvaluation.workItem?.id ?? req.body?.artifactId ?? `route-${Date.now().toString(36)}`),
        orgId: String(req.body?.orgId ?? trustPacket.subjectId ?? 'org-unknown'),
        customerId: typeof req.body?.customerId === 'string' ? req.body.customerId : undefined,
        relationshipId: typeof trustPacket.relationshipId === 'string' ? trustPacket.relationshipId : String(req.body?.relationshipId ?? 'relationship-unknown'),
        trustPacket,
        trustPolicy: governanceConfig.trustPolicy,
        routeEvaluation,
        provenance: {
          originSystem: 'sovereign-control-plane/router-evaluate',
          originActorId: String(req.body?.actorId ?? 'router-x'),
          method: 'router-evaluate',
          standardsTraceabilityIds: Array.isArray(req.body?.standardsTraceabilityIds)
            ? req.body.standardsTraceabilityIds.filter((entry: unknown): entry is string => typeof entry === 'string')
            : ['cis.router.route-decision', 'cis.governance.kernel'],
        },
        decidedBy: String(req.body?.decidedBy ?? 'governance-kernel'),
        decidedAt: typeof req.body?.decidedAt === 'string' ? req.body.decidedAt : new Date().toISOString(),
        configVersion: governanceConfig.configVersion,
        replay: typeof req.body?.replay === 'object' && req.body.replay ? req.body.replay : undefined,
        signingSecret: typeof req.body?.signingSecret === 'string' ? req.body.signingSecret : undefined,
        signer: String(req.body?.signer ?? 'sovereign-control-plane'),
      });

      const governanceDecision = recordGovernanceDecision({
        decisionId: String(req.body?.decisionId ?? `decision-${Date.now().toString(36)}`),
        actionId: String(req.body?.actionId ?? req.body?.requestId ?? `route-${Date.now().toString(36)}`),
        actionType: 'routing',
        result: routeDecisionArtifact.governance.result,
        tier: routeDecisionArtifact.governance.tier,
        domain,
        trustPacket,
        reason: routeDecisionArtifact.governance.reason,
        constraintsApplied: routeDecisionArtifact.governance.constraintsApplied,
        decidedBy: routeDecisionArtifact.governance.decidedBy,
        decidedAt: routeDecisionArtifact.governance.decidedAt,
      });

      const replayReportId = routeDecisionArtifact.replay?.report && typeof routeDecisionArtifact.replay.report === 'object' && routeDecisionArtifact.replay.report
        && 'replayId' in routeDecisionArtifact.replay.report
        ? String((routeDecisionArtifact.replay.report as { replayId?: string }).replayId ?? '')
        : null;
      const record = recordRouteDecision({
        decisionId: routeDecisionArtifact.artifactId,
        requestId: routeDecisionArtifact.requestId,
        orgId: routeDecisionArtifact.orgId,
        customerId: routeDecisionArtifact.customerId,
        artifact: routeDecisionArtifact,
        trustPacket,
        governanceDecision,
        replayReportId: replayReportId || null,
        createdAt: routeDecisionArtifact.createdAt,
      });

      res.status(201).json({
        routeDecisionArtifact,
        governanceDecision,
        governanceConfig,
        record,
        governanceKernelResult,
      });
    } catch (error) {
      res.status(400).json({
        error: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.get('/router/decisions', (_req, res) => {
    res.json({
      decisions: listRouteDecisions(),
      summary: {
        count: listRouteDecisions().length,
      },
    });
  });

  app.get('/router/decisions/:decisionId', (req, res) => {
    const decision = getRouteDecision(String(req.params.decisionId));
    if (!decision) {
      res.status(404).json({ error: 'route decision not found' });
      return;
    }
    res.json(decision);
  });

  app.post('/governance/proposals', (req, res) => {
    try {
      const affectedDomains = Array.isArray(req.body?.affectedDomains)
        ? req.body.affectedDomains.filter((entry: unknown): entry is TrustDomain => normalizeTrustDomain(entry) !== null)
        : ['global'];

      const proposal = createGovernanceProposal({
        proposalId: String(req.body?.proposalId ?? `proposal-${Date.now().toString(36)}`),
        createdAt: typeof req.body?.createdAt === 'string' ? req.body.createdAt : new Date().toISOString(),
        createdByStewardId: String(req.body?.createdByStewardId ?? 'steward-1'),
        motivation: {
          summary: String(req.body?.motivation?.summary ?? 'No motivation provided'),
          linkedDecisionIds: Array.isArray(req.body?.motivation?.linkedDecisionIds) ? req.body.motivation.linkedDecisionIds.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
          linkedFeedbackIds: Array.isArray(req.body?.motivation?.linkedFeedbackIds) ? req.body.motivation.linkedFeedbackIds.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
          linkedReplayReportIds: Array.isArray(req.body?.motivation?.linkedReplayReportIds) ? req.body.motivation.linkedReplayReportIds.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
          externalPolicyReferences: Array.isArray(req.body?.motivation?.externalPolicyReferences) ? req.body.motivation.externalPolicyReferences.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
        },
        currentConfigVersion: String(req.body?.currentConfigVersion ?? getCurrentGovernanceConfig().configVersion),
        targetConfigVersion: String(req.body?.targetConfigVersion ?? `${getCurrentGovernanceConfig().configVersion}-proposed`),
        affectedDomains,
        affectedTiers: Array.isArray(req.body?.affectedTiers) ? req.body.affectedTiers.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
        affectedDelegationChains: Array.isArray(req.body?.affectedDelegationChains) ? req.body.affectedDelegationChains.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
        affectedTrustAlgebraComponents: Array.isArray(req.body?.affectedTrustAlgebraComponents) ? req.body.affectedTrustAlgebraComponents.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
        affectedConformanceRules: Array.isArray(req.body?.affectedConformanceRules) ? req.body.affectedConformanceRules.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
        proposedChanges: Array.isArray(req.body?.proposedChanges) ? req.body.proposedChanges.map((change: Record<string, unknown>) => ({
          path: String(change.path ?? '$'),
          operation: change.operation === 'add' || change.operation === 'retire' ? change.operation : 'modify',
          before: change.before,
          after: change.after,
          retirementMarker: typeof change.retirementMarker === 'string' ? change.retirementMarker : undefined,
        })) : [],
        riskAssessment: {
          impactLevel: req.body?.riskAssessment?.impactLevel === 'low' || req.body?.riskAssessment?.impactLevel === 'medium' || req.body?.riskAssessment?.impactLevel === 'high' || req.body?.riskAssessment?.impactLevel === 'critical'
            ? req.body.riskAssessment.impactLevel
            : 'medium',
          notes: String(req.body?.riskAssessment?.notes ?? ''),
        },
      });
      res.status(201).json({ status: proposal.status, proposalId: proposal.proposalId, proposal });
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.post('/governance/proposals/:proposalId/review', (req, res) => {
    try {
      const result = reviewGovernanceProposal({
        proposalId: String(req.params.proposalId),
        reviewerStewardId: String(req.body?.reviewerStewardId ?? 'steward-1'),
        action: req.body?.action === 'approve' || req.body?.action === 'reject' ? req.body.action : 'request_changes',
        notes: String(req.body?.notes ?? ''),
      });
      res.json(result);
    } catch (error) {
      res.status(404).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.get('/governance/timeline', (_req, res) => {
    res.json({ events: listGovernanceTimeline(), overview: getContinuityOverview() });
  });

  app.post('/replay/sessions', (req, res) => {
    const session = startReplaySession({
      mode: normalizeReplayMode(req.body?.mode),
      scope: normalizeReplayScope(req.body?.scope),
      configVersionUsed: String(req.body?.configVersionUsed ?? getCurrentGovernanceConfig().configVersion),
      timeRange: {
        start: String(req.body?.timeRange?.start ?? new Date().toISOString()),
        end: String(req.body?.timeRange?.end ?? new Date().toISOString()),
      },
      relationshipIds: Array.isArray(req.body?.relationshipIds) ? req.body.relationshipIds.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
      decisionIds: Array.isArray(req.body?.decisionIds) ? req.body.decisionIds.filter((entry: unknown): entry is string => typeof entry === 'string') : [],
    });

    res.status(201).json({
      replayId: session.replayId,
      report: session.report,
      validation: session.validation,
      contract: session.contract,
    });
  });

  app.get('/replay/sessions/:replayId', (req, res) => {
    const session = getReplaySession(String(req.params.replayId));
    if (!session) {
      res.status(404).json({ error: 'replay session not found' });
      return;
    }
    res.json(session);
  });

  app.get('/replay/reports/:replayId', (req, res) => {
    const report = getReplayReport(String(req.params.replayId));
    if (!report) {
      res.status(404).json({ error: 'replay report not found' });
      return;
    }
    res.json(report);
  });

  app.get('/replay/timeline', (_req, res) => {
    res.json(getReplayTimeline());
  });

  app.get('/replay/:commit', (req, res) => {
    res.json(getReplaySnapshot(String(req.params.commit)));
  });

  app.get('/replay', (_req, res) => {
    res.json({
      sessions: getSovereignControlPlaneState().replaySessions.map((session) => ({
        replayId: session.replayId,
        scope: session.request.scope,
        mode: session.request.mode,
        configVersionUsed: session.request.configVersionUsed,
      })),
    });
  });
}
