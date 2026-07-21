import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const form = await request.formData();
  const profile = String(form.get('profile'));
  const res = NextResponse.redirect(new URL('/developer/governance', request.url));
  res.cookies.set('governance_profile', profile, { path: '/', maxAge: 86400 * 30 });
  return res;
}
