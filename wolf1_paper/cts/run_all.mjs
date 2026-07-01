import fs from 'fs';
import path from 'path';
import { parse } from 'yaml';
import { spawnSync } from 'child_process';
import { ROOT } from '../scripts/lib/paths.mjs';
import { getDocument, loadManifest, resolveFromRoot } from '../scripts/lib/version.mjs';

const failures = [];

function fail(msg) {
  failures.push(msg);
  console.error(`[CTS][FAIL] ${msg}`);
}

function pass(msg) {
  console.log(`[CTS] OK: ${msg}`);
}

function readYaml(rel) {
  const p = path.join(ROOT, rel);
  if (!fs.existsSync(p)) {
    fail(`missing registry: ${rel}`);
    return null;
  }
  try {
    return parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    fail(`invalid YAML ${rel}: ${e.message}`);
    return null;
  }
}

// 8. Traceability chains (registry completeness)
function checkTraceability() {
  const py = spawnSync('python', ['scripts/validate_traceability_chain.py'], {
    cwd: ROOT,
    encoding: 'utf8',
    shell: true,
  });
  if (py.status === 0) {
    pass('traceability chains complete');
    return;
  }
  const node = spawnSync(process.execPath, ['scripts/validate_traceability_chain.mjs'], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  if (node.status === 0) {
    if (py.status !== 0 && py.stderr?.includes('not recognized')) {
      console.log('[CTS] WARN: Python unavailable — used Node traceability validator');
    }
    pass('traceability chains complete');
    return;
  }
  fail('traceability chain validation failed');
  if (py.stdout) console.error(py.stdout);
  if (py.stderr) console.error(py.stderr);
  if (node.stdout) console.error(node.stdout);
  if (node.stderr) console.error(node.stderr);
}

console.log('=== [CTS] Constitutional Test Suite ===\n');

// 0. Version manifest
try {
  loadManifest();
  pass('version manifest valid');
} catch (e) {
  fail(e.message);
}

// 1. Registry YAML
const gov = readYaml('registries/governance.yaml');
const req = readYaml('registries/requirements.yaml');
const art = readYaml('registries/artifacts.yaml');
if (gov) pass('governance registry parseable');
if (req) pass('requirements registry parseable');
if (art) pass('artifacts registry parseable');

// 2. ADR structure
const adrDir = path.join(ROOT, 'adr');
const adrs = fs.existsSync(adrDir)
  ? fs.readdirSync(adrDir).filter((f) => /^ADR-/.test(f) && f.endsWith('.md'))
  : [];
if (adrs.length === 0) fail('no ADR files in adr/');
else {
  pass(`${adrs.length} ADR file(s)`);
  for (const file of adrs) {
    const text = fs.readFileSync(path.join(adrDir, file), 'utf8');
    for (const section of ['## Context', '## Decision', '## Evidence']) {
      if (!text.includes(section)) fail(`${file} missing ${section}`);
    }
  }
}

// 3. Requirement → ADR traceability
if (req?.requirements) {
  const adrIds = new Set(adrs.map((f) => f.replace(/\.md$/, '')));
  for (const r of req.requirements) {
    for (const t of r.traceability ?? []) {
      const adrId = t.adr_id;
      if (!adrId || adrId === 'null') continue;
      if (!adrIds.has(adrId)) fail(`requirement ${r.id} references missing ADR: ${adrId}`);
    }
  }
  pass('requirement → ADR traceability');
}

// 4. Artifact registry
if (art?.artifacts) {
  for (const a of art.artifacts) {
    if (!a.id) fail('empty artifact ID');
  }
  pass(`${art.artifacts.length} artifact(s) registered`);
}

// 5. Amendment ordering
const amendDir = path.join(ROOT, 'amendments');
const amendFiles = fs.existsSync(amendDir)
  ? fs.readdirSync(amendDir).filter((f) => /^amendment-\d+\.md$/.test(f))
  : [];
const amendCount = amendFiles.length;
if (amendCount === 0) {
  console.log('[CTS] WARN: no amendment files');
} else {
  for (let i = 1; i <= amendCount; i++) {
    const expected = `amendment-${String(i).padStart(4, '0')}.md`;
    if (!fs.existsSync(path.join(amendDir, expected))) {
      fail(`missing amendment: ${expected}`);
    }
  }
  pass(`amendment sequence 1..${amendCount}`);
}

// 6. Specifications
if (req?.requirements) {
  const specDir = path.join(ROOT, 'specifications');
  for (const r of req.requirements) {
    const spec = r.specification;
    if (!spec) continue;
    const base = path.basename(spec);
    const candidates = [
      path.join(specDir, base),
      path.join(ROOT, spec),
    ];
    if (!candidates.some((p) => fs.existsSync(p))) {
      fail(`missing specification: ${spec}`);
    }
  }
  pass('specification files present');
}

// 7. Governed document source
try {
  const doc = getDocument('wolf1-arch');
  const src = resolveFromRoot(doc.source);
  if (!fs.existsSync(src)) fail(`missing source: ${doc.source}`);
  else pass(`source exists: ${doc.source}`);
} catch (e) {
  fail(e.message);
}

// 8. Traceability chains (registry completeness)
checkTraceability();

// 9. Dashboard index (optional until first receipt)
const indexPath = path.join(ROOT, 'governance', 'receipts-index.json');
if (!fs.existsSync(indexPath)) {
  console.log('[CTS] WARN: governance/receipts-index.json missing (run make receipt)');
} else {
  try {
    JSON.parse(fs.readFileSync(indexPath, 'utf8'));
    pass('receipts-index.json valid');
  } catch {
    fail('receipts-index.json invalid JSON');
  }
}

console.log('');
if (failures.length) {
  console.error(`=== [CTS] ${failures.length} failure(s) ===`);
  process.exit(1);
}
console.log('=== [CTS] All governance checks passed ===');
