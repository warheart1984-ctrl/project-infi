import { readJson, removeStorageItem, writeJson } from './storage';

const HISTORY_KEY = 'aais-history';
const HISTORY_LIMIT = 100;

export function getHistoryEntries() {
  const entries = readJson(HISTORY_KEY, []);
  return Array.isArray(entries) ? entries : [];
}

export function addHistoryEntry(entry) {
  const nextEntry = {
    id: entry?.id || `history-${Date.now()}`,
    createdAt: entry?.createdAt || new Date().toISOString(),
    ...entry,
  };
  const entries = [nextEntry, ...getHistoryEntries().filter((item) => item.id !== nextEntry.id)]
    .slice(0, HISTORY_LIMIT);
  writeJson(HISTORY_KEY, entries);
  return entries;
}

export function deleteHistoryEntry(id) {
  const entries = getHistoryEntries().filter((entry) => entry.id !== id);
  writeJson(HISTORY_KEY, entries);
  return entries;
}

export function clearHistoryEntries() {
  removeStorageItem(HISTORY_KEY);
  return [];
}
