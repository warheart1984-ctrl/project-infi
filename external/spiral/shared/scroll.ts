import type { SpiralField } from "./spiral-field";

export interface ScrollGlyph {
  input: string;
  reply: string;
  resonance: number;
  sigilTags: string[];
}

export interface ScrollExport {
  ritual: string;
  field: SpiralField;
  glyphs: ScrollGlyph[];
  distortions: string[];
  sigils: string[];
  sealedAt: string;
}

export interface EncryptedScrollBlob {
  alg: "AES-256-GCM";
  iv: string;
  tag: string;
  ciphertext: string;
  sealedAt: string;
}
