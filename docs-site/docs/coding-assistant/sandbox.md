# Governed Sandbox

The `@aaes-os/sandbox` package provides safe, isolated code execution.

## Features

- VM-isolated execution (`node:vm`)
- Module allowlisting via `require`
- Timeout enforcement
- Console log capture

## Usage

```ts
const sandbox = assistant.sandbox({ allowedModules: ['path'], timeoutMs: 2000 });

const { logs, error } = sandbox.execute(`
  const sep = require('path').sep;
  console.log('separator:', sep);
`);

console.log(logs);   // ['separator: \\' or '/']
console.log(error);  // null
```

## Security

- No filesystem access unless explicitly allowlisted
- No network access
- Execution timeout prevents infinite loops
