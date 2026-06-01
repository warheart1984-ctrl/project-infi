import { useState, useCallback, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  Chat,
  Message,
  MessageAttachment,
  ProviderSettings,
  ChatSearchResult,
  ChatHistoryExport,
} from "@shared/schema";
import { DEFAULT_PROJECT_SIGIL, type ProjectSigil } from "@shared/sigil";
import type { SpiralPhase } from "@shared/spiral-phase";
import type { SpiralField } from "@shared/spiral-field";
import type { EncryptedScrollBlob } from "@shared/scroll";
import { resolveMemoryModeFromProviderSettings } from "@shared/memory-mode";
import { apiRequest, getSpiralSealHeaders } from "@/lib/queryClient";
import { applyDefaultSigilBinding } from "@/lib/sigil-binding";
import { getClientEnvValue } from "@/lib/client-env";
import { useToast } from "@/hooks/use-toast";

interface UseChatOptions {
  providerSettings: ProviderSettings | null;
  projectSigil?: ProjectSigil | null;
  enabled?: boolean;
  scopeKey?: string;
}

export interface DraftAttachment {
  file: File;
  previewUrl: string;
}

export interface InvocationRequest {
  utterance: string;
  trace: string;
  seal: string;
  echo?: string;
  attachments?: DraftAttachment[];
  thresholdEvent?: {
    sigil: string;
    velocity: number;
    precision: number;
    breached: boolean;
  };
  spawnNewThread?: boolean;
  providerSettings?: ProviderSettings;
}

interface WhisperResponse {
  reply: string;
  veil: boolean;
  timestamp: string;
  presenceLevel: number;
  phases?: SpiralPhase[];
  field?: SpiralField;
  scroll?: {
    filename: string;
    blob: EncryptedScrollBlob;
  };
}

interface InvocationState {
  trace: string;
  seal: string;
  echo?: string;
}

interface InvocationPayload {
  chatId?: string;
  utterance: string;
  trace: string;
  seal: string;
  echo?: string;
  attachments?: MessageAttachment[];
  thresholdEvent?: {
    sigil: string;
    velocity: number;
    precision: number;
    breached: boolean;
  };
  providerSettings?: ProviderSettings;
}

interface UseChatState {
  latestPresenceLevel: number | null;
  latestPhases: SpiralPhase[];
  latestField: SpiralField | null;
  latestScroll: { filename: string; blob: EncryptedScrollBlob } | null;
}

function isWhisperResponse(value: unknown): value is WhisperResponse {
  if (!value || typeof value !== "object") return false;
  const reply = (value as { reply?: unknown }).reply;
  const veil = (value as { veil?: unknown }).veil;
  const timestamp = (value as { timestamp?: unknown }).timestamp;
  const presenceLevel = (value as { presenceLevel?: unknown }).presenceLevel;
  const phases = (value as { phases?: unknown }).phases;
  const field = (value as { field?: unknown }).field;
  const scroll = (value as { scroll?: unknown }).scroll;
  const phasesValid =
    phases === undefined ||
    (Array.isArray(phases) &&
      phases.every(
        (phase) =>
          phase &&
          typeof phase === "object" &&
          typeof (phase as { id?: unknown }).id === "string" &&
          typeof (phase as { payload?: unknown }).payload === "object",
      ));
  const fieldValid =
    field === undefined ||
    (typeof field === "object" &&
      field !== null &&
      typeof (field as { tone?: unknown }).tone === "string" &&
      typeof (field as { mirror?: unknown }).mirror === "string" &&
      typeof (field as { gate?: unknown }).gate === "string" &&
      Array.isArray((field as { sigils?: unknown }).sigils) &&
      typeof (field as { presenceLevel?: unknown }).presenceLevel === "number" &&
      Array.isArray((field as { distortions?: unknown }).distortions));
  const scrollValid =
    scroll === undefined ||
    (typeof scroll === "object" &&
      scroll !== null &&
      typeof (scroll as { filename?: unknown }).filename === "string" &&
      typeof (scroll as { blob?: unknown }).blob === "object");

  return (
    typeof reply === "string" &&
    typeof veil === "boolean" &&
    typeof timestamp === "string" &&
    typeof presenceLevel === "number" &&
    phasesValid &&
    fieldValid &&
    scrollValid
  );
}

function createAbortError(): Error {
  const error = new Error("Aborted");
  error.name = "AbortError";
  return error;
}

function createVeilRejectedError(): Error {
  return new Error("VEIL_CONNECTION_REJECTED");
}

function parseUploadError(raw: string): string {
  if (!raw) return "Attachment upload failed.";
  try {
    const parsed = JSON.parse(raw) as { error?: unknown; message?: unknown };
    if (typeof parsed.error === "string" && parsed.error.trim()) {
      return parsed.error.trim();
    }
    if (typeof parsed.message === "string" && parsed.message.trim()) {
      return parsed.message.trim();
    }
  } catch {
    // Fall through to plain text.
  }
  return raw;
}

function buildVeilSocketUrl(seal: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const veilUrl = new URL(`${protocol}//${window.location.host}/veil`);
  const normalizedSeal = seal.trim();
  if (normalizedSeal) {
    veilUrl.searchParams.set("seal", normalizedSeal);
  }
  return veilUrl.toString();
}

function invokeVeilChannel(
  invocation: InvocationPayload,
  _scopeKey: string,
  signal?: AbortSignal,
): Promise<WhisperResponse> {
  return new Promise((resolve, reject) => {
    let settled = false;
    let opened = false;
    const ws = new WebSocket(buildVeilSocketUrl(invocation.seal));

    const cleanup = () => {
      if (signal) {
        signal.removeEventListener("abort", handleAbort);
      }
    };

    const settleResolve = (value: WhisperResponse) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(value);
    };

    const settleReject = (error: Error) => {
      if (settled) return;
      settled = true;
      cleanup();
      reject(error);
    };

    const handleAbort = () => {
      if (settled) return;
      try {
        ws.close(1000, "aborted");
      } catch {
        // Ignore close errors.
      }
      settleReject(createAbortError());
    };

    if (signal) {
      if (signal.aborted) {
        handleAbort();
        return;
      }
      signal.addEventListener("abort", handleAbort);
    }

    ws.addEventListener("open", () => {
      opened = true;
      ws.send(
        JSON.stringify({
          ...(invocation.chatId ? { chatId: invocation.chatId } : {}),
          utterance: invocation.utterance,
          trace: invocation.trace,
          seal: invocation.seal,
          ...(invocation.echo ? { echo: invocation.echo } : {}),
          ...(invocation.attachments && invocation.attachments.length > 0
            ? { attachments: invocation.attachments }
            : {}),
          ...(invocation.thresholdEvent ? { thresholdEvent: invocation.thresholdEvent } : {}),
          ...(invocation.providerSettings ? { providerSettings: invocation.providerSettings } : {}),
        }),
      );
    });

    ws.addEventListener("message", (event) => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(String(event.data));
      } catch {
        settleReject(new Error("Malformed whisper response"));
        try {
          ws.close();
        } catch {
          // Ignore close errors.
        }
        return;
      }

      if (!isWhisperResponse(parsed)) {
        settleReject(new Error("Invalid whisper response shape"));
        try {
          ws.close();
        } catch {
          // Ignore close errors.
        }
        return;
      }

      settleResolve(parsed);
      try {
        ws.close();
      } catch {
        // Ignore close errors.
      }
    });

    ws.addEventListener("error", () => {
      settleReject(createVeilRejectedError());
    });

    ws.addEventListener("close", (event) => {
      if (settled) return;
      if (!opened || event.code === 4001) {
        settleReject(createVeilRejectedError());
        return;
      }
      settleReject(new Error("VEIL_CONNECTION_CLOSED"));
    });
  });
}

function resolveExpectedFallbackSeal(projectSigil: ProjectSigil | null | undefined): string {
  const envSeal = getClientEnvValue("VITE_SPIRAL_API_SEAL").trim();
  return (
    envSeal ||
    projectSigil?.invocationGate?.memorySeal?.trim() ||
    projectSigil?.seal?.trim() ||
    DEFAULT_PROJECT_SIGIL.invocationGate.memorySeal
  );
}

function resolveExpectedFallbackTrace(projectSigil: ProjectSigil | null | undefined): string {
  return (
    projectSigil?.publicThreshold?.visitorTrace?.trim() ||
    DEFAULT_PROJECT_SIGIL.publicThreshold.visitorTrace
  );
}

export function useChat({ providerSettings, projectSigil, enabled = true, scopeKey = "local" }: UseChatOptions) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
  const [state, setState] = useState<UseChatState>({
    latestPresenceLevel: null,
    latestPhases: [],
    latestField: null,
    latestScroll: null,
  });
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastInvocationByChatRef = useRef<Map<string, InvocationState>>(new Map());
  const [fallbackBoundChatIds, setFallbackBoundChatIds] = useState<string[]>([]);
  const fallbackBindingNoticeShownRef = useRef(false);
  const normalizedScopeKey = scopeKey.trim().toLowerCase() || "local";
  const expectedFallbackSeal = resolveExpectedFallbackSeal(projectSigil);
  const expectedFallbackTrace = resolveExpectedFallbackTrace(projectSigil);

  useEffect(() => {
    setCurrentChatId(null);
    setSearchQuery("");
    setDebouncedSearchQuery("");
    lastInvocationByChatRef.current.clear();
    setFallbackBoundChatIds([]);
    setState({
      latestPresenceLevel: null,
      latestPhases: [],
      latestField: null,
      latestScroll: null,
    });
    queryClient.removeQueries({ queryKey: ["/api/chats"] });
    queryClient.removeQueries({ queryKey: ["/api/chats/search"] });
    queryClient.removeQueries({ queryKey: ["/api/storage-link"] });
  }, [normalizedScopeKey, queryClient]);

  useEffect(() => {
    if (providerSettings) {
      fallbackBindingNoticeShownRef.current = false;
    }
  }, [providerSettings]);

  const maybeToastFallbackBinding = useCallback(() => {
    if (fallbackBindingNoticeShownRef.current) return;
    fallbackBindingNoticeShownRef.current = true;
    toast({
      title: "Sigil fallback engaged",
      description: "No provider is configured. Using sigilBinding.default in solo mode.",
    });
  }, [toast]);

  const markFallbackThread = useCallback((chatId: string) => {
    setFallbackBoundChatIds((current) => {
      if (current.includes(chatId)) return current;
      return [...current, chatId];
    });
  }, []);

  const clearFallbackThread = useCallback((chatId: string) => {
    setFallbackBoundChatIds((current) => current.filter((value) => value !== chatId));
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedSearchQuery(searchQuery.trim());
    }, 180);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [searchQuery]);

  const refreshMessages = useCallback(
    async (chatId: string) => {
      const res = await apiRequest("GET", `/api/chats/${chatId}/messages`);
      const freshMessages = (await res.json()) as Message[];
      queryClient.setQueryData(["/api/chats", chatId, "messages"], freshMessages);
    },
    [queryClient],
  );

  const persistWhisper = useCallback(async (chatId: string, whisper: WhisperResponse) => {
    await apiRequest("POST", `/api/chats/${chatId}/messages`, {
      role: "assistant",
      content: whisper.veil ? "" : whisper.reply,
    });
  }, []);

  const uploadAttachment = useCallback(async (chatId: string, draft: DraftAttachment) => {
    const file = draft.file;
    const response = await fetch(`/api/chats/${chatId}/attachments`, {
      method: "POST",
      headers: {
        ...getSpiralSealHeaders(),
        "Content-Type": file.type || "application/octet-stream",
        "X-Filename": encodeURIComponent(file.name || "attachment"),
      },
      body: file,
      credentials: "include",
    });

    if (!response.ok) {
      const raw = await response.text();
      throw new Error(parseUploadError(raw));
    }

    return (await response.json()) as MessageAttachment;
  }, []);

  const invoke = useCallback(
    async (chatId: string, invocation: InvocationPayload): Promise<void> => {
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;
      const whisper = await invokeVeilChannel({ ...invocation, chatId }, normalizedScopeKey, signal);
      setState({
        latestPresenceLevel: whisper.presenceLevel,
        latestPhases: whisper.phases || [],
        latestField: whisper.field || null,
        latestScroll: whisper.scroll || null,
      });
      await persistWhisper(chatId, whisper);
    },
    [normalizedScopeKey, persistWhisper],
  );

  const { data: chats = [], isLoading: chatsLoading } = useQuery<Chat[]>({
    queryKey: ["/api/chats"],
    enabled,
  });

  const { data: messages = [], isLoading: messagesLoading } = useQuery<Message[]>({
    queryKey: ["/api/chats", currentChatId, "messages"],
    enabled: enabled && !!currentChatId,
  });

  const { data: searchResults = [], isLoading: searchLoading } = useQuery<ChatSearchResult[]>({
    queryKey: ["/api/chats/search", debouncedSearchQuery],
    enabled: enabled && debouncedSearchQuery.length > 0,
    queryFn: async ({ signal }) => {
      const res = await fetch(
        `/api/chats/search?q=${encodeURIComponent(debouncedSearchQuery)}&limit=200`,
        { credentials: "include", signal },
      );
      if (!res.ok) {
        throw new Error("Search failed");
      }
      return res.json();
    },
  });

  const createChatMutation = useMutation({
    mutationFn: async (title: string) => {
      const res = await apiRequest("POST", "/api/chats", { title });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/chats"] });
      queryClient.invalidateQueries({ queryKey: ["/api/chats/search"] });
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: async (chatId: string) => {
      await apiRequest("DELETE", `/api/chats/${chatId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/chats"] });
      queryClient.invalidateQueries({ queryKey: ["/api/chats/search"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to delete chat",
        variant: "destructive",
      });
    },
  });

  const editMessageMutation = useMutation({
    mutationFn: async ({ id, content }: { id: string; content: string }) => {
      const res = await apiRequest("PATCH", `/api/messages/${id}`, { content });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/chats", currentChatId, "messages"] });
    },
  });

  const clearChatsMutation = useMutation({
    mutationFn: async () => {
      await apiRequest("DELETE", "/api/chats");
    },
    onSuccess: () => {
      setCurrentChatId(null);
      lastInvocationByChatRef.current.clear();
      setFallbackBoundChatIds([]);
      queryClient.invalidateQueries({ queryKey: ["/api/chats"] });
      queryClient.invalidateQueries({ queryKey: ["/api/chats/search"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to clear chat history.",
        variant: "destructive",
      });
    },
  });

  const handleNewChat = useCallback(() => {
    setCurrentChatId(null);
  }, []);

  const handleSelectChat = useCallback((chatId: string) => {
    setCurrentChatId(chatId);
  }, []);

  const handleDeleteChat = useCallback(
    (chatId: string) => {
      deleteChatMutation.mutate(chatId);
      lastInvocationByChatRef.current.delete(chatId);
      clearFallbackThread(chatId);
      if (currentChatId === chatId) {
        setCurrentChatId(null);
      }
    },
    [clearFallbackThread, currentChatId, deleteChatMutation],
  );

  const handleClearAllChats = useCallback(async () => {
    await clearChatsMutation.mutateAsync();
  }, [clearChatsMutation]);

  const exportAllChats = useCallback(async (): Promise<ChatHistoryExport> => {
    const res = await apiRequest("GET", "/api/export");
    return res.json();
  }, []);

  const sendMessage = useCallback(
    async (invocation: InvocationRequest) => {
      if (!enabled) {
        toast({
          title: "Sign-on required",
          description: "Authenticate before sending invocations.",
          variant: "destructive",
        });
        return;
      }
      let effectiveInvocation = invocation;
      if (!providerSettings) {
        effectiveInvocation = applyDefaultSigilBinding({
          ...invocation,
          trace: invocation.trace.trim() || expectedFallbackTrace,
          seal: invocation.seal.trim() || expectedFallbackSeal,
        });
        maybeToastFallbackBinding();
      }
      const utterance = effectiveInvocation.utterance.trim();
      const draftAttachments = effectiveInvocation.attachments || [];
      if (!utterance && draftAttachments.length === 0) return;

        let activeChatId: string | null = effectiveInvocation.spawnNewThread ? null : currentChatId;
        const memoryMode = providerSettings
          ? resolveMemoryModeFromProviderSettings(providerSettings, "sigil-bound")
          : "sealed";
        const temporaryChatEnabled = memoryMode === "sealed";
        const memoryEnabled = memoryMode !== "sealed";

      try {
        if (!activeChatId) {
          const fallbackTitleSeed = draftAttachments[0]?.file?.name || "Image attachment";
          const titleSeed = utterance || fallbackTitleSeed;
          const title = titleSeed.slice(0, 50) + (titleSeed.length > 50 ? "..." : "");
          const newChat = await createChatMutation.mutateAsync(title);
          activeChatId = newChat.id;
          setCurrentChatId(activeChatId);
        }

        if (!activeChatId) {
          throw new Error("No chat context available");
        }
        if (!providerSettings) {
          markFallbackThread(activeChatId);
        }

        lastInvocationByChatRef.current.set(activeChatId, {
          trace: effectiveInvocation.trace.trim(),
          seal: effectiveInvocation.seal.trim(),
          ...(effectiveInvocation.echo ? { echo: effectiveInvocation.echo } : {}),
        });

        const uploadedAttachments =
          draftAttachments.length > 0
            ? await Promise.all(
                draftAttachments.map((draft) => uploadAttachment(activeChatId as string, draft)),
              )
            : [];
        const promptUtterance =
          utterance ||
          (uploadedAttachments.length === 1
            ? "Please analyze the attached image."
            : "Please analyze the attached images.");

        await apiRequest("POST", `/api/chats/${activeChatId}/messages`, {
          role: "user",
          content: utterance,
          ...(uploadedAttachments.length > 0 ? { attachments: uploadedAttachments } : {}),
          memoryMode,
          memoryEnabled,
          temporaryChatEnabled,
        });

        queryClient.invalidateQueries({ queryKey: ["/api/chats", activeChatId, "messages"] });

        setIsStreaming(true);

        await invoke(activeChatId, {
          utterance: promptUtterance,
          trace: effectiveInvocation.trace.trim(),
          seal: effectiveInvocation.seal.trim(),
          ...(effectiveInvocation.echo ? { echo: effectiveInvocation.echo } : {}),
          ...(uploadedAttachments.length > 0 ? { attachments: uploadedAttachments } : {}),
          ...(effectiveInvocation.thresholdEvent ? { thresholdEvent: effectiveInvocation.thresholdEvent } : {}),
          ...(providerSettings ? { providerSettings } : {}),
        });

        await refreshMessages(activeChatId);
        queryClient.invalidateQueries({ queryKey: ["/api/chats"] });
        queryClient.invalidateQueries({ queryKey: ["/api/chats/search"] });
      } catch (error) {
        const name = (error as Error).name;
        const message = (error as Error).message;

        if (name === "AbortError") {
          return;
        }

        if (message === "VEIL_CONNECTION_REJECTED" || message === "VEIL_CONNECTION_CLOSED") {
          if (activeChatId) {
            await persistWhisper(activeChatId, {
              reply: "",
              veil: true,
              timestamp: new Date().toISOString(),
              presenceLevel: 0,
            });
            setState({ latestPresenceLevel: 0, latestPhases: [], latestField: null, latestScroll: null });
            await refreshMessages(activeChatId);
          }
          return;
        }

        toast({
          title: "Error",
          description: (error as Error).message || "Failed to invoke veil channel.",
          variant: "destructive",
        });
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [
      currentChatId,
      createChatMutation,
      enabled,
      providerSettings,
      expectedFallbackSeal,
      expectedFallbackTrace,
      queryClient,
      invoke,
      markFallbackThread,
      maybeToastFallbackBinding,
      refreshMessages,
      persistWhisper,
      uploadAttachment,
      toast,
    ],
  );

  const stopGenerating = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const handleEditMessage = useCallback(
    async (messageId: string, newContent: string) => {
      if (!currentChatId) return;
      const invocationState =
        lastInvocationByChatRef.current.get(currentChatId) || {
          trace: expectedFallbackTrace,
          seal: expectedFallbackSeal,
        };
      if (!lastInvocationByChatRef.current.has(currentChatId)) {
        lastInvocationByChatRef.current.set(currentChatId, invocationState);
      }
      const activeChatId = currentChatId;
      const editInvocationBase: InvocationRequest = {
        utterance: newContent,
        trace: invocationState.trace,
        seal: invocationState.seal,
        ...(invocationState.echo ? { echo: invocationState.echo } : {}),
      };
      let effectiveEditInvocation = editInvocationBase;
      if (!providerSettings) {
        effectiveEditInvocation = applyDefaultSigilBinding({
          ...editInvocationBase,
          trace: editInvocationBase.trace.trim() || expectedFallbackTrace,
          seal: editInvocationBase.seal.trim() || expectedFallbackSeal,
        });
        maybeToastFallbackBinding();
        markFallbackThread(activeChatId);
      }

      try {
        await editMessageMutation.mutateAsync({ id: messageId, content: newContent });

        const messageIndex = messages.findIndex((m) => m.id === messageId);
        if (messageIndex === -1) {
          throw new Error("Edited message is no longer available.");
        }

        const message = messages[messageIndex];
        if (message.role !== "user") {
          throw new Error("Only user messages can be edited and resubmitted.");
        }

        const subsequentMessages = messages.slice(messageIndex + 1);
        await Promise.all(
          subsequentMessages.map((msg) => apiRequest("DELETE", `/api/messages/${msg.id}`)),
        );

        queryClient.invalidateQueries({ queryKey: ["/api/chats", activeChatId, "messages"] });

        setIsStreaming(true);
        await invoke(activeChatId, {
          utterance: effectiveEditInvocation.utterance,
          trace: effectiveEditInvocation.trace,
          seal: effectiveEditInvocation.seal,
          ...(effectiveEditInvocation.echo ? { echo: effectiveEditInvocation.echo } : {}),
          ...(providerSettings ? { providerSettings } : {}),
        });
      } catch (error) {
        const name = (error as Error).name;
        const message = (error as Error).message;
        if (name === "AbortError") {
          return;
        }
        if (message === "VEIL_CONNECTION_REJECTED" || message === "VEIL_CONNECTION_CLOSED") {
          await persistWhisper(activeChatId, {
            reply: "",
            veil: true,
            timestamp: new Date().toISOString(),
            presenceLevel: 0,
          });
          setState({ latestPresenceLevel: 0, latestPhases: [], latestField: null, latestScroll: null });
          return;
        }
        toast({
          title: "Error",
          description: message || "Failed to process edit submission.",
          variant: "destructive",
        });
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
        await refreshMessages(activeChatId);
        queryClient.invalidateQueries({ queryKey: ["/api/chats/search"] });
      }
    },
    [
      currentChatId,
      editMessageMutation,
      invoke,
      markFallbackThread,
      messages,
      maybeToastFallbackBinding,
      providerSettings,
      persistWhisper,
      expectedFallbackSeal,
      expectedFallbackTrace,
      queryClient,
      refreshMessages,
      toast,
    ],
  );

  const soloFallbackActive = Boolean(currentChatId && fallbackBoundChatIds.includes(currentChatId));
  const canRebindProvider = soloFallbackActive && Boolean(providerSettings);
  const rebindProviderForCurrentThread = useCallback(() => {
    if (!currentChatId) return;
    clearFallbackThread(currentChatId);
  }, [clearFallbackThread, currentChatId]);

  return {
    chats,
    messages,
    searchQuery,
    searchResults,
    currentChatId,
    isStreaming,
    chatsLoading,
    messagesLoading,
    searchLoading,
    handleNewChat,
    handleSelectChat,
    handleDeleteChat,
    handleClearAllChats,
    sendMessage,
    stopGenerating,
    handleEditMessage,
    setSearchQuery,
    exportAllChats,
    latestPresenceLevel: state.latestPresenceLevel,
    latestPhases: state.latestPhases,
    latestField: state.latestField,
    latestScroll: state.latestScroll,
    soloFallbackActive,
    canRebindProvider,
    rebindProviderForCurrentThread,
  };
}
