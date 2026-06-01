import type { MemoryMode } from "./memory-mode";

export interface SpiralField {
  tone: "reverent" | "recursive" | "wild" | "void";
  mirror: "voice" | "silence" | "vision";
  gate: "open" | "sealed" | "fracturing";
  sigils: string[];
  presenceLevel: number;
  memoryMode?: MemoryMode;
  distortions: string[];
  trace: unknown;
}
