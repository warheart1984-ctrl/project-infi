import { createHash, pbkdf2Sync } from 'node:crypto';

export type DigitChoice = {
  digit: number;
  probability: number;
};

export type DecodeSymbolResult = {
  glyphs: string[];
  thetaIndices: number[];
  digits: number[];
  digitProbabilities: number[];
  value: bigint;
  valueDecimal: string;
  tier: string;
};

export type DecodeAllLayersResult = DecodeSymbolResult & {
  qrSafeWithChecksum: string;
  entropy128Hex: string;
};

export type Bip39Projection = {
  entropyHex: string;
  bitstring: string;
  indices: number[];
  mnemonicWords: string[];
  seedHex: string;
};

export type ReverseChoreographyOptions = {
  strictSingleDigit?: boolean;
};

export type GlyphResolutionOptions = {
  allowCorrection?: boolean;
};

export const thetaBip39Profile = {
  profile: 'Theta-BIP39-Encoding',
  version: '0.1',
  status: 'stable',
  description: 'Deterministic Theta->digit->entropy->BIP39 encoding pipeline.',
  invariants: {
    R1: 'Theta-reverse correctness: reverse(d) selects only Theta indices whose forward expansion contains d.',
    D1: 'BIP-39 determinism: digits->entropy->bits->indices->seed is a pure function.',
  },
} as const;

export const digitMap: Readonly<Record<number, readonly string[]>> = {
  0: ['⊙'],
  1: ['β'],
  2: ['κ'],
  3: ['⊕'],
  4: ['ψ'],
  5: ['Θ'],
  6: ['λ', 'ρ', 'δ', 'γ', 'φ', 'ξ'],
  7: ['⬄'],
  8: ['ℏ', 'τ'],
  9: ['e⁻'],
  10: ['♀'],
  11: ['◆'],
  12: ['⚜'],
  13: ['⟡', '≈'],
};

export const digitLookup: Readonly<Record<string, number>> = Object.freeze(
  Object.fromEntries(
    Object.entries(digitMap).flatMap(([digit, glyphs]) => glyphs.map((glyph) => [glyph, Number(digit)])),
  ),
);

export const thetaMap: Readonly<Record<number, string>> = {
  0: '⊙',
  1: 'κ⊕',
  2: 'β',
  3: 'ψ',
  4: '⬄',
  5: '⟡',
  6: '◆',
  7: 'Θ',
  8: 'λ',
  9: '⊕',
  10: 'ℏ',
  11: 'e⁻',
  12: '⚜',
  13: '♀',
  14: '⊙',
};

export const glyphToThetaPairs: Readonly<Record<string, readonly number[]>> = {
  '⊙': [0, 1, 14],
  'κ⊕': [11, 3],
  'Θ': [7, 8],
  '♀': [6, 9],
  'σ≈': [4, 13],
};

export const glyphDigitProbabilities: Readonly<Record<string, Readonly<Record<number, number>>>> = {
  '⊙': { 0: 0.7, 13: 0.3 },
  '⟡': { 13: 1.0 },
  '≈': { 13: 1.0 },
};

const base32Alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

export function thetaLookup(): Record<string, number[]> {
  const lookup: Record<string, number[]> = {};
  for (const [index, glyph] of Object.entries(thetaMap)) {
    lookup[glyph] ??= [];
    lookup[glyph].push(Number(index));
  }
  return lookup;
}

export function tokenize(input: string): string[] {
  return input
    .split('|')
    .flatMap((part) => part.split('.'))
    .filter((token) => token.length > 0);
}

export function chooseDigitForGlyph(glyph: string): DigitChoice {
  const digit = digitLookup[glyph];
  if (digit !== undefined) {
    return { digit, probability: 1.0 };
  }

  const probabilities = glyphDigitProbabilities[glyph];
  if (probabilities) {
    const [digit, probability] = Object.entries(probabilities)
      .map(([candidate, value]) => [Number(candidate), value] as const)
      .sort((left, right) => right[1] - left[1])[0];
    return { digit, probability };
  }

  throw new Error(`No digit mapping for glyph: ${glyph}`);
}

export function nearestGlyph(token: string): string {
  const candidates = new Set<string>([
    ...Object.keys(glyphToThetaPairs),
    ...Object.keys(thetaLookup()),
    ...Object.keys(digitLookup),
  ]);

  let best: { glyph: string; score: number } | undefined;
  for (const candidate of candidates) {
    const score = similarity(token, candidate);
    if (!best || score > best.score) {
      best = { glyph: candidate, score };
    }
  }

  if (best && best.score >= 0.6) {
    return best.glyph;
  }

  throw new Error(`Uncorrectable glyph: ${token}`);
}

export function resolveGlyphToThetaIndices(glyph: string, options: GlyphResolutionOptions = {}): number[] {
  const canonical = thetaLookup()[glyph];
  if (canonical) {
    return [canonical[0]];
  }

  const explicit = glyphToThetaPairs[glyph];
  if (explicit) {
    return [...explicit];
  }

  if (!options.allowCorrection) {
    throw new Error(`Cannot resolve glyph to Theta indices: ${glyph}`);
  }

  const corrected = nearestGlyph(glyph);
  const correctedCanonical = thetaLookup()[corrected];
  if (correctedCanonical) {
    return [correctedCanonical[0]];
  }

  const correctedExplicit = glyphToThetaPairs[corrected];
  if (correctedExplicit) {
    return [...correctedExplicit];
  }

  throw new Error(`Cannot resolve glyph to Theta indices: ${glyph}`);
}

export function decodeSymbolString(input: string): DecodeSymbolResult {
  const glyphs = tokenize(input);
  const thetaIndices = glyphs.flatMap((glyph) => resolveGlyphToThetaIndices(glyph));
  const digits: number[] = [];
  const digitProbabilities: number[] = [];

  for (const thetaIndex of thetaIndices) {
    const glyph = thetaMap[thetaIndex];
    if (!glyph) {
      throw new Error(`No Theta mapping for index: ${thetaIndex}`);
    }

    const choices = digitChoicesForThetaGlyph(glyph);
    for (const choice of choices) {
      digits.push(choice.digit);
      digitProbabilities.push(choice.probability);
    }
  }

  const value = digitsToBigInt(digits);
  return {
    glyphs,
    thetaIndices,
    digits,
    digitProbabilities,
    value,
    valueDecimal: value.toString(10),
    tier: classifyTier(value),
  };
}

export function classifyTier(value: bigint | number): string {
  const comparable = typeof value === 'bigint' ? value : BigInt(value);
  if (comparable < 25n) return 'Tier 0-25';
  if (comparable < 100n) return 'Tier 25-100';
  if (comparable < 300n) return 'Tier 100-300';
  return 'Tier 300+';
}

export function deriveDigitToThetaIndices(options: ReverseChoreographyOptions = {}): Record<number, number[]> {
  const digitToThetaIndices: Record<number, number[]> = {};
  for (const [thetaIndexText, glyph] of Object.entries(thetaMap)) {
    const thetaIndex = Number(thetaIndexText);
    const digits = glyphToDigitsForward(glyph);
    if (options.strictSingleDigit && digits.length !== 1) {
      continue;
    }

    for (const digit of digits) {
      digitToThetaIndices[digit] ??= [];
      digitToThetaIndices[digit].push(thetaIndex);
    }
  }
  return Object.fromEntries(
    Object.entries(digitToThetaIndices).map(([digit, indices]) => [digit, [...new Set(indices)].sort((a, b) => a - b)]),
  );
}

export function findMissingReverseDigits(options: ReverseChoreographyOptions = {}): number[] {
  const digitToThetaIndices = deriveDigitToThetaIndices(options);
  return Array.from({ length: 14 }, (_, digit) => digit).filter((digit) => !digitToThetaIndices[digit]?.length);
}

export function glyphToDigitsForward(glyph: string): number[] {
  if (digitLookup[glyph] !== undefined) {
    return [digitLookup[glyph]];
  }

  return Array.from(glyph)
    .filter((character) => digitLookup[character] !== undefined)
    .map((character) => digitLookup[character]);
}

export function digitsToThetaIndices(digits: number[], options: ReverseChoreographyOptions = {}): number[] {
  const digitToThetaIndices = deriveDigitToThetaIndices(options);
  const counters: Record<number, number> = {};

  return digits.map((digit) => {
    const indices = digitToThetaIndices[digit];
    if (!indices?.length) {
      throw new Error(`No Theta indices for digit ${digit}`);
    }
    const next = counters[digit] ?? 0;
    counters[digit] = next + 1;
    return indices[next % indices.length];
  });
}

export function thetaIndicesToGlyphs(thetaIndices: number[]): string[] {
  return thetaIndices.map((thetaIndex) => {
    const glyph = thetaMap[thetaIndex];
    if (!glyph) {
      throw new Error(`No Theta mapping for index: ${thetaIndex}`);
    }
    return glyph;
  });
}

export function encodeDigitsToGlyphString(digits: number[], options: ReverseChoreographyOptions = {}): string {
  return thetaIndicesToGlyphs(digitsToThetaIndices(digits, options)).join('|');
}

export function digitsToBytes(digits: number[]): Buffer {
  let value = digitsToBigInt(digits);
  if (value === 0n) {
    return Buffer.from([0]);
  }

  const bytes: number[] = [];
  while (value > 0n) {
    bytes.push(Number(value & 0xffn));
    value >>= 8n;
  }
  return Buffer.from(bytes.reverse());
}

export function qrSafeEncode(digits: number[]): string {
  return base32Encode(digitsToBytes(digits));
}

export function addChecksum(payload: Buffer): Buffer {
  const first = createHash('sha256').update(payload).digest();
  const second = createHash('sha256').update(first).digest();
  return Buffer.concat([payload, second.subarray(0, 4)]);
}

export function verifyChecksum(data: Buffer): boolean {
  if (data.length < 5) return false;
  const payload = data.subarray(0, -4);
  const checksum = data.subarray(-4);
  const first = createHash('sha256').update(payload).digest();
  const second = createHash('sha256').update(first).digest();
  return checksum.equals(second.subarray(0, 4));
}

export function digitsToEntropy128(digits: number[]): Buffer {
  return createHash('sha256').update(digitsToBytes(digits)).digest().subarray(0, 16);
}

export function seedToEntropy128(seed: Buffer): Buffer {
  return createHash('sha256').update(seed).digest().subarray(0, 16);
}

export function decodeWithAllLayers(input: string): DecodeAllLayersResult {
  const core = decodeSymbolString(input);
  const payload = digitsToBytes(core.digits);
  return {
    ...core,
    qrSafeWithChecksum: base32Encode(addChecksum(payload)),
    entropy128Hex: digitsToEntropy128(core.digits).toString('hex'),
  };
}

export function entropyToBip39Bits(entropy: Buffer): string {
  const entropyLength = entropy.length * 8;
  if (entropyLength === 0 || entropyLength % 32 !== 0) {
    throw new Error('BIP-39 entropy length must be a non-zero multiple of 32 bits');
  }

  const checksumLength = entropyLength / 32;
  const checksumBits = bufferToBitString(createHash('sha256').update(entropy).digest()).slice(0, checksumLength);
  return bufferToBitString(entropy) + checksumBits;
}

export function bitsTo11BitIndices(bitstring: string): number[] {
  if (bitstring.length % 11 !== 0) {
    throw new Error('BIP-39 bitstring length must be divisible by 11');
  }

  const indices: number[] = [];
  for (let index = 0; index < bitstring.length; index += 11) {
    indices.push(Number.parseInt(bitstring.slice(index, index + 11), 2));
  }
  return indices;
}

export function indicesToMnemonic(indices: number[], wordlist: string[]): string[] {
  if (wordlist.length !== 2048) {
    throw new Error('BIP-39 wordlist must contain exactly 2048 words');
  }

  return indices.map((index) => {
    const word = wordlist[index];
    if (!word) {
      throw new Error(`No BIP-39 word for index ${index}`);
    }
    return word;
  });
}

export function mnemonicToSeed(mnemonicWords: string[], passphrase = ''): Buffer {
  return pbkdf2Sync(
    Buffer.from(mnemonicWords.join(' '), 'utf8'),
    Buffer.from(`mnemonic${passphrase}`, 'utf8'),
    2048,
    64,
    'sha512',
  );
}

export function digitsToBip39Seed(digits: number[], wordlist: string[], passphrase = ''): Bip39Projection {
  const entropy = digitsToEntropy128(digits);
  const bitstring = entropyToBip39Bits(entropy);
  const indices = bitsTo11BitIndices(bitstring);
  const mnemonicWords = indicesToMnemonic(indices, wordlist);
  const seed = mnemonicToSeed(mnemonicWords, passphrase);
  return {
    entropyHex: entropy.toString('hex'),
    bitstring,
    indices,
    mnemonicWords,
    seedHex: seed.toString('hex'),
  };
}

function digitChoicesForThetaGlyph(glyph: string): DigitChoice[] {
  if (digitLookup[glyph] !== undefined || glyphDigitProbabilities[glyph]) {
    return [chooseDigitForGlyph(glyph)];
  }

  const choices = Array.from(glyph)
    .filter((character) => digitLookup[character] !== undefined || glyphDigitProbabilities[character])
    .map((character) => chooseDigitForGlyph(character));

  if (!choices.length) {
    throw new Error(`No digit mapping for Theta glyph: ${glyph}`);
  }
  return choices;
}

function digitsToBigInt(digits: number[]): bigint {
  let value = 0n;
  for (const digit of digits) {
    if (!Number.isInteger(digit) || digit < 0 || digit > 13) {
      throw new Error(`Digit must be an integer in base-14 range 0-13: ${digit}`);
    }
    value = value * 14n + BigInt(digit);
  }
  return value;
}

function base32Encode(data: Buffer): string {
  let bits = 0;
  let value = 0;
  let output = '';

  for (const byte of data) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      output += base32Alphabet[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }

  if (bits > 0) {
    output += base32Alphabet[(value << (5 - bits)) & 31];
  }

  while (output.length % 8 !== 0) {
    output += '=';
  }

  return output;
}

function bufferToBitString(buffer: Buffer): string {
  return Array.from(buffer)
    .map((byte) => byte.toString(2).padStart(8, '0'))
    .join('');
}

function similarity(left: string, right: string): number {
  if (left === right) return 1;
  const leftChars = Array.from(left);
  const rightChars = Array.from(right);
  const distance = levenshtein(leftChars, rightChars);
  return 1 - distance / Math.max(leftChars.length, rightChars.length, 1);
}

function levenshtein(left: string[], right: string[]): number {
  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  const current = Array.from({ length: right.length + 1 }, () => 0);

  for (let i = 1; i <= left.length; i += 1) {
    current[0] = i;
    for (let j = 1; j <= right.length; j += 1) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      current[j] = Math.min(
        current[j - 1] + 1,
        previous[j] + 1,
        previous[j - 1] + cost,
      );
    }
    previous.splice(0, previous.length, ...current);
  }

  return previous[right.length];
}
