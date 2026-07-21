export type CepArtifactKind = 'promotion-request' | 'replay-job' | 'decision';

export interface CepArtifactRecord<TPayload = unknown> {
  id: string;
  kind: CepArtifactKind;
  title: string;
  source: string;
  organizationId?: string;
  relatedArtifactId?: string;
  recordedAt: string;
  signature?: string;
  payload: TPayload;
}

export interface CepViewState {
  selectedKind: CepArtifactKind;
  selectedArtifactId: string | null;
  updatedAt: string;
  source: 'local' | 'remote';
}

export interface CepArtifactExport {
  storePath: string;
  entryCount: number;
  countsByKind: Record<CepArtifactKind, number>;
  records: CepArtifactRecord[];
  recentRecords: CepArtifactRecord[];
  organizationId?: string | null;
  viewState: CepViewState;
}

export interface CepOrchestratorClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
}

export interface CepArtifactMetadata {
  id?: string;
  title?: string;
  source?: string;
  organizationId?: string;
  relatedArtifactId?: string;
  recordedAt?: string;
  signature?: string;
}

export interface CepOrchestratorBundle {
  promotionRequest: unknown;
  replayJob: unknown;
  decision: unknown;
  promotionRequestMetadata?: CepArtifactMetadata;
  replayJobMetadata?: CepArtifactMetadata;
  decisionMetadata?: CepArtifactMetadata;
}

export class CepOrchestratorClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: CepOrchestratorClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? '').replace(/\/+$/, '');
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async getExport(options: { organizationId?: string } = {}): Promise<CepArtifactExport> {
    const search = new URLSearchParams();
    if (options.organizationId?.trim()) {
      search.set('orgId', options.organizationId.trim());
    }
    return this.request('GET', `/api/cep/artifacts/export.json${search.toString() ? `?${search.toString()}` : ''}`);
  }

  async getViewState(): Promise<{ viewState: CepViewState }> {
    return this.request('GET', '/api/cep/view-state');
  }

  async setViewState(viewState: Partial<Pick<CepViewState, 'selectedKind' | 'selectedArtifactId'>>): Promise<{ viewState: CepViewState }> {
    return this.request('PATCH', '/api/cep/view-state', viewState);
  }

  async postPromotionRequest(payload: unknown, metadata: CepArtifactMetadata = {}): Promise<CepArtifactRecord> {
    return this.request('POST', '/api/cep/artifacts/promotion-request', this.buildArtifactRequest('promotion-request', payload, metadata));
  }

  async postReplayJob(payload: unknown, metadata: CepArtifactMetadata = {}): Promise<CepArtifactRecord> {
    return this.request('POST', '/api/cep/artifacts/replay-job', this.buildArtifactRequest('replay-job', payload, metadata));
  }

  async postDecision(payload: unknown, metadata: CepArtifactMetadata = {}): Promise<CepArtifactRecord> {
    return this.request('POST', '/api/cep/artifacts/decision', this.buildArtifactRequest('decision', payload, metadata));
  }

  async syncBundle(bundle: CepOrchestratorBundle): Promise<{
    promotionRequest: CepArtifactRecord;
    replayJob: CepArtifactRecord;
    decision: CepArtifactRecord;
    viewState: CepViewState;
  }> {
    const promotionRequest = await this.postPromotionRequest(bundle.promotionRequest, bundle.promotionRequestMetadata);
    const replayJob = await this.postReplayJob(bundle.replayJob, {
      relatedArtifactId: promotionRequest.id,
      ...bundle.replayJobMetadata,
    });
    const decision = await this.postDecision(bundle.decision, {
      relatedArtifactId: replayJob.id,
      ...bundle.decisionMetadata,
    });
    const viewState = (await this.setViewState({
      selectedKind: 'decision',
      selectedArtifactId: decision.id,
    })).viewState;

    return { promotionRequest, replayJob, decision, viewState };
  }

  private buildArtifactRequest(kind: CepArtifactKind, payload: unknown, metadata: CepArtifactMetadata): Record<string, unknown> {
    const signature = metadata.signature ?? extractPayloadSignature(payload);
    return {
      kind,
      title: metadata.title ?? this.defaultTitle(kind),
      source: metadata.source ?? 'platform-web',
      organizationId: metadata.organizationId,
      relatedArtifactId: metadata.relatedArtifactId,
      id: metadata.id,
      recordedAt: metadata.recordedAt,
      signature,
      payload,
    };
  }

  private defaultTitle(kind: CepArtifactKind): string {
    switch (kind) {
      case 'promotion-request':
        return 'Promotion Request';
      case 'replay-job':
        return 'Replay Job';
      case 'decision':
        return 'Decision';
    }
  }

  private async request<T>(method: string, path: string, body?: Record<string, unknown>): Promise<T> {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method,
      headers: body ? { 'content-type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error((payload as { error?: string }).error ?? `HTTP ${response.status}`);
    }

    return response.json() as Promise<T>;
  }
}

function extractPayloadSignature(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return undefined;
  }

  const candidate = payload as {
    signature?: {
      algorithm?: string;
      value?: string;
    };
  };
  if (candidate.signature?.algorithm !== 'Ed25519') {
    return undefined;
  }
  if (typeof candidate.signature.value !== 'string' || candidate.signature.value.trim().length === 0) {
    return undefined;
  }
  return candidate.signature.value;
}
