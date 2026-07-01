
// Constitutional Node v0/v1 - DARPA-Style Modular Architecture
// Exports all subsystem modules for convenient consumption

// Invariant Engine
export { InvariantEngine, Invariant } from './invariant/InvariantEngine';

// Evidence Bundle Builder
export { EvidenceBundleBuilder, EvidenceItem } from './evidence/EvidenceBundleBuilder';

// Replay Engine
export { ReplayEngine, Snapshot } from './replay/ReplayEngine';

// EGL Evaluator
export { EglEvaluator, EquivalenceCriterion } from './egl/EglEvaluator';

// Conformance Suite
export { ConformanceSuite, TestCase } from './conformance/ConformanceSuite';

// Governance Module
export { GovernanceModule, GovernanceConfig } from './governance/GovernanceModule';

// Version information
export const VERSION = '0.1.0-DARPA';
export const NAME = 'Constitutional Node';

