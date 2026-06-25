/** Tri-Strata cognitive memory types (AAES-OS v0.1). */

export type IntentHorizon = 'short' | 'mid' | 'long';

export interface IntentRecord {
  intent_id: string;
  timestamp: number;
  operator_id: string;
  semantic_goal: string;
  constraints: string[];
  success_criteria: string[];
  horizon: IntentHorizon;
  version: number;
  signature: string;
  content_hash: string;
  prev_hash: string | null;
}

export interface AuthorityScope {
  resources: string[];
  time_limit_ms: number;
  intent_version: number;
}

export interface AuthorityToken {
  token_id: string;
  issued_by: string;
  issued_to: string;
  capabilities: string[];
  scope: AuthorityScope;
  delegation_chain: string[];
  signature: string;
  revoked: boolean;
}

export interface AuthorityEnvelope {
  token: AuthorityToken;
  nonce: string;
  envelope_signature: string;
}

export type ExecutionSpanState = 'active' | 'completed' | 'terminated' | 'faulted';

export type TraceStepType = 'reasoning' | 'tool_call' | 'observation' | 'decision';

export interface ExecutionTrace {
  timestamp: number;
  step_type: TraceStepType;
  content: string;
  justification: string;
  references: {
    intent_version: number;
    authority_token_id: string;
  };
}

export interface ExecutionSpan {
  span_id: string;
  parent_span: string | null;
  intent_version: number;
  authority_token_id: string;
  start_time: number;
  state: ExecutionSpanState;
  trace: ExecutionTrace[];
}

export interface ReasoningStep {
  content: string;
  justification: string;
  step_type?: TraceStepType;
  confidence?: number;
}

export interface ReplayViolation {
  code: GovernedFaultCode | 'EXECUTION_FAULT';
  message: string;
  step_index?: number;
}

export interface ReplayResult {
  success: boolean;
  violations: ReplayViolation[];
  step_index?: number;
}

export type GovernedFaultCode =
  | 'INTENT_DRIFT'
  | 'AUTHORITY_INVALID'
  | 'AUTHORITY_REVOKED'
  | 'EXECUTION_UNGOVERNED'
  | 'MISSING_TRACE_JUSTIFICATION';
