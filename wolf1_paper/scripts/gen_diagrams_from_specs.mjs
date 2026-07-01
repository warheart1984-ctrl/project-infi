import fs from 'fs';
import path from 'path';
import { parse } from 'yaml';
import { ROOT } from './lib/paths.mjs';
import { getDocument } from './lib/version.mjs';

const doc = getDocument('wolf1-arch');
const diagramsDir = path.join(ROOT, doc.diagrams_dir || 'assets/diagrams');
const specPath = path.join(ROOT, 'specs', 'diagram-specs.yaml');

const defaultSpecs = {
  safe_mode_profiles: {
    output: 'safe_mode_profiles.mmd',
    type: 'flowchart',
    states: ['S0: Full Operations', 'S1: Cognitive Degradation', 'S2: Autonomy Degradation', 'S3: Governance-Only'],
    forward: true,
    reverse: true,
  },
  invariant_promotion: {
    output: 'invariant_promotion_flow.mmd',
    type: 'flowchart',
    states: [
      'Observation',
      'Hypothesis',
      'Stress-Testing',
      'Redundancy Analysis',
      'Constitutional Review',
      'Adoption',
    ],
    forward: true,
    reverse: false,
  },
};

function flowchartFromStates(name, states, { forward, reverse }) {
  let m = 'flowchart LR\n';
  const ids = states.map((s, i) => `S${i}`);
  for (let i = 0; i < states.length; i++) {
    m += `  ${ids[i]}["${states[i]}"]\n`;
  }
  if (forward) {
    for (let i = 0; i < ids.length - 1; i++) {
      m += `  ${ids[i]} --> ${ids[i + 1]}\n`;
    }
  }
  if (reverse && ids.length > 1) {
    for (let i = ids.length - 1; i > 0; i--) {
      m += `  ${ids[i]} -. recovery .-> ${ids[i - 1]}\n`;
    }
  }
  return m;
}

let specs = defaultSpecs;
if (fs.existsSync(specPath)) {
  specs = { ...defaultSpecs, ...parse(fs.readFileSync(specPath, 'utf8')) };
}

fs.mkdirSync(diagramsDir, { recursive: true });

for (const [key, spec] of Object.entries(specs)) {
  if (spec.type !== 'flowchart' || !spec.states) continue;
  const mmd = flowchartFromStates(key, spec.states, spec);
  const out = path.join(diagramsDir, spec.output);
  fs.writeFileSync(out, mmd, 'utf8');
  console.log('[DIAGRAMS] Wrote', path.relative(ROOT, out));
}

console.log('[DIAGRAMS] Done (SVG render requires @mermaid-js/mermaid-cli if needed)');
