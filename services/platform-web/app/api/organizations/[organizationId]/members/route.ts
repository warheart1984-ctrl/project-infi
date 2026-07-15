import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

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

export async function GET(request: Request, { params }: { params: Promise<{ organizationId: string }> }) {
  const { organizationId } = await params;
  const sessionId = readCookie(request, 'platform_customer_session');
  if (!sessionId) {
    return NextResponse.json({ error: 'missing session' }, { status: 401 });
  }
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const response = await fetch(`${baseUrl}/v1/organizations/${organizationId}/members`, {
    headers: { 'x-session-id': sessionId },
  });
  const payload = await response.json().catch(() => ({ error: 'member lookup failed' }));
  return NextResponse.json(payload, { status: response.status });
}

export async function POST(request: Request, { params }: { params: Promise<{ organizationId: string }> }) {
  const { organizationId } = await params;
  const sessionId = readCookie(request, 'platform_customer_session');
  if (!sessionId) {
    return NextResponse.json({ error: 'missing session' }, { status: 401 });
  }
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const body = await request.json().catch(() => ({}));
  const response = await fetch(`${baseUrl}/v1/organizations/${organizationId}/members`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-session-id': sessionId,
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({ error: 'member update failed' }));
  return NextResponse.json(payload, { status: response.status });
}

export async function PATCH(request: Request, { params }: { params: Promise<{ organizationId: string }> }) {
  const { organizationId } = await params;
  const sessionId = readCookie(request, 'platform_customer_session');
  if (!sessionId) {
    return NextResponse.json({ error: 'missing session' }, { status: 401 });
  }
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const body = await request.json().catch(() => ({}));
  const response = await fetch(`${baseUrl}/v1/organizations/${organizationId}/members/${encodeURIComponent(String(body.customerId ?? ''))}`, {
    method: 'PATCH',
    headers: {
      'content-type': 'application/json',
      'x-session-id': sessionId,
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({ error: 'member role update failed' }));
  return NextResponse.json(payload, { status: response.status });
}
