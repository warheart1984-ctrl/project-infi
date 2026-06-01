import { useEffect, useMemo, useState } from "react";
import {
  executorProviderSettingsSchema,
  providerSettingsSchema,
  type ExecutorProviderSettings,
  type ProviderSettings,
} from "@shared/schema";
import { resolveMemoryModeFromProviderSettings } from "@shared/memory-mode";

const STORAGE_KEY = "ai-chat-provider-settings";
const VALID_SIGIL_CONTEXTS = new Set(["balanced", "clarity", "depth", "builder"]);
const VALID_TRANSCRIPT_FORMATS = new Set(["json", "markdown", "spiral-json", "sigil-json"]);

interface StoredProviderSettingsBundle {
  runtimeProviderSettings: ProviderSettings | null;
  executorProviderSettings: ExecutorProviderSettings | null;
}

function safeStorageGet(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeStorageSet(key: string, value: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Storage may be unavailable; keep in-memory state only.
  }
}

function safeStorageRemove(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Ignore storage access failures.
  }
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asTrimmedString(value: unknown): string | undefined {
  const raw = asString(value);
  if (raw === undefined) return undefined;
  const trimmed = raw.trim();
  return trimmed || undefined;
}

function asBoolean(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((entry): entry is string => typeof entry === "string");
}

function normalizeRuntimeProviderSettings(settings: ProviderSettings): ProviderSettings {
  const raw = settings as unknown as Record<string, unknown>;
  const apiKey = asString(raw.apiKey) ?? "";
  const memoryMode = resolveMemoryModeFromProviderSettings(raw, "sigil-bound");
  const memoryEnabled = memoryMode !== "sealed";
  const historyReferenceEnabled = memoryMode === "open" && (asBoolean(raw.historyReferenceEnabled) ?? true);
  const temporaryChatEnabled = memoryMode === "sealed";
  const vowModeEnabled = asBoolean(raw.vowModeEnabled) ?? false;
  const memoryFoldingEnabled = asBoolean(raw.memoryFoldingEnabled) ?? true;
  const presenceCalculatorEnabled = asBoolean(raw.presenceCalculatorEnabled) ?? false;
  const externalStorageAutoSaveOnEnd = asBoolean(raw.externalStorageAutoSaveOnEnd) ?? false;
  const sigilContextRaw = asTrimmedString(raw.sigilContext);
  const externalStorageTranscriptFormatRaw = asTrimmedString(raw.externalStorageTranscriptFormat);
  const sigilContext = sigilContextRaw && VALID_SIGIL_CONTEXTS.has(sigilContextRaw)
    ? (sigilContextRaw as ProviderSettings["sigilContext"])
    : "balanced";
  const externalStorageTranscriptFormat =
    externalStorageTranscriptFormatRaw && VALID_TRANSCRIPT_FORMATS.has(externalStorageTranscriptFormatRaw)
      ? (externalStorageTranscriptFormatRaw as ProviderSettings["externalStorageTranscriptFormat"])
      : "json";
  const normalizedSigilTags = asStringArray(raw.externalStorageSigilTags)
    .map((tag) => tag.trim())
    .filter(Boolean);

  return {
    ...settings,
    apiKey,
    memoryEnabled,
    historyReferenceEnabled,
    memoryMode,
    temporaryChatEnabled,
    sigilContext,
    vowModeEnabled,
    vowText: asString(raw.vowText) ?? "",
    memoryFoldingEnabled,
    presenceCalculatorEnabled,
    externalStorageTranscriptFormat,
    externalStorageAutoSaveOnEnd,
    externalStorageSigilFilter: asTrimmedString(raw.externalStorageSigilFilter),
    externalStorageSigilTags: normalizedSigilTags,
    customSigils: Array.isArray(raw.customSigils)
      ? (raw.customSigils as ProviderSettings["customSigils"])
      : [],
  };
}

function normalizeExecutorProviderSettings(
  settings: ExecutorProviderSettings,
): ExecutorProviderSettings {
  const raw = settings as unknown as Record<string, unknown>;
  const authProfileId = asTrimmedString(raw.authProfileId);
  return {
    provider: "codex-local",
    model: asTrimmedString(raw.model),
    apiKey: "",
    ...(authProfileId ? { authProfileId } : {}),
  };
}

function parseRuntimeProviderSettings(value: unknown): ProviderSettings | null {
  const parsed = providerSettingsSchema.safeParse(value);
  if (!parsed.success) return null;
  return normalizeRuntimeProviderSettings(parsed.data);
}

function parseExecutorProviderSettings(value: unknown): ExecutorProviderSettings | null {
  const parsed = executorProviderSettingsSchema.safeParse(value);
  if (!parsed.success) return null;
  return normalizeExecutorProviderSettings(parsed.data);
}

function emptyBundle(): StoredProviderSettingsBundle {
  return {
    runtimeProviderSettings: null,
    executorProviderSettings: null,
  };
}

function parseStoredBundle(rawJson: string): StoredProviderSettingsBundle {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawJson);
  } catch {
    return emptyBundle();
  }
  if (!parsed || typeof parsed !== "object") {
    return emptyBundle();
  }

  const root = parsed as Record<string, unknown>;
  const hasSplit =
    Object.prototype.hasOwnProperty.call(root, "runtimeProviderSettings") ||
    Object.prototype.hasOwnProperty.call(root, "executorProviderSettings");

  if (hasSplit) {
    return {
      runtimeProviderSettings: parseRuntimeProviderSettings(root.runtimeProviderSettings),
      executorProviderSettings: parseExecutorProviderSettings(root.executorProviderSettings),
    };
  }

  // Legacy single-surface fallback.
  const legacyRuntime = (() => {
    const candidate = {
      ...root,
      authProfileId: undefined,
    };
    return parseRuntimeProviderSettings(candidate);
  })();
  const legacyExecutor = (() => {
    const authProfileId = asTrimmedString(root.authProfileId);
    if (!authProfileId) return null;
    return parseExecutorProviderSettings({
      provider: "codex-local",
      authProfileId,
      model: asTrimmedString(root.model),
    });
  })();

  return {
    runtimeProviderSettings: legacyRuntime,
    executorProviderSettings: legacyExecutor,
  };
}

function persistBundle(key: string, bundle: StoredProviderSettingsBundle): void {
  if (!bundle.runtimeProviderSettings && !bundle.executorProviderSettings) {
    safeStorageRemove(key);
    return;
  }
  safeStorageSet(key, JSON.stringify(bundle));
}

export function useProviderSettings(scopeKeyInput = "local") {
  const scopeKey = scopeKeyInput.trim() || "local";
  const storageKey = useMemo(() => `${STORAGE_KEY}:${scopeKey}`, [scopeKey]);
  const [runtimeSettings, setRuntimeSettings] = useState<ProviderSettings | null>(null);
  const [executorSettings, setExecutorSettings] = useState<ExecutorProviderSettings | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  const loadSettings = (key: string) => {
    const stored = safeStorageGet(key);
    if (!stored) {
      setRuntimeSettings(null);
      setExecutorSettings(null);
      return;
    }
    const bundle = parseStoredBundle(stored);
    if (!bundle.runtimeProviderSettings && !bundle.executorProviderSettings) {
      safeStorageRemove(key);
      setRuntimeSettings(null);
      setExecutorSettings(null);
      return;
    }
    setRuntimeSettings(bundle.runtimeProviderSettings);
    setExecutorSettings(bundle.executorProviderSettings);
    persistBundle(key, bundle);
  };

  useEffect(() => {
    setIsLoaded(false);
    loadSettings(storageKey);

    // Legacy fallback for existing single-scope installs.
    if (scopeKey === "local" && !safeStorageGet(storageKey)) {
      const legacy = safeStorageGet(STORAGE_KEY);
      if (legacy) {
        const migrated = parseStoredBundle(legacy);
        persistBundle(storageKey, migrated);
        safeStorageRemove(STORAGE_KEY);
        loadSettings(storageKey);
      }
    }

    setIsLoaded(true);
  }, [scopeKey, storageKey]);

  const saveRuntimeSettings = (newSettings: ProviderSettings) => {
    const normalized = normalizeRuntimeProviderSettings(newSettings);
    setRuntimeSettings(normalized);
    persistBundle(storageKey, {
      runtimeProviderSettings: normalized,
      executorProviderSettings: executorSettings,
    });
  };

  const saveExecutorSettings = (newSettings: ExecutorProviderSettings | null) => {
    const normalized = newSettings ? normalizeExecutorProviderSettings(newSettings) : null;
    setExecutorSettings(normalized);
    persistBundle(storageKey, {
      runtimeProviderSettings: runtimeSettings,
      executorProviderSettings: normalized,
    });
  };

  const saveSplitSettings = (newSettings: {
    runtimeProviderSettings: ProviderSettings;
    executorProviderSettings: ExecutorProviderSettings | null;
  }) => {
    const normalizedRuntime = normalizeRuntimeProviderSettings(newSettings.runtimeProviderSettings);
    const normalizedExecutor = newSettings.executorProviderSettings
      ? normalizeExecutorProviderSettings(newSettings.executorProviderSettings)
      : null;
    setRuntimeSettings(normalizedRuntime);
    setExecutorSettings(normalizedExecutor);
    persistBundle(storageKey, {
      runtimeProviderSettings: normalizedRuntime,
      executorProviderSettings: normalizedExecutor,
    });
  };

  const clearSettings = () => {
    setRuntimeSettings(null);
    setExecutorSettings(null);
    safeStorageRemove(storageKey);
  };

  return {
    scopeKey,
    runtimeSettings,
    executorSettings,
    settings: runtimeSettings,
    isLoaded,
    saveRuntimeSettings,
    saveExecutorSettings,
    saveSplitSettings,
    saveSettings: saveRuntimeSettings,
    clearSettings,
    isConfigured: !!runtimeSettings?.apiKey?.trim(),
  };
}
