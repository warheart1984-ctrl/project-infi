import type { CanonicalAuditPacket, CanonicalAuditPacketInput } from './schema.js';

export class AuditPacketValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuditPacketValidationError';
  }
}

export function isCanonicalAuditPacketInput(value: unknown): value is CanonicalAuditPacketInput {
  return isCanonicalAuditPacketInputShape(value);
}

export function isCanonicalAuditPacket(value: unknown): value is CanonicalAuditPacket {
  if (!isCanonicalAuditPacketInputShape(value)) {
    return false;
  }

  const packet = value as Partial<CanonicalAuditPacket>;
  return Boolean(
    packet.signature &&
      packet.signature.algorithm === 'Ed25519' &&
      typeof packet.signature.value === 'string' &&
      packet.signature.value.trim().length > 0,
  );
}

export function validateUnsignedAuditPacket(packet: CanonicalAuditPacketInput): void {
  assertString(packet.version, 'version');
  if (packet.version !== '1.0') {
    throw new AuditPacketValidationError('Invalid version');
  }

  assertNonEmptyString(packet.packetId, 'packetId');
  assertNonEmptyString(packet.orgId, 'orgId');
  assertNonEmptyString(packet.requestId, 'requestId');
  assertNonEmptyString(packet.createdAt, 'createdAt');

  if (!['pricing', 'routing', 'entitlements'].includes(packet.domain)) {
    throw new AuditPacketValidationError('Invalid domain');
  }

  assertRecord(packet.input, 'input');
  if (packet.input.prompt !== undefined && typeof packet.input.prompt !== 'string') {
    throw new AuditPacketValidationError('Invalid input.prompt');
  }
  assertRecord(packet.policy, 'policy');
  assertNonEmptyString(packet.policy.id, 'policy.id');
  assertNonEmptyString(packet.policy.name, 'policy.name');
  assertNonEmptyString(packet.policy.dsl, 'policy.dsl');
  if (!Object.prototype.hasOwnProperty.call(packet.policy, 'compiledConstraints')) {
    throw new AuditPacketValidationError('Missing policy.compiledConstraints');
  }

  assertRecord(packet.decision, 'decision');
  assertNonEmptyString(packet.decision.modelId, 'decision.modelId');
  if (!Object.prototype.hasOwnProperty.call(packet.decision, 'outcome')) {
    throw new AuditPacketValidationError('Missing decision.outcome');
  }

  assertRecord(packet.governance, 'governance');
  assertNonEmptyString(packet.governance.level, 'governance.level');
  if (packet.governance.conformanceStatus !== undefined && typeof packet.governance.conformanceStatus !== 'string') {
    throw new AuditPacketValidationError('Invalid governance.conformanceStatus');
  }
  if (packet.governance.driftRisk !== undefined && typeof packet.governance.driftRisk !== 'string') {
    throw new AuditPacketValidationError('Invalid governance.driftRisk');
  }
  if (packet.governance.lineageDepth !== undefined && typeof packet.governance.lineageDepth !== 'number') {
    throw new AuditPacketValidationError('Invalid governance.lineageDepth');
  }

  if (packet.treasury !== undefined) {
    assertRecord(packet.treasury, 'treasury');
    if (packet.treasury.price !== undefined && typeof packet.treasury.price !== 'number') {
      throw new AuditPacketValidationError('Invalid treasury.price');
    }
    if (packet.treasury.currency !== undefined) {
      assertNonEmptyString(packet.treasury.currency, 'treasury.currency');
    }
  }
}

export function validateAuditPacket(packet: CanonicalAuditPacket): void {
  validateUnsignedAuditPacket(packet);

  if (!packet.signature || packet.signature.algorithm !== 'Ed25519') {
    throw new AuditPacketValidationError('Invalid signature algorithm');
  }
  if (typeof packet.signature.value !== 'string' || packet.signature.value.trim().length === 0) {
    throw new AuditPacketValidationError('Missing signature value');
  }
  if (!isBase64Like(packet.signature.value)) {
    throw new AuditPacketValidationError('Signature is not valid base64');
  }
}

function isCanonicalAuditPacketInputShape(value: unknown): value is CanonicalAuditPacketInput {
  if (!isRecord(value)) {
    return false;
  }

  const packet = value as Partial<CanonicalAuditPacketInput>;
  return Boolean(
    packet.version === '1.0' &&
      typeof packet.packetId === 'string' &&
      typeof packet.orgId === 'string' &&
      typeof packet.requestId === 'string' &&
      typeof packet.createdAt === 'string' &&
      typeof packet.domain === 'string' &&
      isRecord(packet.input) &&
      isRecord(packet.policy) &&
      isRecord(packet.decision) &&
      isRecord(packet.governance),
  );
}

function assertRecord(value: unknown, label: string): asserts value is Record<string, unknown> {
  if (!isRecord(value)) {
    throw new AuditPacketValidationError(`Invalid ${label}`);
  }
}

function assertString(value: unknown, label: string): asserts value is string {
  if (typeof value !== 'string') {
    throw new AuditPacketValidationError(`Invalid ${label}`);
  }
}

function assertNonEmptyString(value: unknown, label: string): asserts value is string {
  assertString(value, label);
  if (value.trim().length === 0) {
    throw new AuditPacketValidationError(`Missing ${label}`);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function isBase64Like(value: string): boolean {
  return /^[A-Za-z0-9+/]+={0,2}$/.test(value) && value.length % 4 === 0;
}
