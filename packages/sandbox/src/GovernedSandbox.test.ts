import { describe, expect, it } from 'vitest';
import { GovernedSandbox } from './GovernedSandbox.js';

describe('GovernedSandbox', () => {
  it('captures console output', () => {
    const sandbox = new GovernedSandbox();
    const result = sandbox.execute("console.log('Hello', 42);");
    expect(result.error).toBeNull();
    expect(result.logs).toEqual(['Hello 42']);
  });

  it('blocks disallowed modules', () => {
    const sandbox = new GovernedSandbox({ allowedModules: ['path'] });
    const result = sandbox.execute("require('fs');");
    expect(result.error).toMatch(/Module not allowed: fs/);
  });

  it('allows listed modules', () => {
    const sandbox = new GovernedSandbox({ allowedModules: ['path'] });
    const result = sandbox.execute("console.log(require('path').sep);");
    expect(result.error).toBeNull();
    expect(result.logs.length).toBe(1);
  });

  it('times out long-running code', () => {
    const sandbox = new GovernedSandbox({ timeoutMs: 50 });
    const result = sandbox.execute('while (true) {}');
    expect(result.error).toBeTruthy();
  });
});
