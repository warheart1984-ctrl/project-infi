import { NextResponse } from 'next/server';

export function readCookie(request: Request, name: string): string | null {
  const cookie = request.headers.get('cookie');
  if (!cookie) return null;
  for (const part of cookie.split(';')) {
    const [key, ...value] = part.trim().split('=');
    if (key === name) return decodeURIComponent(value.join('='));
  }
  return null;
}

export async function platformSessionFetch(request: Request, path: string, init?: RequestInit): Promise<Response> {
  const sessionId = readCookie(request, 'platform_customer_session');
  if (!sessionId) return NextResponse.json({ error: 'missing session' }, { status: 401 });
  const baseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
  return fetch(`${baseUrl}${path}`, { ...init, headers: { 'x-session-id': sessionId, ...(init?.headers ?? {}) }, cache: 'no-store' });
}

export async function forwardJson(response: Response): Promise<NextResponse> {
  if (response.status === 204) return new NextResponse(null, { status: 204 });
  const payload = await response.json().catch(() => ({ error: 'platform API request failed' }));
  return NextResponse.json(payload, { status: response.status });
}
