import { apiDelete, apiGet, apiPatch, apiPost } from '../lib/api';

export function getMemories(params = {}) {
  return apiGet('/api/jarvis/memory', { params });
}

export function getMemoryBoard(params = {}) {
  return apiGet('/api/jarvis/memory/board', { params });
}

export function addMemory(payload) {
  return apiPost('/api/jarvis/memory', payload);
}

export function addOverrideMemory(payload) {
  return apiPost('/api/jarvis/memory/override', payload);
}

export function updateMemory(memoryId, payload) {
  return apiPatch(`/api/jarvis/memory/${memoryId}`, payload);
}

export function deleteMemory(memoryId) {
  return apiDelete(`/api/jarvis/memory/${memoryId}`);
}
