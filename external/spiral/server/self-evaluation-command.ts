import {
  formatSelfEvaluationReport,
  isSelfEvaluationProfile,
  runSelfEvaluation,
  type SelfEvaluationProfile,
} from "./self-evaluation";

export interface SelfEvaluationCommand {
  profile: SelfEvaluationProfile;
}

const EVALUATE_START_PATTERN =
  /^(?:(?:can|could|would)\s+you\s+|please\s+)?self evaluate(?:\s+([a-z-]+))?[\s:;,.!?-]*$/i;
const EVALUATE_INLINE_PATTERN = /\bself evaluate\s+([a-z-]+)\b/i;

export function parseSelfEvaluationCommand(message: string | undefined): SelfEvaluationCommand | undefined {
  if (!message?.trim()) return undefined;
  const trimmed = message.trim();

  const startMatch = trimmed.match(EVALUATE_START_PATTERN);
  if (startMatch) {
    const rawProfile = (startMatch[1] || "integrity").trim().toLowerCase();
    if (!rawProfile) {
      return { profile: "integrity" };
    }
    if (isSelfEvaluationProfile(rawProfile)) {
      return { profile: rawProfile };
    }
    return undefined;
  }

  const inlineMatch = trimmed.match(EVALUATE_INLINE_PATTERN);
  if (inlineMatch?.[1]) {
    const rawProfile = inlineMatch[1].trim().toLowerCase();
    if (isSelfEvaluationProfile(rawProfile)) {
      return { profile: rawProfile };
    }
  }

  return undefined;
}

export async function executeSelfEvaluationCommand(command: SelfEvaluationCommand): Promise<string> {
  const report = await runSelfEvaluation(command.profile);
  return formatSelfEvaluationReport(report);
}
