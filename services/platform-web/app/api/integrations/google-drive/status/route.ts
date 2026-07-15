import { forwardJson, platformSessionFetch } from '../../../../../lib/platformSessionProxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request) { return forwardJson(await platformSessionFetch(request, '/v1/integrations/google-drive/status')); }
