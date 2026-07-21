import { NextResponse } from 'next/server';

import { getPlatform } from '../../../../lib/platform';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const form = await request.formData();
  const label = String(form.get('label') ?? 'dashboard-key');
  const platform = getPlatform();
  platform.login('dashboard', 'balanced');
  const result = platform.apiKeys.create({ label, ownerId: 'dashboard', governanceProfile: 'balanced' });
  return NextResponse.redirect(new URL(`/developer/keys?created=${result.record.id}&key=${encodeURIComponent(result.key)}`, request.url));
}
