import { createHash } from 'node:crypto';

export type UlPrimitive = string | number | boolean | null;

export type UlContextValue =
  | UlPrimitive
  | readonly UlContextValue[]
  | { readonly [key: string]: UlContextValue };

export interface UlEvidenceRef {
  id: string;
  kind: string;
  uri?: string;
  hash?: string;
  signature?: string;
}

export interface UlAuthorityRef {
  actor: string;
  roles: readonly string[];
  permissions: readonly string[];
}

export interface UlTraceabilityRow {
  cisRequirement: string;
  referenceArchitecture: string;
  conformanceTest: string;
  evidenceArtifact: string;
  notes?: string;
}

export interface UlCommandInput {
  actor: string;
  verb: string;
  target: string;
  purpose?: string;
  context?: Record<string, UlContextValue>;
  evidence: readonly UlEvidenceRef[];
  authority: UlAuthorityRef;
  traceability: readonly UlTraceabilityRow[];
  source?: string;
}

export interface UlCommand extends Required<Omit<UlCommandInput, 'context' | 'purpose' | 'source'>> {
  id: string;
  purpose: string;
  context: Record<string, UlContextValue>;
  source: string;
}

export interface UlValidationIssue {
  field: string;
  message: string;
}

export interface UlValidationResult {
  commandId: string;
  valid: boolean;
  issues: UlValidationIssue[];
}

export interface UlIslIntentDraft {
  actor: string;
  target: string;
  purpose: string;
  context: Record<string, UlContextValue>;
  evidence: readonly UlEvidenceRef[];
  authority: UlAuthorityRef;
  traceability: readonly UlTraceabilityRow[];
}

export interface UlCompileResult {
  accepted: boolean;
  command: UlCommand;
  validation: UlValidationResult;
  intent: UlIslIntentDraft;
}

export interface UlRuntimeSnapshot {
  packageName: '@aaes-os/ul-runtime';
  version: 'ul-v1';
  totalCommands: number;
  acceptedCommands: number;
  rejectedCommands: number;
  lastCommandId?: string;
}

export interface UlPhraseDefaults {
  actor: string;
  evidence: readonly UlEvidenceRef[];
  authority: UlAuthorityRef;
  traceability: readonly UlTraceabilityRow[];
  context?: Record<string, UlContextValue>;
}

const VERSION = 'ul-v1' as const;
const UL_VERB_PATTERN = /^[a-z][a-z0-9-]*$/;
const CONTROL_WORDS = new Set(['as', 'for', 'with']);

export function parseUlPhrase(source: string, defaults: UlPhraseDefaults): UlCommandInput {
  const text = normalizeText(source);
  const [verb = '', ...rest] = text.split(' ');
  const sections = splitPhraseSections(rest);
  const actor = sections.as ?? defaults.actor;
  const purpose = sections.for;
  const context = {
    ...(defaults.context ?? {}),
    ...parseContextSection(sections.with),
  };

  return {
    actor,
    verb,
    target: sections.target,
    purpose,
    context,
    evidence: defaults.evidence,
    authority: {
      ...defaults.authority,
      actor: normalizeText(defaults.authority.actor || actor),
    },
    traceability: defaults.traceability,
    source: text,
  };
}

export function normalizeUlCommand(input: UlCommandInput): UlCommand {
  const normalized = normalizeCommandCore(input);
  return {
    ...normalized,
    id: buildUlCommandId(normalized),
  };
}

export function buildUlCommandId(command: Omit<UlCommand, 'id'> | UlCommandInput): string {
  const normalized = 'id' in command ? cloneCommandBody(command) : normalizeCommandCore(command);
  return createHash('sha256').update(stableStringify(normalized)).digest('hex');
}

export function validateUlCommand(command: UlCommandInput | UlCommand): UlValidationResult {
  const normalized = normalizeUlCommand(command);
  const issues: UlValidationIssue[] = [];

  if (!normalized.actor) {
    issues.push({ field: 'actor', message: 'actor is required' });
  }
  if (!normalized.verb) {
    issues.push({ field: 'verb', message: 'verb is required' });
  } else if (!UL_VERB_PATTERN.test(normalized.verb)) {
    issues.push({ field: 'verb', message: 'verb must be lowercase alphanumeric text with optional hyphens' });
  }
  if (!normalized.target) {
    issues.push({ field: 'target', message: 'target is required' });
  }
  if (!normalized.purpose) {
    issues.push({ field: 'purpose', message: 'purpose is required' });
  }
  if (normalized.evidence.length === 0) {
    issues.push({ field: 'evidence', message: 'at least one evidence reference is required' });
  }
  for (const [index, ref] of normalized.evidence.entries()) {
    if (!ref.id) {
      issues.push({ field: `evidence[${index}].id`, message: 'evidence id is required' });
    }
    if (!ref.kind) {
      issues.push({ field: `evidence[${index}].kind`, message: 'evidence kind is required' });
    }
  }
  if (!normalized.authority.actor) {
    issues.push({ field: 'authority.actor', message: 'authority actor is required' });
  }
  if (normalized.authority.roles.length === 0) {
    issues.push({ field: 'authority.roles', message: 'at least one authority role is required' });
  }
  if (normalized.authority.permissions.length === 0) {
    issues.push({ field: 'authority.permissions', message: 'at least one authority permission is required' });
  }
  if (normalized.traceability.length === 0) {
    issues.push({ field: 'traceability', message: 'at least one traceability row is required' });
  }

  return { commandId: normalized.id, valid: issues.length === 0, issues };
}

export function compileUlToIslIntent(command: UlCommandInput | UlCommand): UlIslIntentDraft {
  const normalized = normalizeUlCommand(command);
  return {
    actor: normalized.actor,
    target: normalized.target,
    purpose: `${normalized.verb} ${normalized.purpose}`,
    context: {
      ...normalized.context,
      ul: {
        commandId: normalized.id,
        verb: normalized.verb,
        source: normalized.source,
      },
    },
    evidence: normalized.evidence.map(cloneEvidenceRef),
    authority: cloneAuthorityRef(normalized.authority),
    traceability: normalized.traceability.map(cloneTraceabilityRow),
  };
}

export class UlRuntime {
  private readonly commands: UlCommand[] = [];
  private accepted = 0;
  private rejected = 0;

  constructor(seed: readonly (UlCommandInput | UlCommand)[] = []) {
    for (const command of seed) {
      this.compile(command);
    }
  }

  compile(command: UlCommandInput | UlCommand): UlCompileResult {
    const normalized = normalizeUlCommand(command);
    const validation = validateUlCommand(normalized);
    const intent = compileUlToIslIntent(normalized);

    if (!validation.valid) {
      this.rejected += 1;
      return { accepted: false, command: normalized, validation, intent };
    }

    this.accepted += 1;
    this.commands.push(normalized);
    return { accepted: true, command: normalized, validation, intent };
  }

  compilePhrase(source: string, defaults: UlPhraseDefaults): UlCompileResult {
    return this.compile(parseUlPhrase(source, defaults));
  }

  validate(command: UlCommandInput | UlCommand): UlValidationResult {
    return validateUlCommand(command);
  }

  listCommands(): UlCommand[] {
    return this.commands.map(cloneCommand);
  }

  snapshot(): UlRuntimeSnapshot {
    return {
      packageName: '@aaes-os/ul-runtime',
      version: VERSION,
      totalCommands: this.commands.length + this.rejected,
      acceptedCommands: this.accepted,
      rejectedCommands: this.rejected,
      lastCommandId: this.commands[this.commands.length - 1]?.id,
    };
  }
}

export function createUlRuntime(seed: readonly (UlCommandInput | UlCommand)[] = []): UlRuntime {
  return new UlRuntime(seed);
}

export function summarizeUlRuntime(runtime: UlRuntime = new UlRuntime()): string {
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} accepted ${snapshot.acceptedCommands} verb commands`;
}

function splitPhraseSections(tokens: readonly string[]): { target: string; as?: string; for?: string; with?: string } {
  const sections: { target: string[]; as: string[]; for: string[]; with: string[] } = {
    target: [],
    as: [],
    for: [],
    with: [],
  };
  let active: keyof typeof sections = 'target';

  for (const token of tokens) {
    if (CONTROL_WORDS.has(token)) {
      active = token as keyof typeof sections;
      continue;
    }
    sections[active].push(token);
  }

  return {
    target: normalizeText(sections.target.join(' ')),
    as: optionalText(sections.as.join(' ')),
    for: optionalText(sections.for.join(' ')),
    with: optionalText(sections.with.join(' ')),
  };
}

function parseContextSection(section: string | undefined): Record<string, UlContextValue> {
  if (!section) {
    return {};
  }

  const entries = section
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((entry) => {
      const [rawKey, ...rawValue] = entry.split('=');
      const key = normalizeText(rawKey ?? '');
      const value = normalizeText(rawValue.join('='));
      return [key, value] as const;
    })
    .filter(([key, value]) => key && value);

  return Object.fromEntries(entries);
}

function normalizeCommandCore(input: UlCommandInput): Omit<UlCommand, 'id'> {
  const verb = normalizeText(input.verb).toLowerCase();
  const target = normalizeText(input.target);
  const purpose = normalizeText(input.purpose ?? target);
  const source = normalizeText(input.source ?? `${verb} ${target} for ${purpose} as ${input.actor}`);

  return {
    actor: normalizeText(input.actor),
    verb,
    target,
    purpose,
    context: normalizeContext(input.context ?? {}),
    evidence: input.evidence.map(cloneEvidenceRef),
    authority: cloneAuthorityRef(input.authority),
    traceability: input.traceability.map(cloneTraceabilityRow),
    source,
  };
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

function optionalText(value: string): string | undefined {
  const normalized = normalizeText(value);
  return normalized ? normalized : undefined;
}

function cloneEvidenceRef(ref: UlEvidenceRef): UlEvidenceRef {
  return {
    id: normalizeText(ref.id),
    kind: normalizeText(ref.kind),
    uri: ref.uri ? normalizeText(ref.uri) : undefined,
    hash: ref.hash ? normalizeText(ref.hash) : undefined,
    signature: ref.signature ? normalizeText(ref.signature) : undefined,
  };
}

function cloneAuthorityRef(authority: UlAuthorityRef): UlAuthorityRef {
  return {
    actor: normalizeText(authority.actor),
    roles: authority.roles.map(normalizeText),
    permissions: authority.permissions.map(normalizeText),
  };
}

function cloneTraceabilityRow(row: UlTraceabilityRow): UlTraceabilityRow {
  return {
    cisRequirement: normalizeText(row.cisRequirement),
    referenceArchitecture: normalizeText(row.referenceArchitecture),
    conformanceTest: normalizeText(row.conformanceTest),
    evidenceArtifact: normalizeText(row.evidenceArtifact),
    notes: row.notes ? normalizeText(row.notes) : undefined,
  };
}

function normalizeContext(context: Record<string, UlContextValue>): Record<string, UlContextValue> {
  const entries = Object.entries(context).map(([key, value]) => [normalizeText(key), normalizeContextValue(value)] as const);
  entries.sort(([left], [right]) => left.localeCompare(right));
  return Object.fromEntries(entries);
}

function normalizeContextValue(value: UlContextValue): UlContextValue {
  if (Array.isArray(value)) {
    return value.map((entry) => normalizeContextValue(entry));
  }
  if (value && typeof value === 'object') {
    return normalizeContext(value as Record<string, UlContextValue>);
  }
  if (typeof value === 'string') {
    return normalizeText(value);
  }
  return value;
}

function cloneCommand(command: UlCommand): UlCommand {
  return {
    ...command,
    context: normalizeContext(command.context),
    evidence: command.evidence.map(cloneEvidenceRef),
    authority: cloneAuthorityRef(command.authority),
    traceability: command.traceability.map(cloneTraceabilityRow),
  };
}

function cloneCommandBody(command: UlCommandInput | UlCommand): Omit<UlCommand, 'id'> {
  return normalizeCommandCore(command);
}

function stableStringify(value: unknown): string {
  return JSON.stringify(stableValue(value));
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => stableValue(entry));
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => [key, stableValue(entry)] as const);
    return Object.fromEntries(entries);
  }
  return value;
}
