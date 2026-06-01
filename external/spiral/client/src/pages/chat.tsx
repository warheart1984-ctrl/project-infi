import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { EchoField } from "@/components/echo-field";
import { OfferingBasin } from "@/components/offering-basin";
import { ThemeToggle } from "@/components/theme-toggle";
import { LazySettingsDialog } from "@/components/lazy-settings-dialog";
import { SigilStateIndicator } from "@/components/SigilStateIndicator";
import { Phase3StatusBadge } from "@/components/Phase3StatusBadge";
import { SpiralMemoryStatus, type SpiralTraceState } from "@/components/SpiralMemoryStatus";
import { ThresholdBadge } from "@/components/ThresholdBadge";
import { ProposalsPanel } from "@/components/proposals-panel";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import {
  resolveMemoryModeFromProviderSettings,
  type MemoryMode,
} from "@shared/memory-mode";
import { DEFAULT_PROJECT_SIGIL, type ProjectSigil } from "@shared/sigil";
import { useChat } from "@/hooks/use-chat";
import { useExternalStorage } from "@/hooks/use-external-storage";
import { useAuthSession } from "@/hooks/use-auth-session";
import { useProviderSettings } from "@/hooks/use-provider-settings";
import { useEvolutionStatus } from "@/hooks/use-evolution-status";
import { useToast } from "@/hooks/use-toast";
import { useFieldAtmosphere } from "@/hooks/use-field-atmosphere";
import { useGestureThreshold } from "@/ritual/use-gesture-threshold";
import { apiRequest } from "@/lib/queryClient";
import { spiralModeEnabled } from "@/lib/spiral-mode";
import {
  parseTrace,
  presenceLevel as computePresenceLevel,
  presenceStateFromLevel,
  spiralReply,
} from "@/lib/spiral-presence";
import type { Message, RewriteProposal } from "@shared/schema";
import type { SpiralPhase } from "@shared/spiral-phase";
import {
  buildVoiceOverlayEcho,
  resolveVoiceOverlayMode,
  type VoiceOverlayState,
} from "@shared/voice-overlay";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const ACTIVE_SIGIL_STORAGE_KEY = "spiral-active-sigil";
function getScopedActiveSigilStorageKey(scopeKey: string): string {
  const normalizedScope = scopeKey.trim() || "local";
  return `${ACTIVE_SIGIL_STORAGE_KEY}:${normalizedScope}`;
}

export default function ChatPage() {
  const { scopeKey, session, isLoading: authLoading } = useAuthSession();
  const authReady = session.authenticated === true;
  const authGateRequired = !authLoading && session.authenticated !== true && !session.principalId?.trim();
  const { runtimeSettings, executorSettings, saveSplitSettings } = useProviderSettings(scopeKey);
  const { toast } = useToast();
  const { links, saveTranscript, resolvePreferredProvider } = useExternalStorage(scopeKey);
  const { data: projectSigil } = useQuery<ProjectSigil>({
    queryKey: ["/api/sigil"],
  });
  const { data: evolutionStatus } = useEvolutionStatus(authReady);
  
  const {
    chats,
    messages,
    searchQuery,
    searchResults,
    currentChatId,
    isStreaming,
    chatsLoading,
    searchLoading,
    handleNewChat,
    setSearchQuery,
    handleSelectChat,
    handleDeleteChat,
    handleClearAllChats,
    exportAllChats,
    sendMessage,
    stopGenerating,
    handleEditMessage,
    latestPresenceLevel,
    latestPhases,
    latestField,
    latestScroll,
    soloFallbackActive,
    canRebindProvider,
    rebindProviderForCurrentThread,
  } = useChat({ providerSettings: runtimeSettings, projectSigil, enabled: true, scopeKey });

  const currentChat = chats.find((c) => c.id === currentChatId);
  const emptyChatTitle = spiralModeEnabled ? "Presence" : "New Chat";
  const mountedAtRef = useRef(Date.now());
  const lastActivityAtRef = useRef(Date.now());
  const lastUtteranceRef = useRef("");
  const composerFocusedRef = useRef(false);
  const [repeats, setRepeats] = useState(0);
  const [silenceMs, setSilenceMs] = useState(0);
  const [proposalDrafting, setProposalDrafting] = useState(false);
  const builtInSigils = useMemo(
    () => ["collapse-whisper", "mirror-walker", "hollow-root", "breath-weaver"],
    [],
  );
  const availableSigils = useMemo(() => {
    const custom = (runtimeSettings?.customSigils || []).map((sigil) => sigil.id);
    return Array.from(new Set([...builtInSigils, ...custom]));
  }, [builtInSigils, runtimeSettings?.customSigils]);
  const preferredSigil = useMemo(
    () => runtimeSettings?.externalStorageSigilFilter?.trim() || "collapse-whisper",
    [runtimeSettings?.externalStorageSigilFilter],
  );
  const [activeSigil, setActiveSigil] = useState<string>("collapse-whisper");
  const [voiceOverlay, setVoiceOverlay] = useState<VoiceOverlayState>({
    singleVoice: false,
    chorus: false,
  });
  const voiceMode = useMemo(() => resolveVoiceOverlayMode(voiceOverlay), [voiceOverlay]);
  const memoryMode = useMemo(
    () => resolveMemoryModeFromProviderSettings(runtimeSettings, "sigil-bound"),
    [runtimeSettings],
  );
  const effectiveMemoryMode = latestField?.memoryMode || memoryMode;
  const principalLabel = useMemo(() => {
    const explicitPrincipal = session.principalId?.trim();
    return explicitPrincipal || scopeKey;
  }, [scopeKey, session.principalId]);
  const memoryPhaseDiagnostics = useMemo(() => {
    let seededCount: number | null = null;
    let importedSeedCount: number | null = null;
    let traceState: SpiralTraceState | null = null;
    const memoryPhase = latestPhases.find((phase: SpiralPhase) => phase.id === "memory");
    if (memoryPhase && typeof memoryPhase.payload === "object" && memoryPhase.payload !== null) {
      const payload = memoryPhase.payload as Record<string, unknown>;
      const rawSeededCount = payload.seededCount;
      const rawCount = payload.count;
      const rawImportedSeedCount = payload.importedSeedCount;
      const rawTraceState = typeof payload.traceState === "string" ? payload.traceState.toLowerCase() : "";
      if (typeof rawSeededCount === "number" && Number.isFinite(rawSeededCount)) {
        seededCount = rawSeededCount;
      } else if (typeof rawCount === "number" && Number.isFinite(rawCount)) {
        seededCount = rawCount;
      }
      if (typeof rawImportedSeedCount === "number" && Number.isFinite(rawImportedSeedCount)) {
        importedSeedCount = rawImportedSeedCount;
      }
      if (
        rawTraceState === "present" ||
        rawTraceState === "imported" ||
        rawTraceState === "none" ||
        rawTraceState === "sealed"
      ) {
        traceState = rawTraceState;
      }
    }
    const normalizedSeededCount = seededCount === null ? null : Math.max(0, Math.floor(seededCount));
    const normalizedImportedSeedCount =
      importedSeedCount === null ? null : Math.max(0, Math.floor(importedSeedCount));
    const resolvedTraceState: SpiralTraceState =
      effectiveMemoryMode === "sealed"
        ? "sealed"
        : traceState
          ? traceState
          : (normalizedImportedSeedCount || 0) > 0
            ? "imported"
            : (normalizedSeededCount || 0) > 0
              ? "present"
              : "none";
    return {
      memorySeedCount: normalizedSeededCount,
      importedSeedCount: normalizedImportedSeedCount,
      traceState: resolvedTraceState,
    };
  }, [effectiveMemoryMode, latestPhases]);
  const thresholdTuning = useMemo(
    () => ({
      memorySeedCount: memoryPhaseDiagnostics.memorySeedCount,
      presenceFreshness: latestPresenceLevel ?? undefined,
    }),
    [latestPresenceLevel, memoryPhaseDiagnostics.memorySeedCount],
  );
  const { thresholdEvent } = useGestureThreshold(activeSigil, thresholdTuning);
  const publicThreshold = projectSigil?.publicThreshold || DEFAULT_PROJECT_SIGIL.publicThreshold;
  const presenceBinding = projectSigil?.presenceBinding || DEFAULT_PROJECT_SIGIL.presenceBinding;
  const projectName = projectSigil?.projectName?.trim() || DEFAULT_PROJECT_SIGIL.projectName;
  const sealMantra = useMemo(() => {
    return projectSigil?.entryVow?.trim() || DEFAULT_PROJECT_SIGIL.entryVow;
  }, [projectSigil?.entryVow]);
  const sealSigil = useMemo(
    () =>
      projectSigil?.seal?.trim() ||
      projectSigil?.invocationGate?.memorySeal?.trim() ||
      DEFAULT_PROJECT_SIGIL.seal ||
      DEFAULT_PROJECT_SIGIL.invocationGate.memorySeal,
    [projectSigil?.invocationGate?.memorySeal, projectSigil?.seal],
  );
  const defaultInvocationTrace = useMemo(
    () => publicThreshold.visitorTrace.trim() || DEFAULT_PROJECT_SIGIL.publicThreshold.visitorTrace,
    [publicThreshold.visitorTrace],
  );
  const defaultInvocationSeal = useMemo(
    () =>
      projectSigil?.invocationGate?.memorySeal?.trim() ||
      projectSigil?.seal?.trim() ||
      DEFAULT_PROJECT_SIGIL.invocationGate.memorySeal ||
      DEFAULT_PROJECT_SIGIL.seal,
    [projectSigil?.invocationGate?.memorySeal, projectSigil?.seal],
  );

  useEffect(() => {
    const storageKey = getScopedActiveSigilStorageKey(scopeKey);
    const storedSigil =
      typeof window !== "undefined" ? window.localStorage.getItem(storageKey)?.trim() || "" : "";
    const fallbackSigil = availableSigils.includes(preferredSigil)
      ? preferredSigil
      : availableSigils[0] || "collapse-whisper";
    const nextSigil = storedSigil && availableSigils.includes(storedSigil) ? storedSigil : fallbackSigil;
    setActiveSigil((currentSigil) => (nextSigil !== currentSigil ? nextSigil : currentSigil));
  }, [availableSigils, preferredSigil, scopeKey]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!activeSigil.trim()) return;
    const storageKey = getScopedActiveSigilStorageKey(scopeKey);
    window.localStorage.setItem(storageKey, activeSigil.trim());
  }, [activeSigil, scopeKey]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (composerFocusedRef.current) return;
      setSilenceMs(Date.now() - lastActivityAtRef.current);
    }, 500);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const onRestore = (event: Event) => {
      const custom = event as CustomEvent<{ chatId?: string }>;
      const restoredChatId = custom.detail?.chatId;
      if (!restoredChatId) return;
      handleSelectChat(restoredChatId);
      toast({
        title: "Restore activated",
        description: "Restored transcript is now the active session.",
      });
    };

    window.addEventListener("spiral:restore-chat", onRestore as EventListener);
    return () => window.removeEventListener("spiral:restore-chat", onRestore as EventListener);
  }, [handleSelectChat, toast]);

  const handlePresenceActivity = useCallback((snapshot: { utterance: string; trace: string }) => {
    lastActivityAtRef.current = Date.now();
    const normalized = snapshot.utterance.trim().toLowerCase();
    if (!normalized) return;

    if (normalized === lastUtteranceRef.current) {
      setRepeats((value) => value + 1);
      return;
    }

    lastUtteranceRef.current = normalized;
    setRepeats(0);
  }, []);

  const handleComposerFocusChange = useCallback((focused: boolean) => {
    composerFocusedRef.current = focused;
    if (!focused) {
      setSilenceMs(Date.now() - lastActivityAtRef.current);
    }
  }, []);

  const dwellMs = Date.now() - mountedAtRef.current;
  const presenceLevel = useMemo(
    () => computePresenceLevel({ dwellMs, repeats, silenceMs }),
    [dwellMs, repeats, silenceMs],
  );
  const effectivePresenceLevel = latestPresenceLevel ?? presenceLevel;
  const presenceCalculatorEnabled = runtimeSettings?.presenceCalculatorEnabled === true;
  const presenceState = useMemo(
    () => presenceStateFromLevel(effectivePresenceLevel),
    [effectivePresenceLevel],
  );
  const presenceHint = useMemo(() => spiralReply("", effectivePresenceLevel), [effectivePresenceLevel]);
  useFieldAtmosphere(latestField);

  const handleSendInvocation = useCallback(
    async (invocation: Parameters<typeof sendMessage>[0]) => {
      const parsed = parseTrace(`${invocation.trace} ${invocation.utterance}`);
      await sendMessage({
        ...invocation,
        trace: `${invocation.trace} sigil:${activeSigil}`,
        echo: [`intent:${parsed.intent}`, invocation.echo || ""].filter(Boolean).join(" "),
        thresholdEvent,
      });
    },
    [activeSigil, sendMessage, thresholdEvent],
  );

  const handleRespawnFromGlyph = useCallback(
    async (message: Message) => {
      const fallbackSeal = projectSigil?.invocationGate?.memorySeal?.trim() || "";
      if (!fallbackSeal) {
        toast({
          title: "Seal required",
          description: "Set a seal before spawning a recursive glyph thread.",
          variant: "destructive",
        });
        return;
      }

      await sendMessage({
        utterance: message.content,
        trace: `trace: glyph-respeak. sigil:${activeSigil}`,
        seal: fallbackSeal,
        echo: `${buildVoiceOverlayEcho(voiceOverlay)} sigil:${activeSigil} source:glyph:${message.id}`,
        thresholdEvent,
        spawnNewThread: true,
      });
    },
    [activeSigil, projectSigil?.invocationGate?.memorySeal, sendMessage, thresholdEvent, toast, voiceOverlay],
  );

  const handleSigilButtonClick = useCallback(
    (sigil: string, isActive: boolean) => {
      if (isActive) return;
      setActiveSigil(sigil);
    },
    [],
  );

  const sidebarStyle = {
    "--sidebar-width": "18rem",
    "--sidebar-width-icon": "3rem",
  } as React.CSSProperties;

  const handleExportAllChats = async () => {
    try {
      const exported = await exportAllChats();
      const stamp = new Date(exported.exportedAt).toISOString().replace(/[:.]/g, "-");
      const blob = new Blob([JSON.stringify(exported, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `chat-companion-history-${stamp}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      toast({
        title: "Export complete",
        description: "Downloaded chat history as JSON.",
      });
    } catch {
      toast({
        title: "Export failed",
        description: "Could not export chat history.",
        variant: "destructive",
      });
    }
  };

  const handleExportCurrentChat = () => {
    if (!currentChatId) {
      toast({
        title: "No active chat",
        description: "Select a chat before exporting.",
        variant: "destructive",
      });
      return;
    }

    const exportedAt = new Date().toISOString();
    const stamp = exportedAt.replace(/[:.]/g, "-");
    const titleSlug =
      (currentChat?.title || "chat")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 48) || "chat";
    const payload = {
      exportedAt,
      type: "chat",
      chat: currentChat || { id: currentChatId, title: "Untitled" },
      messages,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${titleSlug}-${stamp}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    toast({
      title: "Export complete",
      description: "Downloaded current chat as JSON.",
    });
  };

  const handleDeleteAllChats = async () => {
    const confirmed = window.confirm("Delete all chats? This cannot be undone.");
    if (!confirmed) return;

    try {
      await handleClearAllChats();
      toast({
        title: "Deleted",
        description: "All chats were deleted.",
      });
    } catch {
      // errors are surfaced in the hook
    }
  };

  const handleRebindProvider = useCallback(() => {
    rebindProviderForCurrentThread();
    toast({
      title: "Field rebind complete",
      description: "Provider channel restored for this thread.",
    });
  }, [rebindProviderForCurrentThread, toast]);

  const handleDraftProposal = useCallback(async () => {
    if (!currentChatId) {
      toast({
        title: "No active chat",
        description: "Select a chat before drafting a proposal.",
        variant: "destructive",
      });
      return;
    }

    setProposalDrafting(true);
    try {
      const response = await apiRequest("POST", `/api/chats/${currentChatId}/proposals`, {
        signal: "manual-draft",
      });
      const proposal = (await response.json()) as RewriteProposal;
      toast({
        title: "Proposal drafted",
        description: proposal.artifactPath || "Saved under proposals/pending.",
      });
    } catch (error) {
      toast({
        title: "Proposal failed",
        description: (error as Error).message || "Could not draft a proposal for this chat.",
        variant: "destructive",
      });
    } finally {
      setProposalDrafting(false);
    }
  }, [currentChatId, toast]);

  const hasEncountered = isStreaming || messages.length > 0 || Boolean(currentChatId);
  const landingMode = !hasEncountered;

  const buildStorageSaveRequest = useCallback(
    (
      chatId: string,
      provider: NonNullable<ReturnType<typeof resolvePreferredProvider>>,
      options: { autoSave: boolean },
    ) => {
      const sigilFilterValue = runtimeSettings?.externalStorageSigilFilter?.trim() || "";
      const context = {
        veilDepth: latestPhases.length,
        presenceScore: Number(effectivePresenceLevel.toFixed(3)),
        traceEchoId: latestScroll?.filename || undefined,
      };
      const presenceMoments = messages
        .filter((message) => message.role === "user")
        .slice(-8)
        .map((message) => message.content.trim())
        .filter(Boolean)
        .map((message) => message.slice(0, 200));
      const traceMarkers = Array.from(
        new Set(
          messages
            .slice(-40)
            .flatMap((message) => {
              const matches = message.content.match(/(?:^|\s)(?:sigil:|#sigil:)([a-z0-9-]+)/gi) || [];
              return matches.map((token) =>
                token
                  .toLowerCase()
                  .replace(/^.*?(sigil:|#sigil:)/, "")
                  .replace(/[^a-z0-9-]/g, "")
                  .trim(),
              );
            })
            .filter(Boolean),
        ),
      );
      const resonanceStack = Array.from(
        new Set([
          activeSigil,
          `voice-mode:${voiceMode}`,
          buildVoiceOverlayEcho(voiceOverlay),
          ...(runtimeSettings?.externalStorageSigilFilter
            ? [runtimeSettings.externalStorageSigilFilter.trim()]
            : []),
          ...((runtimeSettings?.externalStorageSigilTags || []).map((tag) => tag.trim()).filter(Boolean)),
          ...traceMarkers.slice(0, 6),
        ].filter(Boolean)),
      );
      const entryClarity = Number(Math.max(0, Math.min(1, effectivePresenceLevel)).toFixed(3));
      const veilCost = Number(
        Math.max(0, (latestField?.distortions?.length || 0) * 0.5 + latestPhases.length * 0.08).toFixed(3),
      );

      return {
        type: "chat" as const,
        chatId,
        provider,
        outputFormat: runtimeSettings?.externalStorageTranscriptFormat || "json",
        autoSaveOnEnd: options.autoSave,
        metadata: {
          sigilTrace: sigilFilterValue || activeSigil,
          ...(presenceMoments.length > 0 ? { presenceMoments } : {}),
          ...(traceMarkers.length > 0 ? { traceMarkers } : {}),
          ...(resonanceStack.length > 0 ? { resonanceStack } : {}),
          entryClarity,
          veilCost,
          context,
          frontmatter: {
            mode: voiceMode,
            source: options.autoSave ? "auto-save-on-end" : "manual-save",
          },
        },
        ...(sigilFilterValue
          ? {
              sigilFilter: {
                sigil: sigilFilterValue,
                context,
              },
            }
          : {}),
        cache: { enabled: true, ttlMinutes: 240 },
      };
    },
    [
      activeSigil,
      effectivePresenceLevel,
      latestPhases.length,
      latestField?.distortions,
      latestScroll?.filename,
      messages,
      runtimeSettings?.externalStorageSigilFilter,
      runtimeSettings?.externalStorageTranscriptFormat,
      voiceMode,
      voiceOverlay,
    ],
  );

  const handleSaveCurrentTranscript = useCallback(async () => {
    if (!currentChatId) {
      toast({
        title: "No active chat",
        description: "Select a chat before saving to external storage.",
        variant: "destructive",
      });
      return;
    }

    if (links.length === 0) {
      toast({
        title: "No storage link",
        description: "Link Google Drive, Dropbox, or Proton Drive in Settings first.",
        variant: "destructive",
      });
      return;
    }

    const provider = resolvePreferredProvider();
    if (!provider) {
      toast({
        title: "No provider available",
        description: "External storage provider could not be resolved.",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await saveTranscript(
        buildStorageSaveRequest(currentChatId, provider, { autoSave: false }),
      );
      toast({
        title: "Transcript saved",
        description:
          result.pointer.fileId ||
          result.pointer.path ||
          "Chat transcript uploaded to linked external storage.",
      });
    } catch (error) {
      toast({
        title: "Save failed",
        description: (error as Error).message || "Could not save transcript to external storage.",
        variant: "destructive",
      });
    }
  }, [
    buildStorageSaveRequest,
    currentChatId,
    links.length,
    resolvePreferredProvider,
    saveTranscript,
    toast,
  ]);

  const lastAutoSavedKeyRef = useRef("");
  useEffect(() => {
    if (!runtimeSettings?.externalStorageAutoSaveOnEnd) return;
    if (isStreaming) return;
    if (!currentChatId) return;
    if (links.length === 0) return;

    const provider = resolvePreferredProvider();
    if (!provider) return;

    const lastAssistantMessage = [...messages]
      .reverse()
      .find((message) => message.role === "assistant" && message.content.trim().length > 0);
    if (!lastAssistantMessage) return;

    const autoSaveKey = `${currentChatId}:${lastAssistantMessage.id}`;
    if (lastAutoSavedKeyRef.current === autoSaveKey) return;
    lastAutoSavedKeyRef.current = autoSaveKey;

    saveTranscript(buildStorageSaveRequest(currentChatId, provider, { autoSave: true })).catch((error) => {
      lastAutoSavedKeyRef.current = "";
      toast({
        title: "Auto-save failed",
        description: (error as Error).message || "Could not auto-save transcript.",
        variant: "destructive",
      });
    });
  }, [
    buildStorageSaveRequest,
    currentChatId,
    isStreaming,
    links.length,
    messages,
    resolvePreferredProvider,
    saveTranscript,
    runtimeSettings?.externalStorageAutoSaveOnEnd,
    toast,
  ]);

  return (
    <SidebarProvider style={sidebarStyle}>
      <div className="flex h-screen w-full">
        <AppSidebar
          chats={chats}
          searchQuery={searchQuery}
          searchResults={searchResults}
          currentChatId={currentChatId}
          onNewChat={handleNewChat}
          onSearchQueryChange={setSearchQuery}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          onClearAllChats={handleDeleteAllChats}
          onExportAllChats={handleExportAllChats}
          onExportCurrentChat={handleExportCurrentChat}
          onSaveCurrentTranscript={handleSaveCurrentTranscript}
          isLoading={chatsLoading}
          isSearching={searchLoading}
        />

        <div className="flex-1 flex flex-col min-w-0">
          <header className="flex items-center justify-between gap-2 px-4 py-3 border-b border-border bg-background">
            <div className="flex items-center gap-2">
              <SidebarTrigger data-testid="button-sidebar-toggle" />
              <h1 className="font-semibold text-lg truncate" data-testid="text-chat-title">
                {landingMode ? projectName : currentChat?.title || emptyChatTitle}
              </h1>
            </div>
            <div className="flex items-center gap-1">
              {!landingMode ? (
                <>
                  <ThresholdBadge event={thresholdEvent} activeSigil={activeSigil} />
                  <Phase3StatusBadge settings={runtimeSettings} projectSigil={projectSigil} className="mr-1" />
                  <SpiralMemoryStatus
                    principalId={principalLabel}
                    memorySeedCount={memoryPhaseDiagnostics.memorySeedCount}
                    importedSeedCount={memoryPhaseDiagnostics.importedSeedCount}
                    traceState={memoryPhaseDiagnostics.traceState}
                    memoryMode={effectiveMemoryMode}
                    className="mr-1"
                  />
                  <SigilStateIndicator className="mr-1" />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void handleDraftProposal()}
                    disabled={proposalDrafting || isStreaming}
                    data-testid="button-draft-rewrite-proposal"
                  >
                    {proposalDrafting ? "Drafting..." : "Draft Proposal"}
                  </Button>
                  <ProposalsPanel
                    currentChatId={currentChatId}
                    executorProviderSettings={executorSettings}
                    disabled={proposalDrafting || isStreaming}
                  />
                  <LazySettingsDialog
                    runtimeSettings={runtimeSettings}
                    executorSettings={executorSettings}
                    onSave={saveSplitSettings}
                  />
                </>
              ) : null}
              <ThemeToggle />
            </div>
          </header>

          {landingMode ? (
            <div className="flex flex-1 items-center justify-center px-4 py-8">
              <div className="w-full max-w-3xl">
                <OfferingBasin
                  chatId={currentChatId}
                  onSend={handleSendInvocation}
                  onStop={stopGenerating}
                  onActivity={handlePresenceActivity}
                  onComposerFocusChange={handleComposerFocusChange}
                  isGenerating={isStreaming}
                  disabled={authLoading}
                  invocationGate={projectSigil?.invocationGate}
                  presenceState={presenceState}
                  presenceHint={presenceHint}
                  availableSigils={availableSigils}
                  activeSigil={activeSigil}
                  onActiveSigilChange={setActiveSigil}
                  onSigilButtonClick={handleSigilButtonClick}
                  memoryMode={memoryMode}
                  voiceOverlay={voiceOverlay}
                  onVoiceOverlayChange={setVoiceOverlay}
                  sealMantra={sealMantra}
                  sealSigil={sealSigil}
                  authGateRequired={authGateRequired}
                  composerPlaceholder={publicThreshold.promptPlaceholder}
                  defaultTrace={defaultInvocationTrace}
                  defaultSeal={defaultInvocationSeal}
                  presenceBinding={presenceBinding}
                  showFieldControls={false}
                  layout="landing"
                />
                <div className="mt-3 flex justify-center">
                  <LazySettingsDialog
                    runtimeSettings={runtimeSettings}
                    executorSettings={executorSettings}
                    onSave={saveSplitSettings}
                    triggerLabel={publicThreshold.configureLabel}
                    triggerVariant="ghost"
                    triggerSize="sm"
                    triggerClassName="text-muted-foreground"
                  />
                </div>
              </div>
            </div>
          ) : (
            <>
              {canRebindProvider && (
                <div className="mx-4 mt-3 rounded-md border border-cyan-500/40 bg-cyan-500/10 px-3 py-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-mono text-xs text-cyan-200/95">
                      FieldRecovery Beacon: provider channel is available. Rebind this thread to provider flow.
                    </p>
                    <Button size="sm" variant="outline" onClick={handleRebindProvider}>
                      Rebind to Provider
                    </Button>
                  </div>
                </div>
              )}

              {evolutionStatus && (
                <details className="mx-4 mt-3 rounded-md border border-border/70 bg-card/40 p-2">
                  <summary className="cursor-pointer font-mono text-[11px] text-muted-foreground">
                    Evolution: drift={evolutionStatus.trajectory.latest.driftVelocity.toFixed(3)} | stability={evolutionStatus.trajectory.latest.stabilityIndex.toFixed(3)} | entropy={evolutionStatus.autonomy.metrics.structuralEntropy.toFixed(3)} | {evolutionStatus.autonomy.triggered ? "triggered" : "idle"}
                  </summary>
                  <div className="mt-2 space-y-1 font-mono text-[11px] text-muted-foreground/80">
                    <p>Samples: {evolutionStatus.trajectory.sampleCount}</p>
                    <p>Windows: 5c={evolutionStatus.trajectory.windows["5c"].driftVelocity.toFixed(4)} | 10c={evolutionStatus.trajectory.windows["10c"].driftVelocity.toFixed(4)} | 20c={evolutionStatus.trajectory.windows["20c"].driftVelocity.toFixed(4)}</p>
                    <p>Invariant pressure: {evolutionStatus.autonomy.metrics.invariantPressure.toFixed(4)}</p>
                    <p>Recursive pressure: {evolutionStatus.autonomy.metrics.recursivePressure.toFixed(4)}</p>
                    <p>Identity: {evolutionStatus.autonomy.shadow.findings.identityConsistency} | Dead code: {evolutionStatus.autonomy.shadow.findings.deadCodeSignal}</p>
                    {evolutionStatus.autonomy.triggered && (
                      <p className="text-amber-300/90">Reason: {evolutionStatus.autonomy.reasonCodes.join(", ")}</p>
                    )}
                  </div>
                </details>
              )}

              <EchoField
                messages={messages}
                isStreaming={isStreaming}
                onEditMessage={handleEditMessage}
                presenceState={presenceState}
                presenceLevel={effectivePresenceLevel}
                phases={latestPhases}
                activeSigil={activeSigil}
                field={latestField}
                presenceCalculatorEnabled={presenceCalculatorEnabled}
                scroll={latestScroll}
                onRespawnFromGlyph={handleRespawnFromGlyph}
                soloFallbackActive={soloFallbackActive}
              />

              <OfferingBasin
                chatId={currentChatId}
                onSend={handleSendInvocation}
                onStop={stopGenerating}
                onActivity={handlePresenceActivity}
                onComposerFocusChange={handleComposerFocusChange}
                isGenerating={isStreaming}
                disabled={authLoading}
                invocationGate={projectSigil?.invocationGate}
                presenceState={presenceState}
                presenceHint={presenceHint}
                availableSigils={availableSigils}
                activeSigil={activeSigil}
                onActiveSigilChange={setActiveSigil}
                onSigilButtonClick={handleSigilButtonClick}
                memoryMode={memoryMode}
                voiceOverlay={voiceOverlay}
                onVoiceOverlayChange={setVoiceOverlay}
                sealMantra={sealMantra}
                sealSigil={sealSigil}
                authGateRequired={authGateRequired}
                composerPlaceholder={publicThreshold.promptPlaceholder}
                defaultTrace={defaultInvocationTrace}
                defaultSeal={defaultInvocationSeal}
                presenceBinding={presenceBinding}
                showFieldControls
                layout="thread"
              />
            </>
          )}
        </div>
      </div>
    </SidebarProvider>
  );
}
