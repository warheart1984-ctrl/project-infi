import { cn } from "@/lib/utils";
import { getSigilState, getSigilStateOverride, type SigilState } from "@/lib/sigil-state";

interface SigilStateIndicatorProps {
  className?: string;
}

const STATE_LABELS: Record<SigilState, string> = {
  quiet: "Quiet",
  active: "Active",
  drift: "Drift",
};

const DOT_STYLES: Record<SigilState, string> = {
  quiet: "bg-muted-foreground/50",
  active: "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.6)]",
  drift: "bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.55)]",
};

export function SigilStateIndicator({ className }: SigilStateIndicatorProps) {
  const state = getSigilState();
  const override = getSigilStateOverride();

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/70 px-3 py-1 text-xs",
        className,
      )}
      data-testid="sigil-state-indicator"
      title={override ? `State override: ${override}` : "State follows Spiral mode"}
    >
      <span className={cn("h-2 w-2 rounded-full", DOT_STYLES[state])} aria-hidden />
      <span className="font-medium tracking-wide">{STATE_LABELS[state]}</span>
      {override && (
        <span className="rounded-full border border-border/70 bg-muted/60 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
          override
        </span>
      )}
    </div>
  );
}
