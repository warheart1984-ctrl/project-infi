import React from 'react';

const STATUS_CLASS = {
  admitted: 'status-pill-admitted',
  experimental: 'status-pill-experimental',
};

export function StatusPill({ status, updated = false }) {
  const cls = STATUS_CLASS[status] || '';
  return (
    <span className={`status-pill ${cls} ${updated ? 'status-pill-updated' : ''}`}>
      {status}
    </span>
  );
}
