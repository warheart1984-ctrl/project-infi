import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { generateCisConformanceSuiteInput } from '../../tools/cis-conformance.js';

describe('cis conformance suite generation', () => {
  it('matches the committed suite input generated from the hierarchy traceability matrix', () => {
    const generated = generateCisConformanceSuiteInput();
    const committed = JSON.parse(
      readFileSync(path.join(process.cwd(), 'docs', 'crk1', 'release', 'CIS_CONFORMANCE_SUITE_INPUT.spec.json'), 'utf8'),
    ) as typeof generated;

    expect(generated).toEqual(committed);
  });
});
