import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request, { params }: { params: Promise<{ provider: string }> }) {
  return handleCallback(request, await params);
}

export async function POST(request: Request, { params }: { params: Promise<{ provider: string }> }) {
  return handleCallback(request, await params);
}

async function handleCallback(request: Request, params: { provider: string }) {
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const { code, state, governanceProfile } = await readCallbackParameters(request);
  const response = await fetch(
    `${baseUrl}/v1/auth/oauth/${params.provider}/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&governanceProfile=${encodeURIComponent(governanceProfile)}`,
  );
  const payload = await response.json().catch(() => ({ error: 'oauth callback failed' }));
  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status });
  }
  const next = NextResponse.redirect(new URL(String((payload as { redirectTo?: string }).redirectTo ?? '/account'), request.url));
  const sessionId = (payload as { session?: { sessionId?: string } }).session?.sessionId;
  if (typeof sessionId === 'string' && sessionId.length > 0) {
    next.cookies.set('platform_customer_session', sessionId, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
    });
  }
  return next;
}

async function readCallbackParameters(request: Request): Promise<{ code: string; state: string; governanceProfile: string }> {
  const url = new URL(request.url);
  const governanceProfile = url.searchParams.get('governanceProfile') ?? 'balanced';
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  if (code && state) {
    return { code, state, governanceProfile };
  }
  const formData = await request.formData().catch(() => null);
  if (formData) {
    return {
      code: String(formData.get('code') ?? ''),
      state: String(formData.get('state') ?? ''),
      governanceProfile: String(formData.get('governanceProfile') ?? governanceProfile),
    };
  }
  return { code: '', state: '', governanceProfile };
}
