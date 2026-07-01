#!/usr/bin/env node
/** Mirror of validate_traceability_chain.py for environments without Python/PyYAML. */
import fs from 'fs';
import path from 'path';
import { parse } from 'yaml';
import { ROOT } from './lib/paths.mjs';

function loadYaml(rel) {
  const p = path.join(ROOT, rel);
  return parse(fs.readFileSync(p, 'utf8')) || {};
}

function main() {
  const reqs = loadYaml('registries/requirements.yaml');
  const adrs = loadYaml('registries/adrs.yaml');
  const impl = loadYaml('registries/implementations.yaml');
  const cts = loadYaml('registries/cts.yaml');
  const ev = loadYaml('registries/evidence.yaml');
  const bench = loadYaml('registries/benchmarks.yaml');

  const adrsByReq = Object.fromEntries((adrs.adrs ?? []).map((a) => [a.requirement_id, a]));
  const implByReq = Object.fromEntries((impl.implementations ?? []).map((i) => [i.requirement_id, i]));
  const ctsByReq = Object.fromEntries((cts.cases ?? []).map((c) => [c.requirement_id, c]));
  const evByReq = Object.fromEntries((ev.entries ?? []).map((e) => [e.requirement_id, e]));
  const benchByReq = Object.fromEntries((bench.benchmarks ?? []).map((b) => [b.requirement_id, b]));

  const failures = [];

  for (const req of reqs.requirements ?? []) {
    const rid = req.id;
    const missing = [];
    if (!(rid in adrsByReq)) missing.push('ADR');
    if (!(rid in implByReq)) missing.push('ReferenceImplementation');
    if (!(rid in ctsByReq)) missing.push('CTS');
    if (!(rid in evByReq)) missing.push('EvidenceLedger');
    if (req.benchmark_required && !(rid in benchByReq)) missing.push('Benchmark');
    if (missing.length) failures.push({ requirement_id: rid, missing });
  }

  if (failures.length) {
    console.error('[TRACEABILITY] Incomplete requirements:');
    console.error(JSON.stringify(failures, null, 2));
    process.exit(1);
  }

  console.log('[TRACEABILITY] All normative requirements have complete chains.');
}

main();
