import type { RewriteProposal, RewriteProposalGovernance } from "@shared/schema";
import {
  getDiffChangedContentLines,
  isCommentOnlyDiffPreview,
  isProposalApplyableDiff,
} from "@shared/proposal-diff";

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function evaluateRewriteProposalGovernance(
  proposedChange: RewriteProposal["proposedChange"],
  now = Date.now(),
): RewriteProposalGovernance {
  const changedLines = getDiffChangedContentLines(proposedChange.diffPreview)
    .map((line) => line.trim())
    .filter(Boolean);
  const commentOnlyDiff = isCommentOnlyDiffPreview(proposedChange.diffPreview);
  const applyableDiff = isProposalApplyableDiff(proposedChange.diffPreview);
  const changeLineCount = clamp(changedLines.length, 0, 400);
  const mutationRisk =
    proposedChange.kind === "guardrail" || changeLineCount > 4 ? "medium" : "low";
  const legibility =
    proposedChange.rationale.trim().length > 480 || changeLineCount > 6 ? "review" : "clear";
  const notes = [
    "Human promotion required before repository apply.",
    applyableDiff
      ? "Diff preview contains a concrete applyable code change."
      : "Diff preview remains advisory and must not be auto-applied.",
    commentOnlyDiff
      ? "Changed lines are comment-only and should remain non-applyable."
      : "Changed lines include non-comment code or UI tokens.",
    `Mutation risk classified as ${mutationRisk}.`,
    `Legibility classified as ${legibility}.`,
  ];

  return {
    checkedAt: Math.max(1, Math.floor(now)),
    requiresHumanPromotion: true,
    applyableDiff,
    commentOnlyDiff,
    changeLineCount,
    mutationRisk,
    legibility,
    notes,
  };
}
