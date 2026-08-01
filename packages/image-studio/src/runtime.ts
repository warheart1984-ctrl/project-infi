import { getAAISProvenance, resolveAAISCapability, type AAISProvenance } from '@aaes-os/aais';

export const IMAGE_STUDIO_CAPABILITY = 'Image-to-Image Studio';

export function describeImageStudioCapability() {
  const resolved = resolveAAISCapability(IMAGE_STUDIO_CAPABILITY);
  if (resolved) {
    return resolved;
  }
  return {
    id: 'image-to-image-studio',
    name: IMAGE_STUDIO_CAPABILITY,
    kind: 'generator' as const,
    summary: 'Transforms existing images using free cloud-hosted image-to-image models.',
  };
}

export function imageStudioProvenance(prompt: string): AAISProvenance {
  return getAAISProvenance({ surface: 'image-studio', prompt });
}
