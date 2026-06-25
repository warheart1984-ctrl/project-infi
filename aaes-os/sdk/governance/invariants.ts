export interface InvariantInfo {
  id: string;
  description: string;
  phase: 'pre' | 'post';
}

export async function listInvariants(baseUrl: string): Promise<InvariantInfo[]> {
  const res = await fetch(`${baseUrl}/governance/invariants`);
  if (!res.ok) {
    throw new Error(`Failed to fetch invariants: ${res.status}`);
  }
  return res.json() as Promise<InvariantInfo[]>;
}

export async function describeInvariant(
  baseUrl: string,
  invariantId: string,
): Promise<InvariantInfo | undefined> {
  const all = await listInvariants(baseUrl);
  return all.find((inv) => inv.id === invariantId);
}
