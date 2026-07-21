import type { LirlOperatorSnapshot, LirlVerdict } from './types.js';

export interface OperatorViewInput {
  verdict: LirlVerdict;
  receiptId: string;
  intentId: string;
  actorId: string;
  action: string;
  memoryWritten: boolean;
  reasons: string[];
  issuedAt: string;
}

export function buildOperatorSnapshot(input: OperatorViewInput): LirlOperatorSnapshot {
  const reasonsHtml =
    input.reasons.length === 0
      ? '<li><em>none</em></li>'
      : input.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>LIRL Operator View</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; background: #0b1020; color: #e8edf4; }
    .card { max-width: 40rem; border: 1px solid #2d3a4f; border-radius: 8px; padding: 1.25rem; background: #141a2a; }
    .ok { color: #3d9970; } .bad { color: #c44; }
    code { word-break: break-all; }
  </style>
</head>
<body>
  <div class="card">
    <h1>LIRL Operator View</h1>
    <p>Verdict: <strong class="${input.verdict === 'ACCEPT' ? 'ok' : 'bad'}">${input.verdict}</strong></p>
    <p>Receipt: <code>${escapeHtml(input.receiptId)}</code></p>
    <p>Intent: <code>${escapeHtml(input.intentId)}</code></p>
    <p>Actor: <code>${escapeHtml(input.actorId)}</code></p>
    <p>Action: <code>${escapeHtml(input.action)}</code></p>
    <p>Memory written: <strong>${input.memoryWritten ? 'yes' : 'no'}</strong></p>
    <p>Issued: ${escapeHtml(input.issuedAt)}</p>
    <h2>Reasons</h2>
    <ul>${reasonsHtml}</ul>
  </div>
</body>
</html>`;

  return { ...input, html };
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}
