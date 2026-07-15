'use client';

import { useCallback, useEffect, useState } from 'react';

type DriveFile = { id: string; name: string; mimeType: string; modifiedTime?: string; webViewLink?: string };
type DriveStatus = { connected: boolean; expiresAt?: string; scope?: string; error?: string };

export default function GoogleDriveIntegrationPage() {
  const [status, setStatus] = useState<DriveStatus | null>(null);
  const [files, setFiles] = useState<DriveFile[]>([]);
  const [name, setName] = useState('AAIS governed artifact.txt');
  const [content, setContent] = useState('Created by AAIS through the governed Google Drive connector.');
  const [message, setMessage] = useState('');

  const refresh = useCallback(async () => {
    const statusRes = await fetch('/api/integrations/google-drive/status', { cache: 'no-store' });
    const nextStatus = await statusRes.json() as DriveStatus;
    setStatus(nextStatus);
    if (statusRes.ok && nextStatus.connected) {
      const filesRes = await fetch('/api/integrations/google-drive/files', { cache: 'no-store' });
      const body = await filesRes.json() as { files?: DriveFile[]; error?: string };
      if (!filesRes.ok) throw new Error(body.error ?? 'Unable to list Drive files');
      setFiles(body.files ?? []);
    }
  }, []);

  useEffect(() => { void refresh().catch((error) => setMessage(error instanceof Error ? error.message : String(error))); }, [refresh]);

  async function createFile(event: React.FormEvent) {
    event.preventDefault();
    setMessage('');
    const response = await fetch('/api/integrations/google-drive/files', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name, content }) });
    const body = await response.json() as { file?: DriveFile; error?: string };
    if (!response.ok) throw new Error(body.error ?? 'Unable to create Drive file');
    setMessage(`Created ${body.file?.name ?? name}`);
    await refresh();
  }

  async function disconnect() {
    const response = await fetch('/api/integrations/google-drive/files', { method: 'DELETE' });
    if (!response.ok) throw new Error('Unable to disconnect Google Drive');
    setFiles([]); setStatus({ connected: false }); setMessage('Google Drive disconnected locally.');
  }

  return <main style={{ maxWidth: 960, margin: '0 auto', padding: '48px 24px', fontFamily: 'system-ui, sans-serif' }}>
    <p style={{ color: '#0f766e', fontWeight: 800, letterSpacing: '.1em' }}>AAIS INTEGRATION</p>
    <h1 style={{ fontSize: 'clamp(2.2rem, 6vw, 4.5rem)', margin: '8px 0' }}>Google Drive</h1>
    <p style={{ color: '#475569', maxWidth: 720 }}>Connect AAIS using least-privilege OAuth. Tokens are encrypted locally, refreshed automatically, and every file operation returns a governed evidence receipt.</p>
    {!status?.connected ? <a href="/api/integrations/google-drive/start" style={button}>Connect Google Drive</a> : <>
      <div style={card}><strong>Connected</strong><p style={{ color: '#64748b' }}>Scope: {status.scope}</p><button onClick={() => void disconnect().catch((error) => setMessage(String(error)))} style={secondary}>Disconnect</button></div>
      <form onSubmit={(event) => void createFile(event).catch((error) => setMessage(String(error)))} style={card}>
        <h2>Create governed text artifact</h2>
        <input value={name} onChange={(event) => setName(event.target.value)} style={input} required />
        <textarea value={content} onChange={(event) => setContent(event.target.value)} style={{ ...input, minHeight: 130 }} />
        <button style={button}>Create in Drive</button>
      </form>
      <section style={card}><h2>Accessible files</h2>{files.length ? <ul>{files.map((file) => <li key={file.id} style={{ margin: '10px 0' }}>{file.webViewLink ? <a href={file.webViewLink} target="_blank" rel="noreferrer">{file.name}</a> : file.name} <small>({file.mimeType})</small></li>)}</ul> : <p>No files are accessible yet. With drive.file scope, AAIS sees files it creates or files explicitly shared with it.</p>}</section>
    </>}
    {message ? <p style={{ fontWeight: 700 }}>{message}</p> : null}
  </main>;
}

const card: React.CSSProperties = { marginTop: 24, padding: 24, border: '1px solid #cbd5e1', borderRadius: 20, display: 'grid', gap: 12 };
const input: React.CSSProperties = { padding: 12, border: '1px solid #94a3b8', borderRadius: 10, font: 'inherit' };
const button: React.CSSProperties = { display: 'inline-block', width: 'fit-content', marginTop: 16, padding: '12px 18px', border: 0, borderRadius: 10, background: '#0f766e', color: 'white', fontWeight: 800, textDecoration: 'none', cursor: 'pointer' };
const secondary: React.CSSProperties = { ...button, marginTop: 0, background: '#e2e8f0', color: '#0f172a' };
