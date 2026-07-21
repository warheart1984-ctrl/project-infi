import { NextResponse } from 'next/server';

import { getCoriAlphaWorkspaceSummary } from '@aaes-os/platform-core';

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

  return NextResponse.json({
    surface: getCoriAlphaWorkspaceSummary(),
    sessionId,
  });
}
