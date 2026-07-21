import { NextResponse } from 'next/server';

import { getMesh } from '../../../../../lib/platform';
import type { GovernanceMode } from '@aaes-os/platform-core';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const form = await request.formData();
  const mesh = getMesh();
  const caps = String(form.get('capabilities') ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  mesh.announce({
    organismId: String(form.get('organismId')),
    endpoint: String(form.get('endpoint')),
    capabilities: caps,
    governanceProfile: (form.get('governanceProfile') as GovernanceMode) ?? 'balanced',
    lawHash: process.env.PLATFORM_LAW_HASH ?? 'platform-law-v1',
  });

  return NextResponse.redirect(new URL('/developer/mesh', request.url));
}
