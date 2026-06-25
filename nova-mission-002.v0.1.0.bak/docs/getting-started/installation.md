# Installation

## Requirements

- Node.js 18+
- npm or pnpm

## From This Repository

```bash
git clone <repo-url> nova-mission-002
cd nova-mission-002
npm install
npm run build
```

## Verify

```bash
npx nova generate "Write a fibonacci function in TypeScript."
```

You should see generated code and a JSON receipts array.

## Configure Invariants

Edit `config/nova.config.ts` and register invariants at startup:

```typescript
import { governance } from "nova-sdk";
import { invariants } from "./nova.config";

for (const inv of invariants) {
  await governance.requireInvariant(inv);
}
```
