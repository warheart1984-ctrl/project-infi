import { useCallback, useEffect, useState } from 'react';
import { fetchLaw } from '../lib/constitutionalApi';

export function useLaw(lawId) {
  const [law, setLaw] = useState(null);
  const [loading, setLoading] = useState(Boolean(lawId));
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    if (!lawId) {
      setLaw(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setLaw(await fetchLaw(lawId));
    } catch (err) {
      setError(err);
      setLaw(null);
    } finally {
      setLoading(false);
    }
  }, [lawId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { law, loading, error, refresh };
}
