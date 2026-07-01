// AAES-OS Governance Dashboard Loader

const THEME_KEY = 'aaes-governance-theme';

async function loadJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Failed to load ${path}: ${response.status}`);
  return response.json();
}

async function loadYAML(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Failed to load ${path}: ${response.status}`);
  return jsyaml.load(await response.text());
}

function setStatus(id, message, isError = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = message;
  el.classList.toggle('error', isError);
}

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(saved);

  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem(THEME_KEY, next);
    });
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const link = document.getElementById('theme-css');
  const btn = document.getElementById('theme-toggle');
  if (link) link.href = theme === 'light' ? 'dashboard-light.css' : 'dashboard-dark.css';
  if (btn) btn.textContent = theme === 'light' ? 'Dark mode' : 'Light mode';
}

async function loadStatus() {
  const status = await loadJSON('governance-status.json');
  const ctsEl = document.getElementById('cts-status');
  const ctsCard = document.getElementById('cts-card');
  const docsEl = document.getElementById('docs-built');
  const adrsEl = document.getElementById('open-adrs');

  if (ctsEl) ctsEl.textContent = status.cts_status ?? 'UNKNOWN';
  if (ctsCard) {
    ctsCard.classList.toggle('pass', status.cts_status === 'PASS');
    ctsCard.classList.toggle('fail', status.cts_status === 'FAIL');
  }
  if (docsEl) docsEl.textContent = String(status.documents_built ?? 0);
  if (adrsEl) adrsEl.textContent = String(status.open_adrs ?? 0);
}

async function loadReceipts() {
  const table = document.getElementById('receipts-table');
  if (!table) return;

  const receipts = await loadJSON('receipts-index.json');
  table.innerHTML = '';

  if (!Array.isArray(receipts) || receipts.length === 0) {
    setStatus('receipts-status', 'No build receipts yet. Run make all or make receipt after make pdf.');
    return;
  }

  receipts.slice(0, 20).forEach((r) => {
    const row = document.createElement('tr');
    const commit = r.commit || 'unknown';
    row.innerHTML = `
      <td>${r.receipt_id ?? r.id ?? '—'}</td>
      <td>${r.document_id ?? '—'}</td>
      <td>${r.version ?? '—'}</td>
      <td>${commit.substring(0, 7)}</td>
      <td>${r.timestamp ?? '—'}</td>
    `;
    table.appendChild(row);
  });

  setStatus('receipts-status', `Showing ${Math.min(20, receipts.length)} of ${receipts.length} receipt(s).`);
}

async function loadRequirements() {
  const table = document.getElementById('requirements-table');
  if (!table) return;

  const reqs = await loadYAML('../registries/requirements.yaml');
  const list = reqs.requirements ?? [];
  table.innerHTML = '';

  list.forEach((req) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${req.id}</td>
      <td>${req.title}</td>
      <td>${req.principle ?? '—'}</td>
    `;
    table.appendChild(row);
  });

  setStatus('requirements-status', `${list.length} requirement(s) from registries/requirements.yaml.`);
}

async function loadEvents() {
  const ul = document.getElementById('gov-feed');
  if (!ul) return;

  const events = await loadJSON('events.json');
  ul.innerHTML = '';

  if (!Array.isArray(events) || events.length === 0) {
    setStatus('events-status', 'No governance events yet. Run make all to populate.');
    return;
  }

  events.slice(0, 20).forEach((e) => {
    const li = document.createElement('li');
    const label = e.summary ?? `${e.type?.toUpperCase() ?? 'EVENT'} — ${e.id}`;
    li.textContent = `[${e.timestamp}] ${label}`;
    ul.appendChild(li);
  });

  setStatus('events-status', `${Math.min(20, events.length)} of ${events.length} event(s).`);
}

async function loadDashboard() {
  initTheme();

  const tasks = [
    ['status', loadStatus, 'governance-status.json'],
    ['receipts', loadReceipts, 'receipts'],
    ['requirements', loadRequirements, 'requirements'],
    ['events', loadEvents, 'events'],
  ];

  for (const [, fn, label] of tasks) {
    try {
      await fn();
    } catch (err) {
      const statusId = label === 'receipts' ? 'receipts-status' : label === 'requirements' ? 'requirements-status' : label === 'events' ? 'events-status' : null;
      if (statusId) setStatus(statusId, err.message, true);
      else console.error(label, err);
    }
  }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
