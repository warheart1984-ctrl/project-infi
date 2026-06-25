# Nova SDK

A Constitutional SDK for Lawful Agentic Coding Systems  
Built on CRK-1, the Constitutional Runtime Kernel.

Nova SDK provides:

- A governed agentic runtime
- A constitutional interface for code-generating agents
- A continuity substrate for traceability and reversibility
- A pattern ledger for action receipts
- A developer-facing API for building tools, agents, and extensions

Nova is not "an LLM wrapper."  
It is a lawful agent with a constitutional boundary contract.

## Features

- Agentic cognition (planning, refactoring, verification)
- Invariant Engine (safety, correctness, governance)
- Governance Receipts (traceable, reproducible actions)
- Continuity Substrate (snapshots, diffs, replay)
- Runtime Integration (workspace, tests, context)
- Event System (plan, action, violation, receipt)

## Install

```bash
npm install
npm run build
```

## Quickstart

```bash
npx nova generate "Write a function to compute Fibonacci numbers."
```

```typescript
import { nova, governance, runtime } from "nova-sdk";

const result = await nova.generateCode({
  prompt: "Write a function to compute Fibonacci numbers.",
});

console.log(result.code);
console.log(result.receipts);
```

## CLI

```bash
nova init              # Initialize a governed project
nova plan <goal>       # Generate a governed plan
nova generate <prompt> # Generate code with receipts
nova continuity        # Show continuity snapshot
nova receipts          # List governance receipts
```

## Documentation

See `/docs` for concepts, API reference, guides, and examples.

## Mission #002

This repository is the founder-independent reproduction bundle for Nova × CRK-1 integration verification. See `MISSION-002.md` and `observer/REPRO_PROTOCOL.md`.

## License

MIT
