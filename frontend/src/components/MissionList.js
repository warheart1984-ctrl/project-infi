import React from "react";

export default function MissionList({ missions, onSelect }) {
  return (
    <div>
      <h2>Recent Missions</h2>
      <ul className="mission-list">
        {missions.length === 0 && <li>No missions found</li>}
        {missions.map((m, idx) => {
          const id = m.mission_id || `anon-${idx}`;
          return (
            <li key={id} onClick={() => onSelect(id)} className="mission-item">
              <div className="mission-time">{m.time}</div>
              <div className="mission-id">{id}</div>
              <div className="mission-status">{m.status || "unknown"}</div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
