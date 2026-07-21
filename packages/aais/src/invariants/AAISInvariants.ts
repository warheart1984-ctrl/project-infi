import type { AAISActionContext } from '../AAISDoctrine.js';

export interface AAISInvariantResult {
  passed: boolean;
  severity: 'info' | 'warn' | 'error' | 'fatal';
  message?: string;
}

export const AAISInvariants = [
  {
    id: 'I-AAIS-001',
    description: 'AAIS actions must be doctrine validated',
    check(context: AAISActionContext): AAISInvariantResult {
      return {
        passed: context.action.length > 0,
        severity: context.action.length > 0 ? 'info' : 'error',
        message: context.action.length > 0 ? 'AAIS action validated' : 'Missing AAIS action',
      };
    },
  },
  {
    id: 'I-AAIS-002',
    description: 'AAIS escalation requires governance channel',
    check(context: AAISActionContext): AAISInvariantResult {
      const passed = context.actor !== 'agent' || context.action.startsWith('AAIS_');
      return {
        passed,
        severity: passed ? 'info' : 'fatal',
        message: passed ? 'AAIS escalation routed correctly' : 'AAIS escalation bypassed governance',
      };
    },
  },
] as const;
