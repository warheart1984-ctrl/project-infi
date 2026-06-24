import { JPA1_REFERENCE } from "./spec";

export type JudgmentPreservingSystemId = "JPSS-2" | "CSS-2" | "CRK-1" | "RA-COS-1";

export interface SystemMandate {
  id: JudgmentPreservingSystemId;
  role: string;
  judgmentPreservingDescription: string;
  priorObserverCentricDescription?: string;
  judgmentActs: string[];
}

/** JPA-1 §7 — four systems reframed as judgment-preserving runtimes. */
export const JUDGMENT_PRESERVING_SYSTEMS: readonly SystemMandate[] = [
  {
    id: "JPSS-2",
    role: "Judgment development pipeline",
    judgmentPreservingDescription:
      "A judgment-preservation system for developing and transmitting observational and judgment capabilities across individuals and generations.",
    priorObserverCentricDescription: "Observer curriculum and development pipeline.",
    judgmentActs: [
      "Train perception, interpretation, valuation, deliberation, reflection",
      "Track judgment drift and correction, not just observer skill",
      "Advance stewards who can revise their own judgments",
    ],
  },
  {
    id: "CSS-2",
    role: "Threshold emergence and recalibration runtime",
    judgmentPreservingDescription:
      "A judgment-preserving runtime for threshold emergence and recalibration.",
    priorObserverCentricDescription: "Threshold stewardship and emergence.",
    judgmentActs: [
      "Treat thresholds and Δ-thresholds as judgment artifacts",
      "Govern how judgments about what matters become formal thresholds",
      "Recalibrate when judgment–reality mismatch persists",
    ],
  },
  {
    id: "CRK-1",
    role: "Constitutional judgment protection",
    judgmentPreservingDescription:
      "A constitutional runtime that protects the conditions for legitimate judgment.",
    priorObserverCentricDescription: "Constitutional invariants and observer protection.",
    judgmentActs: [
      "Non-derogable invariants constrain judgment failure modes",
      "Protect judgment-relevant observers (OPA-1 contained)",
      "Block recalibration that corrupts core identity or judgment legitimacy",
    ],
  },
  {
    id: "RA-COS-1",
    role: "Evidence and trace for judgment correction",
    judgmentPreservingDescription:
      "An evidence and trace system that preserves the information required for judgment correction.",
    priorObserverCentricDescription: "Event loop, evidence loop, and observer trace.",
    judgmentActs: [
      "Link observation → interpretation → decision → outcome → recalibration",
      "Make past judgments auditable and revisable by future stewards",
      "Preserve evidence for judgment correction, not just rule enforcement",
    ],
  },
];

export function getSystemMandate(id: JudgmentPreservingSystemId): SystemMandate | undefined {
  return JUDGMENT_PRESERVING_SYSTEMS.find((s) => s.id === id);
}

export function formatJudgmentPreservingStack(): string {
  let md = `# ${JPA1_REFERENCE} — Judgment-Preserving Stack\n\n`;
  for (const sys of JUDGMENT_PRESERVING_SYSTEMS) {
    md += `## ${sys.id}\n\n`;
    md += `${sys.judgmentPreservingDescription}\n\n`;
    md += `**Judgment acts:**\n`;
    for (const act of sys.judgmentActs) {
      md += `- ${act}\n`;
    }
    md += `\n`;
  }
  return md;
}
