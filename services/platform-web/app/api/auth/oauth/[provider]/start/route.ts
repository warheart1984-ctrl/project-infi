import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request, { params }: { params: Promise<{ provider: string }> }) {
  const { provider } = await params;
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const url = new URL(request.url);
  const mode = url.searchParams.get('mode') ?? 'signup';
  const returnTo = url.searchParams.get('returnTo') ?? '/account';
  const response = await fetch(`${baseUrl}/v1/auth/oauth/${provider}/start?mode=${encodeURIComponent(mode)}&returnTo=${encodeURIComponent(returnTo)}`);
  const payload = await response.json().catch(() => ({ error: 'oauth start failed' }));
  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status });
  }
  return NextResponse.redirect(String((payload as { authorizationUrl?: string }).authorizationUrl ?? '/account'));
}
