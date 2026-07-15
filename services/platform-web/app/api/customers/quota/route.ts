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

export async function GET(request: Request) {
  const sessionId = readCookie(request, 'platform_customer_session');
  if (!sessionId) {
    return NextResponse.json({ error: 'missing session' }, { status: 401 });
  }
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  const response = await fetch(`${baseUrl}/v1/customers/quota`, {
    headers: { 'x-session-id': sessionId },
  });
  const payload = await response.json().catch(() => ({ error: 'quota lookup failed' }));
  return NextResponse.json(payload, { status: response.status });
}
