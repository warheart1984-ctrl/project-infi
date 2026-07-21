import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse as parseYaml } from 'yaml';
import type { CompiledPolicy, PolicyDefinition, PolicyGuardrails, PolicyRouting } from '../types.js';
import { governanceMatches } from '../router/CodingRouter.js';

interface RawPolicyDefinition {
  id: string;
  when: PolicyDefinition['when'];
  then: {
    routing?: {
      allowed_backends?: string[];
      preferred_backends?: string[];
      allowedBackends?: string[];
      preferredBackends?: string[];
    };
    guardrails?: {
      max_tokens_out?: number;
      require_identity_role?: string[];
      maxTokensOut?: number;
      requireIdentityRole?: string[];
    };
  };
}

function normalizeRouting(raw?: RawPolicyDefinition['then']['routing']): PolicyRouting {
  if (!raw) return {};
  return {
    allowedBackends: raw.allowedBackends ?? raw.allowed_backends,
    preferredBackends: raw.preferredBackends ?? raw.preferred_backends,
  };
}

function normalizeGuardrails(raw?: RawPolicyDefinition['then']['guardrails']): PolicyGuardrails {
  if (!raw) return {};
  return {
    maxTokensOut: raw.maxTokensOut ?? raw.max_tokens_out,
    requireIdentityRole: raw.requireIdentityRole ?? raw.require_identity_role,
  };
}

function normalizeDefinition(raw: RawPolicyDefinition): PolicyDefinition {
  return {
    id: raw.id,
    when: raw.when,
    then: {
      routing: normalizeRouting(raw.then.routing),
      guardrails: normalizeGuardrails(raw.then.guardrails),
    },
  };
}

export function compilePolicy(def: PolicyDefinition): CompiledPolicy {
  return {
    id: def.id,
    routing: def.then.routing ?? {},
    guardrails: def.then.guardrails ?? {},
    matches(governance) {
      return governanceMatches(def.when, governance);
    },
  };
}

export function compilePolicies(definitions: PolicyDefinition[]): CompiledPolicy[] {
  return definitions.map(compilePolicy);
}

export function loadPoliciesFromYaml(yamlText: string): CompiledPolicy[] {
  const parsed = parseYaml(yamlText) as RawPolicyDefinition[] | null;
  if (!Array.isArray(parsed)) {
    throw new Error('Policy YAML must be a top-level array');
  }
  return compilePolicies(parsed.map(normalizeDefinition));
}

export function loadCodingPolicyPack(): CompiledPolicy[] {
  const here = dirname(fileURLToPath(import.meta.url));
  const yamlPath = join(here, 'coding.yaml');
  const yamlText = readFileSync(yamlPath, 'utf8');
  return loadPoliciesFromYaml(yamlText);
}

export function loadFreeCodingPolicyPack(): CompiledPolicy[] {
  const here = dirname(fileURLToPath(import.meta.url));
  const yamlPath = join(here, 'coding-free.yaml');
  const yamlText = readFileSync(yamlPath, 'utf8');
  return loadPoliciesFromYaml(yamlText);
}
