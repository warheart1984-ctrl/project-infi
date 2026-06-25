import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  bitsTo11BitIndices,
  decodeSymbolString,
  digitsToEntropy128,
  entropyToBip39Bits,
} from './reference_implementation.js';

type PipelineFromDigits = {
  digits: number[];
  entropyHex: string;
  bitsSha256: string;
  indices: number[];
  indicesSha256: string;
};

type PipelineFromGlyphs = PipelineFromDigits & {
  glyphs: string;
  glyphsSha256: string;
  decodedDigits: number[];
};

type ReproLock = {
  profile: 'Theta-BIP39-Encoding';
  version: '0.1';
  cases: {
    glyphs: PipelineFromGlyphs[];
    digits: PipelineFromDigits[];
  };
};

const canonicalCases = {
  glyphs: ['⊙|κ⊕|⊕.⊕', '⊙', 'κ⊕', '⊕|⊕|⊕'],
  digits: [
    [0, 2, 3, 0, 2, 3, 3, 3],
    [1, 1, 1, 1],
    [13, 13, 13, 13],
    [0, 0, 0, 0],
  ],
} as const;

const here = dirname(fileURLToPath(import.meta.url));
const lockfilePath = resolve(here, 'reproducibility_lock.json');

export function hashString(value: string): string {
  return createHash('sha256').update(value, 'utf8').digest('hex');
}

export function pipelineFromDigits(digits: readonly number[]): PipelineFromDigits {
  const digitArray = [...digits];
  const entropy = digitsToEntropy128(digitArray);
  const bits = entropyToBip39Bits(entropy);
  const indices = bitsTo11BitIndices(bits);
  return {
    digits: digitArray,
    entropyHex: entropy.toString('hex'),
    bitsSha256: hashString(bits),
    indices,
    indicesSha256: hashString(JSON.stringify(indices)),
  };
}

export function pipelineFromGlyphs(glyphs: string): PipelineFromGlyphs {
  const decodedDigits = decodeSymbolString(glyphs).digits;
  return {
    glyphs,
    glyphsSha256: hashString(glyphs),
    decodedDigits,
    ...pipelineFromDigits(decodedDigits),
  };
}

export function generateReproLock(): ReproLock {
  return {
    profile: 'Theta-BIP39-Encoding',
    version: '0.1',
    cases: {
      glyphs: canonicalCases.glyphs.map((glyphs) => pipelineFromGlyphs(glyphs)),
      digits: canonicalCases.digits.map((digits) => pipelineFromDigits(digits)),
    },
  };
}

export function verifyReproLock(stored: ReproLock): void {
  const current = generateReproLock();
  if (JSON.stringify(current) !== JSON.stringify(stored)) {
    throw new Error('Theta-BIP39 v0.1 reproducibility lock drifted');
  }
}

function main(): void {
  const mode = process.argv[2];
  if (mode !== '--generate' && mode !== '--verify') {
    throw new Error('Usage: tsx scripts/reproducibility-harness.ts [--generate|--verify]');
  }

  if (mode === '--generate') {
    writeFileSync(lockfilePath, `${JSON.stringify(generateReproLock(), null, 2)}\n`);
    console.log(`Wrote lockfile: ${lockfilePath}`);
    return;
  }

  verifyReproLock(JSON.parse(readFileSync(lockfilePath, 'utf8')) as ReproLock);
  console.log('Reproducibility check: PASS (all hashes match)');
}

main();
