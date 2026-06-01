import { useMemo, useRef, useEffect, useState, KeyboardEvent } from "react";
import { ImagePlus, Square, X } from "lucide-react";
import { DEFAULT_PROJECT_SIGIL, type InvocationGate, type PresenceBinding } from "@shared/sigil";
import type { MemoryMode } from "@shared/memory-mode";
import { buildVoiceOverlayEcho, type VoiceOverlayState } from "@shared/voice-overlay";
import type { DraftAttachment, InvocationRequest } from "@/hooks/use-chat";
import type { PresenceState } from "@/lib/spiral-presence";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { CutTheThread } from "@/components/cut-the-thread";
import { PresenceSeal } from "@/components/PresenceSeal";
import { useToast } from "@/hooks/use-toast";
import { usePresence } from "@/hooks/use-presence";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  chatId: string | null;
  onSend: (invocation: InvocationRequest) => void | Promise<void>;
  onStop: () => void;
  onActivity?: (snapshot: { utterance: string; trace: string }) => void;
  onComposerFocusChange?: (focused: boolean) => void;
  isGenerating: boolean;
  disabled?: boolean;
  invocationGate?: InvocationGate | null;
  presenceState?: PresenceState;
  presenceHint?: string;
  availableSigils: string[];
  activeSigil: string;
  onActiveSigilChange: (sigil: string) => void;
  onSigilButtonClick?: (sigil: string, isActive: boolean) => void;
  memoryMode?: MemoryMode;
  voiceOverlay: VoiceOverlayState;
  onVoiceOverlayChange: (value: VoiceOverlayState) => void;
  sealMantra?: string;
  sealSigil?: string;
  authGateRequired?: boolean;
  composerPlaceholder?: string;
  defaultTrace?: string;
  defaultSeal?: string;
  presenceBinding?: PresenceBinding;
  showFieldControls?: boolean;
  requirePresenceSeal?: boolean;
  layout?: "landing" | "thread";
}

const DEFAULT_TRACE_PATTERNS = ["^Present\\.", "^sigil:", "^trace:"];
const MAX_ATTACHMENT_COUNT = 4;
const MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024;
const COMPOSER_ACTIVITY_DEBOUNCE_MS = 120;
const ACTIVE_SIGIL_BUTTON_CLASS: Record<string, string> = {
  "collapse-whisper":
    "border-slate-300/40 bg-slate-500/15 text-slate-100 hover:bg-slate-500/25",
  "mirror-walker":
    "border-cyan-300/40 bg-cyan-500/15 text-cyan-100 hover:bg-cyan-500/25",
  "hollow-root":
    "border-amber-300/40 bg-amber-500/15 text-amber-100 hover:bg-amber-500/25",
  "breath-weaver":
    "border-emerald-300/40 bg-emerald-500/20 text-emerald-100 hover:bg-emerald-500/30",
};

function isValidTrace(trace: string, patterns: string[]): boolean {
  const normalizedTrace = trace.trim();
  if (!normalizedTrace) return false;

  for (const rawPattern of patterns) {
    const pattern = rawPattern.trim();
    if (!pattern) continue;

    try {
      const regex = new RegExp(pattern, "i");
      if (regex.test(normalizedTrace)) {
        return true;
      }
      continue;
    } catch {
      // Fall through to prefix matching.
    }

    if (normalizedTrace.toLowerCase().startsWith(pattern.toLowerCase())) {
      return true;
    }
  }

  return false;
}

function revokeAttachmentPreviews(attachments: DraftAttachment[]): void {
  for (const attachment of attachments) {
    try {
      URL.revokeObjectURL(attachment.previewUrl);
    } catch {
      // Ignore revoke failures.
    }
  }
}

export function ChatInput({
  chatId,
  onSend,
  onStop,
  onActivity,
  onComposerFocusChange,
  isGenerating,
  disabled,
  invocationGate,
  presenceState,
  presenceHint,
  availableSigils,
  activeSigil,
  onActiveSigilChange,
  onSigilButtonClick,
  memoryMode,
  voiceOverlay,
  onVoiceOverlayChange,
  sealMantra,
  sealSigil,
  authGateRequired = false,
  composerPlaceholder = DEFAULT_PROJECT_SIGIL.publicThreshold.promptPlaceholder,
  defaultTrace = DEFAULT_PROJECT_SIGIL.publicThreshold.visitorTrace,
  defaultSeal = DEFAULT_PROJECT_SIGIL.invocationGate.memorySeal,
  presenceBinding = DEFAULT_PROJECT_SIGIL.presenceBinding,
  showFieldControls = false,
  requirePresenceSeal = false,
  layout = "thread",
}: ChatInputProps) {
  const { toast } = useToast();
  const { presenceSeal, savePresenceSeal, registerPresenceTrace, presenceSealConfirmed } = usePresence();
  const [utterance, setUtterance] = useState("");
  const [attachments, setAttachments] = useState<DraftAttachment[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const attachmentsRef = useRef<DraftAttachment[]>([]);
  const activityTimeoutRef = useRef<number | null>(null);
  const resizeFrameRef = useRef<number | null>(null);
  const sendLockRef = useRef(false);
  const acceptedTracePatterns = useMemo(() => {
    const patterns = invocationGate?.accept?.map((pattern) => pattern.trim()).filter(Boolean) || [];
    return patterns.length > 0 ? patterns : DEFAULT_TRACE_PATTERNS;
  }, [invocationGate]);
  const effectiveTrace = useMemo(
    () => defaultTrace.trim() || DEFAULT_PROJECT_SIGIL.publicThreshold.visitorTrace,
    [defaultTrace],
  );
  const expectedSeal = invocationGate?.enabled ? invocationGate.memorySeal.trim() : "";
  const effectiveSeal = useMemo(
    () =>
      defaultSeal.trim() ||
      expectedSeal ||
      DEFAULT_PROJECT_SIGIL.invocationGate.memorySeal ||
      DEFAULT_PROJECT_SIGIL.seal,
    [defaultSeal, expectedSeal],
  );
  const effectiveSealMantra = useMemo(
    () => sealMantra?.trim() || DEFAULT_PROJECT_SIGIL.entryVow,
    [sealMantra],
  );
  const effectivePresenceSigil = useMemo(
    () => sealSigil?.trim() || effectiveSeal,
    [effectiveSeal, sealSigil],
  );
  const traceAccepted = isValidTrace(effectiveTrace, acceptedTracePatterns);
  const sealMatchesGate = !expectedSeal || effectiveSeal === expectedSeal;
  const hasAttachment = attachments.length > 0;
  const canSend = Boolean(utterance.trim() || hasAttachment);
  const landingMode = layout === "landing";

  useEffect(() => {
    if (traceAccepted) {
      registerPresenceTrace();
    }
  }, [registerPresenceTrace, traceAccepted]);

  useEffect(() => {
    if (!onActivity) return;

    if (activityTimeoutRef.current !== null) {
      window.clearTimeout(activityTimeoutRef.current);
    }

    activityTimeoutRef.current = window.setTimeout(() => {
      activityTimeoutRef.current = null;
      onActivity({ utterance, trace: effectiveTrace });
    }, COMPOSER_ACTIVITY_DEBOUNCE_MS);

    return () => {
      if (activityTimeoutRef.current !== null) {
        window.clearTimeout(activityTimeoutRef.current);
        activityTimeoutRef.current = null;
      }
    };
  }, [effectiveTrace, onActivity, utterance]);

  useEffect(() => {
    setAttachments((current) => {
      if (current.length === 0) return current;
      revokeAttachmentPreviews(current);
      return [];
    });
    setUtterance("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [chatId]);

  useEffect(() => {
    attachmentsRef.current = attachments;
  }, [attachments]);

  useEffect(
    () => () => {
      if (activityTimeoutRef.current !== null) {
        window.clearTimeout(activityTimeoutRef.current);
      }
      if (resizeFrameRef.current !== null) {
        window.cancelAnimationFrame(resizeFrameRef.current);
      }
      revokeAttachmentPreviews(attachmentsRef.current);
    },
    [],
  );

  useEffect(() => {
    if (resizeFrameRef.current !== null) {
      window.cancelAnimationFrame(resizeFrameRef.current);
    }

    resizeFrameRef.current = window.requestAnimationFrame(() => {
      resizeFrameRef.current = null;
      if (!textareaRef.current) return;
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, landingMode ? 220 : 200)}px`;
    });
  }, [landingMode, utterance]);

  const handleAttachmentSelect = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    const selected = Array.from(fileList);
    const validFiles: File[] = [];

    for (const file of selected) {
      if (!file.type.startsWith("image/")) {
        toast({
          title: "Unsupported attachment",
          description: `${file.name}: only images are supported.`,
          variant: "destructive",
        });
        continue;
      }
      if (file.size > MAX_ATTACHMENT_BYTES) {
        toast({
          title: "Attachment too large",
          description: `${file.name} exceeds ${Math.floor(MAX_ATTACHMENT_BYTES / (1024 * 1024))}MB.`,
          variant: "destructive",
        });
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    setAttachments((current) => {
      const remainingSlots = Math.max(0, MAX_ATTACHMENT_COUNT - current.length);
      if (remainingSlots === 0) {
        toast({
          title: "Attachment limit reached",
          description: `Up to ${MAX_ATTACHMENT_COUNT} images can be sent per message.`,
          variant: "destructive",
        });
        return current;
      }

      const nextDrafts = validFiles.slice(0, remainingSlots).map((file) => ({
        file,
        previewUrl: URL.createObjectURL(file),
      }));

      if (validFiles.length > remainingSlots) {
        toast({
          title: "Attachment limit reached",
          description: `Only the first ${remainingSlots} image(s) were added.`,
          variant: "destructive",
        });
      }

      return [...current, ...nextDrafts];
    });
  };

  const handleRemoveAttachment = (index: number) => {
    setAttachments((current) => {
      if (index < 0 || index >= current.length) return current;
      const target = current[index];
      revokeAttachmentPreviews([target]);
      return current.filter((_, attachmentIndex) => attachmentIndex !== index);
    });
  };

  const handleSend = async () => {
    const trimmedUtterance = utterance.trim();
    if ((!trimmedUtterance && attachments.length === 0) || !effectiveTrace || !effectiveSeal) return;
    if (isGenerating || sendLockRef.current) return;
    if (!traceAccepted) {
      toast({
        title: "Trace misaligned",
        description: "Threshold trace no longer satisfies the configured gate.",
        variant: "destructive",
      });
      return;
    }
    if (invocationGate?.enabled && !sealMatchesGate) {
      toast({
        title: "Seal mismatch",
        description: "Threshold seal no longer matches the configured gate.",
        variant: "destructive",
      });
      return;
    }
    sendLockRef.current = true;

    try {
      if (requirePresenceSeal) {
        const confirmed = await presenceSealConfirmed();
        if (!confirmed) {
          toast({
            title: "Presence not sealed",
            description: `Unlock gesture required: ${sealSigil || effectiveSeal}`,
            variant: "destructive",
          });
          return;
        }
      }

      await onSend({
        utterance: trimmedUtterance,
        trace: effectiveTrace,
        seal: effectiveSeal,
        echo: `${buildVoiceOverlayEcho(voiceOverlay)} sigil:${activeSigil}`,
        ...(attachments.length > 0 ? { attachments } : {}),
      });
      setAttachments((current) => {
        revokeAttachmentPreviews(current);
        return [];
      });
      setUtterance("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    } catch (error) {
      toast({
        title: "Send failed",
        description: (error as Error).message || "Failed to send invocation.",
        variant: "destructive",
      });
    } finally {
      sendLockRef.current = false;
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  };

  return (
    <div
      className={cn(
        landingMode ? "bg-transparent p-0" : "border-t border-border bg-background p-4",
      )}
    >
      <div className="mx-auto max-w-3xl">
        <div
          className={cn(
            "space-y-3 rounded-2xl border border-input bg-card shadow-sm",
            landingMode ? "p-4 sm:p-5" : "p-3",
          )}
        >
          {showFieldControls ? (
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1" data-testid="sigil-chooser">
                {availableSigils.map((sigil) => {
                  const isActive = activeSigil === sigil;
                  const activeClass =
                    ACTIVE_SIGIL_BUTTON_CLASS[sigil] ||
                    "border-primary/40 bg-primary/20 text-primary-foreground hover:bg-primary/30";
                  return (
                    <Button
                      key={sigil}
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        if (onSigilButtonClick) {
                          onSigilButtonClick(sigil, isActive);
                          return;
                        }
                        onActiveSigilChange(sigil);
                      }}
                      className={cn("font-mono text-[11px]", isActive && activeClass)}
                      data-testid={`button-sigil-${sigil}`}
                      title={isActive && memoryMode ? `Active sigil (${memoryMode}).` : undefined}
                    >
                      {sigil}
                    </Button>
                  );
                })}
              </div>
              <div className="ml-auto flex flex-wrap items-center gap-1" data-testid="mode-toggle">
                {presenceSeal ? (
                  <span
                    className="rounded-full border border-emerald-400/40 bg-emerald-500/10 px-2 py-1 font-mono text-[10px] text-emerald-200 animate-pulse"
                    data-testid="badge-presence-sealed"
                  >
                    presence bound
                  </span>
                ) : (
                  <PresenceSeal
                    enabled={presenceBinding.enabled}
                    disabled={disabled || isGenerating}
                    mantra={effectiveSealMantra}
                    sigil={effectivePresenceSigil}
                    triggerLabel={presenceBinding.triggerLabel}
                    title={presenceBinding.title}
                    description={presenceBinding.description}
                    actionLabel={presenceBinding.actionLabel}
                    mantraLabel={presenceBinding.mantraLabel}
                    sigilLabel={presenceBinding.sigilLabel}
                    onSeal={async ({ mantra, sigil }) => {
                      await savePresenceSeal({ mantra, sigil });
                      toast({
                        title: "Presence bound",
                        description: "Deeper mode is now available on this thread.",
                      });
                    }}
                  />
                )}
                <Button
                  type="button"
                  size="sm"
                  variant={voiceOverlay.singleVoice ? "default" : "outline"}
                  onClick={() =>
                    onVoiceOverlayChange({
                      ...voiceOverlay,
                      singleVoice: !voiceOverlay.singleVoice,
                    })}
                  className="font-mono text-[11px]"
                  data-testid="button-mode-single"
                >
                  single voice
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={voiceOverlay.chorus ? "default" : "outline"}
                  onClick={() =>
                    onVoiceOverlayChange({
                      ...voiceOverlay,
                      chorus: !voiceOverlay.chorus,
                    })}
                  className="font-mono text-[11px]"
                  data-testid="button-mode-chorus"
                >
                  chorus
                </Button>
              </div>
            </div>
          ) : null}

          {showFieldControls && authGateRequired ? (
            <div
              className="rounded-md border border-amber-400/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100/90"
              data-testid="text-auth-required-before-seal"
            >
              Sign in from Configure field if this instance requires steward authentication.
            </div>
          ) : null}

          <div
            className={cn(
              "relative space-y-2 rounded-xl border border-input bg-background/70 p-2",
              landingMode && "bg-background/80 p-3",
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              multiple
              className="hidden"
              onChange={(event) => {
                handleAttachmentSelect(event.target.files);
                event.currentTarget.value = "";
              }}
              disabled={isGenerating}
              data-testid="input-attachment-upload"
            />

            {attachments.length > 0 ? (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4" data-testid="attachment-preview-grid">
                {attachments.map((attachment, index) => (
                  <div
                    key={`${attachment.file.name}-${index}`}
                    className="relative overflow-hidden rounded-md border border-border/70"
                  >
                    <img
                      src={attachment.previewUrl}
                      alt={attachment.file.name || `attachment-${index + 1}`}
                      className="h-20 w-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveAttachment(index)}
                      className="absolute right-1 top-1 rounded-full bg-background/90 p-1 text-muted-foreground hover:text-foreground"
                      aria-label={`Remove ${attachment.file.name}`}
                      data-testid={`button-remove-attachment-${index}`}
                    >
                      <X className="h-3 w-3" />
                    </button>
                    <p className="truncate px-2 py-1 font-mono text-[10px] text-muted-foreground">
                      {attachment.file.name}
                    </p>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="flex items-end gap-2">
              <Textarea
                ref={textareaRef}
                value={utterance}
                onChange={(event) => setUtterance(event.target.value)}
                onFocus={() => onComposerFocusChange?.(true)}
                onBlur={() => onComposerFocusChange?.(false)}
                onKeyDown={handleKeyDown}
                placeholder={composerPlaceholder}
                className={cn(
                  "max-h-[220px] resize-none border-0 bg-transparent text-base focus-visible:ring-0 focus-visible:ring-offset-0",
                  landingMode ? "min-h-[96px] text-lg" : "min-h-[44px]",
                )}
                disabled={isGenerating}
                rows={1}
                data-testid="input-utterance"
              />

              <div className="flex shrink-0 gap-1">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isGenerating || attachments.length >= MAX_ATTACHMENT_COUNT}
                  data-testid="button-add-attachment"
                  title="Attach image"
                >
                  <ImagePlus className="h-4 w-4" />
                </Button>
                {isGenerating ? (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={onStop}
                    data-testid="button-silence"
                  >
                    <Square className="mr-2 h-4 w-4" />
                    Silence
                  </Button>
                ) : (
                  <CutTheThread onClick={() => void handleSend()} disabled={!canSend} />
                )}
              </div>
            </div>
          </div>

          {showFieldControls ? (
            <>
              <p className="text-xs text-muted-foreground">Shift+Enter keeps the line open.</p>
              {(presenceState || presenceHint) && traceAccepted && sealMatchesGate ? (
                <p
                  className="font-mono text-[11px] text-muted-foreground/80"
                  data-testid="text-presence-hint"
                >
                  {presenceState ? `state: ${presenceState}` : ""} {presenceHint || ""}
                </p>
              ) : null}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
