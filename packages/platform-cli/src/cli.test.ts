import { describe, expect, it } from 'vitest';

import { parseArgs, COMMANDS } from './cli.js';

describe('platform-cli', () => {
  it('defines all required commands', () => {
    expect(Object.keys(COMMANDS)).toEqual(
      expect.arrayContaining(['login', 'publish', 'governance', 'connect', 'completion', 'lirl intent']),
    );
  });

  it('parses flags', () => {
    const args = parseArgs(['login', '--owner', 'dev', '--profile', 'strict']);
    expect(args._).toBe('login');
    expect(args.owner).toBe('dev');
    expect(args.profile).toBe('strict');
  });
});
