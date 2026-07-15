import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code') ?? '';
  const state = url.searchParams.get('state') ?? '';
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const response = await fetch(`${baseUrl}/v1/integrations/google-drive/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`, { cache: 'no-store' });
  const payload = await response.json().catch(() => ({ error: 'Google Drive callback failed' }));
  if (!response.ok) return NextResponse.json(payload, { status: response.status });
  return NextResponse.redirect(new URL(String((payload as { returnTo?: string }).returnTo ?? '/integrations/google-drive'), request.url));
}
