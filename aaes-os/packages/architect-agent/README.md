# Architect Agent

`@aaes-os/architect-agent` implements the governed architect-agent loop:

1. `UGRUCRBridge` derives a deterministic `CognitiveModeContract` from a
   `UnifiedGovernanceContract` and a cognitive situation.
2. `ArchitectRuntime` produces the invariant-bound architecture plan.
3. `BuilderRuntime` creates deterministic patches for every authorized target
   and binds them to an explicit pre-state snapshot.
4. `IntegrationRuntime` wraps all patches in one reversible mutation envelope.
5. `SafetyRuntime` verifies contract lineage, target authorization, inverse
   operations, patch hashes, envelope hashes, and EGL-1 status.
6. `ArchitectAgentLoop` replays integration, evaluates EGL-1, applies the
   safety veto, and emits an evidence receipt for the governed act.

## Usage

```typescript
import {
  ArchitectAgentLoop,
  createDefaultUnifiedGovernanceContract,
} from '@aaes-os/architect-agent';

const loop = new ArchitectAgentLoop(createDefaultUnifiedGovernanceContract());
const act = loop.execute({
  situation: {
    situationId: 'situation:example',
    intent: 'build a governed runtime change',
    risk: 'high',
    requestedRuntimes: [
      'ArchitectRuntime',
      'BuilderRuntime',
      'IntegrationRuntime',
      'SafetyRuntime',
    ],
    targetFiles: ['src/runtime.ts'],
  },
  pre_state: {
    'src/runtime.ts': 'export const version = 1;\n',
  },
  issued_at: '2026-06-30T20:00:00.000Z',
});

if (act.safety.verdict !== 'ALLOW') {
  throw new Error(act.safety.reason);
}
```

The caller supplies exact pre-state content and an explicit issuance timestamp.
The loop has no filesystem mutation, clock access, network access, or hidden
state. Applying the authorized patches remains the responsibility of a
separate mutation executor.

## Security Boundary

The package provides deterministic SHA-256 integrity identifiers, exact inverse
patches, replay equivalence, and evidence-receipt binding. These hashes detect
drift and tampering inside the governed pipeline; they are not identities or
cryptographic signatures. Production authority still requires an external,
key-backed signer and durable append-only ledger.

See [SECURITY.md](SECURITY.md) for the package threat model, trust assumptions,
side-effect inventory, sensitive-data warning, and non-goals.

## Verification

```bash
pnpm --filter @aaes-os/architect-agent run build
pnpm --filter @aaes-os/architect-agent run test
pnpm smoke:architect-agent
```
