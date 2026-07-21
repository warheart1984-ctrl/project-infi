#!/usr/bin/env node
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { buildRequestPacket } from './codex-handoff-core.js';

function usage(): string {
  return [
    'Usage:',
    '  pnpm codex-handoff-prompt "<prompt>" --next-action "<text>" --files "<path>" --verification "<cmd>" [--current-state "<text>"] [--done "<text>"] [--blockers "<text>"] [--output <file>]',
  ].join('\n');
}

function die(message: string): never {
  console.error(message);
  console.error('');
  console.error(usage());
  process.exit(1);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function parseArgs(argv: string[]): { prompt: string; options: Map<string, string[]> } {
  if (argv.length === 0) {
    die(usage());
  }

  const [prompt, ...rest] = argv;
  if (!isNonEmptyString(prompt)) {
    die('The prompt must be a non-empty string.');
  }

  const options = new Map<string, string[]>();
  for (let i = 0; i < rest.length; i += 1) {
    const token = rest[i];
    if (!token.startsWith('--')) {
      die(`Unexpected argument: ${token}`);
    }

    const key = token.slice(2);
    const next = rest[i + 1];
    if (next === undefined || next.startsWith('--')) {
      die(`Missing value for --${key}`);
    }

    const current = options.get(key) ?? [];
    current.push(next);
    options.set(key, current);
    i += 1;
  }

  return { prompt, options };
}

function required(options: Map<string, string[]>, key: string): string {
  const value = options.get(key)?.[0];
  if (!isNonEmptyString(value)) {
    die(`Missing required --${key}`);
  }
  return value;
}

function main(): void {
  const { prompt, options } = parseArgs(process.argv.slice(2));
  required(options, 'next-action');
  required(options, 'verification');
  const packet = buildRequestPacket(prompt, options);
  const output = options.get('output')?.[0];

  if (output) {
    const target = path.resolve(output);
    writeFileSync(target, `${JSON.stringify(packet, null, 2)}\n`, 'utf8');
    process.stdout.write(`${JSON.stringify(packet)}\n`);
    return;
  }

  process.stdout.write(`${JSON.stringify(packet)}\n`);
}

main();
