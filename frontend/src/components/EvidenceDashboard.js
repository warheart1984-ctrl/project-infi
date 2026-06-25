import React, { useEffect, useState } from "react";
import { listEvidenceCycles } from "../api";

export default function EvidenceDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const rows = await listEvidenceCycles();
        if (!cancelled) {
          setData(rows);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <div className="error">Error loading evidence cycles: {error.message}</div>;
  }
  if (!data) {
    return <div className="placeholder">Loading evidence cycles…</div>;
  }
  if (data.length === 0) {
    return <div className="placeholder">No verified evidence cycles yet.</div>;
  }

  return (
    <div className="evidence-dashboard">
      <h2>PEL + Claims + Verification</h2>
      <table className="evidence-table">
        <thead>
          <tr>
            <th>PEL ID</th>
            <th>Decision</th>
            <th>Claim</th>
            <th>Tier</th>
            <th>Verification</th>
            <th>Verified At</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.verification.id}>
              <td>{row.pel.id}</td>
              <td>{row.pel.decision}</td>
              <td>{row.claim.summary}</td>
              <td>{row.claim.tier}</td>
              <td>{row.verification.status}</td>
              <td>{row.verification.verified_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
