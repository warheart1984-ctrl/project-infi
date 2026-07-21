export type OperatorConfig = {
  identity: {
    name: string;
    version: string;
    purpose: string;
  };
  proofSurfaceCatalog: {
    defaultUrl: string;
    localUrl: string;
    queryKey: string;
    storageKey: string;
    localRegistryValue: string;
  };
};

export const operatorConfig: OperatorConfig = {
  identity: {
    name: 'AAES-OS Operator Config',
    version: '1.0.0',
    purpose: 'Shared operator defaults for proof-surface catalog selection and backend routing.',
  },
  proofSurfaceCatalog: {
    defaultUrl: 'http://127.0.0.1:4000/proof-surfaces',
    localUrl: '/proof-surfaces',
    queryKey: 'catalogUrl',
    storageKey: 'aaes-os.operator.proof-surface-catalog-url',
    localRegistryValue: 'local-registry',
  },
} as const;

export const DEFAULT_PROOF_SURFACE_CATALOG_URL = operatorConfig.proofSurfaceCatalog.defaultUrl;
export const LOCAL_PROOF_SURFACE_CATALOG_URL = operatorConfig.proofSurfaceCatalog.localRegistryValue;
export const PROOF_SURFACE_CATALOG_QUERY_KEY = operatorConfig.proofSurfaceCatalog.queryKey;
export const PROOF_SURFACE_CATALOG_STORAGE_KEY = operatorConfig.proofSurfaceCatalog.storageKey;

export function normalizeProofSurfaceCatalogUrl(value: string | null | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) {
    return DEFAULT_PROOF_SURFACE_CATALOG_URL;
  }

  const normalized = trimmed.toLowerCase();
  if (normalized === 'local' || normalized === LOCAL_PROOF_SURFACE_CATALOG_URL) {
    return LOCAL_PROOF_SURFACE_CATALOG_URL;
  }

  return trimmed;
}

export function resolveInitialProofSurfaceCatalogUrl(
  search: string,
  storedValue: string | null,
): string {
  if (typeof search === 'string' && search.length > 0) {
    const queryValue = new URLSearchParams(search).get(PROOF_SURFACE_CATALOG_QUERY_KEY);
    if (queryValue !== null) {
      return normalizeProofSurfaceCatalogUrl(queryValue);
    }
  }

  return normalizeProofSurfaceCatalogUrl(storedValue);
}

export function isLocalProofSurfaceCatalogUrl(catalogUrl: string): boolean {
  return catalogUrl === LOCAL_PROOF_SURFACE_CATALOG_URL;
}

