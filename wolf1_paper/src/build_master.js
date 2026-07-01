#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sectionsDir = path.join(__dirname, 'sections');
const outFile = path.join(__dirname, 'wolf1_v1.1.md');

const HEADER = `# WOLF-1: Copilot in Orbit
## Architecture Document v1.1
**Project Infinity — AAIS / Mythar Root Systems**
**Author:** Jon Halstead
**Architectural review:** Bradley Bates (SkillsMcGee)
**Date:** June 25, 2026
**License:** Apache 2.0

---

`;

const ORDER = [
  '00_collaborator_credit.md',
  '01_mission_context.md',
  '02_system_architecture.md',
  '03_bus_architecture.md',
  '04_invariants.md',
  '04_9_invariant_promotion.md',
  '04_10_meta_governance_crk1.md',
  '05_power_propulsion.md',
  '06_sequence_diagram.md',
  '06_4_epistemic_receipts.md',
  '07_fault_taxonomy.md',
  '08_safe_mode.md',
  '08_5_graded_safe_mode.md',
  '09_secondary_systems.md',
  '10_cas_schemas.md',
  '11_llm_tenancy.md',
  '12_telemetry_observability.md',
  '12_4_anomaly_discovery.md',
  '13_conclusion.md',
  '14_constitutional_evolution.md',
];

let body = HEADER;
for (const file of ORDER) {
  const p = path.join(sectionsDir, file);
  if (!fs.existsSync(p)) {
    console.warn('skip missing', file);
    continue;
  }
  body += fs.readFileSync(p, 'utf8').trim() + '\n\n---\n\n';
}
body += '\n# End of Document\n**WOLF-1 Architecture Document v1.1**\n';

fs.writeFileSync(outFile, body, 'utf8');
console.log('Wrote', outFile);
