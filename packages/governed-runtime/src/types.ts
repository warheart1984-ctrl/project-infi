import type { AuthToken } from '@aaes-os/sovren';

export type CognitiveRisk = 'low' | 'medium' | 'high' | 'critical';

export interface Intent {
  id: string;
  kind: string;
  description: string;
}

export interface Identity {
  actorId: string;
  role: string;
}

export interface GovernanceContext {
  domain: string;
  risk: CognitiveRisk;
  tags?: string[];
}

export interface TraceContext {
  traceId: string;
  intentId: string;
  actorId: string;
  policyIds: string[];
  timestamps: { createdAt: number };
}

export interface ChatInput {
  systemPrompt: string;
  userContent: string;
  context?: string;
}

export interface GovernedChatRequest {
  intent: Intent;
  identity: Identity;
  governance: GovernanceContext;
  trace: TraceContext;
  input: ChatInput;
  authToken?: AuthToken;
}

export interface ChatOutput {
  text: string;
  tokensIn: number;
  tokensOut: number;
  latencyMs: number;
}

export interface GovernanceResult {
  policyIds: string[];
  violations: string[];
}

export interface GovernedChatResponse {
  intentId: string;
  backendName: string;
  trace: TraceContext;
  output: ChatOutput;
  governance: GovernanceResult;
}

export interface CodeCompletionRequest {
  intent: Intent;
  identity: Identity;
  governance: GovernanceContext;
  trace: TraceContext;
  prefix: string;
  suffix?: string;
  language?: string;
}

export interface CodeCompletionResponse {
  intentId: string;
  backendName: string;
  completion: string;
  tokensIn: number;
  tokensOut: number;
  latencyMs: number;
}

export interface BackendSupports {
  chat: boolean;
  code: boolean;
  tools?: boolean;
}

export interface CodingBackend {
  name: string;
  supports: BackendSupports;
  chat(req: GovernedChatRequest): Promise<GovernedChatResponse>;
  completeCode?(req: CodeCompletionRequest): Promise<CodeCompletionResponse>;
}

export interface PolicyRouting {
  allowedBackends?: string[];
  preferredBackends?: string[];
}

export interface PolicyGuardrails {
  maxTokensOut?: number;
  requireIdentityRole?: string[];
}

export interface PolicyDefinition {
  id: string;
  when: {
    domain?: string;
    risk?: CognitiveRisk;
    tags?: string[];
  };
  then: {
    routing?: PolicyRouting;
    guardrails?: PolicyGuardrails;
  };
}

export interface CompiledPolicy {
  id: string;
  routing: PolicyRouting;
  guardrails: PolicyGuardrails;
  matches(governance: GovernanceContext): boolean;
}
