import { describe, expect, it } from 'vitest';

import {
  DEFAULT_PROOF_SURFACE_CATALOG_URL,
  LOCAL_PROOF_SURFACE_CATALOG_URL,
  normalizeProofSurfaceCatalogUrl,
  operatorConfig,
  resolveInitialProofSurfaceCatalogUrl,
} from './index.js';

describe('operatorConfig', () => {
  it('publishes one shared proof-surface catalog manifest', () => {
    expect(operatorConfig.proofSurfaceCatalog.defaultUrl).toBe(DEFAULT_PROOF_SURFACE_CATALOG_URL);
    expect(operatorConfig.proofSurfaceCatalog.localRegistryValue).toBe(LOCAL_PROOF_SURFACE_CATALOG_URL);
  });

  it('normalizes explicit local and remote catalog values', () => {
    expect(normalizeProofSurfaceCatalogUrl('local')).toBe(LOCAL_PROOF_SURFACE_CATALOG_URL);
    expect(normalizeProofSurfaceCatalogUrl('https://example.com/proof-surfaces')).toBe(
      'https://example.com/proof-surfaces',
    );
  });

  it('resolves the query string before stored defaults', () => {
    expect(resolveInitialProofSurfaceCatalogUrl('?catalogUrl=local-registry', 'https://stored.example/catalog')).toBe(
      LOCAL_PROOF_SURFACE_CATALOG_URL,
    );
  });
});
