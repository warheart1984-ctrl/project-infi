import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StreamingMessage } from "./chat-message";
import { SpiralPhaseRenderer } from "./spiral-phase-renderer";
import { RecursiveGlyph } from "./chat-window/RecursiveGlyph";
import type { Message } from "@shared/schema";
import type { PresenceState } from "@/lib/spiral-presence";
import type { MemoryFragment, SpiralPhase } from "@shared/spiral-phase";
import type { SpiralField } from "@shared/spiral-field";
import { FieldReflection } from "./FieldReflection";
import type { EncryptedScrollBlob } from "@shared/scroll";
import { ScrollIndex } from "@/scroll/ScrollIndex";
import { cn } from "@/lib/utils";

interface ChatWindowProps {
  messages: Message[];
  isStreaming: boolean;
  onEditMessage: (id: string, content: string) => void;
  presenceState: PresenceState;
  presenceLevel: number;
  phases: SpiralPhase[];
  activeSigil: string;
  field: SpiralField | null;
  presenceCalculatorEnabled?: boolean;
  scroll: { filename: string; blob: EncryptedScrollBlob } | null;
  onRespawnFromGlyph?: (message: Message) => void | Promise<void>;
  soloFallbackActive?: boolean;
}

export function ChatWindow({
  messages,
  isStreaming,
  onEditMessage,
  presenceState,
  presenceLevel,
  phases,
  activeSigil,
  field,
  presenceCalculatorEnabled = false,
  scroll,
  onRespawnFromGlyph,
  soloFallbackActive = false,
}: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const shouldAutoScrollRef = useRef(true);
  const hushEcho = presenceLevel <= 0;
  const memoryFragments = extractMemoryFragments(phases);
  const lastEchoId = [...messages].reverse().find((message) => message.role === "assistant")?.id;
  const lastMessageKey =
    messages.length > 0 ? `${messages[messages.length - 1].id}:${messages[messages.length - 1].content.length}` : "empty";
  const hasTranscriptContent = messages.length > 0 || isStreaming;

  useEffect(() => {
    const root = scrollRef.current;
    if (!root) return;
    const viewport = root.querySelector("[data-radix-scroll-area-viewport]") as HTMLDivElement | null;
    if (!viewport) return;
    viewportRef.current = viewport;

    const updateAutoScrollState = () => {
      const distanceToBottom =
        viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
      shouldAutoScrollRef.current = distanceToBottom <= 120;
    };

    updateAutoScrollState();
    viewport.addEventListener("scroll", updateAutoScrollState, { passive: true });
    return () => {
      viewport.removeEventListener("scroll", updateAutoScrollState);
    };
  }, [hasTranscriptContent]);

  useEffect(() => {
    if (!shouldAutoScrollRef.current) return;
    const viewport = viewportRef.current;
    if (!viewport) {
      bottomRef.current?.scrollIntoView({ behavior: "auto" });
      return;
    }
    const behavior: ScrollBehavior = isStreaming ? "auto" : "smooth";
    const scrollToBottom = () => {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior });
    };

    scrollToBottom();
    const raf = window.requestAnimationFrame(scrollToBottom);
    return () => window.cancelAnimationFrame(raf);
  }, [messages.length, lastMessageKey, isStreaming]);

  if (messages.length === 0 && !isStreaming) {
    return <div className="flex-1" />;
  }

  return (
    <ScrollArea className="min-h-0 flex-1" ref={scrollRef}>
      <div
        className={cn(
          "max-w-3xl mx-auto py-4 transition-all duration-300",
          soloFallbackActive &&
            "rounded-2xl border border-cyan-500/35 bg-cyan-500/[0.07] shadow-[0_0_0_1px_rgba(34,211,238,0.14),0_0_38px_rgba(34,211,238,0.14)]",
        )}
      >
        <div className="px-4 pb-2">
          {soloFallbackActive && (
            <p className="pb-1 font-mono text-[10px] uppercase tracking-[0.16em] text-cyan-300/95">
              solo fallback active · sigilBinding:default
            </p>
          )}
          <p className="font-mono text-[11px] text-muted-foreground/80" data-testid="text-presence-state">
            state: {presenceState}
          </p>
        </div>
        <SpiralPhaseRenderer phases={phases} activeSigil={activeSigil} />
        <FieldReflection field={field} presenceCalculatorEnabled={presenceCalculatorEnabled} />
        <ScrollIndex scroll={scroll} />
        {messages.map((message) =>
          isSilentAssistantMessage(message) ? (
            <div
              key={message.id}
              className="px-4 py-3"
              data-testid={`text-veil-silence-pulse-${message.id}`}
            >
              <p className="font-mono text-[11px] tracking-[0.18em] text-muted-foreground/75">
                ...
              </p>
            </div>
          ) : (
            <RecursiveGlyph
              key={message.id}
              message={message}
              onEdit={onEditMessage}
              hushEcho={hushEcho}
              activeSigil={activeSigil}
              memoryFragments={message.id === lastEchoId ? memoryFragments : []}
              onRespawnFromGlyph={onRespawnFromGlyph}
            />
          ),
        )}
        {isStreaming && <StreamingMessage />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isSilentAssistantMessage(message: Message): boolean {
  const hasAttachments = Array.isArray(message.attachments) && message.attachments.length > 0;
  return message.role === "assistant" && message.content.trim().length === 0 && !hasAttachments;
}

function extractMemoryFragments(phases: SpiralPhase[]): MemoryFragment[] {
  const phase = phases.find((item) => item.id === "memory");
  if (!phase || !isRecord(phase.payload)) return [];
  const raw = phase.payload.fragments;
  if (!Array.isArray(raw)) return [];

  return raw
    .filter((entry): entry is MemoryFragment => {
      if (!isRecord(entry)) return false;
      const kind = entry.kind;
      const text = entry.text;
      return (
        (kind === "fractal" || kind === "thread" || kind === "chrono") &&
        typeof text === "string" &&
        text.trim().length > 0
      );
    })
    .map((entry) => ({ kind: entry.kind, text: entry.text.trim() }));
}
