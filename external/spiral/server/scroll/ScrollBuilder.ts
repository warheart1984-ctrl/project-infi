import crypto from "node:crypto";
import type { SpiralField } from "@shared/spiral-field";
import type { EncryptedScrollBlob, ScrollExport, ScrollGlyph } from "@shared/scroll";

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function deriveKeyMaterial(primarySigil: string, sealedAt: string, ritual: string): Buffer {
  const passphrase = `${primarySigil}|${sealedAt}|${ritual}`;
  return crypto.createHash("sha256").update(passphrase).digest();
}

function deriveAesKey(primarySigil: string, sealedAt: string, ritual: string): Buffer {
  const material = deriveKeyMaterial(primarySigil, sealedAt, ritual);
  return crypto.scryptSync(material, `${sealedAt}:${ritual}`, 32);
}

export function encryptScroll(
  scroll: ScrollExport,
  args?: { primarySigil?: string; ritualSalt?: string },
): EncryptedScrollBlob {
  const sealedAt = normalize(scroll.sealedAt) || new Date().toISOString();
  const primarySigil = normalize(args?.primarySigil) || scroll.sigils[0] || "sigil:void";
  const ritual = normalize(args?.ritualSalt) || normalize(scroll.ritual) || "fracturing";
  const key = deriveAesKey(primarySigil, sealedAt, ritual);
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const plaintext = Buffer.from(JSON.stringify(scroll), "utf8");
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag();

  return {
    alg: "AES-256-GCM",
    iv: iv.toString("base64"),
    tag: tag.toString("base64"),
    ciphertext: ciphertext.toString("base64"),
    sealedAt,
  };
}

export function decryptScroll(
  blob: EncryptedScrollBlob,
  args: { primarySigil: string; ritualSalt?: string },
): ScrollExport {
  const sealedAt = normalize(blob.sealedAt);
  const ritual = normalize(args.ritualSalt) || "fracturing";
  const key = deriveAesKey(args.primarySigil, sealedAt, ritual);
  const iv = Buffer.from(blob.iv, "base64");
  const tag = Buffer.from(blob.tag, "base64");
  const ciphertext = Buffer.from(blob.ciphertext, "base64");
  const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(tag);
  const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  return JSON.parse(plaintext.toString("utf8")) as ScrollExport;
}

export function captureScroll(args: {
  ritual: string;
  field: SpiralField;
  glyphs: ScrollGlyph[];
}): ScrollExport {
  const sealedAt = new Date().toISOString();
  const normalizedGlyphs = args.glyphs.map((glyph) => ({
    ...glyph,
    resonance: clamp(glyph.resonance, 0, 1),
    sigilTags: Array.from(new Set(glyph.sigilTags.map((tag) => normalize(tag)).filter(Boolean))),
  }));

  return {
    ritual: normalize(args.ritual) || "fracturing",
    field: args.field,
    glyphs: normalizedGlyphs,
    distortions: [...args.field.distortions],
    sigils: [...args.field.sigils],
    sealedAt,
  };
}
