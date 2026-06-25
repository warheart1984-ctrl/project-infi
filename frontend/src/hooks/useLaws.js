import { useCallback, useEffect, useState } from 'react';
import { fetchLaws } from '../lib/constitutionalApi';

export function useLaws() {
  const [laws, setLaws] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await fetchLaws();
      setLaws(Array.isArray(rows) ? rows : []);
    } catch (err) {
      setError(err);
      setLaws([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { laws, loading, error, refresh };
}
