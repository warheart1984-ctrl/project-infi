import { apiGet, apiPost } from './api';

export async function fetchSurvivabilityDashboard({ refresh = false } = {}) {
  const query = refresh ? '?refresh=true' : '';
  const response = await apiGet(`/api/survivability/dashboard${query}`);
  return response.data;
}

export async function refreshSurvivabilityDashboard() {
  const response = await apiGet('/api/survivability/dashboard?refresh=true');
  return response.data;
}

export async function fetchSurvivabilityAmendmentTemplate() {
  const response = await apiGet('/api/survivability/amendment-template');
  return response.data;
}

export function zoneTone(zone) {
  const normalized = String(zone || '').toLowerCase();
  if (normalized === 'green') return 'connected';
  if (normalized === 'red') return 'error';
  return 'warning';
}

export function formatScore(value, digits = 2) {
  const num = Number(value);
  if (Number.isNaN(num)) return '—';
  return num.toFixed(digits);
}
