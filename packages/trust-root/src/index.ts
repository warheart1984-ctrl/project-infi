import { createHash } from 'node:crypto';

export type HashAlg = 'sha3-256';
export type Measurement = string & { readonly __brand: 'Measurement' };

export interface TrustRootInput {
  hashAlg?: HashAlg;
  hKernelImage: string;
  hLawSpine: string;
  hCorridors: string;
  hBootManifest: string;
}

export interface TrustRoot {
  hashAlg: HashAlg;
  hKernelImage: Measurement;
  hLawSpine: Measurement;
  hCorridors: Measurement;
  hBootManifest: Measurement;
  hTrustRoot: Measurement;
}

export interface UCRTrustContext {
  hashAlg: HashAlg;
  hLawSpine: Measurement;
  hCorridors: Measurement;
  hTrustRoot: Measurement;
}

export interface EarlyBootResult {
  bootResult: 'OK' | 'HALT';
  trustRoot: TrustRoot;
  detail?: string;
}

const MEASUREMENT_RE = /^sha3-256:[0-9a-f]{64}$/;
const TRUST_ROOT_DOMAIN = Buffer.from('AAES-TRUST-ROOT-v1\0', 'utf8');

let sealedTrustRoot: TrustRoot | undefined;

export function isMeasurement(value: string): value is Measurement {
  return MEASUREMENT_RE.test(value);
}

export function asMeasurement(value: string): Measurement {
  if (!isMeasurement(value)) {
    throw new Error(`invalid measurement: ${value}`);
  }
  return value as Measurement;
}

export function computeMeasurement(value: string | Buffer): Measurement {
  return asMeasurement(`sha3-256:${createHash('sha3-256').update(value).digest('hex')}`);
}

export function computeHTrustRoot(input: TrustRootInput): Measurement {
  const hashAlg = input.hashAlg ?? 'sha3-256';
  if (hashAlg !== 'sha3-256') {
    throw new Error(`unsupported hash algorithm: ${hashAlg}`);
  }
  const parts = [
    asMeasurement(input.hKernelImage),
    asMeasurement(input.hLawSpine),
    asMeasurement(input.hCorridors),
    asMeasurement(input.hBootManifest),
  ].map((measurement) => Buffer.from(measurement.slice('sha3-256:'.length), 'hex'));

  return asMeasurement(`sha3-256:${createHash(hashAlg).update(Buffer.concat([TRUST_ROOT_DOMAIN, ...parts])).digest('hex')}`);
}

export function buildTrustRoot(input: TrustRootInput): TrustRoot {
  return {
    hashAlg: input.hashAlg ?? 'sha3-256',
    hKernelImage: asMeasurement(input.hKernelImage),
    hLawSpine: asMeasurement(input.hLawSpine),
    hCorridors: asMeasurement(input.hCorridors),
    hBootManifest: asMeasurement(input.hBootManifest),
    hTrustRoot: computeHTrustRoot(input),
  };
}

export function sealTrustRoot(trustRoot: TrustRoot): void {
  if (sealedTrustRoot) {
    throw new Error('trust root already sealed');
  }
  sealedTrustRoot = trustRoot;
}

export function getTrustRoot(): TrustRoot {
  if (!sealedTrustRoot) {
    throw new Error('trust root is not sealed');
  }
  return sealedTrustRoot;
}

export function isTrustRootSealed(): boolean {
  return Boolean(sealedTrustRoot);
}

export function resetTrustRootForTests(): void {
  sealedTrustRoot = undefined;
}

export function toUcrContext(trustRoot: TrustRoot): UCRTrustContext {
  return {
    hashAlg: trustRoot.hashAlg,
    hLawSpine: trustRoot.hLawSpine,
    hCorridors: trustRoot.hCorridors,
    hTrustRoot: trustRoot.hTrustRoot,
  };
}

export function getTrustRootSyscall(): Record<string, string> {
  const trustRoot = getTrustRoot();
  return {
    sealed: 'true',
    hashAlg: trustRoot.hashAlg,
    hLawSpine: trustRoot.hLawSpine,
    hCorridors: trustRoot.hCorridors,
    hTrustRoot: trustRoot.hTrustRoot,
  };
}

export function runEarlyBoot(input: TrustRootInput): EarlyBootResult {
  const trustRoot = buildTrustRoot(input);
  sealTrustRoot(trustRoot);
  return {
    bootResult: 'OK',
    trustRoot,
  };
}
