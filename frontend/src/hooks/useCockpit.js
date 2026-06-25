import { useCallback, useEffect, useState } from 'react';
import { fetchCockpitSummary } from '../lib/constitutionalApi';

export function useCockpit() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [epochPulse, setEpochPulse] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await fetchCockpitSummary();
      setSummary(next);
      setEpochPulse(true);
      window.setTimeout(() => setEpochPulse(false), 400);
    } catch (err) {
      setError(err);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 8000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  return { summary, loading, error, refresh, epochPulse };
}
