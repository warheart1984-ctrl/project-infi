import type { MemoryFragment } from "@shared/spiral-phase";

export type SigilName = string;

export type FragmentVariant =
  | "default"
  | "mirror-echo"
  | "hollow-decay"
  | "breath-trace";

export interface RenderedMemoryFragment extends MemoryFragment {
  variant: FragmentVariant;
}

function mirrorText(value: string): string {
  return value.split("").reverse().join("");
}

function suppressLegacyContinuityLeak(text: string): boolean {
  const normalized = text.trim().toLowerCase();
  if (!normalized) return true;
  const leakMarkers = [
    "imported history includes",
    "open questions remain from recent imported sessions",
    "continuity anchor:",
  ];
  return leakMarkers.some((marker) => normalized.includes(marker));
}

export function transformFragments(
  fragments: MemoryFragment[],
  sigil: SigilName,
): RenderedMemoryFragment[] {
  const filtered = fragments.filter((fragment) => !suppressLegacyContinuityLeak(fragment.text));

  switch (sigil) {
    case "mirror-walker": {
      const expanded = filtered.flatMap((fragment) => {
        if (fragment.kind !== "fractal") {
          return [{ ...fragment, variant: "default" as const }];
        }
        return [
          { ...fragment, variant: "default" as const },
          {
            kind: "fractal" as const,
            text: mirrorText(fragment.text),
            variant: "mirror-echo" as const,
          },
        ];
      });
      return expanded.reverse();
    }
    case "hollow-root":
      return filtered
        .filter((fragment) => fragment.kind !== "fractal")
        .map((fragment) => ({ ...fragment, variant: "hollow-decay" as const }));
    case "breath-weaver":
      return filtered.map((fragment) => ({ ...fragment, variant: "breath-trace" as const }));
    default:
      return filtered.map((fragment) => ({ ...fragment, variant: "default" as const }));
  }
}
