import { mkdtemp, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { tmpdir } from 'node:os';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { buildGoogleDriveAuthorization, canonicalize, googleDriveStatus, listGoogleDriveFiles, revokeGoogleDriveToken, storeGoogleDriveToken } from './googleDrive.js';

describe('governed Google Drive connector', () => {
  let directory: string;
  const actor = 'owner-1'; const organization = 'org-1';

  beforeEach(async () => {
    directory = await mkdtemp(path.join(tmpdir(), 'aais-drive-'));
    process.env.GOOGLE_CLIENT_ID = 'test-client.apps.googleusercontent.com';
    process.env.GOOGLE_CLIENT_SECRET = 'test-secret';
    process.env.GOOGLE_DRIVE_STATE_SECRET = 'state-secret-for-tests';
    process.env.GOOGLE_DRIVE_TOKEN_KEY = 'token-key-for-tests';
    process.env.GOOGLE_DRIVE_TOKEN_VAULT = path.join(directory, 'tokens.json');
    process.env.GOOGLE_DRIVE_EVIDENCE_LOG = path.join(directory, 'evidence.jsonl');
    delete process.env.GOOGLE_DRIVE_SCOPES;
  });

  afterEach(async () => { vi.unstubAllGlobals(); await rm(directory, { recursive: true, force: true }); });

  it('requests offline least-privilege access and persists no access token plaintext', async () => {
    const authorization = buildGoogleDriveAuthorization(actor, organization, 'https://unsafe.example');
    const url = new URL(authorization.authorizationUrl);
    expect(url.searchParams.get('access_type')).toBe('offline');
    expect(url.searchParams.get('scope')).toContain('openid email profile');
    expect(url.searchParams.get('scope')).toContain('https://www.googleapis.com/auth/drive.file');
    expect(url.searchParams.get('prompt')).toBe('consent');
    await storeGoogleDriveToken(actor, organization, { accessToken: 'access-secret', refreshToken: 'refresh-secret', expiresAt: new Date(Date.now()+3600000).toISOString(), scope: 'drive.file', tokenType: 'Bearer' });
    const raw = await readFile(process.env.GOOGLE_DRIVE_TOKEN_VAULT!, 'utf8');
    expect(raw).not.toContain('access-secret'); expect(raw).not.toContain('refresh-secret');
    expect(await googleDriveStatus(actor, organization)).toMatchObject({ connected: true });
  });

  it('lists files with canonical evidence and revokes fail-closed', async () => {
    await storeGoogleDriveToken(actor, organization, { accessToken: 'access', refreshToken: 'refresh', expiresAt: new Date(Date.now()+3600000).toISOString(), scope: 'drive.file', tokenType: 'Bearer' });
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ files: [{ id: 'file-1', name: 'Artifact' }] }), { status: 200 }))
      .mockResolvedValueOnce(new Response('', { status: 200 })));
    const result = await listGoogleDriveFiles(actor, organization);
    expect(result.receipt).toMatchObject({ operation: 'list', actor_id: actor, organization_id: organization, provider: 'google-drive' });
    expect(result.receipt.replay_receipt.canonical_hash).toMatch(/^[a-f0-9]{64}$/);
    await revokeGoogleDriveToken(actor, organization);
    expect(await googleDriveStatus(actor, organization)).toEqual({ connected: false });
  });

  it('implements deterministic NFC canonicalization and rejects non-finite values', () => {
    expect(canonicalize({ b: 'e\u0301', a: 1 })).toBe('{"a":1,"b":"é"}');
    expect(() => canonicalize({ value: Number.NaN })).toThrow('HALT:CANONICALIZATION_ERROR');
  });
});
