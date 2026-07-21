import { afterEach, describe, expect, it, vi } from 'vitest';

import { buildCanonicalUgrRuntimeJson, parseUgrRuntimeCliArgs, runUgrRuntimeCli } from './cli.js';

describe('UGR runtime CLI', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('parses flags deterministically', () => {
    expect(parseUgrRuntimeCliArgs([])).toEqual({
      mode: 'snapshot',
      pretty: false,
      host: '127.0.0.1',
      port: 0,
    });
    expect(parseUgrRuntimeCliArgs(['serve', '--pretty', '--host', '0.0.0.0', '--port', '4040'])).toEqual({
      mode: 'serve',
      pretty: true,
      host: '0.0.0.0',
      port: 4040,
    });
  });

  it('builds canonical runtime JSON', async () => {
    const payload = await buildCanonicalUgrRuntimeJson();

    expect(payload.package).toBe('@aaes-os/ugr-runtime');
    expect(payload.version).toBe('0.1.0');
    expect(payload.runtime.api.routes).toEqual(expect.arrayContaining([
      expect.objectContaining({ method: 'GET', path: '/ugr/v1/glyphs' }),
    ]));
    expect(payload.runtime.records).toEqual({
      glyphs: [],
      artifacts: [],
      lineageEvents: [],
      organisms: [],
    });
  });

  it('emits JSON to stdout', async () => {
    const write = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
    const code = await runUgrRuntimeCli(['--pretty']);

    expect(code).toBe(0);
    expect(write).toHaveBeenCalledTimes(1);
    const output = String(write.mock.calls[0]?.[0] ?? '');
    expect(output).toContain('\n  "package": "@aaes-os/ugr-runtime"');
  });
});
