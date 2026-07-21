import { forwardJson, platformSessionFetch } from '../../../../../lib/platformSessionProxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get('q');
  return forwardJson(await platformSessionFetch(request, `/v1/integrations/google-drive/files${q ? `?q=${encodeURIComponent(q)}` : ''}`));
}

export async function POST(request: Request) {
  return forwardJson(await platformSessionFetch(request, '/v1/integrations/google-drive/files', { method: 'POST', headers: { 'content-type': 'application/json' }, body: await request.text() }));
}

export async function DELETE(request: Request) {
  return forwardJson(await platformSessionFetch(request, '/v1/integrations/google-drive', { method: 'DELETE' }));
}
