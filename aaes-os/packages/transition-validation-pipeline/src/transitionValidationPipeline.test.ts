import { describe, expect, it } from 'vitest';

import { ConstitutionalEnforcementNode, createResourceFloorInvariant } from '@aaes-os/constitutional-enforcement-node';
import { runTransitionPipeline, validateTransition } from './index.js';

const context = {
  actor: 'operator',
  mriSnapshot: { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
  runtimeContext: { corridorId: 'ops', capabilities: ['state:commit'] },
};

describe('transition validation pipeline', () => {
  it('stops malformed transitions before CEN evaluation', () => {
    const validation = validateTransition({ transitionId: '', payload: null });

    expect(validation.valid).toBe(false);
    expect(validation.stage).toBe('pre_validation');
  });

  it('blocks commits on CEN denial and commits exactly once on allow', () => {
    const node = new ConstitutionalEnforcementNode({
      invariants: [createResourceFloorInvariant('coordination', 60)],
    });
    const denied = runTransitionPipeline({
      transitionId: 'tvp:deny',
      transitionType: 'state_update',
      payload: { coordination: 42 },
      requestedCapabilities: ['state:commit'],
      context,
    }, node);
    const allowed = runTransitionPipeline({
      transitionId: 'tvp:allow',
      transitionType: 'state_update',
      payload: { coordination: 64 },
      requestedCapabilities: ['state:commit'],
      context,
    }, node);

    expect(denied.allowed).toBe(false);
    expect(denied.committed).toBe(false);
    expect(denied.stages).toEqual(['pre_validation', 'constitutional_validation', 'block', 'receipt']);
    expect(allowed.allowed).toBe(true);
    expect(allowed.committed).toBe(true);
    expect(node.getState('tvp:allow')).toEqual({ coordination: 64 });
  });
});
