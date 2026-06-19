import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import {
  bitsTo11BitIndices,
  decodeWithAllLayers,
  deriveDigitToThetaIndices,
  digitsToBip39Seed,
  digitsToEntropy128,
  encodeDigitsToGlyphString,
  entropyToBip39Bits,
  findMissingReverseDigits,
  glyphToDigitsForward,
  indicesToMnemonic,
  mnemonicToSeed,
  resolveGlyphToThetaIndices,
  seedToEntropy128,
  thetaBip39Profile,
  thetaMap,
} from './reference_implementation.js';

const profileDir = resolve(dirname(fileURLToPath(import.meta.url)), '../profile');
const workspaceRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');

describe('theta codec', () => {
  it('declares the implemented Theta-BIP39 v0.1 profile', () => {
    expect(thetaBip39Profile).toEqual({
      profile: 'Theta-BIP39-Encoding',
      version: '0.1',
      status: 'stable',
      description: 'Deterministic Theta->digit->entropy->BIP39 encoding pipeline.',
      invariants: {
        R1: expect.stringContaining('Theta-reverse correctness'),
        D1: expect.stringContaining('pure function'),
      },
    });
  });

  it('decodes glyphs through Theta indices into base-14 digits and derived artifacts', () => {
    const result = decodeWithAllLayers('⊕|Θ|λ|◆');

    expect(result.glyphs).toEqual(['⊕', 'Θ', 'λ', '◆']);
    expect(result.thetaIndices).toEqual([9, 7, 8, 6]);
    expect(result.digits).toEqual([3, 5, 6, 11]);
    expect(result.valueDecimal).toBe('9307');
    expect(result.tier).toBe('Tier 300+');
    expect(result.qrSafeWithChecksum).toBe('ERNZEZBPY4======');
    expect(result.entropy128Hex).toBe('90eb0470e3a2d088cb626cbf03ef44a1');
  });

  it('derives a Theta-consistent reverse map from theta and digit tables', () => {
    expect(deriveDigitToThetaIndices()).toEqual({
      0: [0, 14],
      1: [2],
      2: [1],
      3: [1, 9],
      4: [3],
      5: [7],
      6: [8],
      7: [4],
      8: [10],
      9: [11],
      10: [13],
      11: [6],
      12: [12],
      13: [5],
    });

    expect(encodeDigitsToGlyphString([0, 2, 3, 0, 5, 6, 11, 13])).toBe('⊙|κ⊕|κ⊕|⊙|Θ|λ|◆|⟡');
  });

  it('rejects digits outside the base-14 space', () => {
    expect(() => encodeDigitsToGlyphString([14])).toThrow('No Theta indices for digit 14');
  });

  it('keeps fuzzy correction outside the canonical decoder path', () => {
    expect(() => decodeWithAllLayers('not-a-theta-glyph')).toThrow('Cannot resolve glyph to Theta indices');
    expect(() => resolveGlyphToThetaIndices('not-a-theta-glyph')).toThrow('Cannot resolve glyph to Theta indices');
  });

  it('satisfies Theta reverse correctness for every derived reverse digit path', () => {
    const digitToThetaIndices = deriveDigitToThetaIndices();

    for (const [digitText, thetaIndices] of Object.entries(digitToThetaIndices)) {
      const digit = Number(digitText);
      for (const thetaIndex of thetaIndices) {
        expect(glyphToDigitsForward(thetaMap[thetaIndex])).toContain(digit);
      }
    }
  });

  it('satisfies v0.1 digit-space coverage and reports strict-mode compound coverage', () => {
    expect(findMissingReverseDigits()).toEqual([]);
    expect(findMissingReverseDigits({ strictSingleDigit: true })).toEqual([2]);
  });

  it('documents that non-strict compound glyphs are R1-safe but not one-digit round trips', () => {
    const encoded = encodeDigitsToGlyphString([2]);
    const decoded = decodeWithAllLayers(encoded);

    expect(encoded).toBe('κ⊕');
    expect(decoded.digits).toEqual([2, 3]);
  });

  it('fuzzes strict single-digit Theta round trips over the encodable digit space', () => {
    const encodableDigits = Object.keys(deriveDigitToThetaIndices({ strictSingleDigit: true })).map(Number);
    const rng = seededRandom(42);

    for (let run = 0; run < 200; run += 1) {
      const length = 1 + Math.floor(rng() * 16);
      const digits = Array.from({ length }, () => encodableDigits[Math.floor(rng() * encodableDigits.length)]);
      const glyphString = encodeDigitsToGlyphString(digits, { strictSingleDigit: true });
      const decoded = decodeWithAllLayers(glyphString);

      expect(digitsToEntropy128(decoded.digits).toString('hex')).toBe(digitsToEntropy128(digits).toString('hex'));
    }
  });

  it('projects digit entropy into BIP-39 checksum bits, word indices, and seed material', () => {
    const entropy = Buffer.from('6cc546d381bf25d1928c514d6e3ba65f', 'hex');
    const bitstring = entropyToBip39Bits(entropy);

    expect(bitstring).toHaveLength(132);
    expect(bitstring.slice(-4)).toBe('0010');
    expect(bitsTo11BitIndices(bitstring)).toEqual([870, 337, 1447, 27, 1938, 1862, 593, 1105, 619, 910, 1868, 1522]);

    const wordlist = Array.from({ length: 2048 }, (_, index) => `word${String(index).padStart(4, '0')}`);
    const result = digitsToBip39Seed([0, 2, 3, 0, 5, 6, 11], wordlist, 'operator');

    expect(result.entropyHex).toBe('6cc546d381bf25d1928c514d6e3ba65f');
    expect(result.indices).toEqual([870, 337, 1447, 27, 1938, 1862, 593, 1105, 619, 910, 1868, 1522]);
    expect(result.mnemonicWords).toEqual([
      'word0870',
      'word0337',
      'word1447',
      'word0027',
      'word1938',
      'word1862',
      'word0593',
      'word1105',
      'word0619',
      'word0910',
      'word1868',
      'word1522',
    ]);
    expect(result.seedHex).toBe(
      '53d5aa1c2cffcd6287ce35996c9a9ea84b4ea1f2e3e2dd52dcd7b96641f78598fcd4185606d0dfc0178ee1ea61fbfa8bad19163f5c119fb04e64b1802193f51a',
    );
  });

  it('keeps BIP-39 projection deterministic and treats seed feedback as a new projection', () => {
    const wordlist = Array.from({ length: 2048 }, (_, index) => `w${index}`);
    const vectors = [
      [0, 2, 3, 0, 2, 3, 3, 3],
      [1, 1, 1, 1],
      [13, 13, 13, 13, 13],
      [0, 0, 0, 0, 0, 0, 0, 0],
      [3, 6, 9, 12, 5, 2, 8, 11, 10],
    ];

    for (const digits of vectors) {
      const first = digitsToBip39Seed(digits, wordlist);
      const second = digitsToBip39Seed(digits, wordlist);
      expect(second).toEqual(first);

      const seedFeedbackEntropy = seedToEntropy128(Buffer.from(first.seedHex, 'hex'));
      const feedbackBits = entropyToBip39Bits(seedFeedbackEntropy);
      const feedbackIndices = bitsTo11BitIndices(feedbackBits);
      const feedbackSeed = mnemonicToSeed(indicesToMnemonic(feedbackIndices, wordlist)).toString('hex');

      expect(feedbackIndices).not.toEqual(first.indices);
      expect(feedbackSeed).not.toBe(first.seedHex);
    }
  });

  it('ships the v0.1 profile spec pack and reproducibility lock', () => {
    const requiredFiles = [
      'theta-bip39-profile.v0.1.json',
      'theta-bip39-profile.v0.1.toml',
      'README.md',
      'GOVERNANCE_CHARTER.md',
      'SECURITY_AUDIT_CHECKLIST.md',
      'FORMAL_VERIFICATION_PLAN.md',
      'VERIFICATION_REPORT_TEMPLATE.md',
      'VERIFICATION_REPORT_EXAMPLE.md',
      'THREAT_MITIGATION_MATRIX.md',
      'ARCHITECTURE.md',
      'COMPLIANCE_CHECKLIST.md',
      'PROFILE_CHANGE_PROPOSAL_TEMPLATE.md',
      'MIGRATION_V0_1_TO_V0_2.md',
      'SPEC_PACK_MANIFEST.txt',
      'conformance-badge.svg',
      'conformance-badge-ascii.txt',
      'ci-pipeline.yml',
      'repro-lock-v0.1.json',
    ];

    for (const file of requiredFiles) {
      expect(existsSync(resolve(profileDir, file)), file).toBe(true);
    }

    const lock = JSON.parse(readFileSync(resolve(profileDir, 'repro-lock-v0.1.json'), 'utf8')) as {
      profile: string;
      version: string;
      cases: {
        glyphs: Array<{
          glyphs: string;
          decodedDigits: number[];
          entropyHex: string;
          bitsSha256: string;
          indices: number[];
          indicesSha256: string;
        }>;
        digits: Array<{
          digits: number[];
          entropyHex: string;
          bitsSha256: string;
          indices: number[];
          indicesSha256: string;
        }>;
      };
    };

    expect(lock.profile).toBe('Theta-BIP39-Encoding');
    expect(lock.version).toBe('0.1');

    for (const glyphCase of lock.cases.glyphs) {
      const decoded = decodeWithAllLayers(glyphCase.glyphs);
      expect(decoded.digits).toEqual(glyphCase.decodedDigits);
      expect(decoded.entropy128Hex).toBe(glyphCase.entropyHex);

      const bitstring = entropyToBip39Bits(Buffer.from(glyphCase.entropyHex, 'hex'));
      const indices = bitsTo11BitIndices(bitstring);
      expect(hashString(bitstring)).toBe(glyphCase.bitsSha256);
      expect(indices).toEqual(glyphCase.indices);
      expect(hashString(JSON.stringify(indices))).toBe(glyphCase.indicesSha256);
    }

    for (const digitCase of lock.cases.digits) {
      const entropy = digitsToEntropy128(digitCase.digits);
      const bitstring = entropyToBip39Bits(entropy);
      const indices = bitsTo11BitIndices(bitstring);
      expect(entropy.toString('hex')).toBe(digitCase.entropyHex);
      expect(hashString(bitstring)).toBe(digitCase.bitsSha256);
      expect(indices).toEqual(digitCase.indices);
      expect(hashString(JSON.stringify(indices))).toBe(digitCase.indicesSha256);
    }
  });

  it('publishes Profile v0.1 as a governed AAES/NexusOS standard', () => {
    const standardDir = resolve(workspaceRoot, 'standards/theta-bip39/v0.1');
    const artifactPath = resolve(workspaceRoot, 'governance/artifacts/theta-bip39-profile-v0.1/artifact.json');
    const requiredStandardFiles = [
      'manifest.json',
      'README.md',
      'governance_charter.md',
      'formal_verification_plan.md',
      'threat_mitigation_matrix.md',
      'conformance_badge.svg',
      'verification_report_template.md',
      'verification_report_example.md',
      'reproducibility_lock.json',
      'reference_implementation.ts',
      'test_runner.ts',
      'reproducibility_harness.ts',
      'profile_diff.ts',
      'theta-bip39-profile-v0.1-spec.md',
      'test_vectors.json',
      'IMPLEMENTATION_GUIDE.md',
    ];

    for (const file of requiredStandardFiles) {
      expect(existsSync(resolve(standardDir, file)), file).toBe(true);
    }

    expect(existsSync(resolve(workspaceRoot, 'nexus/governance/modules/theta-bip39-v0.1.md'))).toBe(true);
    expect(existsSync(resolve(workspaceRoot, 'developers/onboarding/theta-bip39-v0.1.md'))).toBe(true);

    const artifact = JSON.parse(readFileSync(artifactPath, 'utf8')) as {
      artifact_id: string;
      status: string;
      hashes: Record<string, string>;
    };

    expect(artifact.artifact_id).toBe('theta-bip39-profile-v0.1');
    expect(artifact.status).toBe('verified');
    expect(artifact.hashes.manifest_json_sha256).toBe(hashFile(resolve(standardDir, 'manifest.json')));
    expect(artifact.hashes.spec_markdown_sha256).toBe(
      hashFile(resolve(standardDir, 'theta-bip39-profile-v0.1-spec.md')),
    );
    expect(artifact.hashes.test_vectors_json_sha256).toBe(hashFile(resolve(standardDir, 'test_vectors.json')));
    expect(artifact.hashes.reproducibility_lock_sha256).toBe(
      hashFile(resolve(standardDir, 'reproducibility_lock.json')),
    );
    expect(artifact.hashes.reference_implementation_sha256).toBe(
      hashFile(resolve(standardDir, 'reference_implementation.ts')),
    );
    expect(artifact.hashes.test_runner_sha256).toBe(hashFile(resolve(standardDir, 'test_runner.ts')));
    expect(artifact.hashes.reproducibility_harness_sha256).toBe(
      hashFile(resolve(standardDir, 'reproducibility_harness.ts')),
    );
    expect(artifact.hashes.profile_diff_sha256).toBe(hashFile(resolve(standardDir, 'profile_diff.ts')));
    expect(artifact.hashes.nexus_governance_module_sha256).toBe(
      hashFile(resolve(workspaceRoot, 'nexus/governance/modules/theta-bip39-v0.1.md')),
    );
    expect(artifact.hashes.developer_onboarding_sha256).toBe(
      hashFile(resolve(workspaceRoot, 'developers/onboarding/theta-bip39-v0.1.md')),
    );
  });
});

function hashString(value: string): string {
  return createHash('sha256').update(value, 'utf8').digest('hex');
}

function hashFile(path: string): string {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}
