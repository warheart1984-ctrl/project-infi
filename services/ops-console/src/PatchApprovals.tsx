import { useCallback, useEffect, useState } from 'react';

export interface PatchRecordView {
  patchId: string;
  status: string;
  proposedBy: string;
  approvedBy?: string;
  createdAt: string;
  updatedAt: string;
}

interface PatchApprovalsProps {
  apiBase: string;
}

export function PatchApprovals({ apiBase }: PatchApprovalsProps) {
  const [patches, setPatches] = useState<PatchRecordView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/patches`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const body = (await response.json()) as { patches: PatchRecordView[] };
      setPatches(body.patches);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const act = async (patchId: string, action: 'approve' | 'reject' | 'deploy') => {
    const response = await fetch(`${apiBase}/patches/${encodeURIComponent(patchId)}/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actor: 'operator-console' }),
    });
    if (!response.ok) {
      const text = await response.text();
      setError(text || `Failed to ${action} ${patchId}`);
      return;
    }
    await refresh();
  };

  if (loading) {
    return <p>Loading patch ledger…</p>;
  }

  return (
    <section>
      <h2>Patch approvals</h2>
      {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
        <thead>
          <tr>
            <th align="left">Patch ID</th>
            <th align="left">Status</th>
            <th align="left">Proposed by</th>
            <th align="left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {patches.map((patch) => (
            <tr key={patch.patchId}>
              <td>{patch.patchId}</td>
              <td>{patch.status}</td>
              <td>{patch.proposedBy}</td>
              <td>
                {patch.status === 'PROPOSED' ? (
                  <>
                    <button type="button" onClick={() => void act(patch.patchId, 'approve')}>
                      Approve
                    </button>{' '}
                    <button type="button" onClick={() => void act(patch.patchId, 'reject')}>
                      Reject
                    </button>
                  </>
                ) : null}
                {patch.status === 'APPROVED' ? (
                  <button type="button" onClick={() => void act(patch.patchId, 'deploy')}>
                    Deploy
                  </button>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
