import type { WorldChangeProposal, LineageChange } from "./domain.js";

export function proposalToLineageChange(p: WorldChangeProposal): LineageChange {
  return {
    id: p.id,
    description: p.description,
    affectsInvariants: p.affectsSystems,
    status: "PROVISIONAL",
    acceptedAt: new Date().toISOString(),
    validatedAt: null,
    originType: p.origin,
  };
}
