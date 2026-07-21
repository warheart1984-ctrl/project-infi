import type { AAISPreferredModel, AAISRoutingHint, AAISRoutingCatalog } from './capabilities.js';

export type AAISCodingCapabilityName =
  | 'RefactorCode'
  | 'GenerateModule'
  | 'ExplainCode'
  | 'AddTests'
  | 'MigrateAPI'
  | 'DesignSchema';

export type AAISCodingRoutingKey = keyof AAISRoutingCatalog;

export interface AAISCodingCapability {
  id: string;
  name: AAISCodingCapabilityName;
  description: string;
  inputs: readonly string[];
  governanceConstraints: readonly string[];
  routing: Partial<Record<AAISCodingRoutingKey, AAISRoutingHint>>;
}

function createCapability(
  name: AAISCodingCapabilityName,
  description: string,
  inputs: readonly string[],
  governanceConstraints: readonly string[],
  routingHints: Partial<Record<AAISCodingRoutingKey, AAISRoutingHint>>,
): AAISCodingCapability {
  return {
    id: name,
    name,
    description,
    inputs,
    governanceConstraints,
    routing: routingHints,
  };
}

export const AAISCodingCapabilities = [
  createCapability(
    'RefactorCode',
    'Refactors existing code while preserving behavior and guarded logic.',
    ['target files', 'repo context', 'constraints', 'language', 'framework'],
    ['must preserve tests passing', 'must not remove guarded logic', 'must retain behavior unless explicitly approved'],
    {
      fastIteration: {
        preferredModel: 'qwen-3b',
        reason: 'small diffs',
      },
      deepReasoning: {
        preferredModel: 'qwen-7b',
        reason: 'large refactors',
      },
    },
  ),
  createCapability(
    'GenerateModule',
    'Generates a new module that matches the existing architecture and wiring.',
    ['target repo', 'architecture constraints', 'container wiring', 'tests'],
    ['must align with existing architecture', 'must register in DI/container', 'must include minimal tests'],
    {
      largePrompt: {
        preferredModel: 'qwen-7b',
        reason: 'module generation',
      },
    },
  ),
  createCapability(
    'ExplainCode',
    'Explains concrete code using live repository evidence and line references.',
    ['source files', 'target lines', 'language', 'framework'],
    ['no hallucinated APIs', 'must reference actual code lines', 'must distinguish fact from inference'],
    {
      smallPrompt: {
        preferredModel: 'qwen-3b',
        reason: 'short explanation',
      },
    },
  ),
  createCapability(
    'AddTests',
    'Adds tests that cover critical paths and enforce requirements.',
    ['target files', 'requirements', 'test framework', 'expected failure cases'],
    ['must compile', 'must cover critical paths', 'must link to requirements'],
    {
      deepReasoning: {
        preferredModel: 'qwen-7b',
        reason: 'test design requires deeper reasoning',
      },
      conformanceSuiteGenerator: {
        preferredModel: 'qwen-7b',
        reason: 'conformance suite generation',
      },
    },
  ),
  createCapability(
    'MigrateAPI',
    'Migrates an API while preserving behavior and documenting deprecated paths.',
    ['source API', 'target API', 'compatibility constraints', 'docs'],
    ['must preserve behavior', 'must mark deprecated paths', 'must update docs'],
    {
      deepReasoning: {
        preferredModel: 'qwen-7b',
        reason: 'API migration and compatibility analysis',
      },
    },
  ),
  createCapability(
    'DesignSchema',
    'Designs governed data shapes that remain traceable to requirements.',
    ['requirements', 'data shapes', 'constraints', 'evidence'],
    ['must align with governed data shapes', 'must be traceable to requirements', 'must support provenance'],
    {
      referenceRuntimeComposer: {
        preferredModel: 'qwen-7b',
        reason: 'schema design requires approved runtime composition',
      },
    },
  ),
] as const;

export function listAAISCodingCapabilities(): readonly AAISCodingCapability[] {
  return AAISCodingCapabilities;
}

export function resolveAAISCodingCapability(name: string): AAISCodingCapability | undefined {
  const normalized = name.trim().toLowerCase();
  return AAISCodingCapabilities.find((capability) => capability.name.toLowerCase() === normalized || capability.id.toLowerCase() === normalized);
}

export function getCodingCapabilityRouting(
  name: AAISCodingCapabilityName,
): Partial<Record<AAISCodingRoutingKey, AAISRoutingHint>> {
  return resolveAAISCodingCapability(name)?.routing ?? {};
}

export function getCodingCapabilityPrimaryModel(name: AAISCodingCapabilityName): AAISPreferredModel | undefined {
  const capability = resolveAAISCodingCapability(name);
  if (!capability) {
    return undefined;
  }

  const preferredHint =
    capability.routing.fastIteration ??
    capability.routing.smallPrompt ??
    capability.routing.largePrompt ??
    capability.routing.deepReasoning ??
    capability.routing.referenceRuntimeComposer ??
    capability.routing.conformanceSuiteGenerator ??
    capability.routing.implementationGapResolver;

  return preferredHint?.preferredModel;
}
