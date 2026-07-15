import {
  appendCodexHandoffLedgerEntry,
  buildCodexHandoffLedgerEntry,
  verifySignedCodexReplyPacket,
} from '../../../../../lib/codexHandoff';
import {
  publishPricingEvaluationCepArtifacts,
} from '../../../../../lib/pricingCep';
import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function getPlatformApiBaseUrl(): string {
  return (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
}

function getOpsConsoleBaseUrl(): string {
  return (process.env.OPS_CONSOLE_URL ?? 'http://localhost:4000').replace(/\/+$/, '');
}

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

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const sessionId = String(body.sessionId ?? readCookie(request, 'platform_customer_session') ?? '');
  if (!sessionId) {
    return NextResponse.json({ error: 'missing sessionId' }, { status: 401 });
  }

  const response = await fetch(`${getPlatformApiBaseUrl()}/v1/billing/pricing/evaluate`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-session-id': sessionId,
    },
    body: JSON.stringify(body),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status });
  }

  const reply = payload?.reply ?? null;
  const signedReply = payload?.signedReply ?? null;
  const auditSurface = payload?.auditSurface ?? null;
  let handoffLedgerPath: string | null = null;
  let cepPublication: {
    published: boolean;
    promotionRequestId?: string;
    replayJobId?: string;
    decisionId?: string;
    viewState?: { selectedKind: string; selectedArtifactId: string | null; updatedAt: string; source: 'local' | 'remote' };
    error?: string;
  } | null = null;

  if (reply) {
    const signingSecret = process.env.CODEX_HANDOFF_SIGNING_SECRET;
    if (signedReply && signingSecret && !verifySignedCodexReplyPacket(signedReply, signingSecret)) {
      return NextResponse.json({ error: 'invalid signed Codex reply packet' }, { status: 502 });
    }

    const entry = buildCodexHandoffLedgerEntry({
      sourceFile: 'services/platform-web/app/api/customer/pricing/evaluate/route.ts',
      objective: `Customer-authenticated pricing evaluation for ${body.segment ?? 'Professional'}`,
      packet: reply,
      signature: signedReply?.signature,
      signer: signedReply?.signer,
      signatureVerified: Boolean(signedReply && signingSecret),
    });
    handoffLedgerPath = appendCodexHandoffLedgerEntry(entry);
  }

  try {
    const organizationId = String(
      payload?.auditSurface?.surface?.organizationId ??
        payload?.customer?.organizationId ??
        body.organizationId ??
        '',
    ).trim() || undefined;
    const publication = await publishPricingEvaluationCepArtifacts(
      {
        sessionId,
        customerId: String(payload?.evaluation?.requestPacket?.customerId ?? body.customerId ?? sessionId),
        customerPlanId: String(payload?.auditSurface?.surface?.planId ?? payload?.customer?.planId ?? body.planId ?? 'free'),
        customerPlanName: String(payload?.auditSurface?.surface?.planName ?? payload?.customer?.planName ?? body.planName ?? 'Free'),
        organizationId,
        segment: String(body.segment ?? 'Professional'),
        trustSurface: body.trustSurface ?? body.trustPacket ?? undefined,
        requestBody: body as Record<string, unknown>,
        responseBody: payload as {
          evaluation?: {
            requestId?: string;
            recommendedScenario?: {
              strategy?: string;
              packaging?: string;
            };
            routing?: {
              modelDecision?: { model?: string };
              backend?: string;
            };
            economics?: Record<string, unknown>;
            requestPacket?: Record<string, unknown>;
          };
          treasuryPlan?: unknown;
          reply?: unknown;
          signedReply?: unknown;
          auditSurface?: {
            surface?: {
              requestId?: string;
              planId?: string;
              planName?: string;
              quota?: Record<string, unknown>;
              pricingJustification?: string;
              routingJustification?: string;
              trust?: unknown;
              routeDecisionArtifact?: unknown;
            };
          };
          quota?: Record<string, unknown>;
          ledger?: Record<string, unknown>;
          routeDecisionArtifact?: unknown;
        },
      },
      undefined,
      { baseUrl: getOpsConsoleBaseUrl(), fetchImpl: fetch },
    );
    cepPublication = {
      published: true,
      promotionRequestId: publication.promotionRequest.id,
      replayJobId: publication.replayJob.id,
      decisionId: publication.decision.id,
      viewState: publication.viewState,
    };
  } catch (error) {
    cepPublication = {
      published: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }

  return NextResponse.json({
    ...payload,
    handoff: {
      persisted: Boolean(handoffLedgerPath),
      ledgerPath: handoffLedgerPath,
    },
    auditSurface,
    cep: cepPublication,
  });
}
