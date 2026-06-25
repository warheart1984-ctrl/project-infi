import type { AgentAction } from "./actions";

export type InvariantSeverity = "error" | "warn";

export interface InvariantState {
  action: AgentAction;
  diff?: string;
  code?: string;
  prompt?: string;
  runTests?: () => Promise<{ failures: number }>;
}

export interface Invariant {
  id: string;
  description: string;
  severity: InvariantSeverity;
  check: (state: InvariantState) => boolean | Promise<boolean>;
}

export interface InvariantViolation {
  id: string;
  invariantId: string;
  description: string;
  message: string;
  severity: InvariantSeverity;
  action: AgentAction;
}
