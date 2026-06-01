import { DEFAULT_PROJECT_SIGIL } from "@shared/sigil";

export const PRESENCE_SEAL_KEY = "spiral-presence-seal";
export const PRESENCE_TRACE_KEY = "spiral-presence-trace";
export const PRESENCE_SEAL_RECORD_KEY = "spiral-presence-seal-record";
export const PRESENCE_STORAGE_MODE_KEY = "spiral-presence-storage-mode";
export const SPIRAL_PRESENCE_SIGIL = DEFAULT_PROJECT_SIGIL.seal;

export interface SealTrace {
  seal?: string;
  sealConfirmed?: boolean;
}

export interface SpiralSealRecord {
  sigil: string;
  mantra: string;
  sealedAt: number;
  remember: boolean;
}

function normalizeSealSigil(value: string | undefined): string {
  const collapsed = (value || "").trim().replace(/\s+/g, " ").replace(/\\\\+/g, "\\");
  return collapsed.replace(/\/\s*\\/g, "/ \\");
}

function safeStorageGet(storage: Storage, key: string): string | null {
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

function safeStorageSet(storage: Storage, key: string, value: string): void {
  try {
    storage.setItem(key, value);
  } catch {
    // no-op
  }
}

function safeStorageRemove(storage: Storage, key: string): void {
  try {
    storage.removeItem(key);
  } catch {
    // no-op
  }
}

export function readSpiralSealRecord(): SpiralSealRecord | null {
  if (typeof window === "undefined") return null;
  const raw =
    safeStorageGet(window.localStorage, PRESENCE_SEAL_RECORD_KEY) ||
    safeStorageGet(window.sessionStorage, PRESENCE_SEAL_RECORD_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<SpiralSealRecord>;
    if (
      typeof parsed.sigil !== "string" ||
      typeof parsed.mantra !== "string" ||
      typeof parsed.sealedAt !== "number" ||
      typeof parsed.remember !== "boolean"
    ) {
      return null;
    }
    return parsed as SpiralSealRecord;
  } catch {
    return null;
  }
}

export function writeSpiralSealRecord(record: SpiralSealRecord): void {
  if (typeof window === "undefined") return;
  const serialized = JSON.stringify(record);
  safeStorageSet(window.sessionStorage, PRESENCE_SEAL_RECORD_KEY, serialized);
  if (record.remember) {
    safeStorageSet(window.localStorage, PRESENCE_SEAL_RECORD_KEY, serialized);
  } else {
    safeStorageRemove(window.localStorage, PRESENCE_SEAL_RECORD_KEY);
  }
  window.dispatchEvent(new Event("spiral:seal-updated"));
}

export function writeSealFlag(key: string, value: boolean, remember: boolean): void {
  if (typeof window === "undefined") return;
  if (value) {
    safeStorageSet(window.sessionStorage, key, "1");
    if (remember) {
      safeStorageSet(window.localStorage, key, "1");
    } else {
      safeStorageRemove(window.localStorage, key);
    }
    return;
  }
  safeStorageRemove(window.localStorage, key);
  safeStorageRemove(window.sessionStorage, key);
}

export function writeSealChoice(key: string, value: string, remember: boolean): void {
  if (typeof window === "undefined") return;
  const normalizedValue = value.trim();
  if (!normalizedValue) {
    safeStorageRemove(window.localStorage, key);
    safeStorageRemove(window.sessionStorage, key);
    return;
  }
  safeStorageSet(window.sessionStorage, key, normalizedValue);
  if (remember) {
    safeStorageSet(window.localStorage, key, normalizedValue);
  } else {
    safeStorageRemove(window.localStorage, key);
  }
}

export function readSealFlag(key: string): boolean {
  if (typeof window === "undefined") return false;
  return safeStorageGet(window.localStorage, key) === "1" || safeStorageGet(window.sessionStorage, key) === "1";
}

export function readSealChoice(key: string): string {
  if (typeof window === "undefined") return "";
  const raw =
    safeStorageGet(window.localStorage, key) ||
    safeStorageGet(window.sessionStorage, key);
  return raw ? raw.trim() : "";
}

export function hasPresenceSealConfirmation(): boolean {
  return readSealFlag(PRESENCE_SEAL_KEY);
}

export function requireSeal(
  trace: SealTrace | null | undefined,
  expectedSeal = SPIRAL_PRESENCE_SIGIL,
): asserts trace is SealTrace & { seal: string; sealConfirmed: true } {
  if (!trace || trace.sealConfirmed !== true) {
    throw new Error("Persona access denied: Presence seal not confirmed.");
  }

  const normalizedExpectedSeal = normalizeSealSigil(expectedSeal);
  const normalizedSeal = normalizeSealSigil(trace.seal);
  if (!normalizedSeal || normalizedSeal !== normalizedExpectedSeal) {
    throw new Error("Spiral seal mismatch. Activation denied.");
  }
}
