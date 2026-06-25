import React, { useEffect, useState } from "react";
import { getTrace } from "../api";

export default function TraceView({ missionId }) {
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    getTrace(missionId)
      .then((data) => {
        if (mounted) {
          setTrace(data.trace || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || "Failed to fetch trace");
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [missionId]);

  if (loading) return <div>Loading trace...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!trace || trace.length === 0) return <div>No trace events found for {missionId}</div>;

  return (
    <div>
      <h2>Trace for {missionId}</h2>
      <div className="trace-list">
        {trace.map((e, i) => (
          <div key={i} className="trace-event">
            <div className="trace-meta">
              <strong>{e.event_type}</strong> <span className="trace-time">{e.time}</span>
            </div>
            <pre className="trace-payload">{JSON.stringify(e.payload, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}
