import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function getPlatformApiBaseUrl(): string {
  return (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
}

function readCookie(request: Request, name: string): string | null {
  const cookieHeader = request.headers.get('cookie');
  if (!cookieHeader) {
    return null;
  }
  for (const part of cookieHeader.split(';')) {
    const [rawName, ...rest] = part.trim().split('=');
    if (rawName === name) {
      return decodeURIComponent(rest.join('='));
    }
  }
  return null;
}

export async function GET(request: Request) {
  const sessionId = readCookie(request, 'platform_customer_session');
  if (!sessionId) {
    return NextResponse.json({ error: 'missing session' }, { status: 401 });
  }

  const response = await fetch(`${getPlatformApiBaseUrl()}/v1/customers/me`, {
    headers: { 'x-session-id': sessionId },
  });
  const payload = await response.json().catch(() => ({ error: 'session lookup failed' }));
  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status });
  }

  const me = payload as {
    customer: {
      id: string;
      ownerId: string;
      email: string;
      displayName?: string;
      authProvider: string;
      authSubject?: string;
      planId: string;
      planName: string;
      entitlements: Record<string, unknown>;
      organizationId?: string;
      organizationRole?: string;
    };
    planId: string;
    planName: string;
    governanceProfile: 'strict' | 'balanced' | 'experimental';
    organizationId?: string;
    organizationRole?: string;
    organization?: unknown;
  };

  return NextResponse.json({
    customer: me.customer,
    session: {
      sessionId,
      customerId: me.customer.id,
      ownerId: me.customer.ownerId,
      email: me.customer.email,
      planId: me.planId,
      planName: me.planName,
      entitlements: me.customer.entitlements,
      governanceProfile: me.governanceProfile,
      organizationId: me.customer.organizationId ?? me.organizationId,
      organizationRole: me.customer.organizationRole ?? me.organizationRole,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    },
  });
}
