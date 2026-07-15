import { randomUUID } from 'node:crypto';

import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

import type { AgentEntity } from './AgentEntity.js';

export type AgentActionType = 'move' | 'writeKnowledge' | 'compute' | 'communicate';

export interface AgentAction {
  type: AgentActionType;
  agentId: string;
  payload: Record<string, unknown>;
}

export function createMoveAction(agent: AgentEntity, x: number, y: number): AgentAction {
  return {
    type: 'move',
    agentId: agent.id,
    payload: { x, y },
  };
}

export function createKnowledgeAction(agent: AgentEntity, fact: string): AgentAction {
  return {
    type: 'writeKnowledge',
    agentId: agent.id,
    payload: { fact },
  };
}

export function createComputeAction(agent: AgentEntity, job: string): AgentAction {
  return {
    type: 'compute',
    agentId: agent.id,
    payload: { job },
  };
}

export function createCommunicateAction(agent: AgentEntity, targetId: string, message: string): AgentAction {
  return {
    type: 'communicate',
    agentId: agent.id,
    payload: { targetId, message },
  };
}

export function sendAgentAction(bus: TriCoreBus, action: AgentAction): TriCoreMessage {
  const message: TriCoreMessage = {
    id: randomUUID(),
    from: 'agent',
    to: 'runtime',
    type: 'AGENT_ACT',
    payload: action,
    timestamp: Date.now(),
    correlationId: action.agentId,
  };
  const routed = bus.send(message);
  return routed ?? message;
}
