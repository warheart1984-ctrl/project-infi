import { readJson, removeStorageItem, writeJson } from './storage';

const ARCHIVE_KEY = 'nova-session-archives';
const ACTIVE_ARCHIVE_KEY = 'nova-active-session-archive';
const PENDING_ARCHIVE_KEY = 'nova-pending-session-archive';

export function buildDefaultNovaArchiveTitle() {
  return `Nova session ${new Date().toLocaleString()}`;
}

export async function listNovaSessionArchives() {
  const entries = readJson(ARCHIVE_KEY, []);
  return Array.isArray(entries) ? entries : [];
}

export async function openNovaSessionArchive(id) {
  const archive = (await listNovaSessionArchives()).find((entry) => entry.id === id);
  if (!archive) {
    throw new Error('Session archive not found.');
  }
  return archive;
}

export async function saveNovaSessionArchive(archive = {}) {
  const entry = {
    id: archive.id || `nova-archive-${Date.now()}`,
    title: archive.title || buildDefaultNovaArchiveTitle(),
    createdAt: archive.createdAt || new Date().toISOString(),
    ...archive,
  };
  const entries = [entry, ...(await listNovaSessionArchives()).filter((item) => item.id !== entry.id)];
  writeJson(ARCHIVE_KEY, entries);
  return entry;
}

export async function deleteNovaSessionArchive(id) {
  const entries = (await listNovaSessionArchives()).filter((entry) => entry.id !== id);
  writeJson(ARCHIVE_KEY, entries);
  return entries;
}

export function setActiveNovaSessionArchive(archive) {
  writeJson(ACTIVE_ARCHIVE_KEY, archive);
}

export function getActiveNovaSessionArchive() {
  return readJson(ACTIVE_ARCHIVE_KEY, null);
}

export function clearActiveNovaSessionArchive() {
  removeStorageItem(ACTIVE_ARCHIVE_KEY);
}

export function setPendingNovaSessionArchive(archive) {
  writeJson(PENDING_ARCHIVE_KEY, archive);
}

export function consumePendingNovaSessionArchive() {
  const archive = readJson(PENDING_ARCHIVE_KEY, null);
  removeStorageItem(PENDING_ARCHIVE_KEY);
  return archive;
}

export function toLoadedSessionArchivePayload(archive) {
  if (!archive) {
    return null;
  }
  return {
    id: archive.id,
    title: archive.title,
    messages: archive.messages || archive.turns || [],
  };
}
