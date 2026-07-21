import { describe, expect, it } from 'vitest';

import { MAGIC, NovaCodaClient, NovaCodaMessageType, encodeHeader, decodeHeader } from './NovaCodaClient.js';

describe('NovaCodaClient', () => {
  it('encodes protocol magic bytes', () => {
    expect(MAGIC).toEqual(Buffer.from([0xc0, 0xda]));
  });

  it('encodes and decodes framed JSON bodies deterministically', () => {
    const body = Buffer.from(JSON.stringify({ capacity: 8, label: 'arena' }), 'utf8');
    const header = encodeHeader(NovaCodaMessageType.AllocArena, body);
    const decoded = decodeHeader(header);

    expect(decoded.msgType).toBe(NovaCodaMessageType.AllocArena);
    expect(decoded.bodyLength).toBe(body.length);
    expect(decoded.crc32).toBeGreaterThan(0);
  });

  it('constructs a client instance', () => {
    const client = new NovaCodaClient();
    expect(client).toBeInstanceOf(NovaCodaClient);
  });
});
