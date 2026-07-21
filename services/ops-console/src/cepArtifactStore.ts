import crypto from 'node:crypto';
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

export type CepArtifactKind = 'promotion-request' | 'replay-job' | 'decision';

export interface CepArtifactRecord<TPayload = unknown> {
  id: string;
  kind: CepArtifactKind;
  title: string;
  source: string;
  organizationId?: string;
  relatedArtifactId?: string;
  recordedAt: string;
  signature?: string;
  payload: TPayload;
}

export interface CepArtifactStoreOptions {
  filePath?: string;
  env?: NodeJS.ProcessEnv;
}

export interface CepArtifactSummary {
  available: boolean;
  storePath: string;
  entryCount: number;
  countsByKind: Record<CepArtifactKind, number>;
  latestByKind: Record<CepArtifactKind, CepArtifactRecord | null>;
  recentRecords: CepArtifactRecord[];
  organizationId?: string | null;
}

export interface CepArtifactExport {
  storePath: string;
  entryCount: number;
  countsByKind: Record<CepArtifactKind, number>;
  records: CepArtifactRecord[];
  recentRecords: CepArtifactRecord[];
  organizationId?: string | null;
}

const CEP_ARTIFACT_KINDS: CepArtifactKind[] = ['promotion-request', 'replay-job', 'decision'];

export class CepArtifactStore {
  private readonly env: NodeJS.ProcessEnv;
  private readonly filePath?: string;

  constructor(options: CepArtifactStoreOptions = {}) {
    this.env = options.env ?? process.env;
    this.filePath = options.filePath;
  }

  append(
    record: Omit<CepArtifactRecord, 'id' | 'recordedAt'> & { id?: string; recordedAt?: string },
  ): CepArtifactRecord {
    const storePath = this.resolveStorePath();
    ensureParentDirectory(storePath);
    const records = this.list(storePath);
    const payloadSignature = extractPayloadSignature(record.payload);
    if (record.signature && payloadSignature && record.signature !== payloadSignature) {
      throw new Error('Conflicting audit packet signatures');
    }
    const signature = record.signature ?? payloadSignature;
    const nextSignature = validateCanonicalPayload(record.payload, signature);
    const nextRecord: CepArtifactRecord = {
      id: record.id?.trim() || `cep-${record.kind}-${(records.length + 1).toString(36)}`,
      kind: record.kind,
      title: record.title,
      source: record.source,
      organizationId: record.organizationId,
      relatedArtifactId: record.relatedArtifactId,
      recordedAt: record.recordedAt ?? new Date().toISOString(),
      signature: nextSignature,
      payload: record.payload,
    };
    appendFileSync(storePath, `${JSON.stringify(nextRecord)}\n`, 'utf8');
    return nextRecord;
  }

  appendPromotionRequest(
    payload: unknown,
    metadata: { title?: string; source?: string; relatedArtifactId?: string; id?: string; recordedAt?: string; signature?: string } = {},
  ): CepArtifactRecord {
    return this.append({
      kind: 'promotion-request',
      title: metadata.title ?? 'Promotion Request',
      source: metadata.source ?? 'ops-console',
      relatedArtifactId: metadata.relatedArtifactId,
      id: metadata.id,
      recordedAt: metadata.recordedAt,
      payload,
    });
  }

  appendReplayJob(
    payload: unknown,
    metadata: { title?: string; source?: string; relatedArtifactId?: string; id?: string; recordedAt?: string; signature?: string } = {},
  ): CepArtifactRecord {
    return this.append({
      kind: 'replay-job',
      title: metadata.title ?? 'Replay Job',
      source: metadata.source ?? 'ops-console',
      relatedArtifactId: metadata.relatedArtifactId,
      id: metadata.id,
      recordedAt: metadata.recordedAt,
      payload,
    });
  }

  appendDecision(
    payload: unknown,
    metadata: { title?: string; source?: string; relatedArtifactId?: string; id?: string; recordedAt?: string; signature?: string } = {},
  ): CepArtifactRecord {
    return this.append({
      kind: 'decision',
      title: metadata.title ?? 'Decision',
      source: metadata.source ?? 'ops-console',
      relatedArtifactId: metadata.relatedArtifactId,
      id: metadata.id,
      recordedAt: metadata.recordedAt,
      payload,
    });
  }

  list(storePath = this.resolveStorePath(), organizationId?: string): CepArtifactRecord[] {
    if (!existsSync(storePath)) {
      return [];
    }

    const content = readFileSync(storePath, 'utf8');
    const records = content
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line) as CepArtifactRecord)
      .filter((record) => isCepArtifactRecord(record));
    return organizationId ? records.filter((record) => record.organizationId === organizationId) : records;
  }

  getArtifact(id: string): CepArtifactRecord | null {
    return this.list().find((record) => record.id === id) ?? null;
  }

  listByKind(kind: CepArtifactKind): CepArtifactRecord[] {
    return this.list().filter((record) => record.kind === kind);
  }

  summary(organizationId?: string): CepArtifactSummary {
    const storePath = this.resolveStorePath();
    const records = this.list(storePath, organizationId);
    const countsByKind = buildKindCounts(records);
    const latestByKind = buildLatestByKind(records);

    return {
      available: records.length > 0,
      storePath,
      entryCount: records.length,
      countsByKind,
      latestByKind,
      recentRecords: records.slice(-8).reverse(),
      organizationId: organizationId ?? null,
    };
  }

  exportJson(organizationId?: string): CepArtifactExport {
    const storePath = this.resolveStorePath();
    const records = this.list(storePath, organizationId);
    return {
      storePath,
      entryCount: records.length,
      countsByKind: buildKindCounts(records),
      records,
      recentRecords: records.slice(-20).reverse(),
      organizationId: organizationId ?? null,
    };
  }

  private resolveStorePath(): string {
    if (this.filePath?.trim()) {
      return path.resolve(this.filePath.trim());
    }

    const envPath = this.env.CEP_ARTIFACT_STORE?.trim();
    if (envPath) {
      return path.resolve(envPath);
    }

    return path.resolve(process.cwd(), '.runtime', 'cep-artifacts.jsonl');
  }
}

export function createCepArtifactStore(options: CepArtifactStoreOptions = {}): CepArtifactStore {
  return new CepArtifactStore(options);
}

export function verifyCepArtifactSignature(record: CepArtifactRecord, publicKeyPem: string): boolean {
  if (!publicKeyPem.trim() || !record.signature || !isCanonicalAuditPacketInput(record.payload)) {
    return false;
  }

  const signedPacket = {
    ...record.payload,
    signature: {
      algorithm: 'Ed25519' as const,
      value: record.signature,
    },
  } as CanonicalAuditPacket;
  return verifyCanonicalAuditPacket(signedPacket, publicKeyPem.trim());
}

function buildKindCounts(records: CepArtifactRecord[]): Record<CepArtifactKind, number> {
  return CEP_ARTIFACT_KINDS.reduce((counts, kind) => {
    counts[kind] = records.filter((record) => record.kind === kind).length;
    return counts;
  }, {} as Record<CepArtifactKind, number>);
}

function buildLatestByKind(records: CepArtifactRecord[]): Record<CepArtifactKind, CepArtifactRecord | null> {
  return CEP_ARTIFACT_KINDS.reduce((latest, kind) => {
    const recordsOfKind = records.filter((record) => record.kind === kind);
    latest[kind] = recordsOfKind.length > 0 ? recordsOfKind[recordsOfKind.length - 1] : null;
    return latest;
  }, {} as Record<CepArtifactKind, CepArtifactRecord | null>);
}

function ensureParentDirectory(storePath: string): void {
  mkdirSync(path.dirname(storePath), { recursive: true });
}

function isCepArtifactRecord(value: unknown): value is CepArtifactRecord {
  return Boolean(
    value &&
      typeof value === 'object' &&
      typeof (value as CepArtifactRecord).id === 'string' &&
      typeof (value as CepArtifactRecord).kind === 'string' &&
      typeof (value as CepArtifactRecord).title === 'string' &&
      typeof (value as CepArtifactRecord).source === 'string' &&
      (typeof (value as CepArtifactRecord).organizationId === 'string' || typeof (value as CepArtifactRecord).organizationId === 'undefined') &&
      (typeof (value as CepArtifactRecord).signature === 'string' || typeof (value as CepArtifactRecord).signature === 'undefined') &&
      typeof (value as CepArtifactRecord).recordedAt === 'string',
  );
}

function extractPayloadSignature(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return undefined;
  }

  const candidate = payload as {
    signature?: {
      algorithm?: string;
      value?: string;
    };
  };
  if (candidate.signature?.algorithm !== 'Ed25519') {
    return undefined;
  }
  if (typeof candidate.signature.value !== 'string' || candidate.signature.value.trim().length === 0) {
    return undefined;
  }
  return candidate.signature.value;
}

function validateCanonicalPayload(payload: unknown, signature: string | undefined): string | undefined {
  if (!isCanonicalAuditPacketInput(payload)) {
    return signature;
  }

  if (!signature) {
    throw new Error('Missing signature for canonical audit packet');
  }

  const signedPacket = {
    ...payload,
    signature: {
      algorithm: 'Ed25519' as const,
      value: signature,
    },
  } as CanonicalAuditPacket;
  validateCanonicalAuditPacket(signedPacket);
  const publicKey = process.env.AUDIT_PUBLIC_KEY ?? process.env.AUDIT_PUBLIC_KEY_PEM;
  if (publicKey?.trim() && !verifyCanonicalAuditPacket(signedPacket, publicKey.trim())) {
    throw new Error('Invalid canonical audit packet signature');
  }

  return signature;
}

type CanonicalAuditPacketInput = {
  version: '1.0';
  packetId: string;
  orgId: string;
  customerId?: string;
  requestId: string;
  createdAt: string;
  domain: 'pricing' | 'routing' | 'entitlements';
  input: {
    prompt?: string;
    context?: unknown;
  };
  policy: {
    id: string;
    name: string;
    dsl: string;
    compiledConstraints: unknown;
  };
  decision: {
    modelId: string;
    outcome: unknown;
    scores?: unknown;
  };
  governance: {
    level: string;
    conformanceStatus?: string;
    driftRisk?: string;
    lineageDepth?: number;
  };
  treasury?: {
    price?: number;
    currency?: string;
    reserves?: unknown;
  };
};

type CanonicalAuditPacket = CanonicalAuditPacketInput & {
  signature: {
    algorithm: 'Ed25519';
    value: string;
  };
};

function isCanonicalAuditPacketInput(value: unknown): value is CanonicalAuditPacketInput {
  if (!isRecord(value)) {
    return false;
  }

  return Boolean(
    value.version === '1.0' &&
      typeof value.packetId === 'string' &&
      typeof value.orgId === 'string' &&
      typeof value.requestId === 'string' &&
      typeof value.createdAt === 'string' &&
      typeof value.domain === 'string' &&
      isRecord(value.input) &&
      isRecord(value.policy) &&
      isRecord(value.decision) &&
      isRecord(value.governance),
  );
}

function verifyCanonicalAuditPacket(packet: CanonicalAuditPacket, publicKeyPem: string): boolean {
  const { signature, ...unsignedPacket } = packet;
  return crypto.verify(null, Buffer.from(canonicalizeJson(unsignedPacket)), publicKeyPem, Buffer.from(signature.value, 'base64'));
}

function validateCanonicalAuditPacket(packet: CanonicalAuditPacket): void {
  if (!isCanonicalAuditPacketInput(packet)) {
    throw new Error('Invalid canonical audit packet');
  }
  if (!packet.signature || packet.signature.algorithm !== 'Ed25519') {
    throw new Error('Invalid signature algorithm');
  }
  if (typeof packet.signature.value !== 'string' || packet.signature.value.trim().length === 0) {
    throw new Error('Missing signature value');
  }
  if (!isBase64Like(packet.signature.value)) {
    throw new Error('Signature is not valid base64');
  }
}

function canonicalizeJson(value: unknown): string {
  const normalized = normalizeJsonValue(value);
  const json = JSON.stringify(normalized);
  if (json === undefined) {
    throw new TypeError('Cannot verify an undefined audit payload');
  }
  return json;
}

function normalizeJsonValue(value: unknown, seen = new WeakSet<object>()): unknown {
  if (value instanceof Date) {
    return value.toISOString();
  }
  if (typeof value === 'bigint' || typeof value === 'symbol' || typeof value === 'function') {
    throw new TypeError('Unsupported audit payload value');
  }
  if (value === null || typeof value !== 'object') {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map((item) => normalizeJsonValue(item, seen));
  }

  if (seen.has(value)) {
    throw new TypeError('Cannot verify cyclic audit payloads');
  }
  seen.add(value);

  const normalized: Record<string, unknown> = {};
  for (const key of Object.keys(value).sort()) {
    normalized[key] = normalizeJsonValue((value as Record<string, unknown>)[key], seen);
  }

  seen.delete(value);
  return normalized;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function isBase64Like(value: string): boolean {
  return /^[A-Za-z0-9+/]+={0,2}$/.test(value) && value.length % 4 === 0;
}
