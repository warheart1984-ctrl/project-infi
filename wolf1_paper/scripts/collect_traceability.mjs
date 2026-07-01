import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';
import { parse } from 'yaml';
import { ROOT } from './lib/paths.mjs';

function loadYaml(rel) {
  const p = path.join(ROOT, rel);
  return parse(fs.readFileSync(p, 'utf8'));
}

export function collectTraceability() {
  const reqs = loadYaml('registries/requirements.yaml');
  const adrs = loadYaml('registries/adrs.yaml');
  const impl = loadYaml('registries/implementations.yaml');
  const cts = loadYaml('registries/cts.yaml');
  const ev = loadYaml('registries/evidence.yaml');
  const bench = loadYaml('registries/benchmarks.yaml');

  const requirementIds = (reqs.requirements ?? []).map((r) => r.id);

  const adrIds = (adrs.adrs ?? [])
    .filter((a) => requirementIds.includes(a.requirement_id))
    .map((a) => a.id);

  const referenceImplementations = (impl.implementations ?? [])
    .filter((i) => requirementIds.includes(i.requirement_id))
    .flatMap((i) => i.paths ?? []);

  const ctsCases = (cts.cases ?? [])
    .filter((c) => requirementIds.includes(c.requirement_id))
    .flatMap((c) => c.test_ids ?? []);

  const evidenceEntries = (ev.entries ?? [])
    .filter((e) => requirementIds.includes(e.requirement_id))
    .flatMap((e) => e.evidence_ids ?? []);

  const benchmarks = (bench.benchmarks ?? [])
    .filter((b) => requirementIds.includes(b.requirement_id))
    .map((b) => b.id);

  return {
    requirements: requirementIds,
    adr_ids: adrIds,
    reference_implementations: referenceImplementations,
    cts_cases: ctsCases,
    evidence_entries: evidenceEntries,
    benchmarks,
  };
}

const invoked = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (invoked) {
  console.log(JSON.stringify(collectTraceability(), null, 2));
}
