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

export async function GET(request: Request, { params }: { params: Promise<{ organizationId: string; kind: string }> }) {
  const sessionId = readCookie(request, 'platform_customer_session');
  if (!sessionId) {
    return NextResponse.json({ error: 'missing session' }, { status: 401 });
  }

  const { organizationId, kind } = await params;
  if (!['pricing', 'routing', 'entitlements'].includes(kind)) {
    return NextResponse.json({ error: 'unsupported audit kind' }, { status: 400 });
  }

  const response = await fetch(`${getPlatformApiBaseUrl()}/v1/organizations/${encodeURIComponent(organizationId)}/audit/${encodeURIComponent(kind)}`, {
    headers: { 'x-session-id': sessionId },
  });
  const payload = await response.json().catch(() => ({ error: 'organization audit lookup failed' }));
  return NextResponse.json(payload, { status: response.status });
}
