#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import {
  buildReplyPacket,
  buildRequestPacket,
  formatValidationError,
  packetSummary,
  type Packet,
  type ValidationIssue,
  validatePacket,
} from './codex-handoff-core.js';

type Command =
  | { kind: 'write-request'; output?: string; json: boolean }
  | { kind: 'write-reply'; output?: string; json: boolean }
  | { kind: 'read'; file: string; json: boolean }
  | { kind: 'validate'; file: string; json: boolean };

interface ParsedArgs {
  command: Command;
  values: Map<string, string[]>;
}

interface JsonResult {
  ok: boolean;
  kind: 'request' | 'reply' | 'validation' | 'read';
  file?: string;
  packet?: Packet;
  valid?: boolean;
  issues?: ValidationIssue[];
}

function usage(): string {
  return [
    'Usage:',
    '  pnpm codex-handoff write request --objective "<text>" --done "<text>" --files "<path>" --verification "<cmd>" --next-action "<text>" [--current-state "<text>"] [--blockers "<text>"] [--output <file>]',
    '  pnpm codex-handoff write reply --status done|blocked|partial --summary "<text>" --changed-file "<path>" --verification "<cmd>" --next-action "<text>" [--blockers "<text>"] [--output <file>]',
    '  pnpm codex-handoff read <file>',
    '  pnpm codex-handoff validate <file>',
  ].join('\n');
}

function die(message: string): never {
  console.error(message);
  console.error('');
  console.error(usage());
  process.exit(1);
}

function normalizeValues(values: string[] | undefined): string[] {
  if (!values) {
    return [];
  }

  const expanded: string[] = [];
  for (const value of values) {
    for (const item of value.split(',').map((entry) => entry.trim())) {
      if (item.length > 0) {
        expanded.push(item);
      }
    }
  }
  return expanded;
}

function first(values: Map<string, string[]>, key: string): string | undefined {
  return values.get(key)?.[0];
}

function all(values: Map<string, string[]>, key: string): string[] {
  return normalizeValues(values.get(key));
}

function requireString(values: Map<string, string[]>, key: string): string {
  const value = first(values, key);
  if (!value || value.trim().length === 0) {
    die(`Missing required --${key}`);
  }
  return value;
}

function parseArgs(argv: string[]): ParsedArgs {
  if (argv.length === 0) {
    die(usage());
  }

  const values = new Map<string, string[]>();
  const positional: string[] = [];

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--json') {
      const existing = values.get('json') ?? [];
      existing.push('true');
      values.set('json', existing);
      continue;
    }
    if (!token.startsWith('--')) {
      positional.push(token);
      continue;
    }

    const key = token.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) {
      die(`Missing value for --${key}`);
    }

    const existing = values.get(key) ?? [];
    existing.push(next);
    values.set(key, existing);
    i += 1;
  }

  const [verb, kind] = positional;
  const output = first(values, 'output');
  const json = values.has('json');

  if (verb === 'write' && kind === 'request') {
    return { command: { kind: 'write-request', output, json }, values };
  }

  if (verb === 'write' && kind === 'reply') {
    return { command: { kind: 'write-reply', output, json }, values };
  }

  if (verb === 'read' && positional.length === 2) {
    return { command: { kind: 'read', file: positional[1], json }, values };
  }

  if (verb === 'validate' && positional.length === 2) {
    return { command: { kind: 'validate', file: positional[1], json }, values };
  }

  die(usage());
}

function readPacketFile(filePath: string): Packet {
  const raw = readFileSync(filePath, 'utf8');
  return JSON.parse(raw) as Packet;
}

function writePacketFile(filePath: string, packet: Packet): void {
  const payload = `${JSON.stringify(packet, null, 2)}\n`;
  writeFileSync(filePath, payload, 'utf8');
}

function printPacketSummary(packet: Packet, source: string): void {
  console.log(`${source}:`);
  for (const line of packetSummary(packet)) {
    console.log(line);
  }
}

function writeJsonResult(result: JsonResult): void {
  console.log(JSON.stringify(result));
}

function printWriteResult(filePath: string, packet: Packet): void {
  console.log(filePath);
  printPacketSummary(packet, filePath);
}

async function main(): Promise<void> {
  const parsed = parseArgs(process.argv.slice(2));

  switch (parsed.command.kind) {
    case 'write-request': {
      const packet = buildRequestPacket(requireString(parsed.values, 'objective'), parsed.values);
      const output = parsed.command.output;
      if (output) {
        const target = path.resolve(output);
        writePacketFile(target, packet);
        if (parsed.command.json) {
          writeJsonResult({ ok: true, kind: 'request', file: target, packet });
          return;
        }
        printWriteResult(target, packet);
        return;
      }
      if (parsed.command.json) {
        writeJsonResult({ ok: true, kind: 'request', packet });
        return;
      }
      console.log(JSON.stringify(packet, null, 2));
      return;
    }
    case 'write-reply': {
      const packet = buildReplyPacket(parsed.values);
      const output = parsed.command.output;
      if (output) {
        const target = path.resolve(output);
        writePacketFile(target, packet);
        if (parsed.command.json) {
          writeJsonResult({ ok: true, kind: 'reply', file: target, packet });
          return;
        }
        printWriteResult(target, packet);
        return;
      }
      if (parsed.command.json) {
        writeJsonResult({ ok: true, kind: 'reply', packet });
        return;
      }
      console.log(JSON.stringify(packet, null, 2));
      return;
    }
    case 'read': {
      const filePath = path.resolve(parsed.command.file);
      const packet = readPacketFile(filePath);
      const validation = validatePacket(packet);
      if (!validation.valid) {
        die(formatValidationError(filePath, validation.issues));
      }
      if (parsed.command.json) {
        writeJsonResult({ ok: true, kind: 'read', file: filePath, packet });
        return;
      }
      printPacketSummary(packet, filePath);
      return;
    }
    case 'validate': {
      const filePath = path.resolve(parsed.command.file);
      const packet = readPacketFile(filePath);
      const validation = validatePacket(packet);
      if (parsed.command.json) {
        writeJsonResult({ ok: true, kind: 'validation', file: filePath, valid: validation.valid, issues: validation.issues });
        if (!validation.valid) {
          process.exitCode = 1;
        }
        return;
      }
      if (!validation.valid) {
        die(formatValidationError(filePath, validation.issues));
      }
      console.log(`valid packet: ${filePath}`);
      return;
    }
  }
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
