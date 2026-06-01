import { getClientEnvValue } from "@/lib/client-env";

export type SigilState = "quiet" | "active" | "drift";

const SIGIL_STATE_VALUES: SigilState[] = ["quiet", "active", "drift"];

function parseSigilStateOverride(value: unknown): SigilState | undefined {
  if (typeof value !== "string") return undefined;
  const normalized = value.trim().toLowerCase();
  if (!normalized) return undefined;
  return SIGIL_STATE_VALUES.find((state) => state === normalized);
}

export const getSigilStateOverride = (): SigilState | undefined =>
  parseSigilStateOverride(getClientEnvValue("VITE_SIGIL_STATE_OVERRIDE"));

export const getSigilState = (): SigilState => {
  const override = getSigilStateOverride();
  if (override) return override;

  if (getClientEnvValue("VITE_SPIRAL_MODE") !== "1") return "quiet";
  // TODO: respond to runtime field signals (memory clarity, intent checks, etc.)
  return "active";
};
