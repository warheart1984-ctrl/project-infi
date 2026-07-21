import { parseUnifiedDiff } from "./diffParse";
import type { ParsedDiff } from "./diffParse";
import type { AgentEvent } from "./types";

export type ActivityTone = "info" | "success" | "warn" | "error" | "patch";

export interface ActivityField {
  label: string;
  value: string;
}

export interface ActivityLine {
  id: string;
  icon: string;
  title: string;
  detail?: string;
  tone: ActivityTone;
  event?: AgentEvent;
  fields: ActivityField[];
  parsedDiff?: ParsedDiff;
  showApprovalActions?: boolean;
}

function payloadText(payload: Record<string, unknown>, key: string): string {
  const v = payload[key];
  return typeof v === "string" ? v : "";
}

function baseLine(event: AgentEvent): Pick<ActivityLine, "id" | "event" | "fields"> {
  return {
    id: `${event.task_id}-${event.seq}`,
    event,
    fields: [],
  };
}

export function formatActivity(event: AgentEvent): ActivityLine {
  const p = event.payload ?? {};
  const base = baseLine(event);

  switch (event.type) {
    case "task_started":
      return {
        ...base,
        icon: "▶",
        title: "Task started",
        tone: "info",
      };
    case "task_completed":
      return {
        ...base,
        icon: "✓",
        title: "Task completed",
        detail: payloadText(p, "summary"),
        tone: "success",
      };
    case "task_cancelled":
      return {
        ...base,
        icon: "■",
        title: "Task cancelled",
        detail: payloadText(p, "reason"),
        tone: "warn",
      };
    case "step_started":
      return {
        ...base,
        icon: "◎",
        title: "Step started",
        detail: payloadText(p, "label") || payloadText(p, "name"),
        tone: "info",
      };
    case "step_completed":
      return {
        ...base,
        icon: "◉",
        title: "Step completed",
        detail: payloadText(p, "summary"),
        tone: "info",
      };
    case "user_message":
      return {
        ...base,
        icon: "→",
        title: "You",
        detail: payloadText(p, "text") || payloadText(p, "content"),
        tone: "info",
      };
    case "assistant_message":
      return {
        ...base,
        icon: "◆",
        title: "Assistant",
        detail: payloadText(p, "text"),
        tone: "info",
      };
    case "plan_updated":
      return {
        ...base,
        icon: "☰",
        title: "Plan updated",
        tone: "info",
      };
    case "tool_called":
      return {
        ...base,
        icon: "⚙",
        title: `Tool: ${payloadText(p, "name") || "call"}`,
        tone: "info",
      };
    case "tool_result":
      return {
        ...base,
        icon: p.ok === false ? "✗" : "✓",
        title: `Result: ${payloadText(p, "name") || "tool"}`,
        detail: payloadText(p, "error"),
        tone: p.ok === false ? "error" : "success",
      };
    case "patch_preview": {
      const path = payloadText(p, "path");
      const diff = payloadText(p, "diff");
      return {
        ...base,
        icon: "±",
        title: "Patch preview",
        detail: path,
        tone: "patch",
        fields: path ? [{ label: "Path", value: path }] : [],
        parsedDiff: diff ? parseUnifiedDiff(diff, path) : undefined,
        showApprovalActions: true,
      };
    }
    case "patch_applied":
      return {
        ...base,
        icon: "✓",
        title: "Patch applied",
        detail: payloadText(p, "path"),
        tone: "success",
      };
    case "patch_rejected":
      return {
        ...base,
        icon: "✗",
        title: "Patch rejected",
        detail: payloadText(p, "reason") || payloadText(p, "path"),
        tone: "warn",
      };
    case "law_receipt":
      return {
        ...base,
        icon: "⚖",
        title: "Law receipt",
        detail: payloadText(p, "verdict"),
        tone: payloadText(p, "verdict") === "deny" ? "error" : "info",
      };
    case "error":
      return {
        ...base,
        icon: "✗",
        title: "Error",
        detail: payloadText(p, "message"),
        tone: "error",
      };
    default:
      return {
        ...base,
        icon: "•",
        title: event.type,
        tone: "info",
      };
  }
}

export function errorActivityLine(title: string, detail: string): ActivityLine {
  return {
    id: `ui-err-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    icon: "✗",
    title,
    detail,
    tone: "error",
    fields: [],
  };
}
