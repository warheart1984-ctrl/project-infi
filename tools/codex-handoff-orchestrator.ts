#!/usr/bin/env node
import { appendFileSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { SovereignXRouter } from '@aaes-os/sovereignx-router';
import {
  assertReplyPacket,
  buildRequestPacket,
  type ReplyPacket,
  type RequestPacket,
} from './codex-handoff-core.js';
import {
  createCodexHandoffRouter,
  routeCodexHandoff,
  type CodexHandoffRouteResult,
} from './codex-handoff-router.js';
import { loadCisStandardsBundle, type CisStandardsBundle } from './cis-standards.js';
import { loadArtifactGovernanceRegistry, summarizeArtifactGovernanceRegistry, type ArtifactGovernanceRegistry } from './artifact-governance.js';
import { loadExternalStandardsSpec, summarizeExternalStandardsSpec, type ExternalStandardsSpec } from './external-standards.js';
import { loadPricingModelSpec, summarizePricingModelSpec, type PricingModelSpec } from './pricing-model.js';

interface LedgerEntry {
  kind: 'codex-handoff-reply';
  recorded_at: string;
  source_file: string;
  route: CodexHandoffRouteResult;
  standards: CisStandardsBundle;
  artifactGovernance: ArtifactGovernanceRegistry;
  externalStandards: ExternalStandardsSpec;
  pricing: PricingModelSpec;
  packet: ReplyPacket;
  task: {
    objective: string;
    next_action: string;
    status: ReplyPacket['status'];
    changed_files: string[];
  };
}

function usage(): string {
  return [
    'Usage:',
    '  pnpm codex-handoff-orchestrate "<prompt>" --next-action "<text>" --files "<path>" --verification "<cmd>" [--current-state "<text>"] [--done "<text>"] [--blockers "<text>"] [--request <file>] [--reply <reply.json>] [--ledger <file>] [--json]',
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

function parseArgs(argv: string[]): { prompt: string; options: Map<string, string[]>; json: boolean } {
  if (argv.length === 0) {
    die(usage());
  }

  const [prompt, ...rest] = argv;
  if (!isNonEmptyString(prompt)) {
    die('The prompt must be a non-empty string.');
  }

  const options = new Map<string, string[]>();
  let json = false;
  for (let i = 0; i < rest.length; i += 1) {
    const token = rest[i];
    if (token === '--json') {
      json = true;
      continue;
    }

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

  return { prompt, options, json };
}

function first(values: Map<string, string[]>, key: string): string | undefined {
  return values.get(key)?.[0];
}

function buildLedgerEntry(
  replyPath: string,
  request: RequestPacket,
  packet: ReplyPacket,
  route: CodexHandoffRouteResult,
  standards: CisStandardsBundle,
  artifactGovernance: ArtifactGovernanceRegistry,
  externalStandards: ExternalStandardsSpec,
  pricing: PricingModelSpec,
): LedgerEntry {
  return {
    kind: 'codex-handoff-reply',
    recorded_at: new Date().toISOString(),
    source_file: path.resolve(replyPath),
    route,
    standards,
    artifactGovernance,
    externalStandards,
    pricing,
    packet,
    task: {
      objective: request.objective,
      next_action: packet.next_action,
      status: packet.status,
      changed_files: packet.changed_files,
    },
  };
}

function main(): void {
  const { prompt, options, json } = parseArgs(process.argv.slice(2));
  const requestPacket = buildRequestPacket(prompt, options);
  const requestPath = path.resolve(first(options, 'request') ?? '.runtime/codex-handoff-request.json');
  writeFileSync(requestPath, `${JSON.stringify(requestPacket, null, 2)}\n`, 'utf8');
  const standards = loadCisStandardsBundle();
  const artifactGovernance = loadArtifactGovernanceRegistry();
  const externalStandards = loadExternalStandardsSpec();
  const pricing = loadPricingModelSpec();

  const replyPath = first(options, 'reply');
  const ledgerPath = path.resolve(first(options, 'ledger') ?? '.runtime/codex-task-ledger.jsonl');
  const router = createCodexHandoffRouter(new SovereignXRouter({ clock: () => Date.now() }));
  const route = routeCodexHandoff(router, {
    request: requestPacket,
    replyPath: replyPath ?? undefined,
    hasReply: Boolean(replyPath),
  });
  const artifactGovernanceSummary = summarizeArtifactGovernanceRegistry(artifactGovernance);
  const externalStandardsSummary = summarizeExternalStandardsSpec(externalStandards);
  const pricingSummary = summarizePricingModelSpec(pricing);

  if (!replyPath) {
    if (json) {
      process.stdout.write(
        `${JSON.stringify({ ok: true, request: { path: requestPath, packet: requestPacket }, route, standards, artifactGovernance, artifactGovernanceSummary, externalStandards, externalStandardsSummary, pricing, pricingSummary })}\n`,
      );
      return;
    }
    console.log(`request written: ${requestPath}`);
    console.log(`selected model: ${route.selectedModel}`);
    console.log(`backend: ${route.backend}`);
    return;
  }

  const rawReply = JSON.parse(readFileSync(replyPath, 'utf8')) as unknown;
  let replyPacket: ReplyPacket;
  try {
    replyPacket = assertReplyPacket(rawReply, replyPath);
  } catch (error) {
    die(error instanceof Error ? error.message : `${replyPath} is not a valid Codex reply packet`);
  }

  const entry = buildLedgerEntry(replyPath, requestPacket, replyPacket, route, standards, artifactGovernance, externalStandards, pricing);
  appendFileSync(ledgerPath, `${JSON.stringify(entry)}\n`, 'utf8');

  if (json) {
    process.stdout.write(
      `${JSON.stringify({
        ok: true,
        request: { path: requestPath, packet: requestPacket },
        route,
        standards,
        artifactGovernance,
        artifactGovernanceSummary,
        externalStandards,
        externalStandardsSummary,
        pricing,
        pricingSummary,
        reply: { path: path.resolve(replyPath), packet: replyPacket },
        ledger: path.resolve(ledgerPath),
        entry,
      })}\n`,
    );
    return;
  }

  console.log(`request written: ${requestPath}`);
  console.log(`selected model: ${route.selectedModel}`);
  console.log(`backend: ${route.backend}`);
  console.log(`reply ingested: ${path.resolve(replyPath)}`);
  console.log(`ledger updated: ${path.resolve(ledgerPath)}`);
}

main();
