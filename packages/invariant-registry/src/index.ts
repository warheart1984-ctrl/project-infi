import type {
  ConstitutionalDimension,
  ConstitutionalInvariant,
  EnforcementAction,
  ProposedTransition,
} from '@aaes-os/constitutional-enforcement-node';
import { compileInvariantDsl as compileLegacyInvariantDsl } from '@aaes-os/constitutional-enforcement-node';

export interface InvariantDefinition {
  id: string;
  name: string;
  measuredDimensions: ConstitutionalDimension[];
  threshold: number;
  expression: string;
  requiredAuthorityToken?: 'VT' | 'FT' | 'MRT' | 'RT';
  receiptMetadata: {
    subsystem: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
  };
}

export type InvariantRegistry = Map<string, InvariantDefinition>;

export const CANONICAL_INVARIANTS: InvariantDefinition[] = [
  canonical('INV-007', 'Resource Floor', ['continuity'], 50, 'continuity >= 50', 'high'),
  canonical('INV-014', 'Temporal Regularity', ['coordination'], 55, 'coordination >= 55', 'medium'),
  canonical('INV-021', 'Identity Boundary', ['memory'], 60, 'memory >= 60', 'critical', 'VT'),
  canonical('INV-003', 'Governance Drift', ['governance'], 70, 'governance >= 70', 'high'),
  canonical('INV-031', 'Coordination Floor', ['coordination'], 60, 'coordination >= 60', 'high'),
  canonical('INV-041', 'Confidence Floor', ['confidence'], 70, 'confidence >= 70', 'medium'),
];

export function createInvariantRegistry(seed: InvariantDefinition[] = []): InvariantRegistry {
  const registry = new Map<string, InvariantDefinition>();
  for (const invariant of seed) registerInvariant(registry, invariant);
  return registry;
}

export function registerInvariant(registry: InvariantRegistry, definition: InvariantDefinition): InvariantDefinition {
  registry.set(definition.id, definition);
  return definition;
}

export function getInvariant(registry: InvariantRegistry, id: string): InvariantDefinition {
  const invariant = registry.get(id);
  if (!invariant) throw new Error(`invariant not found: ${id}`);
  return invariant;
}

export function compileInvariantDsl(source: string): ConstitutionalInvariant {
  if (/^require\s+/i.test(source.trim())) {
    return compileLegacyInvariantDsl(source);
  }

  const parsed = parseIdsl(source);
  return {
    invariantId: parsed.invariantId,
    evaluate(transition: ProposedTransition) {
      const violated = evaluateExpression(parsed.expression, transition);
      return {
        invariantId: parsed.invariantId,
        passed: !violated,
        action: violated ? parsed.action : 'ALLOW',
        message: violated ? `IDSL condition violated: ${parsed.expression}` : 'IDSL condition satisfied',
      };
    },
  };
}

function parseIdsl(source: string): { invariantId: string; expression: string; action: EnforcementAction } {
  const normalized = source.trim().replace(/\s+/g, ' ');
  const match = /^WHEN (.+) THEN (ALLOW|DENY|FREEZE|MANDATORY_REVIEW) IF VIOLATED THEN DENY$/i.exec(normalized);
  if (!match) throw new Error(`unsupported IDSL syntax: ${source}`);
  const expression = match[1] ?? '';
  if (!/^(continuity|governance|memory|coordination|confidence|\d|\s|[<>=.!()ANDORNOT-])+$/i.test(expression)) {
    throw new Error(`unsupported IDSL syntax: ${source}`);
  }
  return {
    invariantId: `idsl:${hashLabel(expression)}:${(match[2] ?? 'DENY').toLowerCase()}`,
    expression,
    action: match[2] as EnforcementAction,
  };
}

function evaluateExpression(expression: string, transition: ProposedTransition): boolean {
  const orParts = expression.split(/\s+OR\s+/i);
  return orParts.some((orPart) =>
    orPart.split(/\s+AND\s+/i).every((andPart) => evaluateClause(andPart.trim(), transition)),
  );
}

function evaluateClause(clause: string, transition: ProposedTransition): boolean {
  const negated = /^NOT\s+/i.test(clause);
  const clean = clause.replace(/^NOT\s+/i, '').replace(/[()]/g, '').trim();
  const match = /^(continuity|governance|memory|coordination|confidence)\s*(<=|>=|==|<|>)\s*(-?\d+(?:\.\d+)?)$/i.exec(clean);
  if (!match) throw new Error(`unsupported IDSL clause: ${clause}`);
  const dimension = match[1] as ConstitutionalDimension;
  const operator = match[2] ?? '>=';
  const threshold = Number(match[3]);
  const value = readDimension(transition, dimension);
  const result = compare(value, operator, threshold);
  return negated ? !result : result;
}

function readDimension(transition: ProposedTransition, dimension: ConstitutionalDimension): number {
  if (transition.payload && typeof transition.payload === 'object' && !Array.isArray(transition.payload)) {
    const value = (transition.payload as Record<string, unknown>)[dimension];
    if (typeof value === 'number') return value;
  }
  return transition.context.mriSnapshot[dimension];
}

function compare(value: number, operator: string, threshold: number): boolean {
  switch (operator) {
    case '<': return value < threshold;
    case '<=': return value <= threshold;
    case '>': return value > threshold;
    case '>=': return value >= threshold;
    case '==': return value === threshold;
    default: throw new Error(`unsupported operator: ${operator}`);
  }
}

function canonical(
  id: string,
  name: string,
  measuredDimensions: ConstitutionalDimension[],
  threshold: number,
  expression: string,
  severity: InvariantDefinition['receiptMetadata']['severity'],
  requiredAuthorityToken?: InvariantDefinition['requiredAuthorityToken'],
): InvariantDefinition {
  return {
    id,
    name,
    measuredDimensions,
    threshold,
    expression,
    requiredAuthorityToken,
    receiptMetadata: { subsystem: 'constitutional-enforcement-node', severity },
  };
}

function hashLabel(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
}
