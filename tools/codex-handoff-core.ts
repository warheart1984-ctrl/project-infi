import { createHmac } from 'node:crypto';

export interface RequestPacket {
  objective: string;
  current_state?: string;
  done: string[];
  next_action: string;
  files: string[];
  verification: string;
  blockers: string[];
}

export interface ReplyPacket {
  status: 'done' | 'blocked' | 'partial';
  summary: string;
  changed_files: string[];
  verification: string[];
  next_action: string;
  blockers?: string[];
}

export interface SignedReplyPacket {
  signer: string;
  signed_at: string;
  signature: string;
  reply: ReplyPacket;
}

export type Packet = RequestPacket | ReplyPacket;

export interface ValidationIssue {
  path: string;
  message: string;
}

export interface ValidationResult<T> {
  valid: boolean;
  issues: ValidationIssue[];
  value?: T;
}

const REQUEST_KEYS = ['objective', 'current_state', 'done', 'next_action', 'files', 'verification', 'blockers'] as const;
const REPLY_KEYS = ['status', 'summary', 'changed_files', 'verification', 'next_action', 'blockers'] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isNonEmptyString);
}

function splitList(values: string[] | undefined): string[] {
  if (!values) {
    return [];
  }

  const result: string[] = [];
  for (const value of values) {
    for (const item of value.split(',').map((part) => part.trim())) {
      if (item.length > 0) {
        result.push(item);
      }
    }
  }
  return result;
}

function first(values: Map<string, string[]>, key: string): string | undefined {
  return values.get(key)?.[0];
}

function all(values: Map<string, string[]>, key: string): string[] {
  return splitList(values.get(key));
}

function ensureString(values: Map<string, string[]>, key: string): string {
  const value = first(values, key);
  if (!isNonEmptyString(value)) {
    throw new Error(`Missing required --${key}`);
  }
  return value;
}

function addIssue(issues: ValidationIssue[], path: string, message: string): void {
  issues.push({ path, message });
}

function validateStringField(
  value: unknown,
  path: string,
  issues: ValidationIssue[],
  required: boolean,
  allowEmpty = false,
): void {
  if (value === undefined) {
    if (required) {
      addIssue(issues, path, 'is required');
    }
    return;
  }

  if (typeof value !== 'string') {
    addIssue(issues, path, 'must be a string');
    return;
  }

  if (!allowEmpty && value.trim().length === 0) {
    addIssue(issues, path, 'must be a non-empty string');
  }
}

function validateArrayField(value: unknown, path: string, issues: ValidationIssue[], required: boolean): void {
  if (value === undefined) {
    if (required) {
      addIssue(issues, path, 'is required');
    }
    return;
  }

  if (!Array.isArray(value)) {
    addIssue(issues, path, 'must be an array');
    return;
  }

  value.forEach((item, index) => {
    if (!isNonEmptyString(item)) {
      addIssue(issues, `${path}[${index}]`, 'must be a non-empty string');
    }
  });
}

function validateExactKeys(value: Record<string, unknown>, allowedKeys: readonly string[], issues: ValidationIssue[]): void {
  for (const key of Object.keys(value)) {
    if (!allowedKeys.includes(key)) {
      addIssue(issues, key, 'is not allowed by the schema');
    }
  }
}

export function validateRequestPacket(value: unknown): ValidationResult<RequestPacket> {
  const issues: ValidationIssue[] = [];
  if (!isRecord(value)) {
    addIssue(issues, '', 'must be an object');
    return { valid: false, issues };
  }

  validateExactKeys(value, REQUEST_KEYS, issues);
  validateStringField(value.objective, 'objective', issues, true);
  validateStringField(value.current_state, 'current_state', issues, false, true);
  validateArrayField(value.done, 'done', issues, true);
  validateStringField(value.next_action, 'next_action', issues, true);
  validateArrayField(value.files, 'files', issues, true);
  validateStringField(value.verification, 'verification', issues, true);
  validateArrayField(value.blockers, 'blockers', issues, true);

  if (issues.length > 0) {
    return { valid: false, issues };
  }

  return {
    valid: true,
    issues,
    value: {
      objective: value.objective as string,
      current_state: value.current_state as string | undefined,
      done: value.done as string[],
      next_action: value.next_action as string,
      files: value.files as string[],
      verification: value.verification as string,
      blockers: value.blockers as string[],
    },
  };
}

export function validateReplyPacket(value: unknown): ValidationResult<ReplyPacket> {
  const issues: ValidationIssue[] = [];
  if (!isRecord(value)) {
    addIssue(issues, '', 'must be an object');
    return { valid: false, issues };
  }

  validateExactKeys(value, REPLY_KEYS, issues);
  validateStringField(value.status, 'status', issues, true);
  if (value.status !== undefined && !['done', 'blocked', 'partial'].includes(String(value.status))) {
    addIssue(issues, 'status', 'must be one of: done, blocked, partial');
  }
  validateStringField(value.summary, 'summary', issues, true);
  validateArrayField(value.changed_files, 'changed_files', issues, true);
  validateArrayField(value.verification, 'verification', issues, true);
  validateStringField(value.next_action, 'next_action', issues, true);
  validateArrayField(value.blockers, 'blockers', issues, false);

  if (issues.length > 0) {
    return { valid: false, issues };
  }

  return {
    valid: true,
    issues,
    value: {
      status: value.status as ReplyPacket['status'],
      summary: value.summary as string,
      changed_files: value.changed_files as string[],
      verification: value.verification as string[],
      next_action: value.next_action as string,
      blockers: value.blockers as string[] | undefined,
    },
  };
}

export function validatePacket(value: unknown): ValidationResult<Packet> {
  const request = validateRequestPacket(value);
  if (request.valid) {
    return request;
  }

  const reply = validateReplyPacket(value);
  if (reply.valid) {
    return reply;
  }

  return {
    valid: false,
    issues: [...request.issues, ...reply.issues],
  };
}

export function assertRequestPacket(value: unknown, label = 'request packet'): RequestPacket {
  const result = validateRequestPacket(value);
  if (!result.valid || !result.value) {
    throw new Error(formatValidationError(label, result.issues));
  }
  return result.value;
}

export function assertReplyPacket(value: unknown, label = 'reply packet'): ReplyPacket {
  const result = validateReplyPacket(value);
  if (!result.valid || !result.value) {
    throw new Error(formatValidationError(label, result.issues));
  }
  return result.value;
}

export function formatValidationError(label: string, issues: ValidationIssue[]): string {
  if (issues.length === 0) {
    return `${label} is invalid`;
  }

  return [label, ...issues.map((issue) => `- ${issue.path || '<root>'}: ${issue.message}`)].join('\n');
}

export function buildRequestPacket(prompt: string, values: Map<string, string[]>): RequestPacket {
  const packet: RequestPacket = {
    objective: prompt,
    current_state: first(values, 'current-state'),
    done: all(values, 'done'),
    next_action: ensureString(values, 'next-action'),
    files: all(values, 'files'),
    verification: ensureString(values, 'verification'),
    blockers: all(values, 'blockers'),
  };
  return assertRequestPacket(packet);
}

export function buildReplyPacket(values: Map<string, string[]>): ReplyPacket {
  const changedFiles = [...all(values, 'changed-file'), ...all(values, 'changed-files')];
  const blockers = all(values, 'blockers');
  const packet: ReplyPacket = {
    status: (() => {
      const status = ensureString(values, 'status');
      if (!['done', 'blocked', 'partial'].includes(status)) {
        throw new Error('status must be done, blocked, or partial');
      }
      return status as ReplyPacket['status'];
    })(),
    summary: ensureString(values, 'summary'),
    changed_files: changedFiles,
    verification: all(values, 'verification'),
    next_action: ensureString(values, 'next-action'),
    blockers: blockers.length > 0 ? blockers : undefined,
  };

  return assertReplyPacket(packet);
}

export function packetSummary(packet: Packet): string[] {
  if ('objective' in packet) {
    const lines = [
      `objective: ${packet.objective}`,
      `next_action: ${packet.next_action}`,
      `files: ${packet.files.join(' | ') || '(none)'}`,
      `verification: ${packet.verification}`,
      `blockers: ${packet.blockers.join(' | ') || '(none)'}`,
    ];
    if (packet.current_state) {
      lines.splice(1, 0, `current_state: ${packet.current_state}`);
    }
    return lines;
  }

  return [
    `status: ${packet.status}`,
    `summary: ${packet.summary}`,
    `changed_files: ${packet.changed_files.join(' | ') || '(none)'}`,
    `verification: ${packet.verification.join(' | ') || '(none)'}`,
    `next_action: ${packet.next_action}`,
    `blockers: ${(packet.blockers ?? []).join(' | ') || '(none)'}`,
  ];
}

function canonicalizeSignedReplyPacket(signedReply: SignedReplyPacket): string {
  return JSON.stringify({
    signer: signedReply.signer,
    signed_at: signedReply.signed_at,
    reply: {
      status: signedReply.reply.status,
      summary: signedReply.reply.summary,
      changed_files: [...signedReply.reply.changed_files],
      verification: [...signedReply.reply.verification],
      next_action: signedReply.reply.next_action,
      blockers: signedReply.reply.blockers ? [...signedReply.reply.blockers] : undefined,
    },
  });
}

export function signReplyPacket(reply: ReplyPacket, secret: string, signer = 'codex', signedAt = new Date().toISOString()): SignedReplyPacket {
  const signedReply: SignedReplyPacket = {
    signer,
    signed_at: signedAt,
    signature: '',
    reply,
  };
  const signature = createHmac('sha256', secret).update(canonicalizeSignedReplyPacket(signedReply)).digest('hex');
  return {
    ...signedReply,
    signature,
  };
}

export function verifySignedReplyPacket(signedReply: SignedReplyPacket, secret: string): boolean {
  const expected = signReplyPacket(signedReply.reply, secret, signedReply.signer, signedReply.signed_at).signature;
  return expected === signedReply.signature;
}
