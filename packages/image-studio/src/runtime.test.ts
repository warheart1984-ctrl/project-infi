import { describe, expect, it } from 'vitest';

import { describeImageStudioCapability, imageStudioProvenance, IMAGE_STUDIO_CAPABILITY } from './runtime.js';

describe('image-studio AAIS integration', () => {
  it('exposes the Image-to-Image Studio capability', () => {
    const capability = describeImageStudioCapability();
    expect(capability.name).toBe(IMAGE_STUDIO_CAPABILITY);
    expect(capability.id).toBe('image-to-image-studio');
    expect(capability.kind).toBe('generator');
  });

  it('produces AAIS provenance for an image prompt', () => {
    const provenance = imageStudioProvenance('watercolor version');
    expect(provenance.capabilityName).toBe('Capability Discovery Engine');
    expect(provenance.routingHint).toBeDefined();
  });
});
