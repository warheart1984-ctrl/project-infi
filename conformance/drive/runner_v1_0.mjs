#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const resultDir = path.join(root, 'conformance', 'drive', 'results');
const evidencePath = process.env.GOOGLE_DRIVE_EVIDENCE_LOG || path.join(root, '.local', 'google-drive', 'evidence.jsonl');
const statuses = [];
const add = (test_id, status, detail) => statuses.push({ test_id, status, detail });

let evidence = [];
try { evidence = (await readFile(evidencePath, 'utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse); }
catch (error) { if (error?.code !== 'ENOENT') add('C4.1', 'FAIL', 'Evidence log is unreadable'); }

const operations = new Set(evidence.map(item => item.operation));
for (const [id, operation] of [['C1.1','auth'],['C1.2','store'],['C1.3','load'],['C1.4','revoke'],['C2.1','list'],['C2.2','search'],['C2.3','fetch|export'],['C2.4','upload'],['C2.5','update']]) {
  const choices = operation.split('|'); add(id, choices.some(value => operations.has(value)) ? 'PASS' : 'SKIP', `Expected evidence: ${operation}`);
}

const completeBinding = evidence.every(item => item.actor_id && item.organization_id && item.provider === 'google-drive');
const intervals = evidence.every(item => item.temporal_interval?.semantics === 'half-open' && item.lineage?.node_id);
const canonical = evidence.every(item => item.replay_receipt?.canonicalization === 'ceip-jcs-nfc-v1' && /^[a-f0-9]{64}$/.test(item.replay_receipt?.canonical_hash || ''));
add('C3.1', evidence.length && completeBinding ? 'PASS' : evidence.length ? 'FAIL' : 'SKIP', 'CEIP actor/org/provider binding');
add('C3.2', evidence.length && intervals ? 'PASS' : evidence.length ? 'FAIL' : 'SKIP', 'Half-open intervals and lineage nodes');
add('C3.3', evidence.length && canonical ? 'PASS' : evidence.length ? 'FAIL' : 'SKIP', 'Canonical receipt and SHA-256');

const source = await readFile(path.join(root, 'services', 'platform-api', 'src', 'googleDrive.ts'), 'utf8');
add('C4.1', source.includes('HALT:EVIDENCE_ERROR') ? 'PASS' : 'FAIL', 'Evidence failure halt');
add('C4.2', source.includes('HALT:AUTHORITY_ERROR') ? 'PASS' : 'FAIL', 'Authority failure halt');
add('C4.3', source.includes('HALT:CANONICALIZATION_ERROR') ? 'PASS' : 'FAIL', 'Canonicalization failure halt');

const categoryPassed = prefix => statuses.filter(t => t.test_id.startsWith(prefix)).every(t => t.status === 'PASS');
let level = 0;
if (categoryPassed('C1.')) level = 1;
if (level === 1 && ['C2.1','C2.2','C2.3'].every(id => statuses.find(t => t.test_id === id)?.status === 'PASS')) level = 2;
if (level === 2 && categoryPassed('C2.')) level = 3;
if (level === 3 && categoryPassed('C3.')) level = 4;
if (level === 4 && categoryPassed('C4.')) level = 5;
const report = { suite: 'AAIS-DRIVE-CONFORMANCE-V1.0', vector: 'v1_0', generated_at: new Date().toISOString(), level_achieved: level, declaration: level === 5 ? 'AAIS-DRIVE-CONFORMANCE-V1.0-L5' : null, summary_digest: createHash('sha256').update(JSON.stringify(statuses)).digest('hex'), tests: statuses };
await mkdir(resultDir, { recursive: true });
await writeFile(path.join(resultDir, 'evidence_log_v1_0.json'), `${JSON.stringify(evidence, null, 2)}\n`);
await writeFile(path.join(resultDir, 'report_v1_0.json'), `${JSON.stringify(report, null, 2)}\n`);
console.table(statuses); console.log(`Conformance level achieved: ${level}`);
process.exit(statuses.some(test => test.status === 'FAIL') ? 1 : 0);
