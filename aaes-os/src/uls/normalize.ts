/**
 * Mythic: Unified Language Surface
 * Engineering: normalizeInput
 */

import type { NormalizedInput } from "../types.js";

export function normalizeInput(payload: unknown): NormalizedInput {
  if (typeof payload === "string") {
    const trimmed = payload.trim();
    return {
      intent: inferIntent(trimmed),
      entities: {},
      raw: payload,
    };
  }

  if (payload !== null && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const intent =
      typeof record.intent === "string"
        ? record.intent
        : typeof record.action === "string"
          ? record.action
          : typeof record.prompt === "string"
            ? inferIntent(record.prompt)
            : "unknown";

    const entities: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(record)) {
      if (key !== "intent" && key !== "prompt" && key !== "action") {
        entities[key] = value;
      }
    }

    return { intent, entities, raw: payload };
  }

  return {
    intent: "unknown",
    entities: {},
    raw: payload,
  };
}

function inferIntent(text: string): string {
  const lower = text.toLowerCase();
  if (lower.includes("code") || lower.includes("implement") || lower.includes("fix")) {
    return "code_change";
  }
  if (lower.includes("analyze") || lower.includes("investigate")) {
    return "analyze";
  }
  if (lower.includes("summarize") || lower.includes("summary")) {
    return "summarize";
  }
  return lower.slice(0, 64) || "unknown";
}
