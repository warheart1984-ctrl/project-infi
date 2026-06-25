import axios from "axios";

const DASHBOARD_BASE = process.env.REACT_APP_DASHBOARD_URL || "http://127.0.0.1:8100";

export async function listMissions(limit = 100) {
  const resp = await axios.get(`${DASHBOARD_BASE}/dashboard/missions?limit=${limit}`);
  return resp.data;
}

export async function getTrace(missionId) {
  const resp = await axios.get(
    `${DASHBOARD_BASE}/dashboard/trace/${encodeURIComponent(missionId)}`
  );
  return resp.data;
}

export async function lawKernelSummary(limit = 50) {
  const resp = await axios.get(`${DASHBOARD_BASE}/dashboard/law_kernel?limit=${limit}`);
  return resp.data;
}

export async function listEvidenceCycles() {
  const resp = await axios.get(`${DASHBOARD_BASE}/dashboard/evidence-cycles`);
  return resp.data;
}
