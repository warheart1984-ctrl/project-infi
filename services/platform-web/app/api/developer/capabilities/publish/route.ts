import { NextResponse } from 'next/server';

import { getPlatform } from '../../../../../lib/platform';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const form = await request.formData();
  const platform = getPlatform();
  const ctx = { ownerId: 'dashboard', governanceProfile: 'balanced' as const, scopes: ['*'] };

  platform.publishCapability(ctx, {
    id: String(form.get('id')),
    name: String(form.get('name')),
    description: String(form.get('description') ?? ''),
    organId: String(form.get('organId')),
    version: String(form.get('version')),
  });

  return NextResponse.redirect(new URL('/developer/capabilities', request.url));
}
