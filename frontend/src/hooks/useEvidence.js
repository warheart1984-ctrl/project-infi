import { useCallback, useEffect, useState } from 'react';
import { fetchEvidence } from '../lib/constitutionalApi';

export function useEvidence(evidenceId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(evidenceId));
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    if (!evidenceId) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await fetchEvidence(evidenceId));
    } catch (err) {
      setError(err);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [evidenceId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
