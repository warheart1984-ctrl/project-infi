import { NextResponse } from 'next/server';

import { getDefaultManagedServiceId, listManagedServiceSummaries } from '../../../lib/operatorConsole';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({
    defaultServiceId: getDefaultManagedServiceId(),
    services: listManagedServiceSummaries(),
  });
}
