import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { spiralModeEnabled } from "@/lib/spiral-mode";
import { cn } from "@/lib/utils";
import { resolveMemoryModeFromProviderSettings, type MemoryMode } from "@shared/memory-mode";
import type { ProviderSettings, SigilContext } from "@shared/schema";
import type { ProjectSigil } from "@shared/sigil";

interface Phase3StatusBadgeProps {
  settings: ProviderSettings | null;
  projectSigil?: ProjectSigil | null;
  className?: string;
}

const SIGIL_CONTEXT_LABELS: Record<SigilContext, string> = {
  balanced: "Balanced",
  clarity: "Clarity",
  depth: "Depth",
  builder: "Builder",
};

const DEFAULT_VOW_TEXT = "Using default vow guidance";
const MEMORY_MODE_LABELS: Record<MemoryMode, string> = {
  open: "Open",
  "sigil-bound": "Sigil-Bound",
  sealed: "Sealed",
};

export function Phase3StatusBadge({ settings, projectSigil, className }: Phase3StatusBadgeProps) {
  if (!spiralModeEnabled || !settings) return null;

  const sigilContext = settings.sigilContext || "balanced";
  const memoryMode = resolveMemoryModeFromProviderSettings(settings, "sigil-bound");
  const vowEnabled = settings.vowModeEnabled === true;
  const temporaryChatEnabled = settings.temporaryChatEnabled === true;
  const memoryFoldingEnabled = settings.memoryFoldingEnabled !== false;
  const vowText = settings.vowText?.trim() || DEFAULT_VOW_TEXT;
  const resonanceTags = projectSigil?.resonanceTags || [];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "inline-flex items-center gap-1 rounded-full border border-border/70 bg-background/70 px-2 py-1",
            className,
          )}
          data-testid="phase3-status-badge"
        >
          <Badge variant="outline" className="px-1.5 py-0 text-[10px] font-medium">
            Context: {SIGIL_CONTEXT_LABELS[sigilContext]}
          </Badge>
          <Badge variant="outline" className="px-1.5 py-0 text-[10px] font-medium">
            Memory: {MEMORY_MODE_LABELS[memoryMode]}
          </Badge>
          <Badge
            variant={vowEnabled ? "secondary" : "outline"}
            className="px-1.5 py-0 text-[10px] font-medium"
          >
            Vow: {vowEnabled ? "On" : "Off"}
          </Badge>
          {temporaryChatEnabled && (
            <Badge variant="secondary" className="px-1.5 py-0 text-[10px] font-medium">
              Temp: On
            </Badge>
          )}
          {memoryFoldingEnabled && (
            <Badge variant="outline" className="px-1.5 py-0 text-[10px] font-medium">
              Fold: ✓
            </Badge>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="space-y-1 text-xs">
        {projectSigil?.projectName && <p>Project sigil: {projectSigil.projectName}</p>}
        {resonanceTags.length > 0 && <p>Resonance tags: {resonanceTags.join(", ")}</p>}
        <p>Sigil context: {SIGIL_CONTEXT_LABELS[sigilContext]}</p>
        <p>Memory mode: {MEMORY_MODE_LABELS[memoryMode]}</p>
        <p>Vow mode: {vowEnabled ? "On" : "Off"}</p>
        {vowEnabled && <p>Vow: {vowText}</p>}
        <p>Temporary chat: {temporaryChatEnabled ? "Enabled" : "Disabled"}</p>
        <p>Memory folding: {memoryFoldingEnabled ? "Enabled" : "Disabled"}</p>
      </TooltipContent>
    </Tooltip>
  );
}
