import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function getOpsConsoleBaseUrl(): string {
  return (process.env.OPS_CONSOLE_URL ?? 'http://localhost:4000').replace(/\/+$/, '');
}

async function proxyCep(request: Request, pathSegments: string[]) {
  const baseUrl = getOpsConsoleBaseUrl();
  const url = new URL(request.url);
  const destination = `${baseUrl}/cep/${pathSegments.map((segment) => encodeURIComponent(segment)).join('/')}${url.search}`;
  const init: RequestInit = {
    method: request.method,
    headers: {},
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    const contentType = request.headers.get('content-type');
    if (contentType) {
      (init.headers as Record<string, string>)['content-type'] = contentType;
    }
    init.body = await request.text();
  }

  const response = await fetch(destination, init);
  const contentType = response.headers.get('content-type') ?? 'application/json';
  const body = await response.text();

  return new NextResponse(body, {
    status: response.status,
    headers: { 'content-type': contentType },
  });
}

export async function GET(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  return proxyCep(request, (await params).path ?? []);
}

export async function POST(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  return proxyCep(request, (await params).path ?? []);
}

export async function PATCH(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  return proxyCep(request, (await params).path ?? []);
}
