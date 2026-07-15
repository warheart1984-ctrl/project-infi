import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const body = await request.json().catch(() => ({}));
  const response = await fetch(`${baseUrl}/v1/customers/signup`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      email: String(body.email ?? ''),
      password: body.password ? String(body.password) : undefined,
      displayName: body.displayName ? String(body.displayName) : undefined,
      authProvider: String(body.authProvider ?? 'email'),
      authSubject: body.authSubject ? String(body.authSubject) : undefined,
      planId: body.planId ?? 'free',
      organizationId: body.organizationId ? String(body.organizationId) : undefined,
      organizationName: body.organizationName ? String(body.organizationName) : undefined,
      organizationRole: body.organizationRole ? String(body.organizationRole) : undefined,
      governanceProfile: String(body.governanceProfile ?? 'balanced'),
    }),
  });

  const payload = await response.json().catch(() => ({ error: 'signup failed' }));
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
