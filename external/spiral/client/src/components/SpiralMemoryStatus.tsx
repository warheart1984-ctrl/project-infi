import { cn } from "@/lib/utils";
import type { MemoryMode } from "@shared/memory-mode";
import { useEffect, useRef, useState } from "react";

export type SpiralTraceState = "present" | "imported" | "none" | "sealed";

interface SpiralMemoryStatusProps {
  principalId: string;
  memorySeedCount: number | null;
  importedSeedCount: number | null;
  traceState: SpiralTraceState;
  memoryMode: MemoryMode;
  className?: string;
}

function compactPrincipal(principalId: string): string {
  const normalized = principalId.trim();
  if (!normalized) return "unknown";
  if (normalized.length <= 28) return normalized;
  return `${normalized.slice(0, 18)}…${normalized.slice(-8)}`;
}

const TRACE_GLYPH_BY_STATE: Record<SpiralTraceState, string> = {
  present: "▲",
  imported: "△",
  none: "▽",
  sealed: "⟁",
};

const TRACE_GLYPH_COLOR_BY_STATE: Record<SpiralTraceState, string> = {
  present: "text-emerald-400",
  imported: "text-teal-300",
  none: "text-muted-foreground/80",
  sealed: "text-slate-400",
};

const TRACE_BADGE_SURFACE_BY_STATE: Record<SpiralTraceState, string> = {
  present: "border-emerald-400/35 bg-emerald-500/5",
  imported: "border-teal-300/35 bg-teal-300/5",
  none: "",
  sealed: "border-slate-400/25 bg-slate-400/5 opacity-85",
};

const TRACE_GLYPH_PULSE_BY_STATE: Record<SpiralTraceState, string> = {
  present:
    "motion-safe:animate-[spiral-recursive-pulse_780ms_ease-in-out_1] drop-shadow-[0_0_10px_rgba(16,185,129,0.75)]",
  imported:
    "motion-safe:animate-[spiral-wild-flicker_900ms_steps(2,end)_1] drop-shadow-[0_0_8px_rgba(45,212,191,0.55)]",
  none: "",
  sealed: "",
};

const TRACE_BADGE_AURA_BY_STATE: Record<SpiralTraceState, string> = {
  present: "spiral-badge-aura--present",
  imported: "spiral-badge-aura--imported",
  none: "",
  sealed: "",
};

export function SpiralMemoryStatus({
  principalId,
  memorySeedCount,
  importedSeedCount,
  traceState,
  memoryMode,
  className,
}: SpiralMemoryStatusProps) {
  const lines = Math.max(0, Math.floor(memorySeedCount ?? 0));
  const importedLines = Math.max(0, Math.floor(importedSeedCount ?? 0));
  const resolvedTraceState = memoryMode === "sealed" ? "sealed" : traceState;
  const [pulseState, setPulseState] = useState<SpiralTraceState | null>(null);
  const [badgeAuraState, setBadgeAuraState] = useState<SpiralTraceState | null>(null);
  const initializedRef = useRef(false);
  const auraInitializedRef = useRef(false);
  const previousTraceStateRef = useRef<SpiralTraceState>(resolvedTraceState);
  const triangle = TRACE_GLYPH_BY_STATE[resolvedTraceState];
  const traceLabel =
    resolvedTraceState === "imported"
      ? `imported (${Math.max(importedLines, lines)} lines)`
      : resolvedTraceState;
  const principalLabel = compactPrincipal(principalId);

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      return;
    }
    setPulseState(resolvedTraceState === "sealed" ? null : resolvedTraceState);
    const timeoutId = window.setTimeout(() => {
      setPulseState(null);
    }, resolvedTraceState === "imported" ? 900 : 780);
    return () => window.clearTimeout(timeoutId);
  }, [memoryMode, resolvedTraceState]);

  useEffect(() => {
    if (!auraInitializedRef.current) {
      auraInitializedRef.current = true;
      previousTraceStateRef.current = resolvedTraceState;
      return;
    }

    const previous = previousTraceStateRef.current;
    previousTraceStateRef.current = resolvedTraceState;
    if (previous === resolvedTraceState) return;

    if (resolvedTraceState !== "present" && resolvedTraceState !== "imported") {
      setBadgeAuraState(null);
      return;
    }

    setBadgeAuraState(resolvedTraceState);
    const timeoutId = window.setTimeout(() => {
      setBadgeAuraState(null);
    }, 300);
    return () => window.clearTimeout(timeoutId);
  }, [resolvedTraceState]);

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-border/70 bg-background/70 px-2 py-1 font-mono text-[10px]",
        TRACE_BADGE_SURFACE_BY_STATE[resolvedTraceState],
        badgeAuraState ? TRACE_BADGE_AURA_BY_STATE[badgeAuraState] : "",
        className,
      )}
      data-testid="spiral-memory-status"
      title={`trace: ${traceLabel} · principal: ${principalId || "unknown"} · memory: ${lines} lines`}
    >
      <span
        className={cn(
          "font-semibold transition-[filter,color,opacity] duration-300",
          TRACE_GLYPH_COLOR_BY_STATE[resolvedTraceState],
          pulseState ? TRACE_GLYPH_PULSE_BY_STATE[pulseState] : "",
        )}
        aria-hidden
      >
        {triangle}
      </span>
      <span className="text-muted-foreground">trace:</span>
      <strong>{traceLabel}</strong>
      <span className="text-muted-foreground">· memory:</span>
      <strong>{lines}</strong>
      <span className="text-muted-foreground">lines</span>
      <span className="text-muted-foreground">· principal:</span>
      <code className="max-w-[14rem] truncate">{principalLabel}</code>
    </div>
  );
}
