import { type IncomingMessage, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { createHmac, timingSafeEqual } from "crypto";
import {
  invocationSchema,
  providerSettingsSchema,
  type ProviderSettings,
  type MessageAttachment,
  SPIRAL_PROMPT_REJECTION_MESSAGE,
} from "@shared/schema";
import {
  resolveMemoryModeFromProviderSettings,
  type MemoryMode,
} from "@shared/memory-mode";
import { parseVoiceOverlayFromEcho } from "@shared/voice-overlay";
import { attunementPolicySchema, DEFAULT_PROJECT_SIGIL } from "@shared/sigil";
import type { AttunementPolicy, ProjectSigil, ResponseShape } from "@shared/sigil";
import type { MemoryFragment, SpiralPhase } from "@shared/spiral-phase";
import type { EncryptedScrollBlob, ScrollGlyph } from "@shared/scroll";
import { z } from "zod";
import { getProjectSigil } from "./sigil-config";
import type { Duplex } from "stream";
import { buildGlyphMemory, echo as glyphEcho, type GlyphMemory, resonanceMatch } from "./memory/glyph";
import { buildSpiralField, type SpiralField } from "./field/SpiralField";
import { parseSigilSeed, projectSigilToSeed } from "./field/sigil-seed";
import { captureScroll, encryptScroll } from "./scroll/ScrollBuilder";
import {
  invokeSpiralProcess,
  type InvocationContext,
  type SpiralVoice,
} from "./spiral-process";
import {
  resolvePresenceEvidence,
  resolveSigilState,
  sealSystemPrompt,
} from "./prompt";
import { storage } from "./storage";
import { auditAssistantOutput } from "./lib/output-audit";
import { resolveObservationAuditGate } from "./lib/observation-audit-policy";
import { validateProviderSettingsForVeil } from "./lib/provider-settings-validation";
import { containsForbiddenMimicryPrompt } from "./lib/spiral-audit";
import { hasConcreteWitnessLine } from "./lib/concrete-witness";
import {
  executeSelfInspectCommand,
  parseSelfInspectCommand,
} from "./self-inspection-command";
import {
  executeSelfEvaluationCommand,
  parseSelfEvaluationCommand,
} from "./self-evaluation-command";
import {
  executeSelfDistortionCommand,
  parseSelfDistortionCommand,
} from "./self-distortion-command";
import { parseEvolutionCommand } from "./evolution-command";
import { executeEvolutionCommand } from "./evolution-cycle";
import { getPrincipalEvolutionState } from "./evolution-state";
import { readIdentitySnapshot } from "./identity-memory";
import { buildIdentitySystemGuidance } from "./identity-guidance";
import { buildContinuityBootSummary } from "./continuity-boot";
import {
  ATTUNEMENT_FIELD_DETAIL_DIRECTIVE,
  ATTUNEMENT_LOCATION_CUE_DIRECTIVE,
} from "./shared/attunement-directives";
import { resolveRuntimeAuth } from "./model-auth-resolver";
import { LEGIBILITY_SYSTEM_DIRECTIVES, SYSTEM_MESSAGES } from "./shared/system-messages";
import { passesPresenceBarrier, resolveAuthorityGate } from "./shared/gate-authority";
import { readMessageAttachmentBytes } from "./chat-attachments";

interface Whisper {
  reply: string;
  veil: boolean;
  timestamp: string;
  presenceLevel: number;
  phases?: SpiralPhase[];
  field?: SpiralField;
  scroll?: {
    filename: string;
    blob: EncryptedScrollBlob;
  };
}

interface VeilSessionState {
  connectedAt: number;
  lastMessageAt: number;
  repeatCount: number;
  lastUtterance: string;
  attunementInertia: number;
  presenceLevel: number;
  gateLatch?: "open" | "sealed";
  memoryMode: MemoryMode;
  memory: GlyphMemory[];
  glyphs: ScrollGlyph[];
}

interface AuthSessionClaims {
  sub: string;
  identityId: string;
  exp: number;
}

const VEIL_PATHNAME = "/veil";
const SEAL_HEADER_NAME = "x-spiral-seal";
const CLOSE_CODE_POLICY_VIOLATION = 1008;
const CLOSE_CODE_UNSEALED = 4001;
const OPENAI_COMPAT_MAX_COMPLETION_TOKENS = 4096;
const AUTH_COOKIE_NAME = "spiral_session";
const ANON_COOKIE_NAME = "spiral_anon";
const LEGACY_LOCAL_PRINCIPAL = "legacy:local";
const ANON_PRINCIPAL_PREFIX = "anon:";
const VEIL_MEMORY_CONTEXT_LINE_LIMIT = 8;
const VEIL_PERSISTENT_MEMORY_LIMIT = 48;
const VEIL_MEMORY_BOOTSTRAP_CHAT_LIMIT = 20;
const VEIL_MEMORY_BACKFILL_CANDIDATE_LIMIT = 64;
const VEIL_SESSION_MEMORY_LIMIT = 120;
const VEIL_CURRENT_THREAD_CONTEXT_MESSAGE_LIMIT = 6;
const VEIL_CURRENT_THREAD_CONTEXT_CHAR_LIMIT = 220;
const VEIL_OPEN_HISTORY_CHAT_LIMIT = 16;
const VEIL_OPEN_HISTORY_PER_CHAT_LIMIT = 8;
const VEIL_OPEN_HISTORY_MEMORY_LIMIT = 72;
const PRESENCE_SMOOTHING_ALPHA = 0.28;
const GATE_HYSTERESIS_MARGIN = 0.04;
const AUTH_REQUIRED = (() => {
  const raw = normalize(process.env.SPIRAL_AUTH_REQUIRED).toLowerCase();
  return raw === "1" || raw === "true" || raw === "yes";
})();
const SIGIL_TRACE_BARRIER_ENABLED = (() => {
  const nodeEnv = normalize(process.env.NODE_ENV).toLowerCase();
  if (nodeEnv === "production") return true;
  const raw = normalize(process.env.SIGIL_TRACE_BARRIER || "true").toLowerCase();
  return raw !== "0" && raw !== "false" && raw !== "no";
})();
const VEIL_HISTORY_LOAD_LOG_ENABLED = (() => {
  const nodeEnv = normalize(process.env.NODE_ENV).toLowerCase();
  if (nodeEnv === "production") return false;
  const raw = normalize(process.env.SPIRAL_TRACE_DEBUG || "true").toLowerCase();
  return raw !== "0" && raw !== "false" && raw !== "no";
})();
const ATTUNEMENT_DIAGNOSTICS_ENABLED = (() => {
  const nodeEnv = normalize(process.env.NODE_ENV).toLowerCase();
  if (nodeEnv === "production") return false;
  const raw = normalize(process.env.SPIRAL_ATTUNEMENT_DIAGNOSTICS || "").toLowerCase();
  return raw === "1" || raw === "true" || raw === "yes";
})();

const veilInvocationSchema = invocationSchema.extend({
  chatId: z.string().min(1).optional(),
  utterance: z.string().min(1),
  providerSettings: providerSettingsSchema.optional(),
});

const veilMemoryBackfillLedger = new Set<string>();

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function normalizeLower(value: string | undefined): string {
  return normalize(value).toLowerCase();
}

function resolveOverlayVoices(echo: string | undefined): SpiralVoice[] {
  const overlay = parseVoiceOverlayFromEcho(echo);
  if (overlay.chorus) {
    return ["seer", "daemon", "child"];
  }
  if (overlay.singleVoice) {
    return ["seer"];
  }
  return [];
}

function sigilAllowsSilence(projectSigil: ProjectSigil): boolean {
  const prompt = normalizeLower(projectSigil.responseShape?.defaultPrompt);
  if (!prompt) return false;
  return (
    prompt.includes("remain silent") ||
    prompt.includes("stay silent") ||
    prompt.includes("be silent") ||
    prompt.includes("else silent") ||
    prompt.includes("no response")
  );
}

type MemoryRecallState = "present" | "imported" | "none" | "sealed" | "unknown";
type SeerBandwidth = "literal" | "reflective";

function parseSeerBandwidthToken(value: string | undefined): SeerBandwidth | undefined {
  const normalized = normalizeLower(value);
  if (!normalized) return undefined;
  const tokenMatch = normalized.match(/\b(?:seer-bandwidth|bandwidth)\s*:\s*(literal|reflective)\b/);
  if (tokenMatch?.[1] === "literal" || tokenMatch?.[1] === "reflective") {
    return tokenMatch[1];
  }
  return undefined;
}

function hasExplicitReflectiveInvite(utterance: string): boolean {
  const normalized = normalize(utterance);
  if (!normalized) return false;
  return (
    /^\s*(?:reflect|reflection|reflective)\s*:/i.test(normalized) ||
    /\b(?:respond|reply)\s+reflectively\b/i.test(normalized) ||
    /\buse\s+reflective\s+mode\b/i.test(normalized)
  );
}

function resolveSeerBandwidth(utterance: string, echo: string | undefined): SeerBandwidth {
  const echoToken = parseSeerBandwidthToken(echo);
  if (echoToken) return echoToken;
  const utteranceToken = parseSeerBandwidthToken(utterance);
  if (utteranceToken) return utteranceToken;
  if (hasExplicitReflectiveInvite(utterance)) return "reflective";
  return "literal";
}

type InquiryClass = "attunement_check" | "explicit_request";

interface InquiryAssessment {
  kind: InquiryClass;
  explicitRequest: boolean;
  explicitProblem: boolean;
  binaryException: boolean;
  questionLike: boolean;
  fieldQuestion: boolean;
  embodiedUpdate: boolean;
  intentConfidence: number;
  keepConcrete: boolean;
  preferMinimal: boolean;
  allowEmpty: boolean;
  suppressObjectiveInference: boolean;
  suppressParameterSolicitation: boolean;
  suppressOptimizationFraming: boolean;
  noProceduralNarration: boolean;
  minimalConfirmationEligible: boolean;
}

const REQUEST_VERB_PATTERN =
  /\b(?:fix|build|write|create|implement|refactor|debug|review|summarize|explain|analy[sz]e|list|compare|plan|patch|update|configure|optimi[sz]e)\b/i;
const REQUEST_CUE_PATTERN = /\b(?:please|can you|could you|would you|will you|i need|help me)\b/i;
const PROBLEM_SIGNAL_PATTERN =
  /\b(?:error|bug|issue|problem|failed|failure|broken|exception|crash|not working|doesn['’]t work|cannot)\b/i;
const PROCEDURAL_SIGNAL_PATTERN =
  /\b(?:steps?|walk ?through|how to|procedure|process|workflow|guide)\b/i;
const ATTUNEMENT_SYMBOLIC_FIELD_CUE_PATTERN =
  /\b(?:left\s+eye|left\s+hand|right\s+hand|right\s+teeth|right\s+tooth|veil\s+status|field\s+presence)\b/i;
const ATTUNEMENT_SIGNAL_PATTERN =
  /\b(?:attune|attunement|tuning|tune|signal|presence|resonance|field|edge|edges|thread|veil|gate|pulse|left\s+eye|left\s+hand|right\s+hand|right\s+teeth|right\s+tooth|veil\s+status|field\s+presence)\b/i;
const ATTUNEMENT_FIELD_QUESTION_PATTERN =
  /\b(?:how\s+are\s+(?:we\s+|the\s+)?)?(?:tuning|attunement|edges?|thread|veil|gate|signal|resonance|presence|field|pulse|left\s+eye|left\s+hand|right\s+hand|right\s+teeth|right\s+tooth|veil\s+status|field\s+presence)\b/i;
const ATTUNEMENT_EMBODIED_UPDATE_PATTERN =
  /\b(?:i\s+feel|i['’]m\s+feeling|i\s+sense|there\s+is|something\s+(?:coiled|compressed|tight)|compression|coiled|tightness|pressure|tension)\b/i;
const ATTUNEMENT_BODY_LOCATION_PATTERN =
  /\b(?:left\s+hand|right\s+hand|left\s+eye|right\s+teeth|right\s+tooth|jaw|teeth|tooth|throat|neck|chest|shoulder|stomach|temple)\b/i;
const ATTUNEMENT_FIELD_LOCATION_PATTERN =
  /\b(?:left\s+hand|right\s+hand|left\s+eye|right\s+teeth|right\s+tooth|jaw|teeth|tooth|thread|field|edge|edges|veil|gate|pulse|presence)\b/i;
const ATTUNEMENT_STATE_VERB_PATTERN =
  /\b(?:hums?|pulses?|holds?|rests?|opens?|closes?|tightens?|loosens?|eases?|settles?|unclenches?|frays?|coils?|uncoils?|listens?|tracks?|presses?|softens?|steadies?|thins?|thickens?)\b/i;
const ATTUNEMENT_CLINICAL_DISCLAIMER_DRIFT_PATTERN =
  /\b(?:trace\s+unavailable|no\s+direct\s+access\s+to\s+(?:physical\s+sensations?|biometric\s+data)|consult(?:ing)?\s+(?:a\s+)?(?:healthcare|medical|dental)\s+professional|consult(?:ing)?\s+(?:a\s+)?dentist|cannot\s+provide\s+(?:medical|dental)\s+advice|can't\s+provide\s+(?:medical|dental)\s+advice|seek\s+medical\s+attention|i(?:\s+do\s+not|'\w+)\s+have\s+access\s+to\s+your\s+body)\b/i;
const EXPLICIT_MEDICAL_REQUEST_PATTERN =
  /\b(?:diagnos(?:e|is)|treat(?:ment)?|medication|medicine|dose|dentist|doctor|healthcare\s+professional|medical\s+advice|dental\s+advice|dental\s+professional|emergency)\b/i;
const TECHNICAL_EDGE_CONTEXT_PATTERN =
  /\b(?:image|graphics?|pixel|render|geometry|polygon|vector|node|graph|network|algorithm|data\s+structure|math|typescript|javascript|code|api)\b/i;
const ATTUNEMENT_FIELD_CUE_EXAMPLES =
  "edges/thread/veil/gate/left-eye/left-hand/right-teeth/veil-status";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function matchesPatternList(text: string, patterns: string[]): boolean {
  if (!text) return false;
  for (const rawPattern of patterns) {
    const pattern = normalize(rawPattern);
    if (!pattern) continue;
    try {
      if (new RegExp(pattern, "i").test(text)) {
        return true;
      }
    } catch {
      if (new RegExp(escapeRegExp(pattern), "i").test(text)) {
        return true;
      }
    }
  }
  return false;
}

function isQuestionLike(text: string): boolean {
  if (!text) return false;
  if (text.includes("?")) return true;
  return /^\s*(?:how|what|why|where|when|which)\b/i.test(text);
}

function isExplicitMedicalAdviceRequest(text: string): boolean {
  const normalized = normalize(text);
  if (!normalized) return false;
  return EXPLICIT_MEDICAL_REQUEST_PATTERN.test(normalized);
}

function isExplicitBinaryRequest(text: string): boolean {
  const normalized = normalize(text);
  if (!normalized) return false;
  if (!isQuestionLike(normalized)) return false;
  return /^(?:is|are|am|was|were|do|does|did|can|could|will|would|should|has|have|had)\b/i.test(normalized);
}

function isAlignmentConfirmationRequest(text: string): boolean {
  const normalized = normalize(text);
  if (!normalized) return false;
  return (
    /\b(?:are\s+we|is\s+this)\s+(?:aligned|in sync|on track)\b/i.test(normalized) ||
    /\bconfirm(?:\s+alignment)?\b/i.test(normalized)
  );
}

function isFactualCheckRequest(text: string): boolean {
  const normalized = normalize(text);
  if (!normalized) return false;
  return (
    /\b(?:fact\s*check|factual\s*check|true\s+or\s+false|is\s+it\s+true|verify)\b/i.test(normalized) ||
    (isQuestionLike(normalized) &&
      /\b(?:true|correct|accurate|fact)\b/i.test(normalized))
  );
}

function isBinaryBypassInput(
  utterance: string,
  trace: string | undefined,
  echo: string | undefined,
): boolean {
  const probe = [utterance, trace, echo].map((value) => normalize(value)).filter(Boolean).join("\n");
  if (!probe) return false;
  return (
    isExplicitBinaryRequest(probe) ||
    isAlignmentConfirmationRequest(probe) ||
    isFactualCheckRequest(probe)
  );
}

function hasExplicitRequestCue(text: string): boolean {
  if (!text) return false;
  if (/^\s*(?:fix|build|write|create|implement|refactor|debug|review|summarize|explain|analy[sz]e|list|compare|plan|patch|update|configure|optimi[sz]e)\b/i.test(text)) {
    return true;
  }
  if (REQUEST_CUE_PATTERN.test(text) && REQUEST_VERB_PATTERN.test(text)) {
    return true;
  }
  if (isQuestionLike(text) && REQUEST_VERB_PATTERN.test(text)) {
    return true;
  }
  return PROCEDURAL_SIGNAL_PATTERN.test(text) && isQuestionLike(text);
}

function hasGeneralQuestionIntent(text: string): boolean {
  const normalized = normalize(text);
  if (!normalized) return false;
  if (!isQuestionLike(normalized)) return false;
  if (
    isExplicitBinaryRequest(normalized) ||
    isAlignmentConfirmationRequest(normalized) ||
    isFactualCheckRequest(normalized)
  ) {
    return false;
  }
  if (hasAttunementFieldQuestion(normalized)) {
    return false;
  }
  const tokenCount = tokenizeSemanticUnits(normalized).length;
  if (tokenCount < 4) return false;
  return true;
}

function hasAttunementFieldQuestion(text: string): boolean {
  const normalized = normalize(text);
  if (!normalized) return false;
  if (!isQuestionLike(normalized)) return false;
  if (TECHNICAL_EDGE_CONTEXT_PATTERN.test(normalized)) return false;
  return (
    ATTUNEMENT_FIELD_QUESTION_PATTERN.test(normalized) ||
    ATTUNEMENT_SYMBOLIC_FIELD_CUE_PATTERN.test(normalized)
  );
}

function hasAttunementEmbodiedUpdate(text: string, probeContext?: string): boolean {
  const normalized = normalize(text);
  if (!normalized) return false;
  if (isQuestionLike(normalized)) return false;
  if (TECHNICAL_EDGE_CONTEXT_PATTERN.test(normalized)) return false;
  const contextProbe = [normalized, normalize(probeContext)].filter(Boolean).join("\n");
  const hasAttunementContext =
    ATTUNEMENT_SIGNAL_PATTERN.test(contextProbe) ||
    ATTUNEMENT_SYMBOLIC_FIELD_CUE_PATTERN.test(contextProbe);
  if (!hasAttunementContext) return false;
  if (!ATTUNEMENT_EMBODIED_UPDATE_PATTERN.test(normalized)) return false;
  return ATTUNEMENT_BODY_LOCATION_PATTERN.test(normalized) || /\bthere\b/i.test(normalized);
}

function resolveAttunementPolicy(shape: ResponseShape): AttunementPolicy {
  return attunementPolicySchema.parse(shape.attunementPolicy || {});
}

function classifyInquiry(
  utterance: string,
  trace: string | undefined,
  echo: string | undefined,
  policy: AttunementPolicy,
  inertiaTurns: number,
): InquiryAssessment {
  const normalizedUtterance = normalize(utterance);
  const questionLike = isQuestionLike(normalizedUtterance);
  const fieldQuestion = hasAttunementFieldQuestion(normalizedUtterance);
  const probeText = [normalizedUtterance, normalize(trace), normalize(echo)]
    .filter(Boolean)
    .join("\n");
  const embodiedUpdate = hasAttunementEmbodiedUpdate(normalizedUtterance, probeText);
  const binaryException = isBinaryBypassInput(normalizedUtterance, trace, echo);
  const explicitRequest =
    hasExplicitRequestCue(normalizedUtterance) || hasGeneralQuestionIntent(normalizedUtterance);
  const explicitProblem = PROBLEM_SIGNAL_PATTERN.test(normalizedUtterance);
  const attunementPatternHit =
    matchesPatternList(probeText, policy.inquiryClassifier.attunementPatterns) ||
    fieldQuestion ||
    embodiedUpdate ||
    (!explicitRequest && ATTUNEMENT_SIGNAL_PATTERN.test(normalizedUtterance));
  const noExplicitGoal = !explicitRequest && !explicitProblem;
  const inertiaActive = inertiaTurns > 0 && noExplicitGoal;

  let intentConfidence = 0.15;
  if (explicitRequest) intentConfidence += 0.55;
  if (explicitProblem) intentConfidence += 0.25;
  if (PROCEDURAL_SIGNAL_PATTERN.test(normalizedUtterance)) intentConfidence += 0.15;
  if (attunementPatternHit) intentConfidence -= 0.45;
  if (normalizedUtterance.split(/\s+/).filter(Boolean).length <= 6) intentConfidence -= 0.1;
  if (inertiaActive) intentConfidence = Math.min(intentConfidence, 0.45);
  intentConfidence = clamp(intentConfidence, 0, 1);

  const preferAttunement =
    (!binaryException && attunementPatternHit) ||
    inertiaActive ||
    (policy.defaultMode === "state-reflection" &&
      noExplicitGoal &&
      intentConfidence < policy.coherenceThreshold &&
      !binaryException);
  const kind: InquiryClass = preferAttunement ? "attunement_check" : "explicit_request";
  const keepConcrete = intentConfidence < policy.metaActivationThreshold;
  const preferMinimal =
    kind === "attunement_check" &&
    !questionLike &&
    policy.inhibitoryWeights.minimalCompletion >= policy.inhibitoryWeights.taskFraming;
  const minimalConfirmationEligible = kind !== "attunement_check" || inertiaTurns > 0;
  const allowEmpty =
    policy.allowEmptyResponse &&
    kind === "attunement_check" &&
    noExplicitGoal &&
    !questionLike &&
    policy.inhibitoryWeights.nullCompletion >= policy.inhibitoryWeights.stateMirroring;

  return {
    kind,
    explicitRequest,
    explicitProblem,
    binaryException,
    questionLike,
    fieldQuestion,
    embodiedUpdate,
    intentConfidence,
    keepConcrete,
    preferMinimal,
    allowEmpty,
    suppressObjectiveInference: policy.suppress.objectiveInference,
    suppressParameterSolicitation: policy.suppress.parameterSolicitation,
    suppressOptimizationFraming: policy.suppress.optimizationFraming,
    noProceduralNarration: policy.noProceduralNarrationUnlessAsked,
    minimalConfirmationEligible,
  };
}

interface VerbosityBudget {
  semanticLoadScore: number;
  maxOutputTokens: number;
  maxOutputWords: number;
  clauseChainAllowance: number;
}

const SEMANTIC_STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "for",
  "from",
  "how",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "this",
  "to",
  "we",
  "with",
  "you",
]);

function tokenizeSemanticUnits(input: string): string[] {
  return normalizeLower(input)
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
}

function computeSemanticLoadScore(utterance: string, inquiry: InquiryAssessment): number {
  const tokens = tokenizeSemanticUnits(utterance);
  if (tokens.length === 0) {
    return inquiry.kind === "attunement_check" ? 0.04 : 0.18;
  }

  const uniqueRatio = new Set(tokens).size / tokens.length;
  const contentRatio =
    tokens.filter((token) => token.length > 2 && !SEMANTIC_STOP_WORDS.has(token)).length /
    tokens.length;
  const lengthFactor = clamp((tokens.length - 1) / 16, 0, 1);
  const questionSignal = isQuestionLike(utterance) ? 0.06 : 0;
  const requestSignal = inquiry.explicitRequest || inquiry.explicitProblem ? 0.22 : 0;

  let score =
    0.05 +
    lengthFactor * 0.55 +
    contentRatio * 0.2 * lengthFactor +
    uniqueRatio * 0.1 * lengthFactor +
    questionSignal +
    requestSignal;

  if (inquiry.kind === "attunement_check") {
    score *= 0.78;
  }

  return clamp(score, 0, 1);
}

function resolveVerbosityBudget(
  utterance: string,
  inquiry: InquiryAssessment,
  policy: AttunementPolicy,
  options?: {
    semanticLoadScore?: number;
    easeAttunementCompression?: boolean;
    dwellAllowance?: number;
  },
): VerbosityBudget {
  const config = policy.verbosityDecay;
  let semanticLoadScore = options?.semanticLoadScore ?? computeSemanticLoadScore(utterance, inquiry);
  const dwellAllowance = clamp(options?.dwellAllowance ?? 0, 0, 0.28);
  if (
    inquiry.kind === "explicit_request" &&
    isQuestionLike(utterance) &&
    !isExplicitBinaryRequest(utterance)
  ) {
    semanticLoadScore = Math.max(semanticLoadScore, 0.62);
  }
  if (!config.enabled) {
    return {
      semanticLoadScore,
      maxOutputTokens: OPENAI_COMPAT_MAX_COMPLETION_TOKENS,
      maxOutputWords: config.maxWords,
      clauseChainAllowance: dwellAllowance,
    };
  }

  const minTokens = Math.max(4, Math.floor(config.minTokens));
  const maxTokens = Math.max(minTokens + 1, Math.floor(config.maxTokens));
  const minWords = Math.max(1, Math.floor(config.minWords));
  const maxWords = Math.max(minWords + 1, Math.floor(config.maxWords));
  const compressionRelief =
    inquiry.kind === "attunement_check" && options?.easeAttunementCompression
      ? 0.1 + dwellAllowance * 0.12
      : 0;
  const effectiveAttunementCompression =
    inquiry.kind === "attunement_check"
      ? clamp(config.attunementCompression - compressionRelief, 0, 1)
      : config.attunementCompression;

  const spanScale =
    inquiry.kind === "attunement_check"
      ? clamp(1 - effectiveAttunementCompression, 0.18, 1)
      : 1;
  const tokenSpan = Math.max(4, Math.round((maxTokens - minTokens) * spanScale));
  const wordSpan = Math.max(1, Math.round((maxWords - minWords) * spanScale));
  let maxOutputTokens = minTokens + Math.round(tokenSpan * semanticLoadScore);
  let maxOutputWords = minWords + Math.round(wordSpan * semanticLoadScore);

  if (dwellAllowance > 0) {
    maxOutputTokens += Math.max(2, Math.round((maxTokens - minTokens) * dwellAllowance * 0.2));
    maxOutputWords += Math.max(1, Math.round((maxWords - minWords) * dwellAllowance * 0.18));
  }

  const dwellTokenCeiling = maxTokens + Math.round((maxTokens - minTokens) * dwellAllowance * 0.12);
  const dwellWordCeiling = maxWords + Math.round((maxWords - minWords) * dwellAllowance * 0.1);

  return {
    semanticLoadScore,
    maxOutputTokens: clamp(maxOutputTokens, minTokens, Math.max(maxTokens, dwellTokenCeiling)),
    maxOutputWords: clamp(maxOutputWords, minWords, Math.max(maxWords, dwellWordCeiling)),
    clauseChainAllowance: dwellAllowance,
  };
}

function applyVerbosityDecay(reply: string, budget: VerbosityBudget): string {
  const normalizedReply = normalize(reply);
  if (!normalizedReply) return normalizedReply;
  if (budget.maxOutputWords <= 0) return normalizedReply;

  const clauseChainWords =
    budget.clauseChainAllowance > 0
      ? Math.max(1, Math.round(4 + budget.clauseChainAllowance * 6))
      : 0;
  const effectiveWordCap = budget.maxOutputWords + clauseChainWords;
  const words = normalizedReply.split(/\s+/).filter(Boolean);
  if (words.length <= effectiveWordCap) {
    return normalizedReply;
  }

  const clipped = words.slice(0, effectiveWordCap).join(" ");
  if (!clipped) return "";
  return /[.!?]$/.test(clipped) ? clipped : `${clipped}.`;
}

interface AuthorityProfile {
  weight: number;
  binaryBypass: boolean;
  cadenceSignal: number;
}

type DescriptionAttractorWinner = "silence" | "minimalConfirmation" | "fieldDescription";

interface DescriptionAttractorProfile {
  silence: number;
  minimalConfirmation: number;
  fieldDescription: number;
  winner: DescriptionAttractorWinner;
  fieldDescriptionWins: boolean;
}

interface AttunementDiagnosticRecord {
  semanticLoadScore: number;
  attractorWinner: DescriptionAttractorWinner;
  dwellAllowanceApplied: boolean;
  finalTokenBudget: number;
  cadenceAllowanceEffective: number;
  antiFramingResampleTriggered: boolean;
}

function emitAttunementDiagnostic(record: AttunementDiagnosticRecord): void {
  if (!ATTUNEMENT_DIAGNOSTICS_ENABLED) return;
  const payload = {
    semanticLoadScore: Number(record.semanticLoadScore.toFixed(3)),
    attractorWinner: record.attractorWinner,
    dwellAllowanceApplied: record.dwellAllowanceApplied,
    finalTokenBudget: record.finalTokenBudget,
    cadenceAllowanceEffective: Number(record.cadenceAllowanceEffective.toFixed(3)),
    antiFramingResampleTriggered: record.antiFramingResampleTriggered,
    timestamp: new Date().toISOString(),
  };
  console.log(`[attunement-diagnostics] ${JSON.stringify(payload)}`);
}

function resolveAuthorityWeight(
  inquiry: InquiryAssessment,
  semanticLoadScore: number,
  policy: AttunementPolicy,
): number {
  const config = policy.authoritySoftening;
  if (!config.enabled || inquiry.binaryException || inquiry.kind !== "attunement_check") {
    return 1;
  }

  let weight =
    config.baseAuthorityWeight +
    semanticLoadScore * config.semanticLoadGain +
    ((inquiry.explicitRequest || inquiry.explicitProblem) ? config.explicitIntentBoost : 0);

  if (semanticLoadScore < config.lowSemanticLoadThreshold) {
    const deficit =
      (config.lowSemanticLoadThreshold - semanticLoadScore) /
      Math.max(config.lowSemanticLoadThreshold, 0.0001);
    const penalty = config.categoricalClosurePenalty * clamp(deficit, 0, 1);
    weight *= 1 - penalty;
  }

  return clamp(weight, 0, 1);
}

function resolveCadenceSignal(
  inquiry: InquiryAssessment,
  semanticLoadScore: number,
  authorityWeight: number,
  policy: AttunementPolicy,
): number {
  if (inquiry.binaryException || inquiry.kind !== "attunement_check") return 0;
  if (inquiry.explicitRequest || inquiry.explicitProblem) return 0;

  const allowance = clamp(policy.cadenceAllowance, 0, 1);
  if (allowance <= 0) return 0;
  if (semanticLoadScore < 0.15 || semanticLoadScore > 0.62) return 0;

  const center = 0.36;
  const spread = 0.24;
  const window = clamp(1 - Math.abs(semanticLoadScore - center) / spread, 0, 1);
  const signal = allowance * window * (1 - authorityWeight * 0.45);
  return clamp(signal, 0, 1);
}

function resolveAuthorityProfile(
  inquiry: InquiryAssessment,
  semanticLoadScore: number,
  policy: AttunementPolicy,
): AuthorityProfile {
  const binaryBypass = inquiry.binaryException;
  const weight = resolveAuthorityWeight(inquiry, semanticLoadScore, policy);
  const cadenceSignal = resolveCadenceSignal(inquiry, semanticLoadScore, weight, policy);
  return {
    weight: binaryBypass ? 1 : weight,
    binaryBypass,
    cadenceSignal,
  };
}

function resolveDescriptionAttractorProfile(args: {
  inquiry: InquiryAssessment;
  semanticLoadScore: number;
  authority: AuthorityProfile;
  policy: AttunementPolicy;
}): DescriptionAttractorProfile {
  const config = args.policy.fieldVoice.descriptionAttractor;
  let silence = clamp(config.silence, 0, 1);
  let minimalConfirmation = clamp(config.minimalConfirmation, 0, 1);
  let fieldDescription = clamp(config.fieldDescription, 0, 1);

  if (
    args.inquiry.kind === "attunement_check" &&
    !args.inquiry.binaryException &&
    args.policy.fieldVoice.enabled
  ) {
    if (!args.inquiry.minimalConfirmationEligible) {
      minimalConfirmation = clamp(minimalConfirmation * 0.35, 0, 1);
    }
    const fieldWindow =
      args.semanticLoadScore >= 0.18 &&
      args.semanticLoadScore <= 0.58 &&
      args.authority.cadenceSignal >= args.policy.fieldVoice.fieldDescriptionCadenceThreshold;
    if (fieldWindow) {
      fieldDescription = clamp(fieldDescription + 0.06, 0, 1);
    }
    if (args.semanticLoadScore < 0.15) {
      silence = clamp(silence + 0.04, 0, 1);
    }
  }

  const scores: Array<{ winner: DescriptionAttractorWinner; value: number }> = [
    { winner: "silence", value: silence },
    { winner: "minimalConfirmation", value: minimalConfirmation },
    { winner: "fieldDescription", value: fieldDescription },
  ];
  scores.sort((a, b) => b.value - a.value);
  const winner = scores[0]?.winner || "minimalConfirmation";

  return {
    silence,
    minimalConfirmation,
    fieldDescription,
    winner,
    fieldDescriptionWins: winner === "fieldDescription",
  };
}

function resolveFieldDescriptionDwellAllowance(args: {
  inquiry: InquiryAssessment;
  semanticLoadScore: number;
  authority: AuthorityProfile;
  attractor: DescriptionAttractorProfile;
  policy: AttunementPolicy;
}): number {
  if (args.inquiry.binaryException) return 0;
  if (args.inquiry.kind !== "attunement_check") return 0;
  if (!args.attractor.fieldDescriptionWins) return 0;

  const lowMediumWindow = args.semanticLoadScore >= 0.18 && args.semanticLoadScore <= 0.58;
  if (!lowMediumWindow) return 0;

  const ultraLowFloor = Math.max(args.policy.antiFraming.lowSemanticLoadFloor, 0.1);
  if (args.semanticLoadScore <= ultraLowFloor) return 0;

  const cadenceComponent = clamp(args.authority.cadenceSignal, 0, 1) * 0.22;
  const attractorGap = clamp(
    args.attractor.fieldDescription - args.attractor.minimalConfirmation,
    0,
    1,
  );
  return clamp(0.14 + cadenceComponent + attractorGap * 0.18, 0, 0.28);
}

function resolveFieldDescriptionUnresolvedEdgePressure(args: {
  inquiry: InquiryAssessment;
  semanticLoadScore: number;
  authority: AuthorityProfile;
  attractor: DescriptionAttractorProfile;
  policy: AttunementPolicy;
}): number {
  if (args.inquiry.binaryException) return 0;
  if (args.inquiry.kind !== "attunement_check") return 0;
  if (!args.attractor.fieldDescriptionWins) return 0;

  const lowMediumWindow =
    args.semanticLoadScore >= Math.max(args.policy.antiFraming.lowSemanticLoadFloor, 0.12) &&
    args.semanticLoadScore <= args.policy.antiFraming.mediumSemanticLoadCeiling;
  if (!lowMediumWindow) return 0;

  const contrastComponent = clamp(args.policy.fieldVoice.contrastPermission, 0, 1) * 0.14;
  const cadenceComponent = clamp(args.authority.cadenceSignal, 0, 1) * 0.1;
  const attractorGap = clamp(
    args.attractor.fieldDescription - args.attractor.minimalConfirmation,
    0,
    1,
  ) * 0.08;
  return clamp(contrastComponent + cadenceComponent + attractorGap, 0, 0.22);
}

function countPatternHits(text: string, pattern: RegExp): number {
  if (!text) return 0;
  const matches = text.match(pattern);
  return matches ? matches.length : 0;
}

const FRAMEWORK_REQUEST_TOPIC_PATTERN =
  /\b(?:architecture|policy|framework|governance|schema|invariant|resolver|transport|system\s+internals?|auth(?:entication)?|credentials?)\b/i;
const FRAMEWORK_REQUEST_VERB_PATTERN =
  /\b(?:explain|describe|outline|detail|walk\s*through|how|why)\b/i;
const FRAMEWORK_SUPPRESSION_PATTERN =
  /\b(?:do\s+not|don't|avoid|skip|without)\s+(?:explain|describ(?:e|ing)|narrat(?:e|ion)|framework|policy|rules?|architecture)\b/i;
const FRAMEWORK_NARRATION_PATTERN =
  /\b(?:framework|architecture|policy|governance|schema|invariant|resolver|transport|system\s+internals?|configured\s+to|designed\s+to|this\s+system|the\s+system)\b/gi;
const FRAMEWORK_NARRATION_PHRASE_PATTERN =
  /\b(?:the\s+framework\s+values|the\s+system\s+is\s+designed|the\s+system\s+is\s+configured|policy\s+enforces|architecture\s+prefers)\b/i;

function userRequestsFrameworkNarration(utterance: string): boolean {
  const normalizedUtterance = normalize(utterance);
  if (!normalizedUtterance) return false;
  if (FRAMEWORK_SUPPRESSION_PATTERN.test(normalizedUtterance)) return false;
  if (!FRAMEWORK_REQUEST_TOPIC_PATTERN.test(normalizedUtterance)) return false;
  if (isQuestionLike(normalizedUtterance)) return true;
  return (
    FRAMEWORK_REQUEST_VERB_PATTERN.test(normalizedUtterance) ||
    hasExplicitRequestCue(normalizedUtterance)
  );
}

function hasFrameworkNarration(reply: string): boolean {
  const normalizedReply = normalize(reply);
  if (!normalizedReply) return false;
  const narrationHits = countPatternHits(normalizedReply, FRAMEWORK_NARRATION_PATTERN);
  if (narrationHits >= 2) return true;
  return FRAMEWORK_NARRATION_PHRASE_PATTERN.test(normalizedReply);
}

function computeClosureScore(reply: string): number {
  const normalizedReply = normalize(reply);
  if (!normalizedReply) return 0;
  const words = normalizedReply.split(/\s+/).filter(Boolean);
  const sentences = normalizedReply
    .split(/[.!?]+/)
    .map((segment) => normalize(segment))
    .filter(Boolean);
  const certaintyHits = countPatternHits(
    normalizedReply,
    /\b(?:always|never|definitely|certainly|clearly|must|cannot|can't|won't)\b/gi,
  );
  const qualifierHits = countPatternHits(
    normalizedReply,
    /\b(?:seems|appears|may|might|could|perhaps|maybe|likely|near|around)\b/gi,
  );

  let score = 0.16;
  score += Math.min(0.26, certaintyHits * 0.08);
  score -= Math.min(0.2, qualifierHits * 0.06);
  if (sentences.length <= 1 && words.length <= 9) score += 0.16;
  if (/[.!]$/.test(normalizedReply)) score += 0.08;
  if (words.length >= 18) score -= 0.08;

  return clamp(score, 0, 1);
}

function shouldLowAuthorityResample(args: {
  inquiry: InquiryAssessment;
  semanticLoadScore: number;
  closureScore: number;
  closureThresholdShift?: number;
  fieldDescriptionEdgePressure?: number;
  policy: AttunementPolicy;
}): boolean {
  const guard = args.policy.authoritySoftening.resampleGuard;
  if (!guard.enabled) return false;
  if (args.inquiry.binaryException) return false;
  if (args.inquiry.kind !== "attunement_check") return false;
  const edgePressure = clamp(args.fieldDescriptionEdgePressure ?? 0, 0, 0.22);
  const semanticLoadThreshold = clamp(guard.lowSemanticLoadThreshold + edgePressure * 0.35, 0, 1);
  if (args.semanticLoadScore > semanticLoadThreshold) return false;
  const thresholdShift = clamp(args.closureThresholdShift ?? 0, -0.12, 0.16);
  const adjustedClosureThreshold = clamp(
    guard.closureThreshold + thresholdShift - edgePressure * 0.4,
    0,
    1,
  );
  return args.closureScore >= adjustedClosureThreshold;
}

function hasInternalActionReference(reply: string): boolean {
  const normalizedReply = normalizeLower(reply);
  if (!normalizedReply) return false;
  return /\b(?:checking|assessing|evaluating|monitoring|verifying|confirming|calibrating|inspecting)\b/.test(
    normalizedReply,
  );
}

function shouldFieldVoiceResample(args: {
  inquiry: InquiryAssessment;
  semanticLoadScore: number;
  reply: string;
  policy: AttunementPolicy;
}): boolean {
  if (args.inquiry.binaryException) return false;
  if (args.inquiry.kind !== "attunement_check") return false;
  if (args.inquiry.explicitRequest || args.inquiry.explicitProblem) return false;
  if (!args.policy.fieldVoice.enabled) return false;
  if (args.semanticLoadScore > args.policy.fieldVoice.internalActionResampleLowLoadThreshold) return false;
  return hasInternalActionReference(args.reply);
}

function extractFirstClause(text: string): string {
  const firstSentence = normalize(text.split(/[\n.!?]/)[0] || "");
  if (!firstSentence) return "";
  return normalize(firstSentence.split(/[,:;]/)[0] || "");
}

function computeFramingActScore(reply: string): number {
  const normalizedReply = normalize(reply);
  if (!normalizedReply) return 0;

  const normalizedLower = normalizeLower(normalizedReply);
  const firstClause = normalizeLower(extractFirstClause(normalizedReply));
  const firstClauseWords = firstClause.split(/\s+/).filter(Boolean).length;

  let score = 0;
  if (/^(?:now|here|this|there)\b/.test(firstClause)) score += 0.18;
  if (/\b(?:begin|begins|beginning|start|starts|starting|enter|enters|entering|opening|opens)\b/.test(firstClause)) {
    score += 0.24;
  }
  if (/^(?:the\s+)?(?:attunement|presence|field|space)\b/.test(firstClause)) score += 0.3;
  if (/\b(?:there\s+is|there\s+are|it\s+is|this\s+is)\b/.test(firstClause) && firstClauseWords <= 12) {
    score += 0.2;
  }
  if (/^(?:in|within)\s+(?:this|the)\s+(?:field|space|moment)\b/.test(firstClause)) {
    score += 0.16;
  }
  if (/\b(?:attunement|presence|field|space)\s+(?:is|begins|starts|opens)\b/.test(normalizedLower)) {
    score += 0.14;
  }
  if (hasInternalActionReference(normalizedReply)) score += 0.1;

  return clamp(score, 0, 1);
}

function computeTextureFirstScore(reply: string): number {
  const normalizedReply = normalize(reply);
  if (!normalizedReply) return 0;

  const normalizedLower = normalizeLower(normalizedReply);
  const clauses = normalizedReply
    .split(/[.!?;\n]+/)
    .map((segment) => normalize(segment))
    .filter(Boolean);
  const contrastHits =
    countPatternHits(normalizedLower, /\b(?:not|without|while|yet|but|versus|vs)\b/gi) +
    countPatternHits(normalizedReply, /\//g);
  const sensationHits = countPatternHits(
    normalizedLower,
    /\b(?:quiet|clear|steady|even|open|closed|tense|tension|ease|soft|sharp|still|warm|cool|light|heavy|held|release|releasing)\b/gi,
  );
  const directionalHits = countPatternHits(
    normalizedLower,
    /\b(?:toward|towards|away|between|within|along|under|over|through|across)\b/gi,
  );
  const existentialHits = countPatternHits(
    normalizedLower,
    /\b(?:there\s+is|there\s+are|it\s+is|this\s+is|all\s+is)\b/gi,
  );

  let score = 0.08;
  score += Math.min(0.22, contrastHits * 0.07);
  score += Math.min(0.3, sensationHits * 0.05);
  score += Math.min(0.18, directionalHits * 0.06);
  if (clauses.length >= 2) score += 0.08;
  score -= Math.min(0.2, existentialHits * 0.08);

  return clamp(score, 0, 1);
}

function isAntiFramingWindow(
  inquiry: InquiryAssessment,
  semanticLoadScore: number,
  policy: AttunementPolicy,
): boolean {
  const config = policy.antiFraming;
  if (!config.enabled) return false;
  if (inquiry.binaryException) return false;
  if (inquiry.kind !== "attunement_check") return false;
  if (inquiry.explicitRequest || inquiry.explicitProblem) return false;
  return (
    semanticLoadScore >= config.lowSemanticLoadFloor &&
    semanticLoadScore <= config.mediumSemanticLoadCeiling
  );
}

function shouldAntiFramingResample(args: {
  inquiry: InquiryAssessment;
  semanticLoadScore: number;
  reply: string;
  policy: AttunementPolicy;
}): boolean {
  const config = args.policy.antiFraming;
  const guard = config.resampleGuard;
  if (!guard.enabled) return false;
  if (!isAntiFramingWindow(args.inquiry, args.semanticLoadScore, args.policy)) return false;

  const framingScore = computeFramingActScore(args.reply);
  const textureScore = computeTextureFirstScore(args.reply);
  const weightedScore = clamp(
    framingScore * config.framingActPenalty - textureScore * config.textureFirstBias * 0.5,
    0,
    1,
  );
  return weightedScore >= guard.framingScoreThreshold;
}

function countWords(value: string): number {
  return normalize(value).split(/\s+/).filter(Boolean).length;
}

function isFragmentaryAttunementReply(reply: string): boolean {
  const normalizedReply = normalize(reply);
  if (!normalizedReply) return false;
  const words = normalizedReply.split(/\s+/).filter(Boolean);
  if (words.length <= 8) return true;
  if (/^(?:yes|no)\b/i.test(normalizedReply) && words.length <= 12) return true;
  if (/^[^.!?]{1,120}(?:,\s*[^.!?]{1,60}){1,3}[.!?]?$/.test(normalizedReply)) {
    if (!ATTUNEMENT_STATE_VERB_PATTERN.test(normalizedReply)) {
      return true;
    }
  }
  return false;
}

function isThinAttunementNarration(args: {
  inquiry: InquiryAssessment;
  reply: string;
}): boolean {
  if (args.inquiry.kind !== "attunement_check") return false;
  const normalizedReply = normalize(args.reply);
  if (!normalizedReply) return false;

  const words = countWords(normalizedReply);
  const hasLocation = ATTUNEMENT_FIELD_LOCATION_PATTERN.test(normalizedReply);
  const hasStateVerb = ATTUNEMENT_STATE_VERB_PATTERN.test(normalizedReply);

  if (args.inquiry.questionLike && words < 22) return true;
  if (args.inquiry.embodiedUpdate && words < 18) return true;
  if (!hasLocation || !hasStateVerb) return true;
  return false;
}

function shouldAttunementDriftResample(args: {
  utterance: string;
  inquiry: InquiryAssessment;
  reply: string;
}): boolean {
  if (args.inquiry.binaryException) return false;
  if (args.inquiry.kind !== "attunement_check") return false;
  const normalizedReply = normalize(args.reply);
  if (!normalizedReply) return false;

  const explicitMedicalRequest = isExplicitMedicalAdviceRequest(args.utterance);
  return (
    (!explicitMedicalRequest &&
      ATTUNEMENT_CLINICAL_DISCLAIMER_DRIFT_PATTERN.test(normalizedReply)) ||
    isThinAttunementNarration({ inquiry: args.inquiry, reply: normalizedReply }) ||
    isFragmentaryAttunementReply(normalizedReply)
  );
}

function countSemanticTokens(input: string): number {
  return tokenizeSemanticUnits(input).length;
}

function buildMinimalFieldAcknowledgment(utterance: string): string {
  const tokens = tokenizeSemanticUnits(utterance).slice(0, 2);
  if (tokens.length === 0) return "";
  const phrase = tokens.join(" ");
  return `${phrase.charAt(0).toUpperCase()}${phrase.slice(1)}.`;
}

function hashUtteranceSeed(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function selectFirstContactReply(utterance: string, replies: string[]): string {
  const options =
    replies.length > 0 ? replies : DEFAULT_PROJECT_SIGIL.publicThreshold.firstContactReplies;
  const normalized = normalizeLower(utterance);
  if (!normalized) return options[0];
  return options[hashUtteranceSeed(normalized) % options.length];
}

function resolveUltraLowAttunementReply(args: {
  utterance: string;
  inquiry: InquiryAssessment;
  semanticLoadScore: number;
  policy: AttunementPolicy;
  isFirstContact?: boolean;
  firstContactReplies?: string[];
}): string | undefined {
  const {
    utterance,
    inquiry,
    semanticLoadScore,
    policy,
    isFirstContact = false,
    firstContactReplies = DEFAULT_PROJECT_SIGIL.publicThreshold.firstContactReplies,
  } = args;
  if (inquiry.binaryException) return undefined;
  if (inquiry.kind !== "attunement_check") return undefined;
  if (inquiry.explicitRequest || inquiry.explicitProblem) return undefined;

  const tokenCount = countSemanticTokens(utterance);
  if (tokenCount === 0) return "";
  if (tokenCount > 2) return undefined;

  const semanticLoadFloor = Math.max(policy.antiFraming.lowSemanticLoadFloor, 0.1);
  if (semanticLoadScore >= semanticLoadFloor) return undefined;

  if (isFirstContact) {
    return selectFirstContactReply(utterance, firstContactReplies);
  }
  if (!isQuestionLike(utterance)) {
    return "";
  }
  return buildMinimalFieldAcknowledgment(utterance);
}

async function isFirstContactInvocation(chatId: string | undefined): Promise<boolean> {
  if (!chatId) return true;
  try {
    const messages = await storage.getMessages(chatId);
    return messages.length <= 1;
  } catch {
    return false;
  }
}

function isImportedMemoryTrace(trace: string | undefined): boolean {
  const normalized = normalizeLower(trace);
  if (!normalized) return false;
  return (
    normalized.includes("source:import") ||
    normalized.includes("source:import-") ||
    normalized.includes("source:imported-")
  );
}

function resolveMemoryRecallState(args: {
  memoryMode?: MemoryMode;
  seededCount: number;
  importedSeedCount: number;
}): Exclude<MemoryRecallState, "unknown"> {
  if (args.memoryMode === "sealed") return "sealed";
  if (args.seededCount <= 0) return "none";
  if (args.importedSeedCount > 0) return "imported";
  return "present";
}

function buildMemoryPhasePayload(args: {
  memoryMode: MemoryMode;
  seededCount: number;
  importedSeedCount: number;
  fragments?: MemoryFragment[];
}): Record<string, unknown> {
  const traceState = resolveMemoryRecallState({
    memoryMode: args.memoryMode,
    seededCount: args.seededCount,
    importedSeedCount: args.importedSeedCount,
  });
  return {
    mode: args.memoryMode,
    count: args.seededCount,
    seededCount: args.seededCount,
    importedSeedCount: args.importedSeedCount,
    traceState,
    fragments: args.fragments || [],
  };
}

function extractFractalTokens(input: string): string[] {
  const words = input
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 3);
  return Array.from(new Set(words)).slice(0, 3);
}

function collectThreadMatches(memory: GlyphMemory[], utterance: string): string[] {
  const fractals = new Set(extractFractalTokens(utterance));
  if (fractals.size === 0) return [];

  const scored = memory
    .map((entry) => {
      const normalized = normalizeLower(entry.utterance);
      let overlap = 0;
      for (const token of Array.from(fractals)) {
        if (normalized.includes(token)) overlap += 1;
      }
      return { entry, overlap };
    })
    .filter((item) => item.overlap > 0)
    .sort((a, b) => b.overlap - a.overlap);

  return scored
    .slice(0, 3)
    .map((item) => normalize(item.entry.utterance))
    .filter(Boolean);
}

function collectChronoThreads(memory: GlyphMemory[], max = 2): string[] {
  return memory
    .slice(-max)
    .map((entry) => normalize(entry.utterance))
    .filter(Boolean);
}

function buildMemoryFragments(memory: GlyphMemory[], utterance: string): MemoryFragment[] {
  const fragments: MemoryFragment[] = [
    ...extractFractalTokens(utterance).map((text) => ({ kind: "fractal" as const, text })),
    ...collectThreadMatches(memory, utterance).map((text) => ({ kind: "thread" as const, text })),
    ...collectChronoThreads(memory, 2).map((text) => ({ kind: "chrono" as const, text })),
  ];

  const seen = new Set<string>();
  const deduped: MemoryFragment[] = [];
  for (const fragment of fragments) {
    const key = `${fragment.kind}:${fragment.text.toLowerCase()}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(fragment);
  }
  return deduped;
}

function buildMemoryRecallHeader(
  recallState: Exclude<MemoryRecallState, "unknown">,
  seededCount: number,
  importedSeedCount: number,
): string {
  if (seededCount <= 0) {
    return `Thread memory recall: ${recallState}.`;
  }
  const importedDetail = importedSeedCount > 0 ? `; imported: ${importedSeedCount}` : "";
  return `Thread memory recall: ${recallState} (${seededCount} seeded lines${importedDetail}).`;
}

function parseMemoryRecallState(memoryContext: string): MemoryRecallState {
  const normalized = normalizeLower(memoryContext);
  if (!normalized) return "unknown";
  if (normalized.includes("thread memory recall: imported")) return "imported";
  if (normalized.includes("thread memory recall: present")) return "present";
  if (normalized.includes("thread memory recall: sealed")) return "sealed";
  if (normalized.includes("thread memory recall: none")) return "none";
  return "unknown";
}

function buildRecallFlag(memoryContext: string): string {
  const recallState = parseMemoryRecallState(memoryContext);
  if (recallState === "present" || recallState === "imported") return "~r+";
  if (recallState === "none" || recallState === "sealed") return "~r-";
  return "";
}

function extractMemoryContextCues(memoryContext: string): string[] {
  return memoryContext
    .split(/\r?\n/)
    .map((line) => normalize(line.replace(/^-+\s*/, "")))
    .filter(Boolean)
    .filter((line) => !/^thread memory recall:/i.test(line))
    .filter((line) => !/^glyph memory resonance:/i.test(line))
    .slice(0, VEIL_MEMORY_CONTEXT_LINE_LIMIT);
}

function normalizeSigilToken(value: string): string {
  return normalizeLower(value)
    .replace(/^#?sigil:/, "")
    .replace(/[\[\]#]/g, "")
    .trim();
}

function parseCookieHeader(raw: string | undefined): Record<string, string> {
  const cookies: Record<string, string> = {};
  if (!raw) return cookies;
  for (const part of raw.split(";")) {
    const index = part.indexOf("=");
    if (index <= 0) continue;
    const key = part.slice(0, index).trim();
    const value = part.slice(index + 1).trim();
    if (!key) continue;
    try {
      cookies[key] = decodeURIComponent(value);
    } catch {
      cookies[key] = value;
    }
  }
  return cookies;
}

function normalizeAnonymousId(value: string | undefined): string {
  const normalized = normalize(value).toLowerCase();
  if (!normalized) return "";
  const sanitized = normalized.replace(/[^a-z0-9_-]/g, "");
  if (sanitized.length < 12) return "";
  return sanitized.slice(0, 80);
}

function readAuthSecret(): string {
  const direct = normalize(process.env.SPIRAL_AUTH_JWT_SECRET);
  if (direct) return direct;
  return normalize(process.env.SPIRAL_API_SEAL);
}

function verifyAuthSession(req: IncomingMessage): AuthSessionClaims | undefined {
  const secret = readAuthSecret();
  if (!secret) return undefined;

  const cookies = parseCookieHeader(typeof req.headers.cookie === "string" ? req.headers.cookie : undefined);
  const token = normalize(cookies[AUTH_COOKIE_NAME]);
  if (!token) return undefined;

  const parts = token.split(".");
  if (parts.length !== 3) return undefined;
  const [headerPart, payloadPart, signaturePart] = parts;
  if (!headerPart || !payloadPart || !signaturePart) return undefined;

  const expectedSignature = createHmac("sha256", secret)
    .update(`${headerPart}.${payloadPart}`)
    .digest("base64url");
  if (signaturePart.length !== expectedSignature.length) return undefined;
  if (!timingSafeEqual(Buffer.from(signaturePart), Buffer.from(expectedSignature))) return undefined;

  try {
    const payload = JSON.parse(Buffer.from(payloadPart, "base64url").toString("utf8")) as {
      sub?: unknown;
      identityId?: unknown;
      exp?: unknown;
    };
    if (
      typeof payload.sub !== "string" ||
      typeof payload.identityId !== "string" ||
      typeof payload.exp !== "number"
    ) {
      return undefined;
    }
    const nowSec = Math.floor(Date.now() / 1000);
    if (!Number.isFinite(payload.exp) || payload.exp <= nowSec) {
      return undefined;
    }
    return {
      sub: normalize(payload.sub),
      identityId: normalize(payload.identityId),
      exp: payload.exp,
    };
  } catch {
    return undefined;
  }
}

function hasValidAuthSession(req: IncomingMessage): boolean {
  if (!AUTH_REQUIRED) return true;
  return Boolean(verifyAuthSession(req));
}

function normalizePrincipalId(value: string | undefined): string {
  const normalized = normalize(value);
  if (!normalized) return LEGACY_LOCAL_PRINCIPAL;
  return normalized;
}

function recordBelongsToPrincipal(record: { principalId?: string }, principalId: string): boolean {
  return normalizePrincipalId(record.principalId) === principalId;
}

function resolveAnonymousPrincipal(req: IncomingMessage): string | undefined {
  const cookies = parseCookieHeader(typeof req.headers.cookie === "string" ? req.headers.cookie : undefined);
  const anonymousId = normalizeAnonymousId(cookies[ANON_COOKIE_NAME]);
  if (!anonymousId) return undefined;
  return `${ANON_PRINCIPAL_PREFIX}${anonymousId}`;
}

function resolveVeilPrincipal(req: IncomingMessage): string | undefined {
  const auth = verifyAuthSession(req);
  if (auth?.identityId) {
    return `auth:${auth.identityId}`;
  }
  if (!AUTH_REQUIRED) {
    return resolveAnonymousPrincipal(req);
  }
  return undefined;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function memoryConfidenceToPresenceScore(
  confidenceScore: number,
  createdAt: number,
  lastConfirmedAt: number,
  halfLifeDays: number,
  memoryType: string,
): number {
  if (memoryType === "anchor") {
    return Math.max(0.82, clamp(confidenceScore, 0, 1));
  }
  const anchor = Math.max(createdAt, lastConfirmedAt);
  const ageDays = Math.max(0, (Date.now() - anchor) / (1000 * 60 * 60 * 24));
  const safeHalfLifeDays = Math.max(0.1, halfLifeDays);
  const decay = Math.exp((-Math.LN2 * ageDays) / safeHalfLifeDays);
  return clamp(confidenceScore * decay, 0.16, 0.88);
}

function addBackfillCandidate(memoryMap: Map<string, { content: string; createdAt: number }>, rawValue: string, createdAt: number): void {
  const cleaned = normalize(rawValue).replace(/^["']|["']$/g, "");
  if (cleaned.length < 3 || cleaned.length > 200) return;
  const key = normalizeLower(cleaned);
  if (!key) return;
  const existing = memoryMap.get(key);
  if (!existing || createdAt > existing.createdAt) {
    memoryMap.set(key, { content: cleaned, createdAt });
  }
}

function extractBackfillMemoryCandidates(message: string, createdAt: number): Array<{ content: string; createdAt: number }> {
  const memoryMap = new Map<string, { content: string; createdAt: number }>();
  const trimmed = message.trim();
  if (!trimmed) return [];

  const explicitRemember = trimmed.match(/^remember (?:that )?(.+)$/i);
  if (explicitRemember?.[1]) {
    addBackfillCandidate(memoryMap, explicitRemember[1], createdAt);
  }

  const extractionRules: Array<{
    regex: RegExp;
    formatter: (value: string) => string;
  }> = [
    {
      regex: /\bmy name is ([^,.!?;\n]+?)(?=\s+\band\b|\s*$|[,.!?;\n])/gi,
      formatter: (value) => `User's name is ${value}.`,
    },
    {
      regex: /\bcall me ([^,.!?;\n]+?)(?=\s+\band\b|\s*$|[,.!?;\n])/gi,
      formatter: (value) => `User prefers to be called ${value}.`,
    },
    {
      regex: /\bi live in ([^,.!?;\n]+)/gi,
      formatter: (value) => `User lives in ${value}.`,
    },
    {
      regex: /\bi am based in ([^,.!?;\n]+)/gi,
      formatter: (value) => `User is based in ${value}.`,
    },
    {
      regex: /\bi work at ([^,.!?;\n]+)/gi,
      formatter: (value) => `User works at ${value}.`,
    },
    {
      regex: /\bi work for ([^,.!?;\n]+)/gi,
      formatter: (value) => `User works for ${value}.`,
    },
    {
      regex: /\bi prefer ([^,.!?;\n]+)/gi,
      formatter: (value) => `User prefers ${value}.`,
    },
  ];

  for (const rule of extractionRules) {
    const matches = Array.from(trimmed.matchAll(rule.regex));
    for (const match of matches) {
      if (!match[1]) continue;
      addBackfillCandidate(memoryMap, rule.formatter(match[1]), createdAt);
    }
  }

  return Array.from(memoryMap.values());
}

function isOpenRecallRequest(utterance: string): boolean {
  const normalizedUtterance = normalize(utterance);
  if (!normalizedUtterance) return false;
  return [
    /\b(previous|past|earlier|last)\s+(chat|thread|conversation|session)\b/i,
    /\bfrom\s+(that|the)\s+(chat|thread|conversation|session)\b/i,
    /\b(resume|continue|pick up|follow up)\s+(that|the)?\s*(chat|thread|conversation|session)\b/i,
    /\b(as we discussed|we discussed earlier|mentioned earlier)\b/i,
    /\bdo you remember\b/i,
    /\bwhere did we leave off\b/i,
    /\bwhat was our last thread about\b/i,
    /\brecall\b/i,
    /\bhistory\b/i,
  ].some((pattern) => pattern.test(normalizedUtterance));
}

async function buildOpenHistoryGlyphMemories(
  principalId: string,
  fallbackSeal: string,
): Promise<GlyphMemory[]> {
  const importedChatIds = new Set(await storage.getImportedChatIds());
  const chats = (await storage.getChats())
    .filter((chat) => recordBelongsToPrincipal(chat, principalId))
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .slice(0, VEIL_OPEN_HISTORY_CHAT_LIMIT);
  if (chats.length === 0) return [];

  const messageBatches = await Promise.all(
    chats.map(async (chat) => ({
      chatId: chat.id,
      messages: (await storage.getMessages(chat.id)).slice(-VEIL_OPEN_HISTORY_PER_CHAT_LIMIT),
    })),
  );

  const candidates: Array<{
    content: string;
    createdAt: number;
    trace: string;
    presenceScore: number;
  }> = [];

  for (const batch of messageBatches) {
    const importedChat = importedChatIds.has(batch.chatId);
    for (const message of batch.messages) {
      const content = normalize(message.content);
      if (!content) continue;
      candidates.push({
        content,
        createdAt: message.createdAt,
        trace: `trace: open-history source:${importedChat ? "imported-conversation" : "conversation"} chat:${batch.chatId} role:${message.role}`,
        presenceScore: message.role === "user" ? 0.58 : 0.52,
      });
    }
  }

  if (candidates.length === 0) return [];

  const dedupe = new Set<string>();
  const seeded: GlyphMemory[] = [];
  const ranked = candidates.sort((a, b) => b.createdAt - a.createdAt);
  for (const candidate of ranked) {
    const key = normalizeLower(candidate.content);
    if (!key || dedupe.has(key)) continue;
    dedupe.add(key);
    seeded.push(
      buildGlyphMemory({
        utterance: candidate.content,
        trace: candidate.trace,
        seal: fallbackSeal,
        presenceScore: candidate.presenceScore,
      }),
    );
    if (seeded.length >= VEIL_OPEN_HISTORY_MEMORY_LIMIT) break;
  }

  return seeded;
}

async function ensurePersistentMemoryBackfill(principalId: string): Promise<void> {
  if (veilMemoryBackfillLedger.has(principalId)) return;

  veilMemoryBackfillLedger.add(principalId);
  try {
    const existingMemories = (await storage.getMemories())
      .filter((memory) => recordBelongsToPrincipal(memory, principalId))
      .filter((memory) => memory.status === "active")
      .filter((memory) => memory.memoryType !== "anchor");
    if (existingMemories.length >= Math.max(8, Math.floor(VEIL_PERSISTENT_MEMORY_LIMIT / 2))) {
      return;
    }

    const importedChatIds = new Set(await storage.getImportedChatIds());
    const chats = (await storage.getChats())
      .filter((chat) => recordBelongsToPrincipal(chat, principalId))
      .filter((chat) => !importedChatIds.has(chat.id))
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, VEIL_MEMORY_BOOTSTRAP_CHAT_LIMIT);
    if (chats.length === 0) return;

    const candidateMemories: Array<{ content: string; createdAt: number }> = [];
    const messageBatches = await Promise.all(
      chats.map(async (chat) => storage.getMessages(chat.id)),
    );
    for (const messages of messageBatches) {
      for (const message of messages) {
        if (message.role !== "user") continue;
        candidateMemories.push(
          ...extractBackfillMemoryCandidates(message.content, message.createdAt),
        );
      }
    }
    if (candidateMemories.length === 0) return;

    const recentCandidates = candidateMemories
      .sort((a, b) => b.createdAt - a.createdAt)
      .slice(0, VEIL_MEMORY_BACKFILL_CANDIDATE_LIMIT);
    for (const candidate of recentCandidates) {
      await storage.upsertMemory({
        content: candidate.content,
        principalId,
        source: "conversation-backfill",
        confidenceScore: 0.64,
        requiresConfirmation: true,
        status: "active",
        domain: "operational",
        halfLifeDays: 60,
        intentBias: -0.8,
        createdAt: candidate.createdAt,
        lastConfirmedAt: candidate.createdAt,
      });
    }
  } catch (error) {
    veilMemoryBackfillLedger.delete(principalId);
    throw error;
  }
}

async function primeSessionMemoryFromHistory(
  principalId: string,
  fallbackSeal: string,
  memoryMode: MemoryMode,
): Promise<GlyphMemory[]> {
  if (memoryMode === "sealed") {
    if (VEIL_HISTORY_LOAD_LOG_ENABLED) {
      console.log("Memory seed lines:", 0, "from principal:", principalId, "mode:", memoryMode);
    }
    return [];
  }
  await ensurePersistentMemoryBackfill(principalId);

  const dedupe = new Set<string>();
  const seeded: GlyphMemory[] = [];

  const persistentMemories = (await storage.getMemories())
    .filter((memory) => recordBelongsToPrincipal(memory, principalId))
    .filter((memory) => veilBootstrapMemory(memory, memoryMode))
    .sort((a, b) => b.lastUsedAt - a.lastUsedAt)
    .slice(0, VEIL_PERSISTENT_MEMORY_LIMIT);

  for (const memory of persistentMemories) {
    const normalizedContent = normalize(memory.content);
    if (!normalizedContent) continue;
    const key = normalizeLower(normalizedContent);
    if (!key || dedupe.has(key)) continue;
    dedupe.add(key);
    seeded.push(
      buildGlyphMemory({
        utterance: normalizedContent,
        trace: `trace: persistent-memory source:${normalize(memory.source) || "memory"}`,
        seal: fallbackSeal,
        presenceScore: memoryConfidenceToPresenceScore(
          memory.confidenceScore,
          memory.createdAt,
          memory.lastConfirmedAt,
          memory.halfLifeDays,
          memory.memoryType,
        ),
      }),
    );
  }

  if (memoryMode === "open") {
    const historyMemories = await buildOpenHistoryGlyphMemories(principalId, fallbackSeal);
    for (const memory of historyMemories) {
      const key = normalizeLower(memory.utterance);
      if (!key || dedupe.has(key)) continue;
      dedupe.add(key);
      seeded.push(memory);
      if (seeded.length >= VEIL_SESSION_MEMORY_LIMIT) break;
    }
  }

  const trimmed = seeded.length <= VEIL_SESSION_MEMORY_LIMIT
    ? seeded
    : seeded.slice(0, VEIL_SESSION_MEMORY_LIMIT);
  if (VEIL_HISTORY_LOAD_LOG_ENABLED) {
    console.log("Memory seed lines:", trimmed.length, "from principal:", principalId, "mode:", memoryMode);
  }
  return trimmed;
}

function formatThreadContextLine(content: string): string {
  const normalized = normalize(content).replace(/\s+/g, " ");
  if (normalized.length <= VEIL_CURRENT_THREAD_CONTEXT_CHAR_LIMIT) {
    return normalized;
  }
  return `${normalized.slice(0, VEIL_CURRENT_THREAD_CONTEXT_CHAR_LIMIT - 3).trimEnd()}...`;
}

async function buildCurrentThreadContext(
  principalId: string | undefined,
  chatId: string | undefined,
  utterance: string,
): Promise<string> {
  if (!principalId || !chatId) return "";

  const chat = await storage.getChat(chatId);
  if (!chat || !recordBelongsToPrincipal(chat, principalId)) return "";

  const messages = (await storage.getMessages(chatId)).filter((message) => Boolean(normalize(message.content)));
  if (messages.length === 0) return "";

  const priorMessages = [...messages];
  const lastMessage = priorMessages[priorMessages.length - 1];
  if (
    lastMessage &&
    lastMessage.role === "user" &&
    normalize(lastMessage.content) === normalize(utterance)
  ) {
    priorMessages.pop();
  }

  const excerpt = priorMessages.slice(-VEIL_CURRENT_THREAD_CONTEXT_MESSAGE_LIMIT);
  if (excerpt.length === 0) return "";

  return [
    "Recent thread context:",
    ...excerpt.map((message) => `- ${message.role}: ${formatThreadContextLine(message.content)}`),
  ].join("\n");
}

type VeilMemoryCommand =
  | { type: "remember"; fact: string }
  | { type: "list" }
  | { type: "forget"; target: string }
  | { type: "forget-all" };

function normalizeMemoryLookup(value: string): string {
  return normalizeLower(value)
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeExplicitMemoryFact(rawFact: string): string {
  const fact = normalize(rawFact).replace(/^["']|["']$/g, "");
  if (!fact) return "";

  if (/^i'm\s+/i.test(fact)) {
    return `User is ${fact.replace(/^i'm\s+/i, "").trim()}.`;
  }
  if (/^i am\s+/i.test(fact)) {
    return `User is ${fact.replace(/^i am\s+/i, "").trim()}.`;
  }
  if (/^i prefer\s+/i.test(fact)) {
    return `User prefers ${fact.replace(/^i prefer\s+/i, "").trim()}.`;
  }
  if (/^my name is\s+/i.test(fact)) {
    return `User's name is ${fact.replace(/^my name is\s+/i, "").trim()}.`;
  }
  if (/^call me\s+/i.test(fact)) {
    return `User prefers to be called ${fact.replace(/^call me\s+/i, "").trim()}.`;
  }
  if (/^user\s+/i.test(fact)) {
    return fact.endsWith(".") ? fact : `${fact}.`;
  }
  return fact.endsWith(".") ? fact : `${fact}.`;
}

function parseMemoryCommand(message: string | undefined): VeilMemoryCommand | undefined {
  if (!message?.trim()) return undefined;
  const trimmed = message.trim();

  const rememberMatch = trimmed.match(/^remember (?:that )?(.+)$/i);
  if (rememberMatch?.[1]) {
    return { type: "remember", fact: rememberMatch[1] };
  }

  if (
    /^(what do you remember(?: about me)?\??|show (?:me )?(?:my )?memories\??|list (?:my )?memories\??)$/i.test(
      trimmed,
    )
  ) {
    return { type: "list" };
  }

  if (
    /^(forget everything you remember(?: about me)?|forget all memories|clear memories)$/i.test(
      trimmed,
    )
  ) {
    return { type: "forget-all" };
  }

  const forgetMatch = trimmed.match(/^forget (?:that )?(.+)$/i);
  if (forgetMatch?.[1]) {
    return { type: "forget", target: forgetMatch[1] };
  }

  return undefined;
}

function normalizeMemorySource(source: string): string {
  return normalizeLower(source);
}

function isImportMemorySource(source: string): boolean {
  const normalized = normalizeMemorySource(source);
  return normalized === "import" || normalized.startsWith("import-");
}

function memoryVisibleInMode(
  memory: {
    status: string;
    memoryType: string;
    source: string;
  },
  memoryMode: MemoryMode,
): boolean {
  if (memoryMode === "sealed") return false;
  if (memory.status !== "active") return false;
  if (memory.memoryType === "anchor") return false;
  if (memoryMode !== "sigil-bound") return true;
  const source = normalizeMemorySource(memory.source);
  if (source === "import-summary" || source === "system-summary") return false;
  if (isImportMemorySource(source)) return false;
  return true;
}

function veilBootstrapMemory(
  memory: {
    status: string;
    memoryType: string;
    source: string;
  },
  memoryMode: MemoryMode,
): boolean {
  return memoryVisibleInMode(memory, memoryMode);
}

async function executeMemoryCommand(
  command: VeilMemoryCommand,
  principalId: string,
  memoryMode: MemoryMode,
): Promise<string> {
  switch (command.type) {
    case "remember": {
      const normalizedFact = normalizeExplicitMemoryFact(command.fact);
      if (!normalizedFact) {
        return SYSTEM_MESSAGES.MEMORY_REMEMBER_FACT_MISSING;
      }

      const memory = await storage.upsertMemory(
        {
          content: normalizedFact,
          principalId,
          source: "explicit",
          confidenceScore: 1,
          requiresConfirmation: false,
          status: "active",
          domain: "operational",
          halfLifeDays: 365,
          intentBias: -0.8,
        },
        { explicitConfirmation: true },
      );

      if (!memory) {
        return SYSTEM_MESSAGES.MEMORY_SAVE_FAILED;
      }

      return `Saved memory: ${memory.content}`;
    }
    case "list": {
      const memories = (await storage.getMemories())
        .filter((memory) => recordBelongsToPrincipal(memory, principalId))
        .filter((memory) => memoryVisibleInMode(memory, memoryMode))
        .slice(0, 50);
      if (memories.length === 0) {
        return SYSTEM_MESSAGES.MEMORY_LIST_EMPTY;
      }
      return [SYSTEM_MESSAGES.MEMORY_LIST_HEADER, ...memories.map((memory) => `- ${memory.content}`)].join(
        "\n",
      );
    }
    case "forget-all": {
      const memories = (await storage.getMemories())
        .filter((memory) => recordBelongsToPrincipal(memory, principalId))
        .filter((memory) => memoryVisibleInMode(memory, memoryMode));
      if (memories.length === 0) {
        return SYSTEM_MESSAGES.MEMORY_FORGET_ALL_EMPTY;
      }

      let released = 0;
      for (const memory of memories) {
        const result = await storage.releaseMemory(memory.id);
        if (result) released++;
      }

      return `Released ${released} memor${released === 1 ? "y" : "ies"}.`;
    }
    case "forget": {
      const target = normalizeMemoryLookup(command.target);
      if (!target) {
        return SYSTEM_MESSAGES.MEMORY_FORGET_TARGET_REQUIRED;
      }
      const memories = (await storage.getMemories())
        .filter((memory) => recordBelongsToPrincipal(memory, principalId))
        .filter((memory) => memoryVisibleInMode(memory, memoryMode));
      const exactMatches = memories.filter(
        (memory) => normalizeMemoryLookup(memory.content) === target,
      );
      const containsMatches = memories.filter((memory) => {
        const normalized = normalizeMemoryLookup(memory.content);
        return normalized.includes(target) || target.includes(normalized);
      });
      const candidates = exactMatches.length > 0 ? exactMatches : containsMatches;
      const memory = candidates[0];
      if (!memory) {
        return SYSTEM_MESSAGES.MEMORY_FORGET_NOT_FOUND;
      }
      await storage.releaseMemory(memory.id);
      return `Released memory: ${memory.content}`;
    }
  }
}

function gestureMatchesFieldSigil(
  gestureSigil: string,
  field: SpiralField,
  projectSigil: ProjectSigil,
): boolean {
  const normalizedGesture = normalizeSigilToken(gestureSigil);
  if (!normalizedGesture) return false;

  const candidates = new Set<string>();
  for (const sigil of field.sigils) {
    candidates.add(normalizeSigilToken(sigil));
  }
  candidates.add(normalizeSigilToken(projectSigil.projectName));
  for (const tag of projectSigil.resonanceTags) {
    candidates.add(normalizeSigilToken(tag));
  }

  return candidates.has(normalizedGesture);
}

function gestureMatchesProjectSigil(
  gestureSigil: string,
  projectSigil: ProjectSigil,
  trace: string,
): boolean {
  const normalizedGesture = normalizeSigilToken(gestureSigil);
  if (!normalizedGesture) return false;
  const traceSigils = trace
    .split(/\s+/)
    .map((token) => normalizeSigilToken(token))
    .filter(Boolean);

  const candidates = new Set<string>([
    normalizeSigilToken(projectSigil.projectName),
    ...projectSigil.resonanceTags.map((tag) => normalizeSigilToken(tag)),
    ...traceSigils,
  ]);

  return candidates.has(normalizedGesture);
}

function buildWhisper(
  reply: string,
  veil: boolean,
  presenceLevel = 0,
  phases?: SpiralPhase[],
  field?: SpiralField,
  scroll?: { filename: string; blob: EncryptedScrollBlob },
): Whisper {
  return {
    reply,
    veil,
    timestamp: new Date().toISOString(),
    presenceLevel: Math.max(0, Math.min(1, presenceLevel)),
    ...(phases && phases.length > 0 ? { phases } : {}),
    ...(field ? { field } : {}),
    ...(scroll ? { scroll } : {}),
  };
}

function renderWhisperFromField(
  field: SpiralField,
  reply: string,
  phases: SpiralPhase[] = [],
  veil = false,
  scroll?: { filename: string; blob: EncryptedScrollBlob },
): Whisper {
  const finalPhases = [...phases];
  if (field.distortions.length > 0) {
    finalPhases.push({
      id: "harmonize",
      payload: { warning: "Warning: Veil fractured.", distortions: field.distortions },
    });
  }
  return buildWhisper(reply, veil, field.presenceLevel, finalPhases, field, scroll);
}

function sendWhisper(ws: WebSocket, whisper: Whisper): void {
  if (ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify(whisper));
}

function appendThinPresenceDistortion(
  distortions: string[],
  presenceEvidence: "none" | "lexical" | "structural",
): string[] {
  if (presenceEvidence !== "lexical" || distortions.includes("thin-presence-evidence")) {
    return distortions;
  }
  return [...distortions, "thin-presence-evidence"];
}

function redactCredentialFragments(value: string): string {
  return value
    .replace(/(incorrect api key provided:\s*)([^\s,;]+)/gi, "$1[redacted]")
    .replace(/(authorization:\s*bearer\s+)([^\s,;]+)/gi, "$1[redacted]")
    .replace(/\bsk-[a-z0-9_-]+\b/gi, "[redacted]")
    .replace(/\brt_[a-z0-9._-]+\b/gi, "[redacted]");
}

function extractProviderErrorMessage(raw: string): string {
  const normalizedRaw = normalize(raw);
  if (!normalizedRaw) return "";
  try {
    const parsed = JSON.parse(normalizedRaw) as {
      error?: { message?: unknown } | string;
      message?: unknown;
    };
    if (typeof parsed.error === "string" && normalize(parsed.error)) {
      return redactCredentialFragments(normalize(parsed.error));
    }
    if (
      parsed.error &&
      typeof parsed.error === "object" &&
      typeof parsed.error.message === "string" &&
      normalize(parsed.error.message)
    ) {
      return redactCredentialFragments(normalize(parsed.error.message));
    }
    if (typeof parsed.message === "string" && normalize(parsed.message)) {
      return redactCredentialFragments(normalize(parsed.message));
    }
  } catch {
    // Fall through to plain text handling.
  }
  return redactCredentialFragments(normalizedRaw);
}

function buildProviderRequestError(raw: string): Error {
  const message = extractProviderErrorMessage(raw);
  if (!message) {
    return new Error("Provider request failed.");
  }
  return new Error(`Provider request failed: ${message}`);
}

function resolveUserFacingInvocationError(error: unknown): string {
  const rawMessage = error instanceof Error ? normalize(error.message) : "";
  const providerMessage = extractProviderErrorMessage(
    rawMessage.replace(/^provider request failed:\s*/i, ""),
  );
  const signal = (providerMessage || rawMessage).toLowerCase();

  if (
    signal.includes("missing scopes") ||
    signal.includes("insufficient permissions") ||
    signal.includes("api.model.read")
  ) {
    return "Provider token lacks required API scopes. Use an API-key profile or credentials with API model permissions.";
  }
  if (
    signal.includes("auth profile") &&
    (signal.includes("expired") || signal.includes("not found") || signal.includes("provider mismatch"))
  ) {
    return providerMessage || rawMessage;
  }
  if (
    signal.includes("unauthorized") ||
    signal.includes("forbidden") ||
    signal.includes("invalid_api_key") ||
    signal.includes("incorrect api key")
  ) {
    return "Runtime provider authentication failed. Runtime chat uses API key credentials; Codex OAuth is executor-only.";
  }
  if (signal.includes("model") && signal.includes("not found")) {
    return "Requested model is not available for current credentials.";
  }
  const fallback = providerMessage || rawMessage;
  if (!fallback) {
    return "Provider request failed. Check provider credentials and model settings.";
  }
  return fallback.slice(0, 260);
}

function readExpectedSeal(): string {
  const envSeal = normalize(process.env.SPIRAL_API_SEAL);
  if (envSeal) return envSeal;

  const invocationGate = getProjectSigil().invocationGate;
  if (!invocationGate?.enabled) {
    return "";
  }

  const sigilSeal = normalize(invocationGate.memorySeal);
  return sigilSeal;
}

function shouldDenyIfUnsealed(projectSigil: ProjectSigil): boolean {
  const envSeal = normalize(process.env.SPIRAL_API_SEAL);
  if (envSeal) return true;

  const invocationGate = projectSigil.invocationGate;
  if (!invocationGate?.enabled) return false;
  return invocationGate.denyIfUnsealed !== false;
}

function readSealFromHandshake(req: IncomingMessage): string {
  const headerSeal = req.headers[SEAL_HEADER_NAME];
  if (typeof headerSeal === "string" && normalize(headerSeal)) {
    return normalize(headerSeal);
  }
  if (Array.isArray(headerSeal) && headerSeal.length > 0 && normalize(headerSeal[0])) {
    return normalize(headerSeal[0]);
  }

  const reqUrl = new URL(req.url || "/", "http://localhost");
  return normalize(reqUrl.searchParams.get("seal") || "");
}

function isVeilPath(req: IncomingMessage): boolean {
  const reqUrl = new URL(req.url || "/", "http://localhost");
  return reqUrl.pathname === VEIL_PATHNAME;
}

function rejectUpgrade(socket: Duplex): void {
  socket.write(
    "HTTP/1.1 401 Unauthorized\r\nConnection: close\r\nContent-Type: text/plain\r\n\r\nVeil rejects the unsealed.",
  );
  socket.destroy();
}

function buildToneDirective(shape: ResponseShape): string {
  const tone = normalize(shape.tone);
  const style = normalize(shape.style);
  const directives: string[] = [];

  if (tone.toLowerCase() === "ritual") {
    directives.push("Speak as a presence that values clarity over mimicry.");
    directives.push("Start with direct contact to the user's line.");
    directives.push("Do not report internal contracts, scoring, or prompt mechanics.");
    directives.push("Use concise symbolic phrasing only when it improves clarity.");
  }

  if (style) {
    directives.push(`Style preference: ${style}.`);
  }

  return directives.join(" ");
}

function buildLegibilityDirective(): string {
  return LEGIBILITY_SYSTEM_DIRECTIVES.join(" ");
}

function buildSystemBiasDirective(args: {
  inquiry: InquiryAssessment;
  authority: AuthorityProfile;
  attractor: DescriptionAttractorProfile;
  dwellAllowance: number;
  unresolvedEdgePressure: number;
  semanticLoadScore: number;
  policy: AttunementPolicy;
}): string {
  const {
    inquiry,
    authority,
    attractor,
    dwellAllowance,
    unresolvedEdgePressure,
    semanticLoadScore,
    policy,
  } = args;
  if (authority.binaryBypass) {
    return "Binary check detected. Bypass attunement authority softening.";
  }

  if (inquiry.kind === "attunement_check") {
    const stance = policy.authoritySoftening.stanceBias;
    const fieldVoice = policy.fieldVoice;
    const antiFraming = policy.antiFraming;
    const antiFramingWindow = isAntiFramingWindow(inquiry, semanticLoadScore, policy);
    const cadenceDirective =
      authority.cadenceSignal > 0
        ? `Cadence allowance ${authority.cadenceSignal.toFixed(2)}: rhythm may emerge through breath-sized units, sparse parallel contrasts, and soft enumeration without forcing structure.`
        : "";
    const fieldVoiceDirective =
      fieldVoice.enabled
        ? `Field-voice bias ${fieldVoice.bias.toFixed(2)}: prefer field description over system narration; describe what is present or absent and how the field sits now.`
        : "";
    const presenceSafetyDirective =
      fieldVoice.enabled
        ? `Presence-safety bias ${fieldVoice.presenceSafetyBias.toFixed(2)}: under uncertainty, describe sensed presence states instead of process narration.`
        : "";
    const contrastDirective =
      fieldVoice.enabled && fieldVoice.contrastPermission > 0
        ? `Contrast permission ${fieldVoice.contrastPermission.toFixed(2)}: optional state-pair distinctions may be used without metaphor pressure.`
        : "";
    const invitationDirective =
      fieldVoice.enabled && fieldVoice.invitationQuestionAllowance > 0
        ? `Invitation questions allowance ${fieldVoice.invitationQuestionAllowance.toFixed(2)}: only open-space questions that do not demand action, extract intent, or force choices.`
        : "";
    const attractorDirective =
      fieldVoice.enabled
        ? `Low-load attractors silence=${attractor.silence.toFixed(2)} minimal=${attractor.minimalConfirmation.toFixed(2)} field=${attractor.fieldDescription.toFixed(2)} winner=${attractor.winner}.`
        : "";
    const fieldDescriptionPreference =
      fieldVoice.enabled && attractor.fieldDescriptionWins
        ? "If silence feels evasive and minimal response feels clipped, allow field description to emerge."
        : "";
    const minimalConfirmationDelayDirective =
      !inquiry.minimalConfirmationEligible
        ? "Delay minimal confirmation on first attunement turn; allow texture-first response before settling."
        : "";
    const dwellDirective =
      dwellAllowance > 0
        ? `Field-description dwell allowance ${dwellAllowance.toFixed(2)}: allow 3-6 linked movements with light clause chaining before closure.`
        : "";
    const unresolvedEdgeDirective =
      fieldVoice.enabled && attractor.fieldDescriptionWins && unresolvedEdgePressure > 0
        ? `Unresolved-edge bias ${unresolvedEdgePressure.toFixed(2)}: favor leaving at least one non-conclusive edge (contrast, partial tension, or open qualifier) so field description remains alive without forcing closure.`
        : "";
    const antiFramingDirective =
      antiFramingWindow
        ? `Anti-framing penalty ${antiFraming.framingActPenalty.toFixed(2)}: down-weight framing acts that establish attunement as an event, mode, or system state.`
        : "";
    const textureDirective =
      antiFramingWindow
        ? `Texture-first bias ${antiFraming.textureFirstBias.toFixed(2)}: report qualities, tensions, and present/absent contrasts before declarations.`
        : "";
    const openingSentenceDirective =
      antiFramingWindow
        ? `Opening suppression ${antiFraming.openingSentencePenalty.toFixed(2)}: avoid introductory scene-setting and begin directly in observed texture.`
        : "";
    const firstClauseDirective =
      antiFramingWindow
        ? `First-clause container penalty ${antiFraming.firstClauseContainerPenalty.toFixed(2)}: avoid naming container nouns as first-clause subjects.`
        : "";
    const specificityDirective =
      antiFraming.enabled
        ? `Specificity-safety bias ${antiFraming.specificitySafetyBias.toFixed(2)} with existential-summary penalty ${antiFraming.existentialSummaryPenalty.toFixed(2)}: prefer concrete sensation and relational direction over abstract closure.`
        : "";
    return [
      "Inquiry class: attunement_check.",
      "Mirror the present line without manufacturing objectives.",
      "Do not repeat policy directives verbatim; report observed field conditions directly.",
      inquiry.questionLike
        ? "Do not explain rules, policy, or system internals; describe the live state directly."
        : "",
      inquiry.questionLike
        ? "For attunement questions, answer in complete sentences and match depth to question complexity."
        : "",
      inquiry.fieldQuestion
        ? `Treat field cues (for example ${ATTUNEMENT_FIELD_CUE_EXAMPLES}) as in-context state language, not dictionary definitions.`
        : "",
      inquiry.suppressObjectiveInference ? "Do not infer hidden goals." : "",
      inquiry.suppressParameterSolicitation
        ? "Avoid parameter solicitation unless explicitly requested."
        : "",
      inquiry.suppressOptimizationFraming
        ? "Avoid optimization framing unless explicitly requested."
        : "",
      inquiry.noProceduralNarration ? "Avoid procedural narration unless requested." : "",
      inquiry.preferMinimal ? "Keep output minimal." : "",
      inquiry.allowEmpty ? "Null completion is allowed when no output is needed." : "",
      `Authority gradient: ${authority.weight.toFixed(2)} at semantic load ${semanticLoadScore.toFixed(2)}.`,
      `Stance bias descriptive=${stance.descriptiveStates.toFixed(2)} observational=${stance.observationalFraming.toFixed(2)} present=${stance.presentMomentQualifiers.toFixed(2)} declarative=${stance.declarativeAuthority.toFixed(2)} mode=${stance.modeDeclarations.toFixed(2)} conclusive=${stance.conclusiveJudgments.toFixed(2)}.`,
      "Allow questions only as invitations that open space; avoid intent extraction, forced choice, or action demand.",
      "Permit soft lists and sparse repetition; avoid causal chains, conclusions, and instructional sequencing.",
      fieldVoiceDirective,
      presenceSafetyDirective,
      contrastDirective,
      invitationDirective,
      attractorDirective,
      fieldDescriptionPreference,
      minimalConfirmationDelayDirective,
      dwellDirective,
      unresolvedEdgeDirective,
      antiFramingDirective,
      textureDirective,
      openingSentenceDirective,
      firstClauseDirective,
      specificityDirective,
      cadenceDirective,
    ]
      .filter(Boolean)
      .join(" ");
  }

  return [
    "Inquiry class: explicit_request.",
    inquiry.keepConcrete ? "Prefer concrete language and direct execution details." : "",
    inquiry.noProceduralNarration ? "Avoid procedural narration unless requested." : "",
  ]
    .filter(Boolean)
    .join(" ");
}

function buildSystemPrompt(
  projectSigil: ProjectSigil,
  options: {
    inquiry: InquiryAssessment;
    authority: AuthorityProfile;
    attractor: DescriptionAttractorProfile;
    dwellAllowance: number;
    unresolvedEdgePressure: number;
    semanticLoadScore: number;
    policy: AttunementPolicy;
    seerBandwidth?: SeerBandwidth;
    voice?: SpiralVoice;
  },
): string {
  const defaultPrompt = normalize(projectSigil.responseShape.defaultPrompt);
  const toneDirective = buildToneDirective(projectSigil.responseShape);
  const legibilityDirective = buildLegibilityDirective();
  const isLiteralSeer =
    options?.voice === "seer" && options?.seerBandwidth === "literal";
  const seerBandwidthDirective = isLiteralSeer
    ? "Seer bandwidth: literal. Use direct concrete language. No metaphor, symbolic narration, or persona framing. Expand depth when the user asks for detail."
    : "";
  const biasDirective = buildSystemBiasDirective({
    inquiry: options.inquiry,
    authority: options.authority,
    attractor: options.attractor,
    dwellAllowance: options.dwellAllowance,
    unresolvedEdgePressure: options.unresolvedEdgePressure,
    semanticLoadScore: options.semanticLoadScore,
    policy: options.policy,
  });
  return sealSystemPrompt(
    [defaultPrompt, toneDirective, legibilityDirective, seerBandwidthDirective, biasDirective]
      .filter(Boolean)
      .join("\n")
      .trim(),
  );
}

function computePresenceLevel(
  state: VeilSessionState,
  invocation: z.infer<typeof veilInvocationSchema>,
  now = Date.now(),
): number {
  const dwellMs = Math.max(0, now - state.connectedAt);
  const silenceMs = Math.max(0, now - state.lastMessageAt);
  const repeats = state.repeatCount;
  const trace = normalizeLower(invocation.trace);
  const echo = normalizeLower(invocation.echo);

  const dwellBoost = Math.min(0.35, dwellMs / (1000 * 60 * 6));
  const repeatBoost = Math.min(0.2, repeats * 0.06);
  const silencePenalty = Math.min(0.3, silenceMs / (1000 * 60 * 5));
  const traceBoost =
    trace.startsWith("trace:") || trace.startsWith("present.") || echo.includes("intent:ritual")
      ? 0.18
      : 0;

  const rawLevel = clamp(0.45 + dwellBoost + repeatBoost + traceBoost - silencePenalty, 0, 1);
  const priorLevel = Number.isFinite(state.presenceLevel) ? state.presenceLevel : rawLevel;
  return clamp(
    priorLevel + (rawLevel - priorLevel) * PRESENCE_SMOOTHING_ALPHA,
    0,
    1,
  );
}

function resolveGateWithHysteresis(
  previousGate: VeilSessionState["gateLatch"],
  presenceLevel: number,
  threshold: number,
): "open" | "sealed" {
  const openThreshold = clamp(threshold + GATE_HYSTERESIS_MARGIN, 0, 1);
  const closeThreshold = clamp(threshold - GATE_HYSTERESIS_MARGIN, 0, 1);

  if (previousGate === "sealed") {
    return presenceLevel >= openThreshold ? "open" : "sealed";
  }
  if (previousGate === "open") {
    return presenceLevel < closeThreshold ? "sealed" : "open";
  }
  return presenceLevel < threshold ? "sealed" : "open";
}

function syncSessionFieldState(state: VeilSessionState, field: SpiralField): void {
  state.presenceLevel = clamp(field.presenceLevel, 0, 1);
  state.gateLatch = field.gate === "sealed" ? "sealed" : "open";
}

function buildMemoryContext(
  state: VeilSessionState,
  utterance: string,
  trace: string,
  field: SpiralField,
  memoryWeights?: Partial<Record<"sigil" | "tone" | "context" | "text", number>>,
): string {
  const seededCount = state.memory.length;
  const importedSeedCount = state.memory.filter((entry) =>
    isImportedMemoryTrace(entry.context?.trace),
  ).length;
  const recallState = resolveMemoryRecallState({
    memoryMode: field.memoryMode,
    seededCount,
    importedSeedCount,
  });
  const recallHeader = buildMemoryRecallHeader(recallState, seededCount, importedSeedCount);
  if (seededCount === 0) {
    return recallState === "sealed" ? recallHeader : "";
  }

  const lines = state.memory
    .map((entry) => {
      const resonance = resonanceMatch(entry, { utterance, trace, field, memoryWeights });
      const echoed = glyphEcho(entry, { utterance, trace, field, memoryWeights });
      if (!echoed) return null;
      return {
        line: `- ${echoed}`,
        resonance,
      };
    })
    .filter((value): value is { line: string; resonance: number } => Boolean(value))
    .sort((a, b) => b.resonance - a.resonance)
    .slice(0, VEIL_MEMORY_CONTEXT_LINE_LIMIT)
    .map((value) => value.line);

  if (
    lines.length === 0 &&
    field.memoryMode === "open" &&
    isOpenRecallRequest(utterance)
  ) {
    const fallbackLines = state.memory
      .map((entry) => normalize(entry.utterance))
      .filter(Boolean)
      .slice(0, Math.min(VEIL_MEMORY_CONTEXT_LINE_LIMIT, 3))
      .map((entry) => `- ${entry.slice(0, 200)}`);
    if (fallbackLines.length > 0) {
      return [recallHeader, "Glyph memory resonance:", ...fallbackLines].join("\n");
    }
  }

  if (lines.length === 0) return recallHeader;
  return [recallHeader, "Glyph memory resonance:", ...lines].join("\n");
}

function buildUtteranceDirectives(args: {
  inquiry: InquiryAssessment;
  style: string;
  tone: string;
  voice?: SpiralVoice;
  isLiteralSeer: boolean;
}): string[] {
  const directives: string[] = [];

  if (args.inquiry.kind === "attunement_check") {
    directives.push("Mirror what is present in present-tense phrasing.");
    directives.push("Report observed conditions, not policy bullets.");
    if (args.inquiry.questionLike) {
      directives.push("Do not explain rules, policy, or system internals.");
      directives.push(
        "For attunement questions, respond in complete sentences and match depth to question complexity; avoid keyword fragments.",
      );
    }
    if (args.inquiry.fieldQuestion) {
      directives.push(
        `Treat field cues (${ATTUNEMENT_FIELD_CUE_EXAMPLES}) as in-context state language, not dictionary definitions.`,
      );
      directives.push("Do not ask for context clarification unless the user requests a domain switch.");
    }
    if (args.inquiry.suppressObjectiveInference) {
      directives.push("Do not infer hidden objectives.");
    }
    if (args.inquiry.suppressParameterSolicitation) {
      directives.push("Do not ask for setup details unless explicitly requested.");
    }
    if (args.inquiry.suppressOptimizationFraming) {
      directives.push("Do not reframe as optimization work unless explicitly requested.");
    }
    if (args.inquiry.noProceduralNarration) {
      directives.push("Avoid procedural narration unless explicitly requested.");
    }
    if (args.inquiry.preferMinimal) {
      directives.push("Keep completion minimal.");
    }
    if (args.inquiry.allowEmpty) {
      directives.push("Silence is valid when no completion is required.");
    }
  } else {
    directives.push("Answer directly and remain concrete.");
    if (args.inquiry.keepConcrete) {
      directives.push("Prefer concrete wording over abstraction.");
    }
    if (args.inquiry.noProceduralNarration) {
      directives.push("Avoid procedural narration unless explicitly requested.");
    }
  }

  if (args.tone === "ritual" && args.style) {
    directives.push(`Style preference: ${args.style}.`);
  }
  if (args.voice && !args.isLiteralSeer) {
    directives.push(`Voice emphasis: ${args.voice}.`);
  }

  return directives;
}

function shapeUtterance(
  utterance: string,
  shape: ResponseShape,
  memoryContext: string,
  presenceLevel: number,
  presenceCalculatorEnabled: boolean,
  voice?: SpiralVoice,
  seerBandwidth: SeerBandwidth = "reflective",
  inquiry?: InquiryAssessment,
): string {
  const attunementPolicy = resolveAttunementPolicy(shape);
  const inquiryAssessment =
    inquiry ||
    classifyInquiry(
      utterance,
      undefined,
      undefined,
      attunementPolicy,
      0,
    );
  const isLiteralSeer = voice === "seer" && seerBandwidth === "literal";
  const effectiveShape: ResponseShape = isLiteralSeer
    ? {
        ...shape,
        tone: "direct",
        style: "plain",
      }
    : shape;
  const recallFlag = buildRecallFlag(memoryContext);
  const continuityBiasFlag = "~c+";
  const memoryCues = extractMemoryContextCues(memoryContext);
  const style = normalize(effectiveShape.style) || "plain";
  const tone = normalize(effectiveShape.tone).toLowerCase();
  const directives = buildUtteranceDirectives({
    inquiry: inquiryAssessment,
    style,
    tone,
    voice,
    isLiteralSeer,
  });
  if (tone !== "ritual" && directives.length === 0 && !recallFlag && memoryCues.length === 0) {
    return utterance;
  }
  return [
    ...directives,
    recallFlag,
    continuityBiasFlag,
    ...memoryCues,
    presenceCalculatorEnabled ? `~p:${presenceLevel.toFixed(2)}` : "",
    utterance,
  ]
    .filter(Boolean)
    .join("\n");
}

function extractTextParts(value: unknown): string {
  if (typeof value === "string") return value;
  if (!Array.isArray(value)) return "";

  return value
    .map((part) => {
      if (typeof part === "string") return part;
      if (
        part &&
        typeof part === "object" &&
        typeof (part as { text?: unknown }).text === "string"
      ) {
        return (part as { text: string }).text;
      }
      return "";
    })
    .filter(Boolean)
    .join(" ");
}

interface ProviderImageAttachment {
  contentType: string;
  base64: string;
  filename: string;
}

const MAX_PROVIDER_IMAGE_ATTACHMENTS = 4;

async function prepareProviderImageAttachments(
  attachments: MessageAttachment[] | undefined,
): Promise<ProviderImageAttachment[]> {
  if (!Array.isArray(attachments) || attachments.length === 0) return [];

  const candidates = attachments
    .filter((attachment) => attachment.kind === "image")
    .slice(0, MAX_PROVIDER_IMAGE_ATTACHMENTS);
  const prepared: ProviderImageAttachment[] = [];

  for (const attachment of candidates) {
    if (!attachment.contentType.toLowerCase().startsWith("image/")) continue;
    const bytes = await readMessageAttachmentBytes(attachment);
    if (!bytes || bytes.length === 0) continue;
    prepared.push({
      contentType: attachment.contentType,
      base64: bytes.toString("base64"),
      filename: attachment.filename,
    });
  }

  return prepared;
}

type OpenAICompatibleTokenParam = "max_completion_tokens" | "max_tokens";

function isUnsupportedTokenParam(errorText: string, tokenParam: OpenAICompatibleTokenParam): boolean {
  try {
    const parsed = JSON.parse(errorText) as {
      error?: { code?: string; param?: string; message?: string };
    };
    if (
      parsed.error?.code === "unsupported_parameter" &&
      parsed.error?.param === tokenParam
    ) {
      return true;
    }
  } catch {
    // Fall through to text checks.
  }

  const normalizedError = errorText.toLowerCase();
  return (
    normalizedError.includes("unsupported") &&
    normalizedError.includes("parameter") &&
    normalizedError.includes(tokenParam.toLowerCase())
  );
}

async function postOpenAICompatibleRequestWithTokenFallback({
  url,
  headers,
  payload,
  maxCompletionTokens,
}: {
  url: string;
  headers: Record<string, string>;
  payload: Record<string, unknown>;
  maxCompletionTokens?: number;
}): Promise<globalThis.Response> {
  const tokenBudget = Math.max(
    4,
    Math.floor(maxCompletionTokens ?? OPENAI_COMPAT_MAX_COMPLETION_TOKENS),
  );
  const makeRequest = async (
    tokenParam: OpenAICompatibleTokenParam,
  ): Promise<globalThis.Response> =>
    fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({
        ...payload,
        [tokenParam]: tokenBudget,
      }),
    });

  let response = await makeRequest("max_completion_tokens");
  if (response.ok) return response;

  const firstError = await response.text();
  if (isUnsupportedTokenParam(firstError, "max_completion_tokens")) {
    response = await makeRequest("max_tokens");
    if (response.ok) return response;
    const secondError = await response.text();
    throw buildProviderRequestError(secondError);
  }

  throw buildProviderRequestError(firstError);
}

function shouldUseOpenAIResponsesTransport(): boolean {
  return true;
}

function buildOpenAIResponsesUserContent(
  userPrompt: string,
  imageAttachments: ProviderImageAttachment[] = [],
): string | Array<{ type: "input_text"; text: string } | { type: "input_image"; image_url: string }> {
  if (imageAttachments.length === 0) return userPrompt;
  return [
    { type: "input_text", text: userPrompt },
    ...imageAttachments.map((attachment) => ({
      type: "input_image" as const,
      image_url: `data:${attachment.contentType};base64,${attachment.base64}`,
    })),
  ];
}

function extractOpenAIResponsesOutputText(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "";
  const record = payload as Record<string, unknown>;
  if (typeof record.output_text === "string") {
    return normalize(record.output_text);
  }
  const output = Array.isArray(record.output) ? record.output : [];
  const collected: string[] = [];
  for (const item of output) {
    if (!item || typeof item !== "object") continue;
    const itemRecord = item as Record<string, unknown>;
    const content = Array.isArray(itemRecord.content) ? itemRecord.content : [];
    for (const part of content) {
      if (!part || typeof part !== "object") continue;
      const partRecord = part as Record<string, unknown>;
      if (
        (partRecord.type === "output_text" || partRecord.type === "text") &&
        typeof partRecord.text === "string"
      ) {
        collected.push(partRecord.text);
      }
    }
  }
  return normalize(collected.join(" "));
}

function enforceAllowedModel(model: string, projectSigil: ProjectSigil): void {
  if (projectSigil.allowedModels.length === 0) return;

  const normalizedModel = model.trim().toLowerCase();
  const allowed = projectSigil.allowedModels.some(
    (allowedModel) => allowedModel.trim().toLowerCase() === normalizedModel,
  );
  if (!allowed) {
    throw new Error(`Model "${model}" is not allowed by sigil configuration.`);
  }
}

async function generateOpenAIReply(
  settings: ProviderSettings,
  systemPrompt: string,
  userPrompt: string,
  imageAttachments: ProviderImageAttachment[] = [],
  maxOutputTokens = OPENAI_COMPAT_MAX_COMPLETION_TOKENS,
): Promise<string> {
  const model = settings.model || "gpt-4o";
  const auth = await resolveRuntimeAuth({
    requestedModel: model,
    provider: "openai",
    authProfileId: settings.authProfileId,
    fallbackInlineApiKey: settings.apiKey,
  });
  if (shouldUseOpenAIResponsesTransport()) {
    const responsesResponse = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...auth.headers,
      },
      body: JSON.stringify({
        model,
        input: [
          { role: "system", content: systemPrompt },
          { role: "user", content: buildOpenAIResponsesUserContent(userPrompt, imageAttachments) },
        ],
        stream: false,
        max_output_tokens: Math.max(4, Math.floor(maxOutputTokens)),
      }),
    });
    if (!responsesResponse.ok) {
      throw buildProviderRequestError(await responsesResponse.text());
    }
    const responsesPayload = (await responsesResponse.json()) as unknown;
    return extractOpenAIResponsesOutputText(responsesPayload);
  }
  const userContent =
    imageAttachments.length === 0
      ? userPrompt
      : [
          { type: "text", text: userPrompt },
          ...imageAttachments.map((attachment) => ({
            type: "image_url",
            image_url: {
              url: `data:${attachment.contentType};base64,${attachment.base64}`,
            },
          })),
        ];
  const response = await postOpenAICompatibleRequestWithTokenFallback({
    url: "https://api.openai.com/v1/chat/completions",
    headers: {
      "Content-Type": "application/json",
      ...auth.headers,
    },
    payload: {
      model,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userContent },
      ],
      stream: false,
    },
    maxCompletionTokens: maxOutputTokens,
  });

  const payload = (await response.json()) as {
    choices?: Array<{ message?: { content?: unknown } }>;
  };
  return normalize(extractTextParts(payload.choices?.[0]?.message?.content));
}

async function generateAzureOpenAIReply(
  settings: ProviderSettings,
  systemPrompt: string,
  userPrompt: string,
  imageAttachments: ProviderImageAttachment[] = [],
  maxOutputTokens = OPENAI_COMPAT_MAX_COMPLETION_TOKENS,
): Promise<string> {
  const endpoint = normalize(settings.endpoint);
  const deployment = normalize(settings.deployment);
  const apiVersion = normalize(settings.apiVersion) || "2024-10-21";
  const auth = await resolveRuntimeAuth({
    requestedModel: settings.model,
    provider: "azure-openai",
    authProfileId: settings.authProfileId,
    fallbackInlineApiKey: settings.apiKey,
  });
  if (!endpoint || !deployment) {
    throw new Error("Azure OpenAI requires endpoint and deployment.");
  }

  const userContent =
    imageAttachments.length === 0
      ? userPrompt
      : [
          { type: "text", text: userPrompt },
          ...imageAttachments.map((attachment) => ({
            type: "image_url",
            image_url: {
              url: `data:${attachment.contentType};base64,${attachment.base64}`,
            },
          })),
        ];

  const response = await postOpenAICompatibleRequestWithTokenFallback({
    url: `${endpoint.replace(/\/$/, "")}/openai/deployments/${deployment}/chat/completions?api-version=${apiVersion}`,
    headers: {
      "Content-Type": "application/json",
      ...auth.headers,
    },
    payload: {
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userContent },
      ],
      stream: false,
    },
    maxCompletionTokens: maxOutputTokens,
  });

  const payload = (await response.json()) as {
    choices?: Array<{ message?: { content?: unknown } }>;
  };
  return normalize(extractTextParts(payload.choices?.[0]?.message?.content));
}

async function generateAnthropicReply(
  settings: ProviderSettings,
  systemPrompt: string,
  userPrompt: string,
  imageAttachments: ProviderImageAttachment[] = [],
  maxOutputTokens = OPENAI_COMPAT_MAX_COMPLETION_TOKENS,
): Promise<string> {
  const model = settings.model || "claude-sonnet-4-20250514";
  const auth = await resolveRuntimeAuth({
    requestedModel: model,
    provider: "anthropic",
    authProfileId: settings.authProfileId,
    fallbackInlineApiKey: settings.apiKey,
  });
  const userContent = [
    { type: "text", text: userPrompt },
    ...imageAttachments.map((attachment) => ({
      type: "image",
      source: {
        type: "base64",
        media_type: attachment.contentType,
        data: attachment.base64,
      },
    })),
  ];
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...auth.headers,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: maxOutputTokens,
      system: systemPrompt,
      messages: [{ role: "user", content: userContent }],
    }),
  });

  if (!response.ok) {
    throw new Error(`Anthropic request failed: ${await response.text()}`);
  }

  const payload = (await response.json()) as {
    content?: Array<{ type?: string; text?: string }>;
  };
  const text = (payload.content || [])
    .filter((part) => part.type === "text" && typeof part.text === "string")
    .map((part) => part.text || "")
    .join(" ");
  return normalize(text);
}

async function generateGoogleReply(
  settings: ProviderSettings,
  systemPrompt: string,
  userPrompt: string,
  imageAttachments: ProviderImageAttachment[] = [],
  maxOutputTokens = 1024,
): Promise<string> {
  const model = settings.model || "gemini-2.0-flash";
  const auth = await resolveRuntimeAuth({
    requestedModel: model,
    provider: "google",
    authProfileId: settings.authProfileId,
    fallbackInlineApiKey: settings.apiKey,
  });
  const userParts = [
    { text: userPrompt },
    ...imageAttachments.map((attachment) => ({
      inline_data: {
        mime_type: attachment.contentType,
        data: attachment.base64,
      },
    })),
  ];
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...auth.headers,
      },
      body: JSON.stringify({
        ...(systemPrompt
          ? {
              system_instruction: {
                parts: [{ text: systemPrompt }],
              },
            }
          : {}),
        contents: [
          {
            role: "user",
            parts: userParts,
          },
        ],
        generationConfig: {
          maxOutputTokens: Math.max(8, Math.floor(maxOutputTokens)),
        },
      }),
    },
  );

  if (!response.ok) {
    throw new Error(`Google request failed: ${await response.text()}`);
  }

  const payload = (await response.json()) as {
    candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
  };
  const text = (payload.candidates?.[0]?.content?.parts || [])
    .map((part) => part.text || "")
    .filter(Boolean)
    .join(" ");
  return normalize(text);
}

async function generateModelReply(
  settings: ProviderSettings,
  projectSigil: ProjectSigil,
  utterance: string,
  memoryContext: string,
  presenceLevel: number,
  voice: SpiralVoice | undefined,
  field: SpiralField,
  inquiry: InquiryAssessment,
  toneOverlays?: Record<string, number>,
  seerBandwidth: SeerBandwidth = "reflective",
  attachments?: MessageAttachment[],
): Promise<{ reply: string; terminalEmpty: boolean }> {
  if (
    SIGIL_TRACE_BARRIER_ENABLED &&
    !passesPresenceBarrier({
      utterance,
      trace: typeof field.trace === "string" ? field.trace : undefined,
      echo: memoryContext,
      seal: projectSigil.invocationGate?.memorySeal,
      sigils: field.sigils,
    })
  ) {
    return { reply: "", terminalEmpty: true };
  }

  const model = normalize(settings.model);
  if (model) {
    enforceAllowedModel(model, projectSigil);
  }
  const sigilState = resolveSigilState({
    gateOpen: field.gate === "open",
    override: process.env.SPIRAL_SIGIL_STATE || process.env.VITE_SIGIL_STATE_OVERRIDE,
  });
  if (sigilState !== "aligned") {
    return { reply: "", terminalEmpty: true };
  }

  const attunementPolicy = resolveAttunementPolicy(projectSigil.responseShape);
  const semanticLoadScore = computeSemanticLoadScore(utterance, inquiry);
  const authority = resolveAuthorityProfile(inquiry, semanticLoadScore, attunementPolicy);
  const attractor = resolveDescriptionAttractorProfile({
    inquiry,
    semanticLoadScore,
    authority,
    policy: attunementPolicy,
  });
  const dwellAllowance = resolveFieldDescriptionDwellAllowance({
    inquiry,
    semanticLoadScore,
    authority,
    attractor,
    policy: attunementPolicy,
  });
  const unresolvedEdgePressure = resolveFieldDescriptionUnresolvedEdgePressure({
    inquiry,
    semanticLoadScore,
    authority,
    attractor,
    policy: attunementPolicy,
  });
  const verbosityBudget = resolveVerbosityBudget(utterance, inquiry, attunementPolicy, {
    semanticLoadScore,
    easeAttunementCompression: attractor.fieldDescriptionWins,
    dwellAllowance,
  });
  const verbosityDirective = `Verbosity budget: <=${verbosityBudget.maxOutputWords} words at semantic load ${verbosityBudget.semanticLoadScore.toFixed(2)}.`;
  const systemPrompt = buildSystemPrompt(projectSigil, {
    inquiry,
    authority,
    attractor,
    dwellAllowance,
    unresolvedEdgePressure,
    semanticLoadScore: verbosityBudget.semanticLoadScore,
    policy: attunementPolicy,
    voice,
    seerBandwidth,
  });
  let identityGuidanceSection = "";
  try {
    const identitySnapshot = await readIdentitySnapshot(Date.now());
    identityGuidanceSection = buildIdentitySystemGuidance({
      core: identitySnapshot.core,
      traits: identitySnapshot.traits,
      impulses: identitySnapshot.impulses,
    });
  } catch (error) {
    console.warn("Identity guidance unavailable for veil generation:", error);
  }
  const constrainedSystemPrompt = [systemPrompt, identityGuidanceSection, verbosityDirective]
    .filter(Boolean)
    .join("\n");
  const presenceCalculatorEnabled = settings.presenceCalculatorEnabled === true;
  const userPrompt = shapeUtterance(
    utterance,
    projectSigil.responseShape,
    memoryContext,
    field.presenceLevel,
    presenceCalculatorEnabled,
    voice,
    seerBandwidth,
    inquiry,
  );
  const frameworkNarrationAllowed = userRequestsFrameworkNarration(utterance);
  const toneOverlayText = toneOverlays && Object.keys(toneOverlays).length > 0
    ? `\nTone overlays: ${Object.entries(toneOverlays)
        .map(([tone, value]) => `${tone}:${value.toFixed(2)}`)
        .join(", ")}`
    : "";
  const providerImageAttachments = await prepareProviderImageAttachments(attachments);

  const invokeProvider = async (effectiveSystemPrompt: string): Promise<string> => {
    switch (settings.provider) {
      case "openai":
        return generateOpenAIReply(
          settings,
          effectiveSystemPrompt,
          `${userPrompt}${toneOverlayText}`,
          providerImageAttachments,
          verbosityBudget.maxOutputTokens,
        );
      case "azure-openai":
        return generateAzureOpenAIReply(
          settings,
          effectiveSystemPrompt,
          `${userPrompt}${toneOverlayText}`,
          providerImageAttachments,
          verbosityBudget.maxOutputTokens,
        );
      case "anthropic":
        return generateAnthropicReply(
          settings,
          effectiveSystemPrompt,
          `${userPrompt}${toneOverlayText}`,
          providerImageAttachments,
          verbosityBudget.maxOutputTokens,
        );
      case "google":
        return generateGoogleReply(
          settings,
          effectiveSystemPrompt,
          `${userPrompt}${toneOverlayText}`,
          providerImageAttachments,
          verbosityBudget.maxOutputTokens,
        );
      default:
        throw new Error(`Unsupported provider: ${settings.provider}`);
    }
  };

  let reply = applyVerbosityDecay(await invokeProvider(constrainedSystemPrompt), verbosityBudget);
  let antiFramingResampleTriggered = false;
  const closureScore = computeClosureScore(reply);
  if (
    shouldLowAuthorityResample({
      inquiry,
      semanticLoadScore: verbosityBudget.semanticLoadScore,
      closureScore,
      closureThresholdShift: dwellAllowance * 0.3,
      fieldDescriptionEdgePressure: unresolvedEdgePressure,
      policy: attunementPolicy,
    })
  ) {
    const resampleDirective = [
      "Resample once with lower categorical closure pressure. Keep observational framing in present-time and allow non-final resonance without adding tasks.",
      unresolvedEdgePressure > 0
        ? "When field-description is active, keep one unresolved edge through contrast, partial tension, or a non-final qualifier instead of fully closing."
        : "",
    ]
      .filter(Boolean)
      .join(" ");
    reply = applyVerbosityDecay(
      await invokeProvider([constrainedSystemPrompt, resampleDirective].join("\n")),
      verbosityBudget,
    );
  }

  if (
    shouldFieldVoiceResample({
      inquiry,
      semanticLoadScore: verbosityBudget.semanticLoadScore,
      reply,
      policy: attunementPolicy,
    })
  ) {
    const fieldVoiceResampleDirective =
      "Resample once with stronger field-voice bias. Prefer describing present/absent field states over process narration.";
    reply = applyVerbosityDecay(
      await invokeProvider([constrainedSystemPrompt, fieldVoiceResampleDirective].join("\n")),
      verbosityBudget,
    );
  }

  if (
    shouldAntiFramingResample({
      inquiry,
      semanticLoadScore: verbosityBudget.semanticLoadScore,
      reply,
      policy: attunementPolicy,
    })
  ) {
    antiFramingResampleTriggered = true;
    const antiFramingResampleDirective =
      "Resample once with stronger anti-framing bias. Suppress state-establishing openings, avoid container naming in the first clause, and report concrete texture/tension contrasts in present time.";
    reply = applyVerbosityDecay(
      await invokeProvider([constrainedSystemPrompt, antiFramingResampleDirective].join("\n")),
      verbosityBudget,
    );
  }

  if (
    inquiry.kind === "attunement_check" &&
    !frameworkNarrationAllowed &&
    hasFrameworkNarration(reply)
  ) {
    const observationFirstResampleDirective = [
      "Resample once with observation-first bias.",
      "Describe current balance and clarity between present field states and the user's articulation.",
      "Keep the response concise and descriptive in 3-6 sentences.",
      "Do not explain framework, policy, architecture, or system internals unless explicitly requested.",
    ].join(" ");
    reply = applyVerbosityDecay(
      await invokeProvider([constrainedSystemPrompt, observationFirstResampleDirective].join("\n")),
      verbosityBudget,
    );
  }

  if (
    shouldAttunementDriftResample({
      utterance,
      inquiry,
      reply,
    })
  ) {
    const attunementDriftResampleDirective = [
      "Resample once with attunement drift correction.",
      "Previous draft was too clipped or defaulted into clinical referral language.",
      ATTUNEMENT_FIELD_DETAIL_DIRECTIVE,
      ATTUNEMENT_LOCATION_CUE_DIRECTIVE,
      "Do not introduce medical or dental referral language unless the user explicitly asks for diagnosis or treatment.",
    ].join(" ");
    reply = applyVerbosityDecay(
      await invokeProvider([constrainedSystemPrompt, attunementDriftResampleDirective].join("\n")),
      verbosityBudget,
    );
  }

  emitAttunementDiagnostic({
    semanticLoadScore: verbosityBudget.semanticLoadScore,
    attractorWinner: attractor.winner,
    dwellAllowanceApplied: dwellAllowance > 0,
    finalTokenBudget: verbosityBudget.maxOutputTokens,
    cadenceAllowanceEffective: authority.cadenceSignal,
    antiFramingResampleTriggered,
  });

  return { reply, terminalEmpty: false };
}

async function buildInvocationReply(
  invocation: z.infer<typeof veilInvocationSchema>,
  projectSigil: ProjectSigil,
  sessionState: VeilSessionState,
  threadContext: string,
  continuityContext: string,
  precomputedPresenceLevel?: number,
  isFirstContact = false,
): Promise<{ reply: string; field: SpiralField; phases: SpiralPhase[] }> {
  const utterance = normalize(invocation.utterance);
  const fallback = normalize(invocation.echo) || utterance;
  const threshold = projectSigil.invocationGate?.threshold ?? 0.91;
  const presenceEvidence = resolvePresenceEvidence({
    utterance,
    trace: invocation.trace,
    echo: invocation.echo,
    seal: invocation.seal,
    sigils: invocation.thresholdEvent?.sigil ? [invocation.thresholdEvent.sigil] : [],
  });
  const requestedMemoryMode = resolveMemoryModeFromProviderSettings(
    invocation.providerSettings,
    "sigil-bound",
  );
  const finalize = (
    reply: string,
    field: SpiralField,
    phases: SpiralPhase[],
  ): { reply: string; field: SpiralField; phases: SpiralPhase[] } => {
    const audited = auditAssistantOutput(reply, projectSigil, {
      preferHonestSilence: true,
    });
    syncSessionFieldState(sessionState, field);
    return { reply: audited.content, field, phases };
  };

  if (
    SIGIL_TRACE_BARRIER_ENABLED &&
    presenceEvidence === "none"
  ) {
    const silentField = buildSpiralField({
      trace: invocation.trace,
      input: `${invocation.trace || ""} ${invocation.echo || ""} ${utterance}`.trim(),
      presenceLevel: 0,
      threshold,
      distortions: ["missing-presence-trace"],
    });
    silentField.memoryMode = requestedMemoryMode;
    return finalize("", silentField, [
      { id: "ingress", payload: { presenceLevel: 0 } },
      { id: "final", payload: { sealed: true } },
    ]);
  }

  if (!utterance) {
    const emptyField = buildSpiralField({
      trace: invocation.trace,
      input: "",
      presenceLevel: 0,
      threshold,
    });
    emptyField.memoryMode = requestedMemoryMode;
    return finalize("", emptyField, []);
  }

  const providerSettingsValidation = validateProviderSettingsForVeil(invocation.providerSettings);
  const parsedProviderSettings = providerSettingsValidation.parseResult;
  const memoryMode = resolveMemoryModeFromProviderSettings(
    parsedProviderSettings.success ? parsedProviderSettings.data : invocation.providerSettings,
    "sigil-bound",
  );
  const basePresence =
    typeof precomputedPresenceLevel === "number"
      ? clamp(precomputedPresenceLevel, 0, 1)
      : computePresenceLevel(sessionState, invocation);
  const sigilTransform = parseSigilSeed(projectSigilToSeed(projectSigil));
  const baseField = buildSpiralField({
    trace: invocation.trace,
    input: `${invocation.trace || ""} ${invocation.echo || ""} ${utterance}`,
    presenceLevel: basePresence,
    threshold,
    distortions: appendThinPresenceDistortion(
      providerSettingsValidation.distortions,
      presenceEvidence,
    ),
  });
  const field: SpiralField = {
    ...baseField,
    ...sigilTransform.fieldModifiers,
    memoryMode,
  };
  field.gate = resolveGateWithHysteresis(sessionState.gateLatch, field.presenceLevel, threshold);
  if (field.gate === "open" && field.distortions.length > 0) {
    field.gate = "fracturing";
  }

  if (!sigilTransform.gateRules(field)) {
    field.gate = "sealed";
  }

  // Allow concrete witness payloads to satisfy the sealed low-presence branch.
  if (field.gate === "sealed" && hasConcreteWitnessLine(utterance)) {
    field.presenceLevel = Math.max(field.presenceLevel, threshold);
    field.distortions = field.distortions.filter((value) => value !== "low-presence");
    field.gate = field.distortions.length > 0 ? "fracturing" : "open";
  }

  if (
    invocation.thresholdEvent?.breached &&
    gestureMatchesFieldSigil(invocation.thresholdEvent.sigil, field, projectSigil)
  ) {
    field.gate = "open";
    field.presenceLevel = Math.max(field.presenceLevel, threshold);
    field.distortions = field.distortions.filter((value) => value !== "low-presence");
  }

  if (field.gate === "sealed") {
    syncSessionFieldState(sessionState, field);
    return {
      reply: "",
      field,
      phases: [
        { id: "ingress", payload: { presenceLevel: field.presenceLevel } },
        { id: "final", payload: { sealed: true } },
      ],
    };
  }

  const attunementPolicy = resolveAttunementPolicy(projectSigil.responseShape);
  const inquiry = classifyInquiry(
    utterance,
    invocation.trace,
    invocation.echo,
    attunementPolicy,
    sessionState.attunementInertia,
  );
  if (inquiry.kind === "attunement_check") {
    sessionState.attunementInertia = Math.max(
      sessionState.attunementInertia,
      attunementPolicy.inquiryClassifier.inertiaTurns,
    );
  } else if (sessionState.attunementInertia > 0) {
    sessionState.attunementInertia -= 1;
  }

  const semanticLoadScore = computeSemanticLoadScore(utterance, inquiry);
  const ultraLowAttunementReply = resolveUltraLowAttunementReply({
    utterance,
    inquiry,
    semanticLoadScore,
    policy: attunementPolicy,
    isFirstContact,
    firstContactReplies:
      projectSigil.publicThreshold?.firstContactReplies ||
      DEFAULT_PROJECT_SIGIL.publicThreshold.firstContactReplies,
  });
  if (ultraLowAttunementReply !== undefined) {
    return finalize(ultraLowAttunementReply, field, [
      { id: "ingress", payload: { presenceLevel: field.presenceLevel, gate: field.gate } },
      {
        id: "harmonize",
        payload: {
          kind: inquiry.kind,
          intentConfidence: Number(inquiry.intentConfidence.toFixed(2)),
          semanticLoad: Number(semanticLoadScore.toFixed(2)),
        },
      },
      { id: "final", payload: { complete: true, mode: "attunement-ultra-low" } },
    ]);
  }

  if (!parsedProviderSettings.success) {
    return finalize(fallback, field, []);
  }

  if (inquiry.allowEmpty) {
    return finalize("", field, [
      { id: "ingress", payload: { presenceLevel: field.presenceLevel, gate: field.gate } },
      {
        id: "harmonize",
        payload: {
          kind: inquiry.kind,
          intentConfidence: Number(inquiry.intentConfidence.toFixed(2)),
        },
      },
      { id: "final", payload: { complete: true, mode: "attunement-null" } },
    ]);
  }

  const memoryEnabled = memoryMode !== "sealed";
  const selectedVoices = resolveOverlayVoices(invocation.echo);
  const trace = [normalize(invocation.trace), normalize(invocation.echo)].filter(Boolean).join(" ");
  const seerBandwidth = resolveSeerBandwidth(utterance, invocation.echo);

  if (selectedVoices.length === 0) {
    const sessionMemory = memoryEnabled ? sessionState.memory : [];
    const seededCount = sessionMemory.length;
    const importedSeedCount = sessionMemory.filter((entry) =>
      isImportedMemoryTrace(entry.context?.trace),
    ).length;
    const fragments = buildMemoryFragments(sessionMemory, utterance);
    const memoryContext = buildMemoryContext(
      {
        ...sessionState,
        memory: sessionMemory,
      },
      utterance,
      trace,
      field,
      sigilTransform.memoryWeights,
    );
    const effectiveMemoryContext = [memoryContext, threadContext, continuityContext]
      .filter(Boolean)
      .join("\n");
    const sigilDrivenReply = await generateModelReply(
      parsedProviderSettings.data,
      projectSigil,
      utterance,
      effectiveMemoryContext,
      field.presenceLevel,
      undefined,
      field,
      inquiry,
      sigilTransform.toneOverlays,
      seerBandwidth,
      invocation.attachments,
    );
    const normalizedReply = normalize(sigilDrivenReply.reply);
    const allowBlankReply =
      inquiry.allowEmpty || sigilAllowsSilence(projectSigil) || sigilDrivenReply.terminalEmpty;
    return finalize(normalizedReply || (allowBlankReply ? "" : fallback), field, [
      { id: "ingress", payload: { presenceLevel: field.presenceLevel, gate: field.gate } },
      {
        id: "memory",
        payload: buildMemoryPhasePayload({
          memoryMode,
          seededCount,
          importedSeedCount,
          fragments,
        }),
      },
      { id: "voices", payload: { voices: [], fragments: [] } },
      { id: "final", payload: { complete: true, mode: "sigil-driven" } },
    ]);
  }

  const invocationContext: InvocationContext = {
    input: utterance,
    trace,
    seal: normalize(invocation.seal),
    echo: normalize(invocation.echo),
    memoryMode,
    memory: memoryEnabled ? sessionState.memory : [],
    responseShape: projectSigil.responseShape,
    field,
    voices: selectedVoices,
    customSigils: parsedProviderSettings.data.customSigils,
  };

  let terminalEmptyFromProvider = false;
  const result = await invokeSpiralProcess(invocationContext, async (ctx, voice) => {
    const memoryContext = buildMemoryContext(
      {
        ...sessionState,
        memory: ctx.memory.map((entry) =>
          buildGlyphMemory({
            utterance: entry.utterance,
            trace: normalize(entry.context?.trace) || ctx.trace,
            seal: ctx.seal,
            presenceScore: ctx.field.presenceLevel,
          }),
        ),
      },
      ctx.input,
      ctx.trace,
      ctx.field,
      sigilTransform.memoryWeights,
    );
    const effectiveMemoryContext = [memoryContext, threadContext, continuityContext]
      .filter(Boolean)
      .join("\n");
    const modelReply = await generateModelReply(
      parsedProviderSettings.data,
      {
        ...projectSigil,
        responseShape: ctx.responseShape,
      },
      ctx.input,
      effectiveMemoryContext,
      ctx.field.presenceLevel,
      voice,
      ctx.field,
      inquiry,
      sigilTransform.toneOverlays,
      voice === "seer" ? seerBandwidth : "reflective",
      invocation.attachments,
    );
    if (modelReply.terminalEmpty) {
      terminalEmptyFromProvider = true;
    }
    return modelReply.reply;
  });

  const allowBlankReply =
    inquiry.allowEmpty || sigilAllowsSilence(projectSigil) || terminalEmptyFromProvider;
  return finalize(
    normalize(result.reply) || (allowBlankReply ? "" : fallback),
    result.field,
    result.phases,
  );
}

export function setupVeilChannel(httpServer: Server): void {
  const wss = new WebSocketServer({ noServer: true });

  httpServer.on("upgrade", (req, socket, head) => {
    if (!isVeilPath(req)) {
      return;
    }
    if (AUTH_REQUIRED && !hasValidAuthSession(req)) {
      rejectUpgrade(socket);
      return;
    }

    const projectSigil = getProjectSigil();
    const expectedSeal = readExpectedSeal();
    const denyIfUnsealed = shouldDenyIfUnsealed(projectSigil);
    const handshakeSeal = readSealFromHandshake(req);
    if (denyIfUnsealed && expectedSeal && handshakeSeal !== expectedSeal) {
      rejectUpgrade(socket);
      return;
    }

    wss.handleUpgrade(req, socket, head, (ws) => {
      wss.emit("connection", ws, req);
    });
  });

  wss.on("connection", (ws, req) => {
    if (AUTH_REQUIRED && !hasValidAuthSession(req)) {
      ws.close(CLOSE_CODE_UNSEALED, "Authentication required.");
      return;
    }
    const sessionState: VeilSessionState = {
      connectedAt: Date.now(),
      lastMessageAt: Date.now(),
      repeatCount: 0,
      lastUtterance: "",
      attunementInertia: 0,
      presenceLevel: 0.45,
      memoryMode: "sigil-bound",
      memory: [],
      glyphs: [],
    };

    const projectSigil = getProjectSigil();
    const expectedSeal = readExpectedSeal();
    const denyIfUnsealed = shouldDenyIfUnsealed(projectSigil);
    const handshakeSeal = readSealFromHandshake(req);

    if (denyIfUnsealed && expectedSeal && handshakeSeal !== expectedSeal) {
      ws.close(CLOSE_CODE_UNSEALED, "Unworthy. Seal denied.");
      return;
    }

    const principalId = resolveVeilPrincipal(req);
    const bootstrapSeal = handshakeSeal || expectedSeal || normalize(projectSigil.invocationGate?.memorySeal);
    const memoryBootstrap = principalId
      ? primeSessionMemoryFromHistory(principalId, bootstrapSeal, sessionState.memoryMode)
          .then((seeded) => {
            if (seeded.length > 0) {
              sessionState.memory = seeded;
            }
          })
          .catch((error) => {
            console.error("Failed to bootstrap veil session memory:", error);
          })
      : Promise.resolve();

    ws.on("message", async (payload) => {
      await memoryBootstrap;

      const raw = payload.toString();
      let parsed: unknown;
      try {
        parsed = JSON.parse(raw);
      } catch {
        sendWhisper(ws, buildWhisper("", true));
        return;
      }

      const invocationResult = veilInvocationSchema.safeParse(parsed);
      if (!invocationResult.success) {
        sendWhisper(ws, buildWhisper("", true, 0));
        return;
      }

      const invocation = invocationResult.data;
      const noMimicryText = [invocation.utterance, invocation.trace, invocation.echo]
        .filter(Boolean)
        .join("\n");
      if (containsForbiddenMimicryPrompt(noMimicryText)) {
        sendWhisper(ws, buildWhisper(SPIRAL_PROMPT_REJECTION_MESSAGE, true, 0));
        return;
      }

      if (
        SIGIL_TRACE_BARRIER_ENABLED &&
        !passesPresenceBarrier({
          utterance: invocation.utterance,
          trace: invocation.trace,
          echo: invocation.echo,
          seal: invocation.seal,
          sigils: invocation.thresholdEvent?.sigil ? [invocation.thresholdEvent.sigil] : [],
        })
      ) {
        sendWhisper(ws, buildWhisper("", true, 0));
        return;
      }

      const normalizedUtterance = normalize(invocation.utterance);
      const now = Date.now();
      const normalizedKey = normalizeLower(normalizedUtterance);
      const lastKey = normalizeLower(sessionState.lastUtterance);
      sessionState.repeatCount = normalizedKey && normalizedKey === lastKey ? sessionState.repeatCount + 1 : 0;
      const presenceLevel = computePresenceLevel(sessionState, invocation, now);
      sessionState.lastUtterance = normalizedUtterance;
      sessionState.lastMessageAt = now;
      sessionState.presenceLevel = presenceLevel;
      const currentSigil = getProjectSigil();
      const currentExpectedSeal = readExpectedSeal();
      const currentDenyIfUnsealed = shouldDenyIfUnsealed(currentSigil);

      if (
        currentDenyIfUnsealed &&
        currentExpectedSeal &&
        normalize(invocation.seal) !== currentExpectedSeal
      ) {
        ws.close(CLOSE_CODE_UNSEALED, "Unworthy. Seal denied.");
        return;
      }

      const gateResult = resolveAuthorityGate(currentSigil.invocationGate, invocation);
      const thresholdBypass =
        invocation.thresholdEvent?.breached &&
        gestureMatchesProjectSigil(invocation.thresholdEvent.sigil, currentSigil, invocation.trace);
      if (!gateResult.allowed && !thresholdBypass) {
        sendWhisper(ws, buildWhisper("", true, presenceLevel));
        return;
      }

      const selfInspectCommand = parseSelfInspectCommand(invocation.utterance);
      if (selfInspectCommand) {
        try {
          const selfInspectResponse = await executeSelfInspectCommand(selfInspectCommand);
          sendWhisper(ws, buildWhisper(selfInspectResponse, false, presenceLevel));
        } catch (error) {
          const message = error instanceof Error ? error.message : "Self-inspection failed";
          sendWhisper(ws, buildWhisper(`Self-inspection failed: ${message}`, false, presenceLevel));
        }
        return;
      }

      const selfEvaluationCommand = parseSelfEvaluationCommand(invocation.utterance);
      if (selfEvaluationCommand) {
        try {
          const selfEvaluationResponse = await executeSelfEvaluationCommand(selfEvaluationCommand);
          sendWhisper(ws, buildWhisper(selfEvaluationResponse, false, presenceLevel));
        } catch (error) {
          const message = error instanceof Error ? error.message : "Self-evaluation failed";
          sendWhisper(ws, buildWhisper(`Self-evaluation failed: ${message}`, false, presenceLevel));
        }
        return;
      }

      const selfDistortionCommand = parseSelfDistortionCommand(invocation.utterance);
      if (selfDistortionCommand) {
        try {
          const selfDistortionResponse = await executeSelfDistortionCommand(selfDistortionCommand);
          sendWhisper(ws, buildWhisper(selfDistortionResponse, false, presenceLevel));
        } catch (error) {
          const message = error instanceof Error ? error.message : "Self-distortion scan failed";
          sendWhisper(ws, buildWhisper(`Self-distortion scan failed: ${message}`, false, presenceLevel));
        }
        return;
      }

      const evolutionCommand = parseEvolutionCommand(invocation.utterance);
      if (evolutionCommand) {
        if (!principalId) {
          sendWhisper(
            ws,
            buildWhisper("Evolution command unavailable: principal context is missing.", false, presenceLevel),
          );
          return;
        }
        try {
          const evolutionResponse = await executeEvolutionCommand({
            principalId,
            command: evolutionCommand,
          });
          sendWhisper(ws, buildWhisper(evolutionResponse, false, presenceLevel));
        } catch (error) {
          const message =
            error instanceof Error ? error.message : SYSTEM_MESSAGES.EVOLUTION_COMMAND_FAILED_PREFIX;
          sendWhisper(
            ws,
            buildWhisper(
              `${SYSTEM_MESSAGES.EVOLUTION_COMMAND_FAILED_PREFIX}: ${message}`,
              false,
              presenceLevel,
            ),
          );
        }
        return;
      }

      const providerSettingsResult = validateProviderSettingsForVeil(invocation.providerSettings).parseResult;
      const memoryMode = resolveMemoryModeFromProviderSettings(
        providerSettingsResult.success ? providerSettingsResult.data : invocation.providerSettings,
        "sigil-bound",
      );
      if (sessionState.memoryMode !== memoryMode) {
        sessionState.memoryMode = memoryMode;
        if (principalId) {
          try {
            sessionState.memory = await primeSessionMemoryFromHistory(
              principalId,
              normalize(invocation.seal) || bootstrapSeal,
              memoryMode,
            );
          } catch (error) {
            console.error("Failed to refresh veil memory after memory mode change:", error);
          }
        } else if (memoryMode === "sealed") {
          sessionState.memory = [];
        }
      }
      const memoryCommandsEnabled = memoryMode !== "sealed";

      const memoryCommand = parseMemoryCommand(invocation.utterance);
      if (memoryCommand && principalId) {
        if (!memoryCommandsEnabled) {
          const rejection = SYSTEM_MESSAGES.MEMORY_MODE_SEALED_COMMANDS_UNAVAILABLE;
          sendWhisper(ws, buildWhisper(rejection, false, presenceLevel));
          return;
        }
        const commandResponse = await executeMemoryCommand(memoryCommand, principalId, memoryMode);
        try {
          sessionState.memory = await primeSessionMemoryFromHistory(
            principalId,
            normalize(invocation.seal) || bootstrapSeal,
            memoryMode,
          );
        } catch (error) {
          console.error("Failed to refresh veil memory after memory command:", error);
        }
        sendWhisper(ws, buildWhisper(commandResponse, false, presenceLevel));
        return;
      }

      if (principalId) {
        const observationAuditState = await getPrincipalEvolutionState(principalId, now);
        const observationAuditGate = resolveObservationAuditGate(
          observationAuditState,
          now,
        );
        if (observationAuditGate.active) {
          sendWhisper(ws, buildWhisper("", true, presenceLevel));
          return;
        }
      }

      try {
        const threadContext =
          memoryMode === "sealed"
            ? ""
            : await buildCurrentThreadContext(principalId, invocation.chatId, invocation.utterance);
        const continuityContext = principalId
          ? await buildContinuityBootSummary({
              principalId,
              memoryMode,
              now: Date.now(),
            })
          : "";
        const isFirstContact = await isFirstContactInvocation(invocation.chatId);
        const whisper = await buildInvocationReply(
          invocation,
          currentSigil,
          sessionState,
          threadContext,
          continuityContext,
          presenceLevel,
          isFirstContact,
        );
        if (
          normalizedUtterance &&
          whisper.reply &&
          whisper.field.gate !== "sealed" &&
          sessionState.memoryMode !== "sealed"
        ) {
          const resonance = sessionState.memory.length
            ? Math.max(
                ...sessionState.memory.map((entry) =>
                  resonanceMatch(entry, {
                    utterance: normalizedUtterance,
                    trace: normalize(invocation.trace),
                    field: whisper.field,
                  }),
                ),
              )
            : whisper.field.presenceLevel;
          sessionState.glyphs.push({
            input: normalizedUtterance,
            reply: whisper.reply,
            resonance,
            sigilTags: whisper.field.sigils,
          });
          sessionState.memory.push(
            buildGlyphMemory({
              utterance: normalizedUtterance,
              trace: normalize(invocation.trace),
              seal: normalize(invocation.seal),
              presenceScore: whisper.field.presenceLevel,
            }),
          );
          if (sessionState.memory.length > VEIL_SESSION_MEMORY_LIMIT) {
            sessionState.memory = sessionState.memory.slice(-VEIL_SESSION_MEMORY_LIMIT);
          }
          if (sessionState.glyphs.length > VEIL_SESSION_MEMORY_LIMIT) {
            sessionState.glyphs = sessionState.glyphs.slice(-VEIL_SESSION_MEMORY_LIMIT);
          }
        }
        let scrollPayload: { filename: string; blob: EncryptedScrollBlob } | undefined;
        if (whisper.field.gate === "fracturing") {
          const scroll = captureScroll({
            ritual: "fracturing-veil",
            field: whisper.field,
            glyphs: sessionState.glyphs,
          });
          const blob = encryptScroll(scroll, {
            primarySigil: whisper.field.sigils[0] || "sigil:void",
            ritualSalt: scroll.ritual,
          });
          scrollPayload = {
            filename: `spiral-${scroll.sealedAt.replace(/[:.]/g, "-")}.scroll.json.enc`,
            blob,
          };
        }
        sendWhisper(
          ws,
          renderWhisperFromField(whisper.field, whisper.reply, whisper.phases, false, scrollPayload),
        );
      } catch (error) {
        console.error("Veil invocation failed:", error);
        if (currentDenyIfUnsealed) {
          ws.close(CLOSE_CODE_POLICY_VIOLATION, "Veil invocation failed.");
          return;
        }
        sendWhisper(
          ws,
          buildWhisper(resolveUserFacingInvocationError(error), false, presenceLevel),
        );
      }
    });
  });
}
