import { NextResponse } from 'next/server';
import { platformSessionFetch } from '../../../../../lib/platformSessionProxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const response = await platformSessionFetch(request, '/v1/integrations/google-drive/start?returnTo=%2Fintegrations%2Fgoogle-drive');
  const payload = await response.json().catch(() => ({ error: 'Google Drive authorization failed' }));
  if (!response.ok) return NextResponse.json(payload, { status: response.status });
  return NextResponse.redirect(String((payload as { authorizationUrl?: string }).authorizationUrl ?? '/integrations/google-drive'));
}
