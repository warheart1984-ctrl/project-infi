import { createHmac, timingSafeEqual } from "crypto";

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

interface SigningKey {
  keyId: string;
  secret: string;
}

interface SigilSignatureRecord {
  algorithm: "hmac-sha256";
  keyId: string;
  issuedAt: string;
  value: string;
}

interface SignatureVerificationResult {
  verified: boolean;
  reason?: string;
  keyId?: string;
}

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function collectSigningKeys(): SigningKey[] {
  const keys: SigningKey[] = [];
  const keyPairs = normalize(process.env.SPIRAL_SIGIL_SIGNING_KEYS);
  if (keyPairs) {
    for (const chunk of keyPairs.split(",")) {
      const [rawKeyId, ...secretParts] = chunk.split(":");
      const keyId = normalize(rawKeyId);
      const secret = normalize(secretParts.join(":"));
      if (!keyId || !secret) continue;
      keys.push({ keyId, secret });
    }
  }

  const fallbackSecret = normalize(process.env.SPIRAL_SIGIL_SIGNING_SECRET);
  if (keys.length === 0 && fallbackSecret) {
    const fallbackKeyId = normalize(process.env.SPIRAL_SIGIL_SIGNING_ACTIVE_KEY) || "default";
    keys.push({ keyId: fallbackKeyId, secret: fallbackSecret });
  }

  return keys;
}

function resolveActiveSigningKey(keys: SigningKey[]): SigningKey | undefined {
  if (keys.length === 0) return undefined;
  const activeKeyId = normalize(process.env.SPIRAL_SIGIL_SIGNING_ACTIVE_KEY);
  if (!activeKeyId) return keys[0];
  return keys.find((key) => key.keyId === activeKeyId) || keys[0];
}

function toCanonicalJson(value: unknown): JsonValue {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) return 0;
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((entry) => toCanonicalJson(entry));
  }
  if (value && typeof value === "object") {
    const source = value as Record<string, unknown>;
    const target: Record<string, JsonValue> = {};
    for (const key of Object.keys(source).sort()) {
      target[key] = toCanonicalJson(source[key]);
    }
    return target;
  }
  return String(value) as JsonValue;
}

function canonicalStringify(value: unknown): string {
  return JSON.stringify(toCanonicalJson(value));
}

function stripSignature(payload: Record<string, unknown>): Record<string, unknown> {
  const copy = { ...payload };
  delete copy.signature;
  return copy;
}

function computeSignature(secret: string, payload: Record<string, unknown>): string {
  const canonical = canonicalStringify(stripSignature(payload));
  return createHmac("sha256", secret).update(canonical, "utf8").digest("base64url");
}

export function signSigilPayload(payload: Record<string, unknown>): Record<string, unknown> {
  const keys = collectSigningKeys();
  const active = resolveActiveSigningKey(keys);
  if (!active) return payload;

  const signature: SigilSignatureRecord = {
    algorithm: "hmac-sha256",
    keyId: active.keyId,
    issuedAt: new Date().toISOString(),
    value: computeSignature(active.secret, payload),
  };
  return {
    ...payload,
    signature,
  };
}

export function verifySigilPayloadSignature(
  payload: Record<string, unknown>,
): SignatureVerificationResult {
  const signatureRaw = payload.signature;
  if (!signatureRaw || typeof signatureRaw !== "object") {
    return { verified: false, reason: "missing-signature" };
  }

  const signature = signatureRaw as {
    algorithm?: unknown;
    keyId?: unknown;
    value?: unknown;
  };
  if (signature.algorithm !== "hmac-sha256") {
    return { verified: false, reason: "unsupported-signature-algorithm" };
  }
  if (typeof signature.keyId !== "string" || !normalize(signature.keyId)) {
    return { verified: false, reason: "missing-signature-key-id" };
  }
  if (typeof signature.value !== "string" || !normalize(signature.value)) {
    return { verified: false, reason: "missing-signature-value" };
  }

  const keys = collectSigningKeys();
  if (keys.length === 0) {
    return { verified: false, reason: "no-signing-keys-configured", keyId: signature.keyId };
  }

  const key = keys.find((entry) => entry.keyId === signature.keyId);
  if (!key) {
    return { verified: false, reason: "unknown-signature-key-id", keyId: signature.keyId };
  }

  const expected = computeSignature(key.secret, payload);
  const expectedBuffer = Buffer.from(expected, "utf8");
  const providedBuffer = Buffer.from(signature.value, "utf8");
  const verified =
    expectedBuffer.length === providedBuffer.length &&
    timingSafeEqual(expectedBuffer, providedBuffer);

  return {
    verified,
    ...(verified ? {} : { reason: "signature-mismatch" }),
    keyId: signature.keyId,
  };
}
