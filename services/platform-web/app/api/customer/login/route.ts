import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const body = await request.json().catch(() => ({}));
  const response = await fetch(`${baseUrl}/v1/customers/login`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      email: String(body.email ?? body.ownerId ?? 'customer@example.com'),
      password: body.password ? String(body.password) : undefined,
      authProvider: String(body.authProvider ?? 'email'),
      authSubject: body.authSubject ? String(body.authSubject) : undefined,
      governanceProfile: String(body.governanceProfile ?? 'balanced'),
    }),
  });

  const payload = await response.json().catch(() => ({ error: 'login failed' }));
  const next = NextResponse.json(payload, { status: response.status });
  const sessionId = payload?.session?.sessionId;
  if (typeof sessionId === 'string' && sessionId.length > 0) {
    next.cookies.set('platform_customer_session', sessionId, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
    });
  }
  return next;
}
