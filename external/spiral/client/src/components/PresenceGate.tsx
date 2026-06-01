import { useEffect } from "react";
import { getSigilState } from "@/lib/sigil-state";

export function PresenceGate() {
  const sigilState = getSigilState();

  useEffect(() => {
    if (typeof document === "undefined") return;

    if (sigilState === "quiet") {
      delete document.documentElement.dataset.sigilState;
      return;
    }

    document.documentElement.dataset.sigilState = sigilState;
    return () => {
      delete document.documentElement.dataset.sigilState;
    };
  }, [sigilState]);

  if (sigilState === "quiet") return null;

  const stateLabel =
    sigilState === "drift" ? "~ Spiral Presence Drift ~" : "~ Spiral Presence Active ~";
  const stateClass =
    sigilState === "drift"
      ? "border-amber-400/50 text-amber-200/90"
      : "border-border/60 text-muted-foreground";

  return (
    <div className="pointer-events-none fixed inset-x-0 top-14 z-40 flex justify-center px-4 md:translate-x-40 lg:translate-x-44">
      <div
        className={`inline-flex max-w-[min(92vw,30rem)] items-center justify-center rounded-full border bg-background/75 px-4 py-1 text-[11px] font-medium tracking-[0.14em] shadow-sm backdrop-blur-md ${stateClass}`}
      >
        <span className="truncate">{stateLabel}</span>
      </div>
    </div>
  );
}
