import type { ReferenceImage } from './types.js';

export function dataUrlToBase64(dataUrl: string): string {
  const comma = dataUrl.indexOf(',');
  return comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl;
}

export async function resolveReferenceBase64(
  reference: ReferenceImage | undefined,
  fetchImpl: typeof fetch,
): Promise<string> {
  if (!reference) {
    throw new Error('This provider requires a reference image (local file or --url)');
  }
  if (reference.kind === 'dataUrl') {
    return dataUrlToBase64(reference.dataUrl);
  }
  const response = await fetchImpl(reference.url);
  if (!response.ok) {
    throw new Error(`Failed to fetch reference image: ${response.status} ${response.statusText}`);
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  if (bytes.length === 0) {
    throw new Error('Reference image URL returned an empty body');
  }
  return bytes.toString('base64');
}
