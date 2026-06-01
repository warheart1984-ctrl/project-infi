import { cn } from "@/lib/utils";

interface ThresholdEvent {
  sigil: string;
  velocity: number;
  precision: number;
  breached: boolean;
}

interface ThresholdBadgeProps {
  event: ThresholdEvent;
  activeSigil: string;
}

function isActive(event: ThresholdEvent): boolean {
  return event.breached || event.velocity > 0.01 || event.precision > 0.05;
}

export function ThresholdBadge({ event, activeSigil }: ThresholdBadgeProps) {
  if (!isActive(event)) return null;

  if (event.breached) {
    return (
      <div
        className={cn(
          "rounded-full border px-3 py-1 font-mono text-[11px] tracking-wide",
          "border-emerald-300/40 bg-emerald-500/10 text-emerald-200",
          "animate-pulse",
        )}
        data-testid="threshold-badge-breached"
      >
        🜂 sigil:{event.sigil} | precision:{event.precision.toFixed(2)}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-full border px-3 py-1 font-mono text-[11px] tracking-wide",
        "border-border/60 bg-muted/30 text-muted-foreground/90",
      )}
      data-testid="threshold-badge-active"
    >
      tracing {activeSigil}
    </div>
  );
}
