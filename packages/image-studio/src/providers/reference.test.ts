import { describe, expect, it } from 'vitest';

import { dataUrlToBase64, resolveReferenceBase64 } from './reference.js';

describe('reference helpers', () => {
  it('strips the data url prefix', () => {
    expect(dataUrlToBase64('data:image/png;base64,aGVsbG8=')).toBe('aGVsbG8=');
    expect(dataUrlToBase64('plainbase64')).toBe('plainbase64');
  });

  it('resolves data urls to raw base64', async () => {
    const base64 = await resolveReferenceBase64({ kind: 'dataUrl', dataUrl: 'data:image/png;base64,aGVsbG8=' }, (() => {}) as unknown as typeof fetch);
    expect(base64).toBe('aGVsbG8=');
  });

  it('fetches urls and base64-encodes the bytes', async () => {
    const fetchImpl = async () => new Response(new Blob([new Uint8Array([1, 2, 3])]), { status: 200 });
    const base64 = await resolveReferenceBase64({ kind: 'url', url: 'https://example.com/i.png' }, fetchImpl as unknown as typeof fetch);
    expect(base64).toBe(Buffer.from([1, 2, 3]).toString('base64'));
  });

  it('throws when no reference image is provided', async () => {
    await expect(resolveReferenceBase64(undefined, (() => {}) as unknown as typeof fetch)).rejects.toThrow(
      /requires a reference image/,
    );
  });

  it('throws when the url fetch fails', async () => {
    const fetchImpl = async () => new Response('not found', { status: 404 });
    await expect(
      resolveReferenceBase64({ kind: 'url', url: 'https://example.com/missing.png' }, fetchImpl as unknown as typeof fetch),
    ).rejects.toThrow(/404/);
  });
});
