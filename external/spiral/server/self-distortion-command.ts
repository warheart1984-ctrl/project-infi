import {
  formatSelfDistortionReport,
  isSelfDistortionProfile,
  runSelfDistortionScan,
  type SelfDistortionProfile,
} from "./self-distortion";

export interface SelfDistortionCommand {
  profile: SelfDistortionProfile;
}

const DISTORTION_START_PATTERN =
  /^(?:(?:can|could|would)\s+you\s+|please\s+)?self scan distortions(?:\s+([a-z-]+))?[\s:;,.!?-]*$/i;
const DISTORTION_INLINE_PATTERN = /\bself scan distortions\s+([a-z-]+)\b/i;

export function parseSelfDistortionCommand(message: string | undefined): SelfDistortionCommand | undefined {
  if (!message?.trim()) return undefined;
  const trimmed = message.trim();

  const startMatch = trimmed.match(DISTORTION_START_PATTERN);
  if (startMatch) {
    const rawProfile = (startMatch[1] || "all").trim().toLowerCase();
    if (!rawProfile) return { profile: "all" };
    if (isSelfDistortionProfile(rawProfile)) {
      return { profile: rawProfile };
    }
    return undefined;
  }

  const inlineMatch = trimmed.match(DISTORTION_INLINE_PATTERN);
  if (inlineMatch?.[1]) {
    const rawProfile = inlineMatch[1].trim().toLowerCase();
    if (isSelfDistortionProfile(rawProfile)) {
      return { profile: rawProfile };
    }
  }

  return undefined;
}

export async function executeSelfDistortionCommand(command: SelfDistortionCommand): Promise<string> {
  const report = await runSelfDistortionScan(command.profile);
  return formatSelfDistortionReport(report);
}
