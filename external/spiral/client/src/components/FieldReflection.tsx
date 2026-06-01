import type { SpiralField } from "@shared/spiral-field";
import { cn } from "@/lib/utils";
import { distortionToneClass, getDistortionDescriptor } from "@/lib/distortion-registry";

interface FieldReflectionProps {
  field: SpiralField | null;
  presenceCalculatorEnabled?: boolean;
}

const toneClass: Record<SpiralField["tone"], string> = {
  reverent: "text-emerald-300",
  recursive: "text-cyan-300",
  wild: "text-amber-300",
  void: "text-slate-300",
};

export function FieldReflection({ field, presenceCalculatorEnabled = false }: FieldReflectionProps) {
  if (!field) return null;
  const distortionDetails = field.distortions.map((id) => ({
    id,
    descriptor: getDistortionDescriptor(id),
  }));

  return (
    <div
      className={cn(
        "mx-4 mb-3 rounded-md border border-border/70 bg-card/40 px-3 py-2",
        field.gate === "sealed" && "bg-black/70",
        field.gate === "fracturing" && "animate-pulse",
      )}
      data-testid="field-reflection"
    >
      <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono">
        <span className={cn("uppercase tracking-[0.12em]", toneClass[field.tone])}>tone:{field.tone}</span>
        <span>mirror:{field.mirror}</span>
        <span>gate:{field.gate}</span>
        <span>memory:{field.memoryMode || "sigil-bound"}</span>
        <span>presence:{presenceCalculatorEnabled ? field.presenceLevel.toFixed(2) : "felt"}</span>
      </div>
      {field.distortions.length > 0 && (
        <div className="mt-1 text-[11px] font-mono">
          <p className="text-amber-300/90">distortions: {field.distortions.join(", ")}</p>
          <div className="mt-1 space-y-1">
            {distortionDetails.map(({ id, descriptor }, index) => (
              <p
                key={`${id}:${index}`}
                className={descriptor ? distortionToneClass(descriptor.tone) : "text-muted-foreground/90"}
                data-testid={`distortion-${id}`}
              >
                {descriptor
                  ? `${id} · ${descriptor.label} · ${descriptor.resonanceHint} · remedy: ${descriptor.ritualRemedy}`
                  : `${id} · unregistered distortion`}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
