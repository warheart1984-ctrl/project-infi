export type ActionType = "edit" | "create" | "delete" | "run" | "plan" | "generate" | "refactor";

export interface AgentAction {
  type: ActionType;
  payload: Record<string, unknown>;
}

export interface CodeContext {
  files?: string[];
  language?: string;
}

export interface ConstraintSet {
  maxLines?: number;
  allowedLanguages?: string[];
}

export interface WorkspaceContext {
  root: string;
  files: string[];
  openFiles: string[];
}

export interface FileContent {
  path: string;
  content: string;
}

export interface ApplyResult {
  success: boolean;
  path?: string;
  message?: string;
}

export interface TestResult {
  name: string;
  passed: boolean;
  message?: string;
}

export interface RefactorResult {
  file: string;
  diff: string;
  receipts: import("./receipts").GovernanceReceipt[];
}

export interface VerificationResult {
  ok: boolean;
  reason?: string;
  invariantsChecked: string[];
}

export interface ValidationResult {
  ok: boolean;
  reason?: string;
  violation?: import("./invariants").InvariantViolation;
}

export interface GenerateCodeInput {
  prompt: string;
  context?: CodeContext;
  constraints?: ConstraintSet;
}

export interface GenerateCodeResult {
  code: string;
  receipts: import("./receipts").GovernanceReceipt[];
}

export interface PlanInput {
  goal: string;
  context?: WorkspaceContext;
}

export interface RefactorInput {
  file: string;
  instructions: string;
}

export interface VerifyInput {
  action: AgentAction;
}

export interface ApplyPatchInput {
  diff: string;
  reason: string;
}

export interface ApplyPatchResult {
  success: boolean;
  receipts: import("./receipts").GovernanceReceipt[];
}
