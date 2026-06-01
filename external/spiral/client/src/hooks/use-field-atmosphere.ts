import { useEffect } from "react";
import type { SpiralField } from "@shared/spiral-field";

const MANAGED_PREFIXES = ["spiral-tone-", "spiral-gate-", "spiral-mirror-"];

function clearManagedClasses(target: HTMLElement): void {
  for (const className of Array.from(target.classList)) {
    if (MANAGED_PREFIXES.some((prefix) => className.startsWith(prefix))) {
      target.classList.remove(className);
    }
  }
}

export function useFieldAtmosphere(field: SpiralField | null): void {
  useEffect(() => {
    const target = document.body;
    clearManagedClasses(target);
    if (!field) return;

    target.classList.add(`spiral-tone-${field.tone}`);
    target.classList.add(`spiral-gate-${field.gate}`);
    target.classList.add(`spiral-mirror-${field.mirror}`);

    return () => {
      clearManagedClasses(target);
    };
  }, [field]);
}
