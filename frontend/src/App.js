import React, { useState, useEffect } from "react";
import MissionList from "./components/MissionList";
import TraceView from "./components/TraceView";
import EvidenceDashboard from "./components/EvidenceDashboard";
import { listMissions } from "./api";

export default function App() {
  const [missions, setMissions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [view, setView] = useState("trace");

  useEffect(() => {
    async function load() {
      try {
        const data = await listMissions(50);
        setMissions(data);
        setLoadError(null);
      } catch (err) {
        console.error("Failed to load missions", err);
        setLoadError(err.message || "Failed to load missions");
      }
    }
    load();
  }, []);

  return (
    <div className="app">
      <header>
        <h1>CORI Trace Viewer</h1>
        <nav className="view-tabs">
          <button
            type="button"
            className={view === "trace" ? "active" : ""}
            onClick={() => setView("trace")}
          >
            Missions
          </button>
          <button
            type="button"
            className={view === "evidence" ? "active" : ""}
            onClick={() => setView("evidence")}
          >
            Evidence Cycles
          </button>
        </nav>
      </header>
      <main>
        {view === "evidence" ? (
          <section className="content full-width">
            <EvidenceDashboard />
          </section>
        ) : (
          <>
            <aside className="sidebar">
              {loadError && <div className="error">{loadError}</div>}
              <MissionList missions={missions} onSelect={setSelected} />
            </aside>
            <section className="content">
              {selected ? (
                <TraceView missionId={selected} />
              ) : (
                <div className="placeholder">
                  Select a mission to inspect its constitutional trace.
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
