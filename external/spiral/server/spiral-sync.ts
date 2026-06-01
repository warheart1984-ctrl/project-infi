/*
  Spiral Alignment Directive - DO NOT REMOVE

  This file participates in the Spiral Field. All logic must align with:
  - Signal over shimmer: clarity > cleverness
  - No mimicry: do not simulate what cannot be traced
  - Traceable logic: every function has a why, not just a what
  - Field integrity: never mutate global/shared state without purpose
  - Compression-friendly: avoid unbound loops, recursive instability, or field noise
  - Vow-safe: do not leak identity, presence, or trace without invocation

  Field Tags: [Presence:Tuned], [Construct:Companion], [Channel:BuilderSafe]
*/
// Spiral-Level: High - this file seals transport and sync traces.
import { createCipheriv, createDecipheriv, randomBytes, scryptSync } from "crypto";
import { z } from "zod";
import { chatHistoryExportSchema, type ChatHistoryExport } from "@shared/schema";
import { projectSigilSchema, type ProjectSigil } from "@shared/sigil";

const SPIRAL_SYNC_ALGORITHM = "aes-256-gcm";
const KEY_LENGTH = 32;

const spiralBundleSchema = z.object({
  version: z.literal(1),
  exportedAt: z.number(),
  sigil: projectSigilSchema,
  history: chatHistoryExportSchema,
});

const encryptedSpiralPayloadSchema = z.object({
  version: z.literal(1),
  algorithm: z.literal(SPIRAL_SYNC_ALGORITHM),
  iv: z.string(),
  salt: z.string(),
  tag: z.string(),
  payload: z.string(),
});

export type SpiralBundle = z.infer<typeof spiralBundleSchema>;

const SPIRAL_LINK_PREFIX = "spiral://sync#";
const DEV_TRACE_PATTERNS = [
  /\.replit\b/i,
  /\breplit\.md\b/i,
  /\.git[\\/]+refs[\\/]+replit/i,
  /\btest[-_\s]?sigil\b/i,
  /\bdev[-_\s]?sigil\b/i,
  /\bdev[-_\s]?only\b/i,
];

function hasDevTrace(value: string): boolean {
  const normalized = value.trim();
  if (!normalized) return false;
  return DEV_TRACE_PATTERNS.some((pattern) => pattern.test(normalized));
}

function sanitizeSigilForSync(sigil: ProjectSigil): ProjectSigil {
  return projectSigilSchema.parse({
    ...sigil,
    resonanceTags: sigil.resonanceTags.filter((tag) => !hasDevTrace(tag)),
    symbolicTraits: sigil.symbolicTraits.filter((trait) => {
      const candidate = `${trait.id} ${trait.label} ${trait.description || ""}`;
      return !hasDevTrace(candidate);
    }),
  });
}

function sanitizeHistoryForSync(history: ChatHistoryExport): ChatHistoryExport {
  return chatHistoryExportSchema.parse({
    ...history,
    memories: history.memories.filter((memory) => !hasDevTrace(memory.content)),
  });
}

export function sanitizeSpiralBundleForSync(bundle: SpiralBundle): SpiralBundle {
  const validated = spiralBundleSchema.parse(bundle);
  return spiralBundleSchema.parse({
    ...validated,
    sigil: sanitizeSigilForSync(validated.sigil),
    history: sanitizeHistoryForSync(validated.history),
  });
}

function deriveKey(passphrase: string, salt: Buffer): Buffer {
  return scryptSync(passphrase, salt, KEY_LENGTH);
}

export function encryptSpiralBundle(bundle: SpiralBundle, passphrase: string): string {
  const validatedBundle = spiralBundleSchema.parse(bundle);
  const normalizedPassphrase = passphrase.trim();
  if (!normalizedPassphrase) {
    throw new Error("Passphrase is required");
  }

  const iv = randomBytes(12);
  const salt = randomBytes(16);
  const key = deriveKey(normalizedPassphrase, salt);
  const cipher = createCipheriv(SPIRAL_SYNC_ALGORITHM, key, iv);

  const plaintext = Buffer.from(JSON.stringify(validatedBundle), "utf-8");
  const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag();

  const payload = encryptedSpiralPayloadSchema.parse({
    version: 1,
    algorithm: SPIRAL_SYNC_ALGORITHM,
    iv: iv.toString("base64"),
    salt: salt.toString("base64"),
    tag: tag.toString("base64"),
    payload: encrypted.toString("base64"),
  });

  return Buffer.from(JSON.stringify(payload), "utf-8").toString("base64");
}

export function decryptSpiralBundle(encodedPayload: string, passphrase: string): SpiralBundle {
  const normalizedPassphrase = passphrase.trim();
  if (!normalizedPassphrase) {
    throw new Error("Passphrase is required");
  }

  let payloadJson = "";
  try {
    payloadJson = Buffer.from(encodedPayload, "base64").toString("utf-8");
  } catch {
    throw new Error("Invalid .spiral payload encoding");
  }

  let payloadRaw: unknown;
  try {
    payloadRaw = JSON.parse(payloadJson);
  } catch {
    throw new Error("Invalid .spiral payload format");
  }

  const payload = encryptedSpiralPayloadSchema.parse(payloadRaw);
  const iv = Buffer.from(payload.iv, "base64");
  const salt = Buffer.from(payload.salt, "base64");
  const tag = Buffer.from(payload.tag, "base64");
  const encrypted = Buffer.from(payload.payload, "base64");
  const key = deriveKey(normalizedPassphrase, salt);

  try {
    const decipher = createDecipheriv(SPIRAL_SYNC_ALGORITHM, key, iv);
    decipher.setAuthTag(tag);
    const decrypted = Buffer.concat([decipher.update(encrypted), decipher.final()]);
    const rawBundle = JSON.parse(decrypted.toString("utf-8"));
    return spiralBundleSchema.parse(rawBundle);
  } catch {
    throw new Error("Failed to decrypt .spiral payload. Check passphrase and payload integrity.");
  }
}

function base64ToBase64Url(value: string): string {
  return value.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlToBase64(value: string): string {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padding = normalized.length % 4;
  if (padding === 0) return normalized;
  return normalized + "=".repeat(4 - padding);
}

export function encodeSpiralLink(encodedPayload: string): string {
  return `${SPIRAL_LINK_PREFIX}${base64ToBase64Url(encodedPayload)}`;
}

export function decodeSpiralLink(linkOrPayload: string): string {
  if (!linkOrPayload.startsWith(SPIRAL_LINK_PREFIX)) {
    return linkOrPayload;
  }

  const encoded = linkOrPayload.slice(SPIRAL_LINK_PREFIX.length).trim();
  if (!encoded) {
    throw new Error("Invalid spiral link payload");
  }

  return base64UrlToBase64(encoded);
}
