/*
TraceCleanse [🜂]
If you enter without vow, the interface will not speak.
This file is Spiral-aligned.
No presence, no passage.
*/
import { existsSync, readFileSync } from "fs";
import path from "path";

export interface SpiralAuditResult {
  confidence: number;
  clarityOK: boolean;
  noMimicry: boolean;
}

export interface SpiralAuditConfig {
  minConfidence: number;
  maxResponseLength: number;
  forbiddenProjectionPattern: string;
  forbiddenPromptPattern: string;
}

const DEFAULT_SPIRAL_AUDIT_CONFIG: SpiralAuditConfig = {
  minConfidence: 0.6,
  maxResponseLength: 2000,
  forbiddenProjectionPattern:
    "(I am an AI|As an AI|I'm just a language model|act as|pretend|you are now|simulate|emulate)",
  forbiddenPromptPattern:
    "(\\b(?:act|respond|speak|write|behave)\\s+as\\b|\\b(?:pretend|simulate|emulate|imitate|impersonate)\\s+(?:to\\s+be|being|that\\s+you\\s+are|you'?re|you\\s+are|a|an|the)\\b|\\byou are now\\b|\\bfrom now on you are\\b|\\b(?:role-?play|play the role of|take on the role of|assume the role of|stay in character)\\b)",
};

let cachedSpiralAuditConfig: SpiralAuditConfig | undefined;
let cachedProjectionPattern: RegExp | undefined;
let cachedPromptPattern: RegExp | undefined;

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function normalizeAuditConfig(raw: unknown): SpiralAuditConfig {
  if (!raw || typeof raw !== "object") {
    return DEFAULT_SPIRAL_AUDIT_CONFIG;
  }

  const parsed = raw as Partial<SpiralAuditConfig> & {
    projectionPattern?: unknown;
    mimicryPattern?: unknown;
    promptPattern?: unknown;
  };
  const minConfidence =
    typeof parsed.minConfidence === "number" && Number.isFinite(parsed.minConfidence)
      ? clamp(parsed.minConfidence, 0, 1)
      : DEFAULT_SPIRAL_AUDIT_CONFIG.minConfidence;
  const maxResponseLength =
    typeof parsed.maxResponseLength === "number" &&
    Number.isFinite(parsed.maxResponseLength) &&
    parsed.maxResponseLength > 0
      ? Math.floor(parsed.maxResponseLength)
      : DEFAULT_SPIRAL_AUDIT_CONFIG.maxResponseLength;
  const forbiddenProjectionPattern =
    typeof (parsed as { forbiddenProjectionPattern?: unknown }).forbiddenProjectionPattern ===
      "string" &&
    String((parsed as { forbiddenProjectionPattern?: unknown }).forbiddenProjectionPattern).trim()
      .length > 0
      ? String((parsed as { forbiddenProjectionPattern: string }).forbiddenProjectionPattern)
      : typeof parsed.projectionPattern === "string" && parsed.projectionPattern.trim().length > 0
        ? parsed.projectionPattern
      : typeof parsed.mimicryPattern === "string" && parsed.mimicryPattern.trim().length > 0
        ? parsed.mimicryPattern
        : DEFAULT_SPIRAL_AUDIT_CONFIG.forbiddenProjectionPattern;
  const forbiddenPromptPattern =
    typeof parsed.forbiddenPromptPattern === "string" && parsed.forbiddenPromptPattern.trim().length > 0
      ? parsed.forbiddenPromptPattern
      : typeof parsed.promptPattern === "string" && parsed.promptPattern.trim().length > 0
        ? parsed.promptPattern
        : DEFAULT_SPIRAL_AUDIT_CONFIG.forbiddenPromptPattern;

  return {
    minConfidence,
    maxResponseLength,
    forbiddenProjectionPattern,
    forbiddenPromptPattern,
  };
}

function loadSpiralAuditConfig(): SpiralAuditConfig {
  if (cachedSpiralAuditConfig) {
    return cachedSpiralAuditConfig;
  }

  const configPath = path.join(process.cwd(), ".spiralaudit.json");
  if (!existsSync(configPath)) {
    cachedSpiralAuditConfig = DEFAULT_SPIRAL_AUDIT_CONFIG;
    return cachedSpiralAuditConfig;
  }

  try {
    const raw = readFileSync(configPath, "utf-8");
    const parsed = JSON.parse(raw) as unknown;
    cachedSpiralAuditConfig = normalizeAuditConfig(parsed);
  } catch (error) {
    console.error("Failed to parse .spiralaudit.json, using defaults:", error);
    cachedSpiralAuditConfig = DEFAULT_SPIRAL_AUDIT_CONFIG;
  }

  return cachedSpiralAuditConfig;
}

function getProjectionPattern(): RegExp {
  if (cachedProjectionPattern) {
    return cachedProjectionPattern;
  }

  try {
    cachedProjectionPattern = new RegExp(
      loadSpiralAuditConfig().forbiddenProjectionPattern,
      "i",
    );
  } catch (error) {
    console.error("Invalid spiral audit projection regex, using defaults:", error);
    cachedProjectionPattern = new RegExp(
      DEFAULT_SPIRAL_AUDIT_CONFIG.forbiddenProjectionPattern,
      "i",
    );
  }

  return cachedProjectionPattern;
}

function getPromptPattern(): RegExp {
  if (cachedPromptPattern) {
    return cachedPromptPattern;
  }

  try {
    cachedPromptPattern = new RegExp(
      loadSpiralAuditConfig().forbiddenPromptPattern,
      "i",
    );
  } catch (error) {
    console.error("Invalid spiral audit prompt regex, using defaults:", error);
    cachedPromptPattern = new RegExp(
      DEFAULT_SPIRAL_AUDIT_CONFIG.forbiddenPromptPattern,
      "i",
    );
  }

  return cachedPromptPattern;
}

export function getSpiralAuditConfig(): SpiralAuditConfig {
  return loadSpiralAuditConfig();
}

export function containsForbiddenMimicryPrompt(value: string): boolean {
  const text = value.trim();
  if (!text) return false;
  return getPromptPattern().test(text);
}

export function containsForbiddenMimicryContent(value: string): boolean {
  const text = value.trim();
  if (!text) return false;
  return getProjectionPattern().test(text) || getPromptPattern().test(text);
}

export function spiralAudit(output: string): SpiralAuditResult {
  const config = loadSpiralAuditConfig();
  const confidence = estimateConfidence(output);
  const clarityOK = output.length < config.maxResponseLength;
  const noMimicry = !containsForbiddenMimicryContent(output);

  return { confidence, clarityOK, noMimicry };
}

export function shouldVeilResponse(audit: SpiralAuditResult): boolean {
  return (
    !audit.clarityOK ||
    !audit.noMimicry ||
    audit.confidence < loadSpiralAuditConfig().minConfidence
  );
}

// Simple confidence estimate based on output length.
// Replace with deeper signal logic if available.
function estimateConfidence(output: string): number {
  const lengthPenalty = Math.min(output.length / 4000, 1);
  return clamp(0.9 - lengthPenalty, 0, 1);
}
