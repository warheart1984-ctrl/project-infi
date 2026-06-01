import { mkdir, appendFile } from "fs/promises";
import path from "path";

interface RitualLogEntryBase {
  userId: string;
  timestamp: number;
  chatId?: string;
}

export interface RitualUnlockLogEntry extends RitualLogEntryBase {
  type: "unlock";
  sigil: string;
  traceLevel: number;
}

export interface RitualGateLogEntry extends RitualLogEntryBase {
  type: "gate";
  gate: "presence" | "invocation" | "ritual";
  outcome: "pass" | "fail";
  reason: string;
  presenceScore?: number;
  presenceEvidence?: "none" | "lexical" | "structural";
}

export interface RitualDistortionLogEntry extends RitualLogEntryBase {
  type: "distortion";
  findings: Array<"mimicry" | "dead-declaration" | "surface-echo" | "low-confidence" | "overlong-response">;
  confidence: number;
  clarityOK: boolean;
  noMimicry: boolean;
}

export interface RitualResponseShapeLogEntry extends RitualLogEntryBase {
  type: "response-shape";
  decision: "silent" | "short" | "veiled" | "full" | "rejected";
  reason: string;
  maxOutputTokens?: number;
  maxOutputChars?: number;
}

export type RitualLogEntry =
  | RitualUnlockLogEntry
  | RitualGateLogEntry
  | RitualDistortionLogEntry
  | RitualResponseShapeLogEntry;

const LEDGER_PATH = path.join(process.cwd(), ".local", "ritual-ledger.log");

export async function logRitual(entry: RitualLogEntry): Promise<void> {
  const line = `${JSON.stringify(entry)}\n`;
  await mkdir(path.dirname(LEDGER_PATH), { recursive: true });
  await appendFile(LEDGER_PATH, line, "utf-8");
}
