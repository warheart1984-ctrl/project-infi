/** Declarative invariant definitions for the governance engine. See governance/invariants/GOV-INV-1.0.md */

export interface InvariantCheck {
  id: string;
  description: string;
  severity: "info" | "warning" | "error" | "critical";
}

export const CONSTITUTIONAL_INVARIANTS: InvariantCheck[] = [
  {
    id: "INV-COR-PURE",
    description: "Governance must not mutate COR state vector",
    severity: "critical",
  },
  {
    id: "INV-HYGIENE",
    description: "Repo hygiene must pass before approve",
    severity: "error",
  },
  {
    id: "INV-STRUCTURAL",
    description: "Critical structural integrity issues block release",
    severity: "error",
  },
  {
    id: "INV-PROOF-CRITICAL",
    description: "Critical proof analysis claims block approve",
    severity: "critical",
  },
  {
    id: "INV-LINEAGE",
    description: "Broken provenance chains block approve decisions",
    severity: "warning",
  },
];
