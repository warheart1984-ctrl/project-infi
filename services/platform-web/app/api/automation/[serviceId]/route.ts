import { NextResponse } from 'next/server';

import { getManagedServiceStatus, runManagedServiceAction } from '../../../../lib/operatorConsole';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type RouteContext = {
  params: Promise<{
    serviceId: string;
  }>;
};

export async function GET(_request: Request, context: RouteContext) {
  const { serviceId } = await context.params;
  const status = await getManagedServiceStatus(serviceId);
  if (!status) {
    return NextResponse.json({ error: 'unknown service' }, { status: 404 });
  }

  return NextResponse.json(status);
}

export async function POST(request: Request, context: RouteContext) {
  const { serviceId } = await context.params;
  const body = await request.json().catch(() => ({}));
  const action = String(body.action ?? '').trim();

  if (!action) {
    return NextResponse.json({ error: 'missing action' }, { status: 400 });
  }

  const result = await runManagedServiceAction(serviceId, action);
  if (!result) {
    return NextResponse.json({ error: 'unknown service' }, { status: 404 });
  }

  const snapshot = await getManagedServiceStatus(serviceId);
  return NextResponse.json({
    status: result.ok ? 'ok' : 'failed',
    result,
    snapshot,
  }, { status: result.ok ? 200 : 500 });
}
