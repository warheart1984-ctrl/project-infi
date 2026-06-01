export const EDITABLE_CLIENT_ENV_KEYS = [
  "VITE_SPIRAL_MODE",
  "VITE_SIGIL_STATE_OVERRIDE",
  "VITE_SPIRAL_API_SEAL",
  "VITE_SPIRAL_TRACE_DEBUG",
  "VITE_ECHO_TRACE_DEBUG",
] as const;

export type EditableClientEnvKey = (typeof EDITABLE_CLIENT_ENV_KEYS)[number];
export type ClientEnvSnapshot = Record<EditableClientEnvKey, string>;
export type ClientEnvOverrides = Partial<Record<EditableClientEnvKey, string>>;

const CLIENT_ENV_STORAGE_KEY = "spiral-client-env-overrides";

function safeGetLocalStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSetLocalStorage(key: string, value: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Ignore storage access failures in strict/private browser modes.
  }
}

function safeRemoveLocalStorage(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Ignore storage access failures.
  }
}

function toImportMetaEnvMap(): Record<string, unknown> {
  return import.meta.env as Record<string, unknown>;
}

function normalizeOverrideValue(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  return trimmed || undefined;
}

export function getStoredClientEnvOverrides(): ClientEnvOverrides {
  if (typeof window === "undefined") return {};

  const raw = safeGetLocalStorage(CLIENT_ENV_STORAGE_KEY);
  if (!raw) return {};

  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const overrides: ClientEnvOverrides = {};
    for (const key of EDITABLE_CLIENT_ENV_KEYS) {
      const normalized = normalizeOverrideValue(parsed[key]);
      if (normalized !== undefined) {
        overrides[key] = normalized;
      }
    }
    return overrides;
  } catch {
    return {};
  }
}

export function setStoredClientEnvOverrides(next: ClientEnvOverrides): void {
  if (typeof window === "undefined") return;

  const normalized: ClientEnvOverrides = {};
  for (const key of EDITABLE_CLIENT_ENV_KEYS) {
    const value = normalizeOverrideValue(next[key]);
    if (value !== undefined) {
      normalized[key] = value;
    }
  }

  if (Object.keys(normalized).length === 0) {
    safeRemoveLocalStorage(CLIENT_ENV_STORAGE_KEY);
    return;
  }

  safeSetLocalStorage(CLIENT_ENV_STORAGE_KEY, JSON.stringify(normalized));
}

export function getClientEnvValue(key: EditableClientEnvKey): string {
  const overrides = getStoredClientEnvOverrides();
  const override = overrides[key];
  if (typeof override === "string") {
    return override;
  }

  const rawValue = toImportMetaEnvMap()[key];
  if (typeof rawValue === "string") {
    return rawValue;
  }
  if (rawValue === undefined || rawValue === null) {
    return "";
  }
  return String(rawValue);
}

export function isClientEnvEnabled(key: EditableClientEnvKey): boolean {
  return getClientEnvValue(key) === "1";
}

export function getClientEnvSnapshot(): ClientEnvSnapshot {
  const snapshot = {} as ClientEnvSnapshot;
  for (const key of EDITABLE_CLIENT_ENV_KEYS) {
    snapshot[key] = getClientEnvValue(key);
  }
  return snapshot;
}
