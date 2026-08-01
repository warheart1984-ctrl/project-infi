import { describe, expect, it } from 'vitest';

import { detectImageType, imageExtension, bufferToDataUrl } from './detectImageType.js';

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const JPEG = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10]);
const GIF = Buffer.from([0x47, 0x49, 0x46, 0x38, 0x39, 0x61]);
const WEBP = Buffer.from('RIFF1234WEBP', 'latin1');
const UNKNOWN = Buffer.from([0x00, 0x01, 0x02, 0x03]);

describe('detectImageType', () => {
  it('detects png, jpeg, gif, and webp magic bytes', () => {
    expect(detectImageType(PNG)).toBe('image/png');
    expect(detectImageType(JPEG)).toBe('image/jpeg');
    expect(detectImageType(GIF)).toBe('image/gif');
    expect(detectImageType(WEBP)).toBe('image/webp');
  });

  it('returns undefined for unknown bytes', () => {
    expect(detectImageType(UNKNOWN)).toBeUndefined();
  });

  it('maps content types to file extensions', () => {
    expect(imageExtension('image/png')).toBe('png');
    expect(imageExtension('image/jpeg')).toBe('jpg');
    expect(imageExtension('image/webp')).toBe('webp');
    expect(imageExtension('application/octet-stream')).toBe('bin');
  });

  it('creates base64 data urls', () => {
    const url = bufferToDataUrl(PNG, 'image/png');
    expect(url.startsWith('data:image/png;base64,')).toBe(true);
    expect(Buffer.from(url.split(',')[1], 'base64')).toEqual(PNG);
  });
});
