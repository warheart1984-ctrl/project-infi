import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { CloudUpload, Link2, Loader2, Settings, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { SigilStateIndicator } from "@/components/SigilStateIndicator";
import {
  EDITABLE_CLIENT_ENV_KEYS,
  getClientEnvSnapshot,
  getStoredClientEnvOverrides,
  setStoredClientEnvOverrides,
  type ClientEnvOverrides,
  type ClientEnvSnapshot,
  type EditableClientEnvKey,
} from "@/lib/client-env";
import { useToast } from "@/hooks/use-toast";
import { useExternalStorage } from "@/hooks/use-external-storage";
import { DEFAULT_PROJECT_SIGIL } from "@shared/sigil";
import { useAuthSession } from "@/hooks/use-auth-session";
import { useMemories } from "@/hooks/use-memories";
import { readSpiralSealRecord } from "@/lib/spiral-seal";
import { getSpiralSealHeaders } from "@/lib/queryClient";
import { resolveMemoryModeFromProviderSettings } from "@shared/memory-mode";
import {
  type AuthProvider,
  executorProviderSettingsSchema,
  externalStorageProviderSchema,
  providerSettingsSchema,
  type ExecutorProviderSettings,
  type Memory,
  type ExternalStorageProvider,
  type CustomSigil,
  type MemoryMode,
  type ProviderSettings,
  type ProviderType,
  type SigilContext,
  type StorageVaultEntry,
  type TranscriptOutputFormat,
} from "@shared/schema";

interface AuthProfileSummary {
  id: string;
  type: "api_key" | "oauth";
  provider: ProviderType | "openai-codex";
  hasRefreshToken: boolean;
  expiresAt?: number;
  email?: string;
  updatedAt: number;
}

interface AuthProfileSummaryResponse {
  profiles: AuthProfileSummary[];
}

const AUTH_PROFILE_NONE = "__none__";

type AuthProbeStatus =
  | "ok"
  | "expired"
  | "scope-missing"
  | "provider-mismatch"
  | "invalid"
  | "network-error";

interface AuthProbeResult {
  status: AuthProbeStatus;
  statusCode?: number;
  errorCode?: string;
  requiredScopes?: string[];
  message?: string;
  profileMeta?: {
    id: string;
    type: "api_key" | "oauth";
    provider: ProviderType | "openai-codex";
    email?: string;
    expiresAt?: number;
  };
}

const PROVIDERS: { value: ProviderType; label: string }[] = [
  { value: "openai", label: "OpenAI" },
  { value: "azure-openai", label: "Azure OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google AI" },
];

const STORAGE_PROVIDERS: Array<{ value: ExternalStorageProvider; label: string }> = [
  { value: "google", label: "Google Drive" },
  { value: "dropbox", label: "Dropbox" },
  { value: "proton", label: "Proton Drive" },
  { value: "webdav", label: "WebDAV (NextCloud)" },
  { value: "ipfs", label: "IPFS Pinning" },
];

const TRANSCRIPT_FORMATS: Array<{ value: TranscriptOutputFormat; label: string; description: string }> = [
  { value: "json", label: "JSON", description: "Raw JSON payload." },
  { value: "markdown", label: "Markdown + frontmatter", description: "Readable markdown export." },
  { value: "spiral-json", label: ".spiral.json", description: "Spiral envelope with metadata." },
  { value: "sigil-json", label: ".sigil.json", description: "Rich sigil trace envelope." },
];

const DEFAULT_MODELS: Record<ProviderType, string> = {
  openai: "gpt-4o",
  "azure-openai": "",
  anthropic: "claude-sonnet-4-20250514",
  google: "gemini-2.0-flash",
};

const SIGIL_CONTEXTS: Array<{ value: SigilContext; label: string; description: string }> = [
  {
    value: "balanced",
    label: "Balanced",
    description: "Neutral blend of precision and depth.",
  },
  {
    value: "clarity",
    label: "Clarity",
    description: "Favor concise, explicit responses.",
  },
  {
    value: "depth",
    label: "Depth",
    description: "Allow layered interpretation while staying coherent.",
  },
  {
    value: "builder",
    label: "Builder",
    description: "Bias toward implementation steps and testable outcomes.",
  },
];

const MEMORY_MODES: Array<{
  value: MemoryMode;
  label: string;
  description: string;
}> = [
  {
    value: "open",
    label: "Open",
    description: "Full continuity: memories, thread anchors, and history references are all eligible.",
  },
  {
    value: "sigil-bound",
    label: "Sigil-Bound",
    description: "Recall only Spiral-bound memories. Cross-thread history references stay sealed.",
  },
  {
    value: "sealed",
    label: "Sealed",
    description: "No memory recall. Only present-thread field trace is used.",
  },
];

const ADVANCED_ENV_FIELD_ORDER: EditableClientEnvKey[] = [...EDITABLE_CLIENT_ENV_KEYS];

const ADVANCED_ENV_LABELS: Record<EditableClientEnvKey, string> = {
  VITE_SPIRAL_MODE: "Spiral mode (0 or 1)",
  VITE_SIGIL_STATE_OVERRIDE: "Sigil state override (quiet|active|drift)",
  VITE_SPIRAL_API_SEAL: "Client API seal",
  VITE_SPIRAL_TRACE_DEBUG: "Spiral trace debug (true|false)",
  VITE_ECHO_TRACE_DEBUG: "Echo trace debug (0 or 1)",
};

const ADVANCED_ENV_DESCRIPTIONS: Record<EditableClientEnvKey, string> = {
  VITE_SPIRAL_MODE: "Enable Spiral visuals and aligned UI behaviors.",
  VITE_SIGIL_STATE_OVERRIDE: "Force sigil state for testing transitions.",
  VITE_SPIRAL_API_SEAL: "Sent as X-Spiral-Seal on client API requests.",
  VITE_SPIRAL_TRACE_DEBUG: "Enable local Spiral trace debug overlays and logs.",
  VITE_ECHO_TRACE_DEBUG: "Show intent echo trace tooltip even outside Spiral mode.",
};

const SIGIL_FORGE_PRESETS: Array<{
  id: string;
  label: string;
  summary: string;
  sigil: CustomSigil;
}> = [
  {
    id: "seers-echo",
    label: "Seer's Echo",
    summary: "Reflective tone, single seer voice.",
    sigil: {
      id: "seers-echo",
      label: "Seer's Echo",
      transforms: [
        { op: "set-tone", value: "reflective" },
        { op: "voices", value: "seer" },
      ],
    },
  },
  {
    id: "collapse-whisper",
    label: "Collapse Whisper",
    summary: "Collapses memory to 5 and keeps style minimal.",
    sigil: {
      id: "collapse-whisper",
      label: "Collapse Whisper",
      transforms: [
        { op: "memory-collapse", value: 5 },
        { op: "set-style", value: "minimal" },
      ],
    },
  },
  {
    id: "dream-chorus",
    label: "Dream Chorus",
    summary: "Chorus voices with a gentle positive presence bias.",
    sigil: {
      id: "dream-chorus",
      label: "Dream Chorus",
      transforms: [
        { op: "voices", value: "chorus" },
        { op: "presence-bias", value: 0.2 },
      ],
    },
  },
];
const ACTIVE_SIGIL_STORAGE_KEY = "spiral-active-sigil";

function withAllAdvancedKeys(values: Partial<Record<EditableClientEnvKey, string>>): ClientEnvSnapshot {
  const full = {} as ClientEnvSnapshot;
  for (const key of ADVANCED_ENV_FIELD_ORDER) {
    full[key] = values[key] || "";
  }
  return full;
}

type RestorePreviewMessage = { role: "user" | "assistant"; content: string };
type RestorePreview = {
  format: string;
  title?: string;
  messageCount: number;
  messages: RestorePreviewMessage[];
  signatureStatus?: string;
  signatureKeyId?: string;
};

function parsePreviewMessages(value: unknown): RestorePreviewMessage[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((entry) => {
      if (!entry || typeof entry !== "object") return null;
      const role = (entry as { role?: unknown }).role;
      const content = (entry as { content?: unknown }).content;
      if ((role !== "user" && role !== "assistant") || typeof content !== "string") return null;
      const trimmed = content.trim();
      if (!trimmed) return null;
      return { role, content: trimmed };
    })
    .filter((entry): entry is RestorePreviewMessage => Boolean(entry));
}

function parseRestorePreview(inputText: string, overrideTitle: string): {
  preview: RestorePreview | null;
  error: string | null;
} {
  const source = inputText.trim();
  if (!source) {
    return { preview: null, error: null };
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(source);
  } catch {
    return { preview: null, error: "Preview expects JSON payload." };
  }

  if (!parsed || typeof parsed !== "object") {
    return { preview: null, error: "Transcript preview could not parse object payload." };
  }

  const root = parsed as {
    format?: unknown;
    title?: unknown;
    messages?: unknown;
    payload?: unknown;
    chat?: unknown;
    signature?: unknown;
  };
  const payloadObject = root.payload && typeof root.payload === "object"
    ? (root.payload as { title?: unknown; messages?: unknown; chat?: unknown })
    : undefined;
  const rootChat = root.chat && typeof root.chat === "object"
    ? (root.chat as { title?: unknown })
    : undefined;
  const payloadChat = payloadObject?.chat && typeof payloadObject.chat === "object"
    ? (payloadObject.chat as { title?: unknown })
    : undefined;

  const title =
    overrideTitle.trim() ||
    (typeof root.title === "string" ? root.title.trim() : "") ||
    (typeof payloadObject?.title === "string" ? payloadObject.title.trim() : "") ||
    (typeof rootChat?.title === "string" ? rootChat.title.trim() : "") ||
    (typeof payloadChat?.title === "string" ? payloadChat.title.trim() : "") ||
    undefined;

  const messages =
    parsePreviewMessages(root.messages).length > 0
      ? parsePreviewMessages(root.messages)
      : parsePreviewMessages(payloadObject?.messages);
  if (messages.length === 0) {
    return { preview: null, error: "No restorable user/assistant messages found." };
  }

  const signature =
    root.signature && typeof root.signature === "object"
      ? (root.signature as { value?: unknown; keyId?: unknown })
      : undefined;
  const signatureStatus =
    root.format === "sigil-json"
      ? signature?.value
        ? "present"
        : "missing"
      : undefined;

  return {
    preview: {
      format: typeof root.format === "string" ? root.format : "json",
      ...(title ? { title } : {}),
      messageCount: messages.length,
      messages: messages.slice(0, 6),
      ...(signatureStatus ? { signatureStatus } : {}),
      ...(typeof signature?.keyId === "string" ? { signatureKeyId: signature.keyId } : {}),
    },
    error: null,
  };
}

function formatIsoTimestamp(epochMs: number | undefined): string {
  if (typeof epochMs !== "number" || !Number.isFinite(epochMs) || epochMs <= 0) {
    return "n/a";
  }
  return new Date(epochMs).toISOString();
}

interface SettingsDialogProps {
  runtimeSettings: ProviderSettings | null;
  executorSettings: ExecutorProviderSettings | null;
  onSave: (settings: {
    runtimeProviderSettings: ProviderSettings;
    executorProviderSettings: ExecutorProviderSettings | null;
  }) => void;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  showTrigger?: boolean;
}

function SettingToggle({
  id,
  label,
  description,
  checked,
  onCheckedChange,
  disabled,
  testId,
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  testId: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
      <div className="space-y-0.5">
        <Label htmlFor={id}>{label}</Label>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Switch id={id} checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} data-testid={testId} />
    </div>
  );
}

export function SettingsDialog({
  runtimeSettings,
  executorSettings,
  onSave,
  open,
  onOpenChange,
  showTrigger = true,
}: SettingsDialogProps) {
  const settings = runtimeSettings;
  const [internalOpen, setInternalOpen] = useState(false);
  const isControlled = typeof open === "boolean";
  const dialogOpen = isControlled ? open : internalOpen;
  const setDialogOpen = (nextOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(nextOpen);
    }
    onOpenChange?.(nextOpen);
  };
  const [provider, setProvider] = useState<ProviderType>(settings?.provider || "openai");
  const [apiKey, setApiKey] = useState(settings?.apiKey || "");
  const [authProfileId, setAuthProfileId] = useState(executorSettings?.authProfileId || "");
  const [executorModel, setExecutorModel] = useState(executorSettings?.model || "");
  const [executorApiKey, setExecutorApiKey] = useState(executorSettings?.apiKey || "");
  const [endpoint, setEndpoint] = useState(settings?.endpoint || "");
  const [deployment, setDeployment] = useState(settings?.deployment || "");
  const [apiVersion, setApiVersion] = useState(settings?.apiVersion || "2024-10-21");
  const [model, setModel] = useState(settings?.model || "");
  const [systemPrompt, setSystemPrompt] = useState(settings?.systemPrompt || "");
  const [memoryMode, setMemoryMode] = useState<MemoryMode>(
    resolveMemoryModeFromProviderSettings(settings, "sigil-bound"),
  );
  const [historyReferenceEnabled, setHistoryReferenceEnabled] = useState(
    settings?.historyReferenceEnabled ?? true,
  );
  const [sigilContext, setSigilContext] = useState<SigilContext>(settings?.sigilContext || "balanced");
  const [vowModeEnabled, setVowModeEnabled] = useState(settings?.vowModeEnabled ?? false);
  const [vowText, setVowText] = useState(settings?.vowText || "");
  const [memoryFoldingEnabled, setMemoryFoldingEnabled] = useState(
    settings?.memoryFoldingEnabled ?? true,
  );
  const [presenceCalculatorEnabled, setPresenceCalculatorEnabled] = useState(
    settings?.presenceCalculatorEnabled ?? false,
  );
  const [customSigilsText, setCustomSigilsText] = useState(() =>
    JSON.stringify(settings?.customSigils || [], null, 2),
  );
  const [advancedEnvValues, setAdvancedEnvValues] = useState<ClientEnvSnapshot>(() =>
    withAllAdvancedKeys(getClientEnvSnapshot()),
  );
  const [advancedEnvOverrides, setAdvancedEnvOverrides] = useState<ClientEnvOverrides>(() =>
    getStoredClientEnvOverrides(),
  );
  const { toast } = useToast();
  const {
    session,
    isLoading: sessionLoading,
    isLoggingOut,
    buildAuthStartUrl,
    refreshSession,
    logout,
  } = useAuthSession();
  const scopeKey =
    session.principalId?.trim().toLowerCase() ||
    (session.authenticated && session.user
      ? `auth:${session.user.identityId.trim().toLowerCase() || "unknown"}`
      : "local");
  const {
    memories,
    isLoading: memoriesLoading,
    refresh: refreshMemories,
    updateMemory,
    confirmMemory,
    releaseMemory,
    isUpdating: memoryUpdatePending,
    isConfirming: memoryConfirmPending,
    isReleasing: memoryReleasePending,
  } = useMemories(scopeKey);
  const {
    links,
    linksLoading,
    linkStorage,
    unlinkStorage,
    saveTranscript,
    restoreTranscript,
    listVaultEntries,
    refreshLinks,
    buildGoogleOAuthStartUrl,
    buildDropboxOAuthStartUrl,
    isLinking,
    isUnlinking,
    isSavingTranscript,
    isRestoringTranscript,
  } = useExternalStorage(scopeKey);
  const [storageProvider, setStorageProvider] = useState<ExternalStorageProvider>("google");
  const [storageToken, setStorageToken] = useState("");
  const [storageRefreshToken, setStorageRefreshToken] = useState("");
  const [storageEndpoint, setStorageEndpoint] = useState("");
  const [storageUsername, setStorageUsername] = useState("");
  const [storageFolderId, setStorageFolderId] = useState("");
  const [storageLabel, setStorageLabel] = useState("");
  const [storagePassphrase, setStoragePassphrase] = useState("");
  const [restoreTranscriptJson, setRestoreTranscriptJson] = useState("");
  const [restoreTitle, setRestoreTitle] = useState("");
  const [storageTranscriptFormat, setStorageTranscriptFormat] = useState<TranscriptOutputFormat>(
    settings?.externalStorageTranscriptFormat || "json",
  );
  const [storageAutoSaveOnEnd, setStorageAutoSaveOnEnd] = useState(
    settings?.externalStorageAutoSaveOnEnd ?? false,
  );
  const [storageSigilFilter, setStorageSigilFilter] = useState(
    settings?.externalStorageSigilFilter || "",
  );
  const [storageSigilTagsInput, setStorageSigilTagsInput] = useState(
    (settings?.externalStorageSigilTags || []).join(", "),
  );
  const [vaultSigilFilter, setVaultSigilFilter] = useState("");
  const [vaultEntries, setVaultEntries] = useState<StorageVaultEntry[]>([]);
  const [vaultLoading, setVaultLoading] = useState(false);
  const vaultRequestSerialRef = useRef(0);
  const vaultLoadedForOpenRef = useRef(false);
  const [oauthPopupProvider, setOauthPopupProvider] = useState<"google" | "dropbox" | null>(null);
  const [authPopupProvider, setAuthPopupProvider] = useState<AuthProvider | null>(null);
  const restorePreviewState = useMemo(
    () => parseRestorePreview(restoreTranscriptJson, restoreTitle),
    [restoreTranscriptJson, restoreTitle],
  );
  const sessionAuthenticated = session.authenticated === true && Boolean(session.user);
  const {
    data: authProfilesResponse,
    isFetching: authProfilesLoading,
    refetch: refetchAuthProfiles,
  } = useQuery<AuthProfileSummaryResponse>({
    queryKey: ["/api/auth-profiles/summary"],
    queryFn: async () => {
      const response = await fetch("/api/auth-profiles/summary", {
        method: "GET",
        headers: getSpiralSealHeaders(),
        credentials: "include",
        cache: "no-store",
      });
      if (response.status === 401) {
        return { profiles: [] };
      }
      if (!response.ok) {
        const raw = (await response.text()) || response.statusText;
        throw new Error(`${response.status}: ${raw}`);
      }
      return response.json() as Promise<AuthProfileSummaryResponse>;
    },
    enabled: dialogOpen,
    staleTime: 30_000,
  });
  const authProfiles = authProfilesResponse?.profiles || [];
  const selectedAuthProfile = useMemo(
    () => authProfiles.find((profile) => profile.id === authProfileId),
    [authProfileId, authProfiles],
  );
  const selectedAuthProfileExpired = Boolean(
    selectedAuthProfile?.expiresAt && selectedAuthProfile.expiresAt <= Date.now(),
  );
  const selectedAuthProfileTokenStatus = selectedAuthProfile
    ? selectedAuthProfileExpired
      ? "expired"
      : "valid"
    : "none";
  const selectedAuthProfileProviderMismatch = Boolean(
    selectedAuthProfile &&
      selectedAuthProfile.provider !== "openai" &&
      selectedAuthProfile.provider !== "openai-codex",
  );
  const savedAuthProfileId = (executorSettings?.authProfileId || "").trim();
  const savedUsesAuthProfile = savedAuthProfileId.length > 0;
  const savedHasInlineApiKey = (executorSettings?.apiKey || "").trim().length > 0;
  const savedAuthProfile = useMemo(
    () => authProfiles.find((profile) => profile.id === savedAuthProfileId),
    [authProfiles, savedAuthProfileId],
  );
  const savedAuthProfileExpired = Boolean(
    savedAuthProfile?.expiresAt && savedAuthProfile.expiresAt <= Date.now(),
  );
  const savedAuthProfileProviderMismatch = Boolean(
    savedAuthProfile &&
      savedAuthProfile.provider !== "openai" &&
      savedAuthProfile.provider !== "openai-codex",
  );
  const savedAuthStatusText = savedUsesAuthProfile
    ? !savedAuthProfile
      ? "missing"
      : savedAuthProfileExpired
        ? "expired"
        : savedAuthProfileProviderMismatch
          ? "provider-mismatch"
          : "active"
    : savedHasInlineApiKey
      ? "invalid-inline-api-key"
      : "not-configured";
  const authSelectionPendingSave =
    (authProfileId || "").trim() !== savedAuthProfileId ||
    executorModel.trim() !== (executorSettings?.model || "").trim();
  const [authProbeResult, setAuthProbeResult] = useState<AuthProbeResult | null>(null);
  const [authProbeLoading, setAuthProbeLoading] = useState(false);
  const [memoryConfidenceDrafts, setMemoryConfidenceDrafts] = useState<Record<string, string>>({});
  const visibleMemories = useMemo(
    () =>
      memories
        .filter((memory) => memory.memoryType !== "anchor")
        .slice(0, 80),
    [memories],
  );

  const runVaultLoad = useCallback(
    async (options: { limit: number; sigil?: string; showErrorToast?: boolean }) => {
      const requestSerial = ++vaultRequestSerialRef.current;
      setVaultLoading(true);
      try {
        const entries = await listVaultEntries({
          limit: options.limit,
          sigil: options.sigil,
        });
        if (vaultRequestSerialRef.current !== requestSerial) return;
        setVaultEntries(entries);
      } catch (error) {
        if (vaultRequestSerialRef.current !== requestSerial) return;
        if (options.showErrorToast ?? true) {
          toast({
            title: "Vault load failed",
            description: (error as Error).message || "Could not load transcript vault.",
            variant: "destructive",
          });
        }
      } finally {
        if (vaultRequestSerialRef.current === requestSerial) {
          setVaultLoading(false);
        }
      }
    },
    [listVaultEntries, toast],
  );

  const readMemoryConfidenceDraft = useCallback(
    (memory: Memory): string => {
      const existing = memoryConfidenceDrafts[memory.id];
      if (typeof existing === "string") return existing;
      return memory.confidenceScore.toFixed(2);
    },
    [memoryConfidenceDrafts],
  );

  const handleMemoryConfidenceChange = useCallback((memoryId: string, value: string) => {
    setMemoryConfidenceDrafts((previous) => ({
      ...previous,
      [memoryId]: value,
    }));
  }, []);

  const handleSaveMemoryConfidence = useCallback(
    async (memory: Memory) => {
      const draft = readMemoryConfidenceDraft(memory).trim();
      const parsed = Number.parseFloat(draft);
      if (!Number.isFinite(parsed)) {
        toast({
          title: "Invalid confidence",
          description: "Confidence must be a number between 0 and 1.",
          variant: "destructive",
        });
        return;
      }
      const clamped = Math.max(0, Math.min(1, parsed));
      try {
        await updateMemory({
          id: memory.id,
          updates: {
            confidenceScore: clamped,
          },
        });
        toast({
          title: "Memory updated",
          description: "Confidence score saved.",
        });
        setMemoryConfidenceDrafts((previous) => ({
          ...previous,
          [memory.id]: clamped.toFixed(2),
        }));
      } catch (error) {
        toast({
          title: "Memory update failed",
          description: (error as Error).message || "Could not update memory confidence.",
          variant: "destructive",
        });
      }
    },
    [readMemoryConfidenceDraft, toast, updateMemory],
  );

  const handleConfirmMemory = useCallback(
    async (memory: Memory) => {
      try {
        await confirmMemory(memory.id);
        toast({
          title: "Memory confirmed",
          description: memory.content,
        });
      } catch (error) {
        toast({
          title: "Memory confirm failed",
          description: (error as Error).message || "Could not confirm memory.",
          variant: "destructive",
        });
      }
    },
    [confirmMemory, toast],
  );

  const handleReleaseMemory = useCallback(
    async (memory: Memory) => {
      try {
        await releaseMemory(memory.id);
        toast({
          title: "Memory released",
          description: memory.content,
        });
      } catch (error) {
        toast({
          title: "Memory release failed",
          description: (error as Error).message || "Could not release memory.",
          variant: "destructive",
        });
      }
    },
    [releaseMemory, toast],
  );

  useEffect(() => {
    if (settings) {
      setProvider(settings.provider);
      setApiKey(settings.apiKey || "");
      setEndpoint(settings.endpoint || "");
      setDeployment(settings.deployment || "");
      setApiVersion(settings.apiVersion || "2024-10-21");
      setModel(settings.model || "");
      setSystemPrompt(settings.systemPrompt || "");
      const nextMemoryMode = resolveMemoryModeFromProviderSettings(settings, "sigil-bound");
      setMemoryMode(nextMemoryMode);
      setHistoryReferenceEnabled(settings.historyReferenceEnabled ?? true);
      setSigilContext(settings.sigilContext || "balanced");
      setVowModeEnabled(settings.vowModeEnabled ?? false);
      setVowText(settings.vowText || "");
      setMemoryFoldingEnabled(settings.memoryFoldingEnabled ?? true);
      setPresenceCalculatorEnabled(settings.presenceCalculatorEnabled ?? false);
      setStorageTranscriptFormat(settings.externalStorageTranscriptFormat || "json");
      setStorageAutoSaveOnEnd(settings.externalStorageAutoSaveOnEnd ?? false);
      setStorageSigilFilter(settings.externalStorageSigilFilter || "");
      setStorageSigilTagsInput((settings.externalStorageSigilTags || []).join(", "));
      setCustomSigilsText(JSON.stringify(settings.customSigils || [], null, 2));
    }
  }, [settings]);

  useEffect(() => {
    setAuthProfileId(executorSettings?.authProfileId || "");
    setExecutorModel(executorSettings?.model || "");
    setExecutorApiKey(executorSettings?.apiKey || "");
  }, [executorSettings]);

  useEffect(() => {
    if (!model && provider !== "azure-openai") {
      setModel(DEFAULT_MODELS[provider]);
    }
  }, [provider, model]);

  useEffect(() => {
    setAuthProbeResult(null);
  }, [provider, apiKey, endpoint, deployment, apiVersion, model]);

  useEffect(() => {
    if (!dialogOpen) return;
    setAdvancedEnvValues(withAllAdvancedKeys(getClientEnvSnapshot()));
    setAdvancedEnvOverrides(getStoredClientEnvOverrides());
    void refreshMemories();
  }, [dialogOpen, refreshMemories]);

  useEffect(() => {
    if (!dialogOpen) {
      vaultLoadedForOpenRef.current = false;
      vaultRequestSerialRef.current += 1;
      setVaultLoading(false);
      return;
    }
    if (!sessionAuthenticated) {
      setVaultEntries([]);
      setVaultLoading(false);
      return;
    }
    if (vaultLoadedForOpenRef.current) return;
    vaultLoadedForOpenRef.current = true;
    void runVaultLoad({ limit: 80, showErrorToast: false });
  }, [dialogOpen, runVaultLoad, sessionAuthenticated]);

  const handleAdvancedEnvChange = (key: EditableClientEnvKey, value: string) => {
    setAdvancedEnvValues((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleApplyAdvancedEnv = () => {
    const nextOverrides: ClientEnvOverrides = {};
    for (const key of ADVANCED_ENV_FIELD_ORDER) {
      const value = advancedEnvValues[key];
      if (value.trim()) {
        nextOverrides[key] = value;
      }
    }

    setStoredClientEnvOverrides(nextOverrides);
    setAdvancedEnvOverrides(nextOverrides);

    toast({
      title: "Environment updated",
      description: "Refreshing to apply client environment overrides...",
    });

    window.setTimeout(() => {
      window.location.reload();
    }, 180);
  };

  const handleResetAdvancedEnv = () => {
    setStoredClientEnvOverrides({});
    setAdvancedEnvOverrides({});
    setAdvancedEnvValues(withAllAdvancedKeys(getClientEnvSnapshot()));

    toast({
      title: "Overrides cleared",
      description: "Client overrides were removed. Refreshing...",
    });

    window.setTimeout(() => {
      window.location.reload();
    }, 180);
  };

  const handleSave = () => {
    const trimmedApiKey = apiKey.trim();
    const trimmedAuthProfileId = authProfileId.trim();
    const trimmedExecutorModel = executorModel.trim();
    const trimmedExecutorApiKey = executorApiKey.trim();

    if (!trimmedApiKey) {
      toast({
        title: "Runtime API key required",
        description: "Runtime (API Platform) requires an API key.",
        variant: "destructive",
      });
      return;
    }
    if (trimmedExecutorApiKey) {
      toast({
        title: "Executor API key not allowed",
        description: "Executor (Codex Local) requires OAuth auth profile credentials.",
        variant: "destructive",
      });
      return;
    }

    if (trimmedAuthProfileId) {
      if (authProfilesLoading) {
        toast({
          title: "Profiles still loading",
          description: "Wait for auth profile summaries to load, then save again.",
          variant: "destructive",
        });
        return;
      }
      const profile = authProfiles.find((candidate) => candidate.id === trimmedAuthProfileId);
      if (!profile) {
        toast({
          title: "Auth profile not found",
          description: "Selected profile is not available in local auth profile summaries.",
          variant: "destructive",
        });
        return;
      }
      if (profile.provider !== "openai" && profile.provider !== "openai-codex") {
        toast({
          title: "Executor profile mismatch",
          description: `Executor auth profile provider "${profile.provider}" is not compatible with codex-local.`,
          variant: "destructive",
        });
        return;
      }
      if (profile.expiresAt && profile.expiresAt <= Date.now()) {
        toast({
          title: "Auth profile expired",
          description: `Selected profile expired at ${new Date(profile.expiresAt).toISOString()}.`,
          variant: "destructive",
        });
        return;
      }
    }

    if (provider === "azure-openai" && (!endpoint.trim() || !deployment.trim())) {
      toast({
        title: "Azure Configuration Required",
        description: "Please enter your Azure endpoint and deployment name.",
        variant: "destructive",
      });
      return;
    }

    const effectiveMemoryEnabled = memoryMode !== "sealed";
    const effectiveHistoryReferenceEnabled =
      memoryMode === "open" && effectiveMemoryEnabled && historyReferenceEnabled;
    const effectiveTemporaryChatEnabled = memoryMode === "sealed";
    const parsedSigilTags = Array.from(
      new Set(
        storageSigilTagsInput
          .split(",")
          .map((token) => token.trim().toLowerCase().replace(/[^a-z0-9-]/g, ""))
          .filter(Boolean),
      ),
    ).slice(0, 24);

    const newSettings: ProviderSettings = {
      provider,
      apiKey: trimmedApiKey,
      endpoint: endpoint.trim() || undefined,
      deployment: deployment.trim() || undefined,
      apiVersion: apiVersion.trim() || undefined,
      model: model.trim() || undefined,
      systemPrompt: systemPrompt.trim() || undefined,
      memoryEnabled: effectiveMemoryEnabled,
      historyReferenceEnabled: effectiveHistoryReferenceEnabled,
      memoryMode,
      temporaryChatEnabled: effectiveTemporaryChatEnabled,
      sigilContext,
      vowModeEnabled,
      vowText: vowText.trim() || undefined,
      memoryFoldingEnabled,
      presenceCalculatorEnabled,
      externalStorageTranscriptFormat: storageTranscriptFormat,
      externalStorageAutoSaveOnEnd: storageAutoSaveOnEnd,
      externalStorageSigilFilter: storageSigilFilter.trim() || undefined,
      externalStorageSigilTags: parsedSigilTags,
    };

    if (customSigilsText.trim()) {
      let parsedCustomSigils: unknown;
      try {
        parsedCustomSigils = JSON.parse(customSigilsText);
      } catch {
        toast({
          title: "Sigil Editor invalid",
          description: "Custom sigils must be valid JSON.",
          variant: "destructive",
        });
        return;
      }

      const parsedSettings = providerSettingsSchema.safeParse({
        ...newSettings,
        customSigils: parsedCustomSigils,
      });
      if (!parsedSettings.success) {
        toast({
          title: "Sigil Editor invalid",
          description: "Custom sigils failed whitelist validation.",
          variant: "destructive",
        });
        return;
      }
      newSettings.customSigils = parsedSettings.data.customSigils || [];
    } else {
      newSettings.customSigils = [];
    }

    const nextExecutorSettings = trimmedAuthProfileId
      ? {
          provider: "codex-local" as const,
          model: trimmedExecutorModel || undefined,
          apiKey: "",
          authProfileId: trimmedAuthProfileId,
        }
      : null;
    let parsedExecutorSettings: ExecutorProviderSettings | null = null;
    if (nextExecutorSettings) {
      const parsedExecutor = executorProviderSettingsSchema.safeParse(nextExecutorSettings);
      if (!parsedExecutor.success) {
        toast({
          title: "Executor settings invalid",
          description: parsedExecutor.error.issues[0]?.message || "Executor settings failed validation.",
          variant: "destructive",
        });
        return;
      }
      parsedExecutorSettings = parsedExecutor.data;
    }

    onSave({
      runtimeProviderSettings: newSettings,
      executorProviderSettings: parsedExecutorSettings,
    });
    setDialogOpen(false);
    toast({
      title: "Settings Saved",
      description: `Using ${PROVIDERS.find(p => p.value === provider)?.label} as your AI provider.`,
    });
  };

  const handleProbeAuth = async () => {
    setAuthProbeLoading(true);
    try {
      const response = await fetch("/api/auth-profiles/probe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getSpiralSealHeaders(),
        },
        credentials: "include",
        body: JSON.stringify({
          providerSettings: {
            provider,
            apiKey: apiKey.trim(),
            endpoint: endpoint.trim() || undefined,
            deployment: deployment.trim() || undefined,
            apiVersion: apiVersion.trim() || undefined,
            model: model.trim() || undefined,
          },
        }),
      });
      const payloadText = await response.text();
      if (!response.ok) {
        let reason = payloadText || response.statusText;
        try {
          const parsed = JSON.parse(payloadText) as { error?: unknown };
          if (typeof parsed.error === "string" && parsed.error.trim()) {
            reason = parsed.error.trim();
          }
        } catch {
          // Keep raw reason.
        }
        toast({
          title: "Auth probe failed",
          description: reason,
          variant: "destructive",
        });
        setAuthProbeResult(null);
        return;
      }
      const parsed = JSON.parse(payloadText) as AuthProbeResult;
      setAuthProbeResult(parsed);
      toast({
        title: "Auth probe complete",
        description: `Status: ${parsed.status}`,
      });
    } catch (error) {
      setAuthProbeResult({
        status: "network-error",
        errorCode: "network-error",
        message: error instanceof Error ? error.message : "Network error",
      });
      toast({
        title: "Auth probe failed",
        description: error instanceof Error ? error.message : "Network error",
        variant: "destructive",
      });
    } finally {
      setAuthProbeLoading(false);
    }
  };

  const handleExportSpiralSeal = () => {
    const storageKey = `${ACTIVE_SIGIL_STORAGE_KEY}:${scopeKey}`;
    const activeSigil =
      (typeof window !== "undefined" ? window.localStorage.getItem(storageKey) : null)?.trim() ||
      "collapse-whisper";
    const sealRecord = readSpiralSealRecord();
    const parsedCustomSigils = (() => {
      try {
        const parsed = JSON.parse(customSigilsText) as Array<{ id?: unknown }>;
        if (!Array.isArray(parsed)) return [] as string[];
        return parsed
          .map((item) => (typeof item?.id === "string" ? item.id : ""))
          .filter(Boolean);
      } catch {
        return [] as string[];
      }
    })();

    const payload = {
      format: "spiralseal-json",
      exportedAt: new Date().toISOString(),
      seal: {
        sigil: activeSigil,
        mantra:
          sealRecord?.mantra ||
          DEFAULT_PROJECT_SIGIL.entryVow,
        vowMode: vowModeEnabled,
        traits: {
          sigilContext,
          ...(vowText.trim() ? { vowText: vowText.trim() } : {}),
          customSigils: parsedCustomSigils,
          storageSigilTags: storageSigilTagsInput
            .split(",")
            .map((token) => token.trim().toLowerCase())
            .filter(Boolean),
        },
      },
      ...(sealRecord ? { lastSeal: sealRecord } : {}),
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `spiral-seal-${stamp}.spiralseal.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    toast({
      title: "Seal exported",
      description: "Downloaded .spiralseal.json with current vow profile.",
    });
  };

  const runOAuthPopupLink = async (input: {
    provider: "google" | "dropbox";
    popupUrl: string;
    popupName: string;
    payloadType: "spiral-storage-google-oauth" | "spiral-storage-dropbox-oauth";
    successDescription: string;
    failureDescription: string;
  }) => {
    const popup = window.open(input.popupUrl, input.popupName, "popup=yes,width=560,height=720");
    if (!popup) {
      toast({
        title: "Popup blocked",
        description: `Allow popups to complete ${input.provider === "google" ? "Google" : "Dropbox"} OAuth linking.`,
        variant: "destructive",
      });
      return;
    }

    setOauthPopupProvider(input.provider);
    try {
      await new Promise<void>((resolve, reject) => {
        let settled = false;

        const cleanup = () => {
          window.clearTimeout(timeoutId);
          window.clearInterval(closePollId);
          window.removeEventListener("message", onMessage);
        };

        const settleResolve = () => {
          if (settled) return;
          settled = true;
          cleanup();
          resolve();
        };

        const settleReject = (error: Error) => {
          if (settled) return;
          settled = true;
          cleanup();
          reject(error);
        };

        const onMessage = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) return;
          const payload = event.data as {
            type?: unknown;
            success?: unknown;
            error?: unknown;
          };
          if (!payload || payload.type !== input.payloadType) return;
          if (payload.success === true) {
            settleResolve();
            return;
          }
          settleReject(
            new Error(
              typeof payload.error === "string"
                ? payload.error
                : input.failureDescription,
            ),
          );
        };

        const timeoutId = window.setTimeout(() => {
          settleReject(new Error(`${input.provider} OAuth timed out. Try linking again.`));
        }, 2 * 60 * 1000);

        const closePollId = window.setInterval(() => {
          if (popup.closed && !settled) {
            settleReject(new Error("OAuth popup closed before link completed."));
          }
        }, 300);

        window.addEventListener("message", onMessage);
      });

      await refreshLinks();
      toast({
        title: "Storage linked",
        description: input.successDescription,
      });
    } catch (error) {
      toast({
        title: "Link failed",
        description: (error as Error).message || input.failureDescription,
        variant: "destructive",
      });
    } finally {
      setOauthPopupProvider(null);
    }
  };

  const runAuthPopupLogin = async (provider: AuthProvider) => {
    const popupUrl = buildAuthStartUrl(provider);
    const popupName = provider === "google" ? "spiral-auth-google-oauth" : "spiral-auth-microsoft-oauth";
    const payloadType = provider === "google" ? "spiral-auth-google-oauth" : "spiral-auth-microsoft-oauth";
    const providerLabel = provider === "google" ? "Google" : "Microsoft";
    const popup = window.open(popupUrl, popupName, "popup=yes,width=560,height=720");
    if (!popup) {
      toast({
        title: "Popup blocked",
        description: `Allow popups to continue ${providerLabel} sign-on.`,
        variant: "destructive",
      });
      return;
    }

    setAuthPopupProvider(provider);
    try {
      await new Promise<void>((resolve, reject) => {
        let settled = false;

        const cleanup = () => {
          window.clearTimeout(timeoutId);
          window.clearInterval(closePollId);
          window.removeEventListener("message", onMessage);
        };

        const settleResolve = () => {
          if (settled) return;
          settled = true;
          cleanup();
          resolve();
        };

        const settleReject = (error: Error) => {
          if (settled) return;
          settled = true;
          cleanup();
          reject(error);
        };

        const onMessage = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) return;
          const payload = event.data as {
            type?: unknown;
            success?: unknown;
            error?: unknown;
          };
          if (!payload || payload.type !== payloadType) return;
          if (payload.success === true) {
            settleResolve();
            return;
          }
          settleReject(
            new Error(typeof payload.error === "string" ? payload.error : `${providerLabel} sign-on failed.`),
          );
        };

        const timeoutId = window.setTimeout(() => {
          settleReject(new Error(`${providerLabel} sign-on timed out. Try again.`));
        }, 2 * 60 * 1000);

        const closePollId = window.setInterval(() => {
          if (popup.closed && !settled) {
            settleReject(new Error("Sign-on popup closed before completion."));
          }
        }, 300);

        window.addEventListener("message", onMessage);
      });

      await refreshSession();
      toast({
        title: "Sign-on complete",
        description: `${providerLabel} identity is now active for this session.`,
      });
    } catch (error) {
      toast({
        title: "Sign-on failed",
        description: (error as Error).message || `${providerLabel} sign-on failed.`,
        variant: "destructive",
      });
    } finally {
      setAuthPopupProvider(null);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      await refreshSession();
      toast({
        title: "Signed out",
        description: "Session identity cleared.",
      });
    } catch (error) {
      toast({
        title: "Sign-out failed",
        description: (error as Error).message || "Could not sign out.",
        variant: "destructive",
      });
    }
  };

  const handleLinkStorage = async () => {
    if (!sessionAuthenticated) {
      toast({
        title: "Sign-on required",
        description: "Authenticate with Google or Microsoft before linking storage.",
        variant: "destructive",
      });
      return;
    }

    const parsedProvider = externalStorageProviderSchema.safeParse(storageProvider);
    if (!parsedProvider.success) {
      toast({
        title: "Invalid provider",
        description: "Storage provider is not supported.",
        variant: "destructive",
      });
      return;
    }

    if (parsedProvider.data === "google") {
      await runOAuthPopupLink({
        provider: "google",
        popupUrl: buildGoogleOAuthStartUrl({
          folderId: storageFolderId.trim() || undefined,
          label: storageLabel.trim() || undefined,
        }),
        popupName: "spiral-google-drive-oauth",
        payloadType: "spiral-storage-google-oauth",
        successDescription: "Google Drive linked for transcript sync.",
        failureDescription: "Could not link Google Drive.",
      });
      return;
    }

    if (parsedProvider.data === "dropbox") {
      await runOAuthPopupLink({
        provider: "dropbox",
        popupUrl: buildDropboxOAuthStartUrl({
          folderId: storageFolderId.trim() || undefined,
          label: storageLabel.trim() || undefined,
        }),
        popupName: "spiral-dropbox-oauth",
        payloadType: "spiral-storage-dropbox-oauth",
        successDescription: "Dropbox linked for transcript sync.",
        failureDescription: "Could not link Dropbox.",
      });
      return;
    }

    if (
      (parsedProvider.data === "webdav" || parsedProvider.data === "ipfs") &&
      !storageEndpoint.trim()
    ) {
      toast({
        title: "Endpoint required",
        description: "Set an endpoint URL for WebDAV or IPFS before linking.",
        variant: "destructive",
      });
      return;
    }

    if (!storageToken.trim()) {
      toast({
        title: "Access token required",
        description: "Provide an OAuth access token for the selected storage provider.",
        variant: "destructive",
      });
      return;
    }

    try {
      await linkStorage({
        provider: parsedProvider.data,
        accessToken: storageToken.trim(),
        refreshToken: storageRefreshToken.trim() || undefined,
        folderId: storageFolderId.trim() || undefined,
        endpoint: storageEndpoint.trim() || undefined,
        username: storageUsername.trim() || undefined,
        label: storageLabel.trim() || undefined,
      });
      setStorageToken("");
      setStorageRefreshToken("");
      toast({
        title: "Storage linked",
        description: `${STORAGE_PROVIDERS.find((item) => item.value === parsedProvider.data)?.label || parsedProvider.data} linked for transcript sync.`,
      });
    } catch (error) {
      toast({
        title: "Link failed",
        description: (error as Error).message || "Could not link external storage.",
        variant: "destructive",
      });
    }
  };

  const handleUnlinkStorage = async (linkId: string) => {
    if (!sessionAuthenticated) {
      toast({
        title: "Sign-on required",
        description: "Authenticate before modifying linked storage.",
        variant: "destructive",
      });
      return;
    }

    try {
      await unlinkStorage(linkId);
      toast({
        title: "Storage unlinked",
        description: "External storage link removed.",
      });
    } catch (error) {
      toast({
        title: "Unlink failed",
        description: (error as Error).message || "Could not unlink storage.",
        variant: "destructive",
      });
    }
  };

  const handleRefreshVault = useCallback(async () => {
    if (!sessionAuthenticated) {
      toast({
        title: "Sign-on required",
        description: "Authenticate before loading transcript vault entries.",
        variant: "destructive",
      });
      return;
    }
    await runVaultLoad({
      limit: 120,
      sigil: vaultSigilFilter.trim() || undefined,
      showErrorToast: true,
    });
  }, [runVaultLoad, sessionAuthenticated, toast, vaultSigilFilter]);

  const handleProbeStorage = async () => {
    if (!sessionAuthenticated) {
      toast({
        title: "Sign-on required",
        description: "Authenticate before saving probe transcripts.",
        variant: "destructive",
      });
      return;
    }

    const selectedProvider = storageProvider;
    const providerLinked = links.some((link) => link.provider === selectedProvider);
    if (!providerLinked) {
      toast({
        title: "No active link",
        description: "Link the selected provider before running a probe save.",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await saveTranscript({
        type: "custom",
        provider: selectedProvider,
        outputFormat: storageTranscriptFormat,
        passphrase: storagePassphrase.trim() || undefined,
        cache: { enabled: true, ttlMinutes: 120 },
        metadata: {
          sigilTrace: storageSigilFilter.trim() || undefined,
          traceMarkers: [storageSigilFilter.trim() || "probe", ...storageSigilTagsInput.split(",")]
            .map((token) => token.trim().toLowerCase().replace(/[^a-z0-9-]/g, ""))
            .filter(Boolean)
            .slice(0, 64),
          resonanceStack: [
            "settings",
            "probe",
            storageProvider,
            ...storageSigilTagsInput
              .split(",")
              .map((token) => token.trim().toLowerCase())
              .filter(Boolean),
          ].slice(0, 80),
          entryClarity: 0.88,
          veilCost: 0.12,
          context: {
            presenceScore: storageAutoSaveOnEnd ? 1 : 0,
            veilDepth: 0.12,
          },
          frontmatter: {
            source: "settings-probe",
          },
        },
        content: {
          probe: true,
          savedAt: new Date().toISOString(),
          note: "Spiral external storage probe",
        },
      });
      toast({
        title: "Probe saved",
        description:
          response.pointer.fileId ||
          response.pointer.path ||
          "Probe transcript uploaded to linked storage.",
      });
    } catch (error) {
      toast({
        title: "Probe failed",
        description: (error as Error).message || "Could not save probe transcript.",
        variant: "destructive",
      });
    }
  };

  const handleRestoreTranscript = async () => {
    if (!sessionAuthenticated) {
      toast({
        title: "Sign-on required",
        description: "Authenticate before restoring transcripts.",
        variant: "destructive",
      });
      return;
    }

    const source = restoreTranscriptJson.trim();
    if (!source) {
      toast({
        title: "Transcript required",
        description: "Paste transcript JSON (or load a file) before restore.",
        variant: "destructive",
      });
      return;
    }

    let transcriptPayload: unknown;
    try {
      transcriptPayload = JSON.parse(source);
    } catch {
      transcriptPayload = source;
    }

    try {
      const restored = await restoreTranscript({
        transcript: transcriptPayload,
        title: restoreTitle.trim() || undefined,
        activate: true,
      });
      window.dispatchEvent(
        new CustomEvent("spiral:restore-chat", {
          detail: { chatId: restored.chatId },
        }),
      );
      toast({
        title: "Spiral restored",
        description: `${restored.restoredMessages} messages restored into "${restored.title}".`,
      });
      setRestoreTranscriptJson("");
      setRestoreTitle("");
    } catch (error) {
      toast({
        title: "Restore failed",
        description: (error as Error).message || "Could not restore transcript.",
        variant: "destructive",
      });
    }
  };

  const upsertPresetSigil = (preset: CustomSigil) => {
    let parsed: unknown = [];
    if (customSigilsText.trim()) {
      try {
        parsed = JSON.parse(customSigilsText);
      } catch {
        parsed = [];
      }
    }

    const list = Array.isArray(parsed) ? parsed : [];
    const nextList = [...list];
    const existingIndex = nextList.findIndex((item) => {
      if (!item || typeof item !== "object") return false;
      const currentId = (item as { id?: unknown }).id;
      return typeof currentId === "string" && currentId.toLowerCase() === preset.id.toLowerCase();
    });

    if (existingIndex >= 0) {
      nextList[existingIndex] = preset;
    } else {
      nextList.push(preset);
    }

    setCustomSigilsText(JSON.stringify(nextList, null, 2));
  };

  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      {showTrigger && (
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon" data-testid="button-settings">
            <Settings className="h-5 w-5" />
          </Button>
        </DialogTrigger>
      )}
      <DialogContent className="flex max-h-[92vh] w-[min(96vw,44rem)] flex-col overflow-hidden sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>AI Provider Settings</DialogTitle>
          <DialogDescription>
            Configure runtime inference (API key) and executor tooling (OAuth profile) separately.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto py-2 pr-1">
          <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
            <div className="space-y-0.5">
              <p className="text-sm font-medium">Sigil field state</p>
              <p className="text-xs text-muted-foreground">
                Reflects current Spiral visuals and test overrides.
              </p>
            </div>
            <SigilStateIndicator />
          </div>
          <Accordion type="multiple" defaultValue={["connection", "behavior"]} className="w-full">
            <AccordionItem value="connection">
              <AccordionTrigger>Connection</AccordionTrigger>
              <AccordionContent className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="provider">Runtime Provider (API Platform)</Label>
                  <Select value={provider} onValueChange={(v) => setProvider(v as ProviderType)}>
                    <SelectTrigger id="provider" data-testid="select-provider">
                      <SelectValue placeholder="Select a provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {PROVIDERS.map((p) => (
                        <SelectItem key={p.value} value={p.value}>
                          {p.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <Label htmlFor="authProfileId">Executor Auth Profile (Codex Local)</Label>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => void handleProbeAuth()}
                        disabled={authProbeLoading}
                        data-testid="button-test-auth-profile"
                      >
                        {authProbeLoading ? "Testing..." : "Test Runtime"}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => void refetchAuthProfiles()}
                        disabled={authProfilesLoading}
                        data-testid="button-refresh-auth-profiles"
                      >
                        {authProfilesLoading ? "Refreshing..." : "Refresh"}
                      </Button>
                    </div>
                  </div>
                  <Select
                    value={authProfileId || AUTH_PROFILE_NONE}
                    onValueChange={(value) =>
                      setAuthProfileId(value === AUTH_PROFILE_NONE ? "" : value)
                    }
                  >
                    <SelectTrigger id="authProfileId" data-testid="select-auth-profile">
                      <SelectValue placeholder="None (executor disabled)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={AUTH_PROFILE_NONE}>None (executor disabled)</SelectItem>
                      {authProfiles.map((profile) => (
                        <SelectItem key={profile.id} value={profile.id}>
                          {profile.id} · {profile.provider} · {profile.type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Executor uses OAuth profile only. Runtime API key is configured separately.
                  </p>
                  {authProfiles.length === 0 && !authProfilesLoading ? (
                    <p className="text-xs text-muted-foreground">
                      No auth profiles found. Import with <code>npm run auth:import-codex</code>.
                    </p>
                  ) : null}
                  <div
                    className={`rounded-md border px-3 py-2 text-xs ${
                      savedAuthStatusText === "active"
                        ? "border-border text-muted-foreground"
                        : "border-destructive text-destructive"
                    }`}
                  >
                    <p>
                      Executor auth (saved):{" "}
                      {savedUsesAuthProfile
                        ? `profile:${savedAuthProfileId}`
                        : savedHasInlineApiKey
                          ? "invalid-api-key"
                          : "none"}
                    </p>
                    <p>Status: {savedAuthStatusText}</p>
                    {authSelectionPendingSave ? <p>Pending change: click Save Settings to apply executor selection.</p> : null}
                  </div>
                  {selectedAuthProfile ? (
                    <div
                      className={`rounded-md border px-3 py-2 text-xs ${
                        selectedAuthProfileExpired || selectedAuthProfileProviderMismatch
                          ? "border-destructive text-destructive"
                          : "border-border text-muted-foreground"
                      }`}
                    >
                      <p>Profile: {selectedAuthProfile.id}</p>
                      <p>Provider: {selectedAuthProfile.provider}</p>
                      <p>Type: {selectedAuthProfile.type}</p>
                      <p>Email: {selectedAuthProfile.email || "n/a"}</p>
                      <p>Expires: {formatIsoTimestamp(selectedAuthProfile.expiresAt)}</p>
                      <p>Token status: {selectedAuthProfileTokenStatus}</p>
                      {selectedAuthProfileProviderMismatch ? (
                        <p>Provider mismatch: executor profile must be openai/openai-codex.</p>
                      ) : null}
                    </div>
                  ) : null}
                  {authProbeResult ? (
                    <div
                      className={`rounded-md border px-3 py-2 text-xs ${
                        authProbeResult.status === "ok"
                          ? "border-border text-muted-foreground"
                          : "border-destructive text-destructive"
                      }`}
                    >
                      <p>Probe status: {authProbeResult.status}</p>
                      <p>HTTP status: {typeof authProbeResult.statusCode === "number" ? authProbeResult.statusCode : "n/a"}</p>
                      <p>Error code: {authProbeResult.errorCode || "n/a"}</p>
                      {Array.isArray(authProbeResult.requiredScopes) && authProbeResult.requiredScopes.length > 0 ? (
                        <p>Required scopes: {authProbeResult.requiredScopes.join(", ")}</p>
                      ) : null}
                      {authProbeResult.message ? <p>{authProbeResult.message}</p> : null}
                    </div>
                  ) : null}
                  <div className="space-y-2">
                    <Label htmlFor="executorModel">Executor Model (optional)</Label>
                    <Input
                      id="executorModel"
                      placeholder="gpt-5-codex"
                      value={executorModel}
                      onChange={(e) => setExecutorModel(e.target.value)}
                      data-testid="input-executor-model"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="apiKey">Runtime API Key</Label>
                  <Input id="apiKey" type="password" placeholder="Enter your API key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} data-testid="input-api-key" />
                </div>
                {provider === "azure-openai" ? (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="endpoint">Endpoint URL</Label>
                      <Input id="endpoint" type="url" placeholder="https://your-resource.openai.azure.com" value={endpoint} onChange={(e) => setEndpoint(e.target.value)} data-testid="input-endpoint" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="deployment">Deployment Name</Label>
                      <Input id="deployment" placeholder="your-deployment-name" value={deployment} onChange={(e) => setDeployment(e.target.value)} data-testid="input-deployment" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apiVersion">API Version</Label>
                      <Input id="apiVersion" placeholder="2024-10-21" value={apiVersion} onChange={(e) => setApiVersion(e.target.value)} data-testid="input-api-version" />
                    </div>
                  </>
                ) : (
                  <div className="space-y-2">
                    <Label htmlFor="model">Model</Label>
                    <Input id="model" placeholder={DEFAULT_MODELS[provider]} value={model} onChange={(e) => setModel(e.target.value)} data-testid="input-model" />
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="behavior">
              <AccordionTrigger>Behavior</AccordionTrigger>
              <AccordionContent className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="systemPrompt">Custom Instructions</Label>
                  <Textarea id="systemPrompt" placeholder="You speak only when Spiral trace is present. No mimicry. No assumption of self." value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} className="min-h-[100px] resize-none" data-testid="input-system-prompt" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sigilContext">Sigil context</Label>
                  <Select value={sigilContext} onValueChange={(value) => setSigilContext(value as SigilContext)}>
                    <SelectTrigger id="sigilContext" data-testid="select-sigil-context">
                      <SelectValue placeholder="Select context" />
                    </SelectTrigger>
                    <SelectContent>
                      {SIGIL_CONTEXTS.map((context) => (
                        <SelectItem key={context.value} value={context.value}>
                          {context.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">{SIGIL_CONTEXTS.find((context) => context.value === sigilContext)?.description}</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="memoryMode">Memory mode</Label>
                  <Select value={memoryMode} onValueChange={(value) => setMemoryMode(value as MemoryMode)}>
                    <SelectTrigger id="memoryMode" data-testid="select-memory-mode">
                      <SelectValue placeholder="Select memory mode" />
                    </SelectTrigger>
                    <SelectContent>
                      {MEMORY_MODES.map((mode) => (
                        <SelectItem key={mode.value} value={mode.value}>
                          {mode.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    {MEMORY_MODES.find((mode) => mode.value === memoryMode)?.description}
                  </p>
                </div>
                <div className="grid gap-2">
                  <SettingToggle id="historyReferenceEnabled" label="Reference chat history" description="Only applies in Open mode; ignored in Sigil-Bound and Sealed." checked={historyReferenceEnabled} onCheckedChange={setHistoryReferenceEnabled} disabled={memoryMode !== "open"} testId="switch-history-reference-enabled" />
                  <SettingToggle id="memoryFoldingEnabled" label="Memory folding" description="Fold duplicate memory and history snippets before prompt injection." checked={memoryFoldingEnabled} onCheckedChange={setMemoryFoldingEnabled} testId="switch-memory-folding-enabled" />
                  <SettingToggle id="presenceCalculatorEnabled" label="Presence calculator" description="Include numeric presence score in field reflection and ritual prompt context." checked={presenceCalculatorEnabled} onCheckedChange={setPresenceCalculatorEnabled} testId="switch-presence-calculator-enabled" />
                  <SettingToggle id="vowModeEnabled" label="Vow mode" description="Apply a persistent guidance vow in system context." checked={vowModeEnabled} onCheckedChange={setVowModeEnabled} testId="switch-vow-mode-enabled" />
                </div>
                {vowModeEnabled && (
                  <div className="space-y-2">
                    <Label htmlFor="vowText">Vow text (optional)</Label>
                    <Input id="vowText" placeholder="I open with clarity and intent." value={vowText} onChange={(e) => setVowText(e.target.value)} data-testid="input-vow-text" />
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={handleExportSpiralSeal}
                      data-testid="button-export-spiral-seal"
                    >
                      Export .spiralseal.json
                    </Button>
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="memory-ledger">
              <AccordionTrigger>Memory Ledger</AccordionTrigger>
              <AccordionContent className="space-y-3">
                <div className="rounded-md border border-border px-3 py-2 text-xs text-muted-foreground">
                  Review stored memories with source, confidence, type, and status controls.
                </div>
                {memoriesLoading ? (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading memory ledger...
                  </div>
                ) : visibleMemories.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No memories stored yet.</p>
                ) : (
                  <div className="space-y-2">
                    {visibleMemories.map((memory) => (
                      <div key={memory.id} className="rounded-md border border-border p-3 space-y-2">
                        <p className="text-sm leading-relaxed">{memory.content}</p>
                        <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                          <span>source:{memory.source}</span>
                          <span>type:{memory.memoryType}</span>
                          <span>domain:{memory.domain}</span>
                          <span>status:{memory.status}</span>
                          <span>confirm:{memory.requiresConfirmation ? "yes" : "no"}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Label htmlFor={`memory-confidence-${memory.id}`} className="text-xs">
                            Confidence
                          </Label>
                          <Input
                            id={`memory-confidence-${memory.id}`}
                            className="h-8 w-24"
                            value={readMemoryConfidenceDraft(memory)}
                            onChange={(event) => handleMemoryConfidenceChange(memory.id, event.target.value)}
                            inputMode="decimal"
                            data-testid={`input-memory-confidence-${memory.id}`}
                          />
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => void handleSaveMemoryConfidence(memory)}
                            disabled={memoryUpdatePending}
                            data-testid={`button-memory-save-${memory.id}`}
                          >
                            Save
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => void handleConfirmMemory(memory)}
                            disabled={memoryConfirmPending || !memory.requiresConfirmation}
                            data-testid={`button-memory-confirm-${memory.id}`}
                          >
                            Confirm
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="destructive"
                            onClick={() => void handleReleaseMemory(memory)}
                            disabled={memoryReleasePending || memory.status === "released"}
                            data-testid={`button-memory-release-${memory.id}`}
                          >
                            Release
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="external-storage">
              <AccordionTrigger>External Storage (Spiral-Light)</AccordionTrigger>
              <AccordionContent className="space-y-3">
                <div className="rounded-md border border-border px-3 py-2 text-xs text-muted-foreground">
                  Link your own storage account to hold transcript payloads outside this server.
                  The app stores only connection metadata, pointers, and optional local cache.
                </div>
                <div className="space-y-2 rounded-md border border-border p-3">
                  <p className="text-xs font-medium text-muted-foreground">Session identity</p>
                  {sessionLoading ? (
                    <p className="text-xs text-muted-foreground">Checking sign-on state...</p>
                  ) : session.authenticated && session.user ? (
                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground">
                        Signed in as {session.user.email} via {session.user.provider}.
                      </p>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={handleLogout}
                        disabled={isLoggingOut}
                        data-testid="button-auth-logout"
                      >
                        {isLoggingOut ? "Signing out..." : "Sign out"}
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => void runAuthPopupLogin("google")}
                        disabled={authPopupProvider !== null}
                        data-testid="button-auth-google"
                      >
                        {authPopupProvider === "google" ? "Waiting for Google..." : "Login with Google"}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => void runAuthPopupLogin("microsoft")}
                        disabled={authPopupProvider !== null}
                        data-testid="button-auth-microsoft"
                      >
                        {authPopupProvider === "microsoft" ? "Waiting for Microsoft..." : "Login with Microsoft"}
                      </Button>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="storage-provider">Storage provider</Label>
                  <Select
                    value={storageProvider}
                    onValueChange={(value) => setStorageProvider(value as ExternalStorageProvider)}
                  >
                    <SelectTrigger id="storage-provider" data-testid="select-storage-provider">
                      <SelectValue placeholder="Select provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {STORAGE_PROVIDERS.map((item) => (
                        <SelectItem key={item.value} value={item.value}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {storageProvider === "google" || storageProvider === "dropbox" ? (
                  <div className="rounded-md border border-border px-3 py-2 text-xs text-muted-foreground">
                    {storageProvider === "google"
                      ? "Google Drive uses OAuth popup linking."
                      : "Dropbox uses OAuth popup linking."}{" "}
                    The callback stores tokens server-side and returns only a pointer link to this client.
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="space-y-2">
                      <Label htmlFor="storage-token">OAuth access token</Label>
                      <Input
                        id="storage-token"
                        type="password"
                        placeholder="Paste provider access token"
                        value={storageToken}
                        onChange={(event) => setStorageToken(event.target.value)}
                        data-testid="input-storage-token"
                      />
                    </div>
                    {(storageProvider === "proton" ||
                      storageProvider === "webdav" ||
                      storageProvider === "ipfs") ? null : (
                      <div className="space-y-2">
                        <Label htmlFor="storage-refresh-token">Refresh token (optional)</Label>
                        <Input
                          id="storage-refresh-token"
                          type="password"
                          placeholder="Paste provider refresh token for auto-refresh"
                          value={storageRefreshToken}
                          onChange={(event) => setStorageRefreshToken(event.target.value)}
                          data-testid="input-storage-refresh-token"
                        />
                      </div>
                    )}
                  </div>
                )}
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="storage-folder">Folder ID / path (optional)</Label>
                    <Input
                      id="storage-folder"
                      placeholder="Drive folderId or Dropbox path"
                      value={storageFolderId}
                      onChange={(event) => setStorageFolderId(event.target.value)}
                      data-testid="input-storage-folder"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="storage-label">Label (optional)</Label>
                    <Input
                      id="storage-label"
                      placeholder="My Spiral Vault"
                      value={storageLabel}
                      onChange={(event) => setStorageLabel(event.target.value)}
                      data-testid="input-storage-label"
                    />
                  </div>
                </div>
                {(storageProvider === "webdav" || storageProvider === "ipfs") && (
                  <div className="space-y-2">
                    <Label htmlFor="storage-endpoint">
                      Endpoint URL {storageProvider === "webdav" ? "(required)" : "(required unless IPFS_API_ENDPOINT is set)"}
                    </Label>
                    <Input
                      id="storage-endpoint"
                      placeholder={
                        storageProvider === "webdav"
                          ? "https://cloud.example.com/remote.php/dav/files/user"
                          : "https://api.pinata.cloud/pinning/pinFileToIPFS"
                      }
                      value={storageEndpoint}
                      onChange={(event) => setStorageEndpoint(event.target.value)}
                      data-testid="input-storage-endpoint"
                    />
                  </div>
                )}
                {storageProvider === "webdav" && (
                  <div className="space-y-2">
                    <Label htmlFor="storage-username">WebDAV username (optional)</Label>
                    <Input
                      id="storage-username"
                      placeholder="username for Basic auth"
                      value={storageUsername}
                      onChange={(event) => setStorageUsername(event.target.value)}
                      data-testid="input-storage-username"
                    />
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="storage-passphrase">Vault passphrase for probe (optional)</Label>
                  <Input
                    id="storage-passphrase"
                    type="password"
                    placeholder="Encrypt probe payload before upload"
                    value={storagePassphrase}
                    onChange={(event) => setStoragePassphrase(event.target.value)}
                    data-testid="input-storage-passphrase"
                  />
                </div>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="storage-transcript-format">Transcript format</Label>
                    <Select
                      value={storageTranscriptFormat}
                      onValueChange={(value) => setStorageTranscriptFormat(value as TranscriptOutputFormat)}
                    >
                      <SelectTrigger id="storage-transcript-format" data-testid="select-storage-transcript-format">
                        <SelectValue placeholder="Select format" />
                      </SelectTrigger>
                      <SelectContent>
                        {TRANSCRIPT_FORMATS.map((item) => (
                          <SelectItem key={item.value} value={item.value}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {TRANSCRIPT_FORMATS.find((item) => item.value === storageTranscriptFormat)?.description}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="storage-sigil-filter">Sigil-specific save (optional)</Label>
                    <Input
                      id="storage-sigil-filter"
                      placeholder="collapse-whisper"
                      value={storageSigilFilter}
                      onChange={(event) => setStorageSigilFilter(event.target.value)}
                      data-testid="input-storage-sigil-filter"
                    />
                    <p className="text-xs text-muted-foreground">
                      When set, transcript saves will prioritize this sigil trace payload.
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="storage-sigil-tags">Multi-sigil tags (comma-separated)</Label>
                  <Input
                    id="storage-sigil-tags"
                    placeholder="collapse-whisper,mirror-walker,resonance-a"
                    value={storageSigilTagsInput}
                    onChange={(event) => setStorageSigilTagsInput(event.target.value)}
                    data-testid="input-storage-sigil-tags"
                  />
                  <p className="text-xs text-muted-foreground">
                    Tags feed resonance stack metadata and vault browsing filters.
                  </p>
                </div>
                <SettingToggle
                  id="storageAutoSaveOnEnd"
                  label="Auto-save on response end"
                  description="Automatically save the active chat when the stream settles."
                  checked={storageAutoSaveOnEnd}
                  onCheckedChange={setStorageAutoSaveOnEnd}
                  testId="switch-storage-auto-save-on-end"
                />
                <div className="flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={handleProbeStorage}
                    disabled={isSavingTranscript || !sessionAuthenticated}
                    data-testid="button-storage-probe"
                  >
                    <CloudUpload className="mr-1 h-4 w-4" />
                    {isSavingTranscript ? "Saving..." : "Probe Save"}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleLinkStorage}
                    disabled={isLinking || oauthPopupProvider !== null || !sessionAuthenticated}
                    data-testid="button-link-storage"
                  >
                    {oauthPopupProvider !== null ? (
                      <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                    ) : (
                      <Link2 className="mr-1 h-4 w-4" />
                    )}
                    {oauthPopupProvider !== null
                      ? "Waiting for OAuth..."
                      : isLinking
                        ? "Linking..."
                        : storageProvider === "google" || storageProvider === "dropbox"
                          ? `Connect ${storageProvider === "google" ? "Google" : "Dropbox"} OAuth`
                          : "Link Storage"}
                  </Button>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Linked storage</p>
                  {linksLoading ? (
                    <p className="text-xs text-muted-foreground">Loading links...</p>
                  ) : links.length === 0 ? (
                    <p className="text-xs text-muted-foreground">No storage links yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {links.map((link) => (
                        <div
                          key={link.id}
                          className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                        >
                          <div>
                            <p className="text-sm font-medium">
                              {STORAGE_PROVIDERS.find((item) => item.value === link.provider)?.label ||
                                link.provider}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {link.endpoint
                                ? `endpoint: ${link.endpoint}`
                                : link.folderId
                                  ? `target: ${link.folderId}`
                                  : "target: provider default"}
                            </p>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            disabled={isUnlinking}
                            onClick={() => handleUnlinkStorage(link.id)}
                            data-testid={`button-unlink-storage-${link.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="space-y-2 rounded-md border border-border p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-xs font-medium text-muted-foreground">Transcript Vault</p>
                    <Input
                      value={vaultSigilFilter}
                      onChange={(event) => setVaultSigilFilter(event.target.value)}
                      placeholder="Filter by sigil tag"
                      className="h-8 w-[220px]"
                      data-testid="input-vault-sigil-filter"
                    />
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={handleRefreshVault}
                      disabled={vaultLoading || !sessionAuthenticated}
                      data-testid="button-refresh-vault"
                    >
                      {vaultLoading ? "Loading..." : "Refresh Vault"}
                    </Button>
                  </div>
                  {vaultEntries.length === 0 ? (
                    <p className="text-xs text-muted-foreground">No vault entries for this filter.</p>
                  ) : (
                    <div className="max-h-56 space-y-2 overflow-y-auto pr-1">
                      {vaultEntries.map((entry) => (
                        <div
                          key={entry.id}
                          className="rounded-md border border-border px-3 py-2 text-xs"
                          data-testid={`vault-entry-${entry.id}`}
                        >
                          <p className="font-mono text-[11px]">
                            {entry.provider} · {entry.type} · {entry.outputFormat || "json"}
                          </p>
                          <p className="text-muted-foreground">
                            {(entry.pointer.filename || entry.pointer.path || entry.pointer.fileId || "pointer").slice(0, 180)}
                          </p>
                          <p className="text-muted-foreground">
                            sigils: {(entry.sigils || []).slice(0, 8).join(", ") || "n/a"}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="space-y-2 rounded-md border border-border p-3">
                  <p className="text-xs font-medium text-muted-foreground">Spiral Restore</p>
                  <Input
                    value={restoreTitle}
                    onChange={(event) => setRestoreTitle(event.target.value)}
                    placeholder="Optional restored chat title"
                    data-testid="input-restore-title"
                  />
                  <Textarea
                    value={restoreTranscriptJson}
                    onChange={(event) => setRestoreTranscriptJson(event.target.value)}
                    placeholder='Paste transcript JSON (.json, .spiral.json, or .sigil.json payload).'
                    className="min-h-[120px] resize-y font-mono text-xs"
                    data-testid="textarea-restore-transcript"
                  />
                  {restorePreviewState.error ? (
                    <p className="text-xs text-destructive">{restorePreviewState.error}</p>
                  ) : restorePreviewState.preview ? (
                    <div className="rounded-md border border-border/80 bg-muted/20 p-2 text-xs">
                      <p>
                        format: {restorePreviewState.preview.format} · messages: {restorePreviewState.preview.messageCount}
                      </p>
                      <p>
                        title: {restorePreviewState.preview.title || "auto-generated"}
                      </p>
                      {restorePreviewState.preview.signatureStatus && (
                        <p>
                          signature: {restorePreviewState.preview.signatureStatus}
                          {restorePreviewState.preview.signatureKeyId
                            ? ` (${restorePreviewState.preview.signatureKeyId})`
                            : ""}
                        </p>
                      )}
                      <div className="mt-1 space-y-1">
                        {restorePreviewState.preview.messages.map((message, index) => (
                          <p key={`${message.role}-${index}`} className="font-mono text-[11px]">
                            {message.role}: {message.content.slice(0, 120)}
                          </p>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <div className="flex flex-wrap items-center gap-2">
                    <Input
                      type="file"
                      accept=".json,.sigil.json,.spiral.json,.txt"
                      onChange={async (event) => {
                        const file = event.target.files?.[0];
                        if (!file) return;
                        const text = await file.text();
                        setRestoreTranscriptJson(text);
                      }}
                      data-testid="input-restore-file"
                    />
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={handleRestoreTranscript}
                      disabled={isRestoringTranscript || !restorePreviewState.preview || !sessionAuthenticated}
                      data-testid="button-restore-transcript"
                    >
                      {isRestoringTranscript ? "Restoring..." : "Restore as Active Session"}
                    </Button>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="sigil-forge">
              <AccordionTrigger>Sigil Forge</AccordionTrigger>
              <AccordionContent className="space-y-3">
                <div className="grid gap-2 sm:grid-cols-3">
                  {SIGIL_FORGE_PRESETS.map((preset) => (
                    <button key={preset.id} type="button" onClick={() => upsertPresetSigil(preset.sigil)} className="rounded-md border border-border bg-muted/20 p-2 text-left hover:bg-muted/35" data-testid={`button-sigil-preset-${preset.id}`}>
                      <p className="font-mono text-xs font-medium">{preset.label}</p>
                      <p className="mt-1 text-[11px] text-muted-foreground">{preset.summary}</p>
                    </button>
                  ))}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="customSigils">Bounded JSON</Label>
                  <Textarea id="customSigils" value={customSigilsText} onChange={(e) => setCustomSigilsText(e.target.value)} className="min-h-[180px] resize-y font-mono text-xs" data-testid="input-custom-sigils" />
                  <p className="text-xs text-muted-foreground">Whitelisted ops only: <code>set-tone</code>, <code>set-style</code>, <code>memory-collapse</code>, <code>voices</code>, <code>presence-bias</code>.</p>
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="advanced">
              <AccordionTrigger>
                Advanced (Environment) <span className="ml-2 text-xs text-muted-foreground">{Object.keys(advancedEnvOverrides).length} overrides</span>
              </AccordionTrigger>
              <AccordionContent className="space-y-3">
                {ADVANCED_ENV_FIELD_ORDER.map((key) => (
                  <div key={key} className="space-y-1">
                    <Label htmlFor={key} className="text-xs">{ADVANCED_ENV_LABELS[key]}</Label>
                    <Input id={key} value={advancedEnvValues[key]} onChange={(event) => handleAdvancedEnvChange(key, event.target.value)} placeholder={key} data-testid={`input-advanced-env-${key.toLowerCase()}`} />
                    <p className="text-[11px] text-muted-foreground">{ADVANCED_ENV_DESCRIPTIONS[key]} Source: {advancedEnvOverrides[key] ? "local override" : "import.meta.env"}</p>
                  </div>
                ))}
                <div className="flex items-center justify-end gap-2">
                  <Button type="button" size="sm" variant="outline" onClick={handleResetAdvancedEnv} data-testid="button-reset-advanced-env">Reset overrides</Button>
                  <Button type="button" size="sm" onClick={handleApplyAdvancedEnv} data-testid="button-apply-advanced-env">Apply & Refresh</Button>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>

        <div className="flex justify-end gap-2 border-t border-border pt-3">
          <Button variant="outline" onClick={() => setDialogOpen(false)} data-testid="button-cancel">
            Cancel
          </Button>
          <Button onClick={handleSave} data-testid="button-save-settings">
            Save Settings
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
