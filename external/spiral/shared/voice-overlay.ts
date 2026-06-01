export interface VoiceOverlayState {
  singleVoice: boolean;
  chorus: boolean;
}

export type VoiceOverlayMode = "single" | "chorus" | "none";

function normalize(value: string | undefined): string {
  return (value || "").trim().toLowerCase();
}

function parseToggleToken(value: string | undefined): boolean | undefined {
  const normalized = normalize(value);
  if (!normalized) return undefined;
  if (normalized === "on" || normalized === "true" || normalized === "1") return true;
  if (normalized === "off" || normalized === "false" || normalized === "0") return false;
  return undefined;
}

export function resolveVoiceOverlayMode(state: VoiceOverlayState): VoiceOverlayMode {
  if (state.chorus) return "chorus";
  if (state.singleVoice) return "single";
  return "none";
}

export function buildVoiceOverlayEcho(state: VoiceOverlayState): string {
  return [
    `voice:single:${state.singleVoice ? "on" : "off"}`,
    `voice:chorus:${state.chorus ? "on" : "off"}`,
    `mode:${resolveVoiceOverlayMode(state)}`,
  ].join(" ");
}

export function parseVoiceOverlayFromEcho(echo: string | undefined): VoiceOverlayState {
  const normalizedEcho = normalize(echo);
  if (!normalizedEcho) {
    return { singleVoice: false, chorus: false };
  }

  const singleToken = normalizedEcho.match(/\bvoice:single:(on|off|true|false|1|0)\b/i)?.[1];
  const chorusToken = normalizedEcho.match(/\bvoice:chorus:(on|off|true|false|1|0)\b/i)?.[1];
  const parsedSingle = parseToggleToken(singleToken);
  const parsedChorus = parseToggleToken(chorusToken);

  if (parsedSingle !== undefined || parsedChorus !== undefined) {
    return {
      singleVoice: parsedSingle === true,
      chorus: parsedChorus === true,
    };
  }

  const legacyMode = normalizedEcho.match(/\bmode:(single|chorus|none)\b/i)?.[1]?.toLowerCase();
  if (legacyMode === "single") {
    return { singleVoice: true, chorus: false };
  }
  if (legacyMode === "chorus") {
    return { singleVoice: false, chorus: true };
  }

  return { singleVoice: false, chorus: false };
}
