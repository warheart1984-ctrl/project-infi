import { createServer, type IncomingMessage, type Server, type ServerResponse } from 'node:http';

import type { Artifact, Embedding, Glyph, LineageEvent, Organism, UgrJsonValue } from './models.js';
import type { UgrGraphStorage } from './storage/graph.js';
import type { UgrSqlStorage } from './storage/sql.js';
import type { UgrVectorStorage } from './storage/vector.js';

export interface UgrApiDependencies {
  sql: UgrSqlStorage;
  graph: UgrGraphStorage;
  vector: UgrVectorStorage;
}

export interface UgrGrpcMethodDescriptor {
  name: string;
  requestType: string;
  responseType: string;
}

export interface UgrApiRouteDescriptor {
  method: 'GET' | 'POST';
  path: string;
  description: string;
}

export interface UgrReplayRepeatCheck {
  objective: string;
  constitutional_context: Record<string, UgrJsonValue>;
  divergence_reason?: string;
}

export interface UgrReplayRepeatDecision {
  has_replayable_result: boolean;
  should_repeat_experiment: boolean;
  reason: 'replayable_result_exists' | 'declared_divergence' | 'no_replayable_result';
  matched_source_id?: string;
}

export class UgrApi {
  constructor(private readonly deps: UgrApiDependencies) {}

  async listGlyphs(): Promise<Glyph[]> {
    return this.deps.sql.fetch_all_glyphs();
  }

  async getGlyph(glyph_id: string): Promise<Glyph | undefined> {
    return (await this.listGlyphs()).find((glyph) => glyph.glyph_id === glyph_id);
  }

  async putGlyph(glyph: Glyph): Promise<Glyph> {
    await this.deps.sql.upsert_glyph(glyph);
    await this.deps.graph.registerGlyph(glyph);
    return glyph;
  }

  async listArtifacts(domain: string): Promise<Artifact[]> {
    return this.deps.sql.fetch_artifacts(domain);
  }

  async putArtifact(artifact: Artifact): Promise<Artifact> {
    await this.deps.sql.upsert_artifact(artifact);
    await this.deps.graph.registerArtifact(artifact);
    return artifact;
  }

  async queryEmbeddings(vector: readonly number[], k: number): Promise<Embedding[]> {
    return this.deps.vector.query_neighbors(vector, k);
  }

  async putEmbedding(embedding: Embedding): Promise<Embedding> {
    await this.deps.vector.store_embedding(embedding);
    return embedding;
  }

  async getLineage(world_id: string): Promise<LineageEvent[]> {
    return this.deps.sql.fetch_lineage(world_id);
  }

  async putLineageEvent(event: LineageEvent): Promise<LineageEvent> {
    await this.deps.sql.insert_lineage_event(event);
    await this.deps.graph.registerEvent(event);
    await this.deps.graph.link_event_to_world(event.event_id, event.world_id);
    return event;
  }

  async getOrganism(id: string): Promise<Organism | undefined> {
    return this.deps.sql.fetch_organism(id);
  }

  async putOrganism(organism: Organism): Promise<Organism> {
    await this.deps.sql.upsert_organism(organism);
    await this.deps.graph.registerOrganism(organism);
    return organism;
  }

  async hasReplayableResult(check: UgrReplayRepeatCheck): Promise<boolean> {
    return (await this.findReplayableMatch(check)) !== undefined;
  }

  async shouldRepeatExperiment(check: UgrReplayRepeatCheck): Promise<UgrReplayRepeatDecision> {
    if (check.divergence_reason && check.divergence_reason.trim().length > 0) {
      const matched = await this.findReplayableMatch(check);
      return {
        has_replayable_result: matched !== undefined,
        should_repeat_experiment: true,
        reason: 'declared_divergence',
        matched_source_id: matched?.source_id,
      };
    }

    const match = await this.findReplayableMatch(check);
    if (match) {
      return {
        has_replayable_result: true,
        should_repeat_experiment: false,
        reason: 'replayable_result_exists',
        matched_source_id: match.source_id,
      };
    }

    return {
      has_replayable_result: false,
      should_repeat_experiment: true,
      reason: 'no_replayable_result',
    };
  }

  async assertExperimentMayRun(check: UgrReplayRepeatCheck): Promise<void> {
    const decision = await this.shouldRepeatExperiment(check);
    if (!decision.should_repeat_experiment) {
      throw new Error(
        `Replayable result already exists for objective "${check.objective}" in the same constitutional context`,
      );
    }
  }

  getRoutes(): readonly UgrApiRouteDescriptor[] {
    return [
      { method: 'GET', path: '/ugr/v1/glyphs', description: 'List glyphs' },
      { method: 'GET', path: '/ugr/v1/glyphs/{glyph_id}', description: 'Fetch a glyph' },
      { method: 'POST', path: '/ugr/v1/glyphs', description: 'Upsert a glyph' },
      { method: 'GET', path: '/ugr/v1/constitution/artifacts', description: 'List artifacts' },
      { method: 'POST', path: '/ugr/v1/constitution/artifacts', description: 'Upsert an artifact' },
      { method: 'POST', path: '/ugr/v1/embeddings/query', description: 'Query vector neighbors' },
      { method: 'POST', path: '/ugr/v1/embeddings', description: 'Upsert an embedding' },
      { method: 'GET', path: '/ugr/v1/lineage/world/{world_id}', description: 'Fetch lineage events' },
      { method: 'POST', path: '/ugr/v1/lineage/events', description: 'Insert lineage event' },
      { method: 'GET', path: '/ugr/v1/organisms/{id}', description: 'Fetch organism' },
      { method: 'POST', path: '/ugr/v1/organisms', description: 'Upsert organism' },
      { method: 'POST', path: '/ugr/v1/replay/check', description: 'Check replay-vs-repeat invariant' },
    ];
  }

  getGrpcService(): readonly UgrGrpcMethodDescriptor[] {
    return [
      { name: 'GetGlyphs', requestType: 'Empty', responseType: 'GlyphList' },
      { name: 'GetGlyph', requestType: 'GlyphRef', responseType: 'Glyph' },
      { name: 'PutGlyph', requestType: 'Glyph', responseType: 'Glyph' },
      { name: 'GetArtifacts', requestType: 'ArtifactQuery', responseType: 'ArtifactList' },
      { name: 'PutArtifact', requestType: 'Artifact', responseType: 'Artifact' },
      { name: 'QueryEmbeddings', requestType: 'EmbeddingQuery', responseType: 'EmbeddingList' },
      { name: 'PutEmbedding', requestType: 'Embedding', responseType: 'Embedding' },
      { name: 'GetLineage', requestType: 'WorldRef', responseType: 'LineageEventList' },
      { name: 'PutLineageEvent', requestType: 'LineageEvent', responseType: 'LineageEvent' },
      { name: 'GetOrganism', requestType: 'OrganismRef', responseType: 'Organism' },
      { name: 'PutOrganism', requestType: 'Organism', responseType: 'Organism' },
      { name: 'HasReplayableResult', requestType: 'ReplayRepeatCheck', responseType: 'BooleanResult' },
      { name: 'ShouldRepeatExperiment', requestType: 'ReplayRepeatCheck', responseType: 'ReplayRepeatDecision' },
    ];
  }

  private async findReplayableMatch(check: UgrReplayRepeatCheck): Promise<{ source_id: string } | undefined> {
    const matches = [
      ...(await this.deps.sql.fetch_all_artifacts()).map((artifact) => ({
        source_id: artifact.artifact_id,
        payload: artifact.conditions,
      })),
      ...(await this.deps.sql.fetch_all_lineage()).map((event) => ({
        source_id: event.event_id,
        payload: event.outcome,
      })),
    ];

    return matches.find((entry) => isReplayablePayload(entry.payload, check));
  }
}

export function createUgrHttpServer(api: UgrApi): Server {
  return createServer(async (req, res) => {
    await handleUgrRequest(api, req, res);
  });
}

export async function handleUgrRequest(api: UgrApi, req: IncomingMessage, res: ServerResponse): Promise<void> {
  const method = req.method ?? 'GET';
  const url = new URL(req.url ?? '/', 'http://localhost');
  try {
    const body = method === 'POST' ? await readJsonBody(req) : undefined;
    const payload = await routeUgrRequest(api, method, url, body);
    writeJson(res, 200, payload);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown UGR API error';
    writeJson(res, 400, { error: message });
  }
}

async function routeUgrRequest(api: UgrApi, method: string, url: URL, body: unknown): Promise<unknown> {
  const { pathname } = url;
  if (method === 'GET' && pathname === '/ugr/v1/glyphs') {
    return { glyphs: await api.listGlyphs() };
  }
  if (method === 'GET' && pathname.startsWith('/ugr/v1/glyphs/')) {
    const glyphId = decodeURIComponent(pathname.slice('/ugr/v1/glyphs/'.length));
    return { glyph: (await api.getGlyph(glyphId)) ?? null };
  }
  if (method === 'POST' && pathname === '/ugr/v1/glyphs') {
    return api.putGlyph(assertRecord<Glyph>(body, 'glyph'));
  }
  if (method === 'GET' && pathname === '/ugr/v1/constitution/artifacts') {
    const domain = url.searchParams.get('domain') ?? '';
    return { artifacts: await api.listArtifacts(domain) };
  }
  if (method === 'POST' && pathname === '/ugr/v1/constitution/artifacts') {
    return api.putArtifact(assertRecord<Artifact>(body, 'artifact'));
  }
  if (method === 'POST' && pathname === '/ugr/v1/embeddings/query') {
    const input = assertRecord(body, 'embedding query');
    return { embeddings: await api.queryEmbeddings(assertNumberArray(input.vector), Number(input.k ?? 0)) };
  }
  if (method === 'POST' && pathname === '/ugr/v1/embeddings') {
    return api.putEmbedding(assertRecord<Embedding>(body, 'embedding'));
  }
  if (method === 'GET' && pathname.startsWith('/ugr/v1/lineage/world/')) {
    const worldId = decodeURIComponent(pathname.slice('/ugr/v1/lineage/world/'.length));
    return { lineage: await api.getLineage(worldId) };
  }
  if (method === 'POST' && pathname === '/ugr/v1/lineage/events') {
    return api.putLineageEvent(assertRecord<LineageEvent>(body, 'lineage event'));
  }
  if (method === 'GET' && pathname.startsWith('/ugr/v1/organisms/')) {
    const organismId = decodeURIComponent(pathname.slice('/ugr/v1/organisms/'.length));
    return { organism: (await api.getOrganism(organismId)) ?? null };
  }
  if (method === 'POST' && pathname === '/ugr/v1/organisms') {
    return api.putOrganism(assertRecord<Organism>(body, 'organism'));
  }
  if (method === 'POST' && pathname === '/ugr/v1/replay/check') {
    return api.shouldRepeatExperiment(assertRecord<UgrReplayRepeatCheck>(body, 'replay repeat check'));
  }

  if (method === 'GET' && pathname === '/health') {
    return { ok: true };
  }

  throw new Error(`No UGR route for ${method} ${pathname}`);
}

async function readJsonBody(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  const raw = Buffer.concat(chunks).toString('utf8').trim();
  return raw ? JSON.parse(raw) : {};
}

function writeJson(res: ServerResponse, statusCode: number, value: unknown): void {
  res.statusCode = statusCode;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.end(`${JSON.stringify(value)}\n`);
}

function assertRecord<T extends object = Record<string, unknown>>(value: unknown, label: string): T {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`Expected ${label} to be an object`);
  }
  return value as T;
}

function assertNumberArray(value: unknown): number[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'number')) {
    throw new Error('Expected vector to be an array of numbers');
  }
  return value;
}

function isReplayablePayload(
  payload: Record<string, UgrJsonValue>,
  check: UgrReplayRepeatCheck,
): boolean {
  return (
    payload.objective === check.objective &&
    jsonValueEquals(payload.constitutional_context, check.constitutional_context) &&
    isTruthy(payload.replayable_result ?? payload.replayable ?? false) &&
    hasEvidence(payload)
  );
}

function hasEvidence(payload: Record<string, UgrJsonValue>): boolean {
  const evidenceIds = payload.evidence_ids;
  if (Array.isArray(evidenceIds) && evidenceIds.length > 0) {
    return true;
  }
  return typeof payload.evidence_ref === 'string' && payload.evidence_ref.trim().length > 0;
}

function isTruthy(value: UgrJsonValue | undefined): boolean {
  return value === true;
}

function jsonValueEquals(left: UgrJsonValue | undefined, right: UgrJsonValue): boolean {
  if (left === right) {
    return true;
  }
  if (Array.isArray(left) && Array.isArray(right)) {
    return left.length === right.length && left.every((entry, index) => jsonValueEquals(entry, right[index]!));
  }
  if (left && right && typeof left === 'object' && typeof right === 'object') {
    const leftEntries = Object.entries(left as Record<string, UgrJsonValue>);
    const rightRecord = right as Record<string, UgrJsonValue>;
    const rightKeys = Object.keys(rightRecord);
    if (leftEntries.length !== rightKeys.length) {
      return false;
    }
    return leftEntries.every(([key, value]) => Object.prototype.hasOwnProperty.call(rightRecord, key) && jsonValueEquals(value, rightRecord[key]));
  }
  return false;
}
