export type ArticleType =
  | "IDENTITY"
  | "MECHANICS"
  | "ECONOMY"
  | "POLITICS"
  | "LORE"
  | "GOVERNANCE"
  | "META";

export interface WorldInvariant {
  id: string;
  name: string;
  description: string;
  domain: ArticleType;
  status: "ACTIVE" | "UNDER_REVIEW" | "DEPRECATED";
  weight: number;
  impact: number;
}

export interface AmendmentRule {
  id: string;
  description: string;
  requiredRoles: string[];
  requiredQuorum: number;
  requiresValidation: boolean;
}

export interface WorldArticle {
  id: string;
  type: ArticleType;
  title: string;
  text: string;
  invariants: string[];
}

export interface WorldConstitution {
  id: string;
  version: string;
  createdAt: string;
  articles: WorldArticle[];
  invariants: WorldInvariant[];
  amendmentRules: AmendmentRule[];
}

export function defaultConstitution(): WorldConstitution {
  const createdAt = new Date().toISOString();
  return {
    id: "world-constitution-v1",
    version: "1.0.0",
    createdAt,
    invariants: [
      {
        id: "K1",
        name: "Identity Coherence",
        description: "LA and SA must keep the world recognizably itself.",
        domain: "IDENTITY",
        status: "ACTIVE",
        weight: 0.9,
        impact: 0.8,
      },
      {
        id: "K2",
        name: "Generative Grammar",
        description: "PLA/LA/SA must strengthen world grammar, not just vocabulary.",
        domain: "MECHANICS",
        status: "ACTIVE",
        weight: 0.85,
        impact: 0.7,
      },
      {
        id: "K3",
        name: "Integrability",
        description: "PLA must integrate into LA; LA into SA; no orphaned branches.",
        domain: "GOVERNANCE",
        status: "ACTIVE",
        weight: 0.8,
        impact: 0.75,
      },
      {
        id: "K4",
        name: "Reconstructability",
        description: "Combined PLA+LA+SA growth must stay below reconstruction threshold.",
        domain: "META",
        status: "ACTIVE",
        weight: 0.9,
        impact: 0.9,
      },
    ],
    articles: [
      {
        id: "ART-IDENTITY",
        type: "IDENTITY",
        title: "World Identity",
        text: "The world maintains continuity across rule changes and player actions.",
        invariants: ["K1"],
      },
      {
        id: "ART-GOV",
        type: "GOVERNANCE",
        title: "Amendment Process",
        text: "World-rule changes require steward quorum and post-acceptance validation.",
        invariants: ["K3", "K4"],
      },
    ],
    amendmentRules: [
      {
        id: "RULE-STEWARD-AMEND",
        description: "Structural amendments require steward role and majority quorum.",
        requiredRoles: ["STEWARD"],
        requiredQuorum: 0.5,
        requiresValidation: true,
      },
    ],
  };
}
