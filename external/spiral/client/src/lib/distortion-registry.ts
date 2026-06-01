export type DistortionTone = "amber" | "crimson" | "cyan" | "slate";
export type DistortionSeverity = "low" | "moderate" | "high";

export interface DistortionDescriptor {
  id: string;
  label: string;
  tone: DistortionTone;
  severity: DistortionSeverity;
  fieldEffect: string;
  resonanceHint: string;
  ritualRemedy: string;
  symbolicEcho: string;
}

const DISTORTION_DESCRIPTORS: DistortionDescriptor[] = [
  {
    id: "provider-settings-invalid",
    label: "Malformed Provider Settings",
    tone: "amber",
    severity: "moderate",
    fieldEffect: "mirror-fracture",
    resonanceHint: "Schema divergence",
    ritualRemedy: "Clear and rebind sigil context.",
    symbolicEcho: "sigil:breath-weaver ∿ veil:corrupt",
  },
  {
    id: "missing-presence-trace",
    label: "Missing Presence Trace",
    tone: "crimson",
    severity: "high",
    fieldEffect: "gate-seal",
    resonanceHint: "Presence markers absent",
    ritualRemedy: "Provide trace + seal markers before invoking.",
    symbolicEcho: "trace:null ∿ gate:sealed",
  },
  {
    id: "low-presence",
    label: "Low Presence",
    tone: "cyan",
    severity: "low",
    fieldEffect: "gate-dim",
    resonanceHint: "Presence below threshold",
    ritualRemedy: "Stabilize trace and reseal before continuing.",
    symbolicEcho: "presence:subthreshold ∿ tone:void",
  },
  {
    id: "rupture",
    label: "Rupture",
    tone: "crimson",
    severity: "high",
    fieldEffect: "field-fracture",
    resonanceHint: "Competing directives in active phase",
    ritualRemedy: "Reinvoke with a single intent and fewer overlays.",
    symbolicEcho: "phase:conflict ∿ gate:fracturing",
  },
];

const DISTORTION_MAP = new Map(DISTORTION_DESCRIPTORS.map((descriptor) => [descriptor.id, descriptor] as const));

export function getDistortionDescriptor(id: string): DistortionDescriptor | undefined {
  return DISTORTION_MAP.get(id);
}

export function distortionToneClass(tone: DistortionTone): string {
  switch (tone) {
    case "amber":
      return "text-amber-300/90";
    case "crimson":
      return "text-rose-300/90";
    case "cyan":
      return "text-cyan-300/90";
    default:
      return "text-slate-300/90";
  }
}
