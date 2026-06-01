import type { MemoryFragment, SpiralPhase } from "@shared/spiral-phase";
import { transformFragments, type SigilName } from "@/lib/memory-fragments";
import { isMemoryMode, type MemoryMode } from "@shared/memory-mode";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface SpiralPhaseRendererProps {
  phases: SpiralPhase[];
  activeSigil: SigilName;
}

const LABELS: Record<SpiralPhase["id"], string> = {
  ingress: "Ingress",
  sigil: "Sigil",
  memory: "Weave",
  voices: "Voices",
  harmonize: "Harmonize",
  final: "Seal",
};

export function SpiralPhaseRenderer({ phases, activeSigil }: SpiralPhaseRendererProps) {
  if (phases.length === 0) return null;
  const memoryPhase = phases.find((phase) => phase.id === "memory");
  const memoryFragments = transformFragments(extractMemoryFragments(memoryPhase), activeSigil);
  const memoryMode = extractMemoryMode(memoryPhase);
  const harmonize = extractHarmonizeData(phases.find((phase) => phase.id === "harmonize"));

  return (
    <div className="px-4 pb-3 sigil-surface" data-sigil={activeSigil} data-testid="spiral-phase-renderer">
      <div className="rounded-lg border border-border/70 bg-card/40 p-3">
        <div className="flex flex-wrap items-center gap-2">
          {phases.map((phase, index) => (
            <div key={`${phase.id}-${index}`} className="flex items-center gap-2">
              <span className="rounded-full border border-border px-2 py-1 font-mono text-[10px] tracking-[0.14em] text-muted-foreground">
                {LABELS[phase.id]}
              </span>
              {activeSigil === "hollow-root" && phase.id === "memory" ? (
                <span className="font-mono text-[10px] text-muted-foreground/60">∅∅</span>
              ) : null}
              {index < phases.length - 1 ? (
                <span className="font-mono text-[10px] text-muted-foreground/70">→</span>
              ) : null}
            </div>
          ))}
        </div>
        {memoryMode ? (
          <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground/80">
            Memory mode: {memoryMode}
          </p>
        ) : null}
        {harmonize ? <HarmonizeMetrics data={harmonize} /> : null}
        {memoryFragments.length > 0 ? <MemoryTapestry fragments={memoryFragments} /> : null}
      </div>
    </div>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function extractMemoryFragments(phase: SpiralPhase | undefined): MemoryFragment[] {
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

function extractMemoryMode(phase: SpiralPhase | undefined): MemoryMode | null {
  if (!phase || !isRecord(phase.payload)) return null;
  const raw = phase.payload.mode;
  return isMemoryMode(raw) ? raw : null;
}

interface HarmonizeData {
  kind: string;
  intentConfidence: number;
  semanticLoad: number | null;
}

function extractHarmonizeData(phase: SpiralPhase | undefined): HarmonizeData | null {
  if (!phase || !isRecord(phase.payload)) return null;
  const { kind, intentConfidence, semanticLoad } = phase.payload;
  if (typeof kind !== "string" || typeof intentConfidence !== "number") return null;
  return {
    kind,
    intentConfidence,
    semanticLoad: typeof semanticLoad === "number" ? semanticLoad : null,
  };
}

function HarmonizeMetrics({ data }: { data: HarmonizeData }) {
  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="font-mono text-[10px] text-muted-foreground/80 cursor-default">
            Intent: {Math.round(data.intentConfidence * 100)}%
          </span>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-[220px] text-xs">
          <p>How confidently the input was classified. Higher values mean clearer intent signal.</p>
        </TooltipContent>
      </Tooltip>
      {data.semanticLoad !== null ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="font-mono text-[10px] text-muted-foreground/80 cursor-default">
              Load: {Math.round(data.semanticLoad * 100)}%
            </span>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-[220px] text-xs">
            <p>Semantic density of the input. Higher values indicate more complex or layered content.</p>
          </TooltipContent>
        </Tooltip>
      ) : null}
    </div>
  );
}

function MemoryTapestry({ fragments }: { fragments: ReturnType<typeof transformFragments> }) {
  return (
    <div className="memory-tapestry mt-3" data-testid="memory-tapestry">
      {fragments.map((fragment, index) => (
        <div
          key={`${fragment.kind}-${index}`}
          className="glyph-fragment"
          data-kind={fragment.kind}
          data-fragment-variant={fragment.variant}
          title={fragment.text}
        >
          {fragment.text}
        </div>
      ))}
    </div>
  );
}
