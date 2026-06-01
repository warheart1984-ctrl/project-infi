import { providerSettingsSchema, type ProviderSettings } from "@shared/schema";
import type { SafeParseReturnType } from "zod";

export type ProviderSettingsValidationState = "missing" | "invalid" | "valid";

export interface ProviderSettingsValidationResult {
  state: ProviderSettingsValidationState;
  hasProviderSettings: boolean;
  parseResult: SafeParseReturnType<unknown, ProviderSettings>;
  distortions: string[];
}

export function validateProviderSettingsForVeil(
  providerSettings: unknown,
): ProviderSettingsValidationResult {
  const hasProviderSettings = providerSettings !== undefined && providerSettings !== null;
  const parseResult = providerSettingsSchema.safeParse(providerSettings);
  if (!hasProviderSettings) {
    return {
      state: "missing",
      hasProviderSettings,
      parseResult,
      distortions: [],
    };
  }
  if (!parseResult.success) {
    return {
      state: "invalid",
      hasProviderSettings,
      parseResult,
      distortions: ["provider-settings-invalid"],
    };
  }
  return {
    state: "valid",
    hasProviderSettings,
    parseResult,
    distortions: [],
  };
}
