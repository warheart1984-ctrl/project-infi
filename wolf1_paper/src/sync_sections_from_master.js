#!/usr/bin/env node
/**
 * Split wolf1_v1.1.md (canonical master) into src/sections/*.md
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const masterPath = path.join(__dirname, 'wolf1_v1.1.md');
const sectionsDir = path.join(__dirname, 'sections');

const master = fs.readFileSync(masterPath, 'utf8');

/** Extract content from start marker (inclusive) to end marker (exclusive). */
function sliceBetween(text, start, end) {
  const i = text.indexOf(start);
  if (i === -1) throw new Error(`start not found: ${start}`);
  const j = end ? text.indexOf(end, i + start.length) : text.length;
  if (end && j === -1) throw new Error(`end not found: ${end}`);
  return text.slice(i, j).trim();
}

const COLLABORATOR = `# Collaborator Credit — Bradley Bates

**Bradley Bates** (review handle: *SkillsMcGee*) contributed substantive architectural critique during the WOLF-1 review cycle. Sections 4.9, 4.10, 6.4, 8.5, 12.4, and 14 were added or strengthened in direct response.

| # | Critique | Section | Status |
|---|----------|---------|--------|
| 1 | Who watches CRK-1? | 4.10 | Resolved — PE/SE evaluators |
| 2 | Where do the 12 invariants come from? | 4.9 | Resolved — promotion pipeline |
| 3 | Receipt ≠ truth | 6.4 | Partial — flags deviation, does not certify truth |
| 4 | Safe-mode should not be binary | 8.5 | Resolved — S0–S3 profiles |
| 5 | Where is anomaly discovery? | 12.4 | Resolved |
| 6 | No architecture for evolution | 14 | Resolved — M0–M4 protocol |
| 7 | Governance mandatory, cognition optional | 1 | Resolved — core principle |

Full traceability map: \`docs/wolf1/Bradley_Bates_Critique_Resolution_Map.md\`
`;

const sections = {
  '00_collaborator_credit.md': COLLABORATOR,
  '01_mission_context.md': sliceBetween(master, '# 1. Mission Context', '# 2. System Architecture'),
  '02_system_architecture.md': sliceBetween(master, '# 2. System Architecture', '# 3. Spacecraft Bus'),
  '03_bus_architecture.md': sliceBetween(master, '# 3. Spacecraft Bus', '# 4. Constitutional Invariant'),
  '04_invariants.md': sliceBetween(master, '# 4. Constitutional Invariant', '## 4.9 Invariant Promotion'),
  '04_9_invariant_promotion.md': sliceBetween(master, '## 4.9 Invariant Promotion', '## 4.10 Meta'),
  '04_10_meta_governance_crk1.md': sliceBetween(master, '## 4.10 Meta', '# 5. Power / Propulsion'),
  '05_power_propulsion.md': sliceBetween(master, '# 5. Power / Propulsion', '# 6. Formal Sequence'),
  '06_sequence_diagram.md': sliceBetween(master, '# 6. Formal Sequence', '## 6.4 Epistemic Receipts'),
  '06_4_epistemic_receipts.md': sliceBetween(master, '## 6.4 Epistemic Receipts', '# 7. Fault Code'),
  '07_fault_taxonomy.md': sliceBetween(master, '# 7. Fault Code', '# 8. Safe'),
  '08_safe_mode.md': sliceBetween(master, '# 8. Safe', '## 8.5 Graded Safe'),
  '08_5_graded_safe_mode.md': sliceBetween(master, '## 8.5 Graded Safe', '# 9. Secondary Systems'),
  '09_secondary_systems.md': sliceBetween(master, '# 9. Secondary Systems', '# 10. CAS Object'),
  '10_cas_schemas.md': sliceBetween(master, '# 10. CAS Object', '# 11. LLM Tenancy'),
  '11_llm_tenancy.md': sliceBetween(master, '# 11. LLM Tenancy', '# 12. Telemetry'),
  '12_telemetry_observability.md': sliceBetween(master, '# 12. Telemetry', '## 12.4 Anomaly Discovery'),
  '12_4_anomaly_discovery.md': sliceBetween(master, '## 12.4 Anomaly Discovery', '# 13. Conclusion'),
  '13_conclusion.md': sliceBetween(master, '# 13. Conclusion', '# 14. Constitutional Evolution'),
  '14_constitutional_evolution.md': sliceBetween(master, '# 14. Constitutional Evolution', '# End of Document'),
};

fs.mkdirSync(sectionsDir, { recursive: true });
for (const [file, content] of Object.entries(sections)) {
  const out = path.join(sectionsDir, file);
  fs.writeFileSync(out, content.trim() + '\n', 'utf8');
  console.log('wrote', file, `(${content.length} chars)`);
}
console.log('Synced', Object.keys(sections).length, 'sections from master.');
