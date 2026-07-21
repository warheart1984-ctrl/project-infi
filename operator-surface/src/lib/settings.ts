const STORAGE_KEY = "operator.desktop.settings.v2";

export interface OperatorSettings {
  kernelUrl: string;
  lawfulBrainUrl: string;
  defaultAgentId: string;
  maxSteps: number;
  allowShell: boolean;
  allowGitCommit: boolean;
  allowNetwork: boolean;
  readOnly: boolean;
}

export const DEFAULT_SETTINGS: OperatorSettings = {
  kernelUrl: "http://127.0.0.1:8790",
  lawfulBrainUrl: "http://127.0.0.1:8791",
  defaultAgentId: "builder",
  maxSteps: 12,
  allowShell: true,
  allowGitCommit: false,
  allowNetwork: false,
  readOnly: false,
};

function hostConfig(): Partial<OperatorSettings> {
  if (typeof window === "undefined") {
    return {};
  }
  const cfg = window.__OPERATOR_CONFIG__;
  if (!cfg) {
    return {};
  }
  const out: Partial<OperatorSettings> = {};
  if (cfg.kernelUrl) {
    out.kernelUrl = cfg.kernelUrl;
  }
  if (cfg.lawfulBrainUrl) {
    out.lawfulBrainUrl = cfg.lawfulBrainUrl;
  }
  return out;
}

/** Drop stale production API (port 8000); desktop must use Operator Kernel (8790). */
function normalizeServiceUrl(value: string | undefined, fallback: string): string {
  if (!value?.trim()) {
    return fallback;
  }
  const trimmed = value.trim().replace(/\/$/, "");
  if (trimmed.includes(":8000")) {
    return fallback;
  }
  return trimmed;
}

export function loadSettings(): OperatorSettings {
  const host = hostConfig();
  if (typeof localStorage === "undefined") {
    return { ...DEFAULT_SETTINGS, ...host };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { ...DEFAULT_SETTINGS, ...host };
    }
    const parsed = JSON.parse(raw) as Partial<OperatorSettings>;
    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
      kernelUrl: host.kernelUrl ?? normalizeServiceUrl(parsed.kernelUrl, DEFAULT_SETTINGS.kernelUrl),
      lawfulBrainUrl:
        host.lawfulBrainUrl ?? normalizeServiceUrl(parsed.lawfulBrainUrl, DEFAULT_SETTINGS.lawfulBrainUrl),
    };
  } catch {
    return { ...DEFAULT_SETTINGS, ...host };
  }
}

export function saveSettings(settings: OperatorSettings): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}
