# Nova Coding Shell

Nova is a Codex-style governed coding terminal.

## Usage

```ts
const nova = assistant.nova(
  { actorId: 'jon', role: 'developer' },
  { systemPrompt: 'You are Nova, a governed coding shell.' },
);

const result = await nova.runCommand('Refactor this function to use async/await');
console.log(result.output.text);
```

## Governance Context

Each command creates a governed request with:

- **domain**: `coding`
- **risk**: `low` (configurable)
- **tags**: `['general']` (configurable)

Policies in the coding policy pack determine which backend handles the request.
