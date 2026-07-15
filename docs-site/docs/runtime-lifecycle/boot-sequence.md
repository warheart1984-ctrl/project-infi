# Boot Sequence

## Coding Subsystem Boot

```ts
import { PatternLedger } from '@aaes-os/aaes-governance';
import { CodingAssistant } from '@aaes-os/coding-assistant';
import {
  CodingRouter,
  CodexBackend,
  CursorBackend,
  DeepSeekCoderBackend,
  GroqBackend,
  LocalLlmBackend,
  loadCodingPolicyPack,
} from '@aaes-os/governed-runtime';

// 1. Register backends
const backends = [
  new CodexBackend(process.env.OPENAI_API_KEY ?? ''),
  new CursorBackend(),
  new DeepSeekCoderBackend(),
  new GroqBackend(process.env.GROQ_API_KEY ?? ''),
  new LocalLlmBackend('http://localhost:8080'),
];

// 2. Load policies
const policies = loadCodingPolicyPack();

// 3. Initialize ledger
const ledger = new PatternLedger();

// 4. Create router and assistant
const router = new CodingRouter(backends, policies, ledger);
const assistant = new CodingAssistant(router);
```

## Verification

```bash
pnpm --filter @aaes-os/governed-runtime test
pnpm --filter @aaes-os/coding-assistant build
```
