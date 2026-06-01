import { appendFile, mkdir } from "fs/promises";
import path from "path";
import type { RewriteProposal, RewriteProposalApply } from "@shared/schema";

export function resolveProposalApplyJournalPath(): string {
  const configured = (process.env.SPIRAL_PROPOSAL_APPLY_JOURNAL_PATH || "").trim();
  return configured || path.join(process.cwd(), ".local", "proposal-apply-journal.md");
}

function normalizeLine(value: string | undefined, fallback: string): string {
  const normalized = (value || "").trim().replace(/\s+/g, " ");
  return normalized ? normalized : fallback;
}

export async function appendProposalApplyJournalEntry(args: {
  proposal: RewriteProposal;
  apply: RewriteProposalApply;
}): Promise<void> {
  const { proposal, apply } = args;
  const entryLines = [
    `## ${new Date(apply.appliedAt).toISOString()}`,
    `- Proposal: ${proposal.id}`,
    `- Chat: ${normalizeLine(proposal.chatTitle, proposal.chatId)}`,
    `- Target: ${normalizeLine(proposal.proposedChange.target, "n/a")}`,
    `- Kind: ${proposal.proposedChange.kind}`,
    `- Applied By: ${normalizeLine(apply.appliedBy, "unknown")}`,
    `- Run: ${normalizeLine(apply.runId, "n/a")}`,
    `- Why: ${normalizeLine(proposal.summary, "No summary recorded.")}`,
    `- Rationale: ${normalizeLine(proposal.proposedChange.rationale, "No rationale recorded.")}`,
    "",
  ];
  const journalPath = resolveProposalApplyJournalPath();
  await mkdir(path.dirname(journalPath), { recursive: true });
  await appendFile(journalPath, `${entryLines.join("\n")}\n`, "utf8");
}
