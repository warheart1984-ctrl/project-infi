const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47]);
const JPEG_MAGIC = Buffer.from([0xff, 0xd8, 0xff]);
const GIF_MAGIC = Buffer.from([0x47, 0x49, 0x46, 0x38]);

export function detectImageType(bytes: Buffer): string | undefined {
  if (bytes.length >= PNG_MAGIC.length && PNG_MAGIC.equals(bytes.subarray(0, PNG_MAGIC.length))) {
    return 'image/png';
  }
  if (bytes.length >= JPEG_MAGIC.length && JPEG_MAGIC.equals(bytes.subarray(0, JPEG_MAGIC.length))) {
    return 'image/jpeg';
  }
  if (bytes.length >= GIF_MAGIC.length && GIF_MAGIC.equals(bytes.subarray(0, GIF_MAGIC.length))) {
    return 'image/gif';
  }
  if (
    bytes.length >= 12 &&
    bytes.toString('latin1', 0, 4) === 'RIFF' &&
    bytes.toString('latin1', 8, 12) === 'WEBP'
  ) {
    return 'image/webp';
  }
  return undefined;
}

export function imageExtension(contentType: string): string {
  switch (contentType) {
    case 'image/png':
      return 'png';
    case 'image/jpeg':
      return 'jpg';
    case 'image/gif':
      return 'gif';
    case 'image/webp':
      return 'webp';
    default:
      return 'bin';
  }
}

export function bufferToDataUrl(bytes: Buffer, contentType: string): string {
  return `data:${contentType};base64,${bytes.toString('base64')}`;
}
