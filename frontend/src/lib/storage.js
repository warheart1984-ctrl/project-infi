export function readJson(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function writeJson(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore unavailable storage, for example private mode quota failures.
  }
}

export function removeStorageItem(key) {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Ignore unavailable storage.
  }
}
