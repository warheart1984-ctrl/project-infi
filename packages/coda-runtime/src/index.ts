import { buildCodaCorpus, findCodaCorpusRecord, summarizeCodaCorpus, type CodaCorpusRecord } from '@aaes-os/coda-doc';
import { NovaCodaRuntime, type NovaCodaRuntimeSnapshot, type NovaCodaTransport } from '@aaes-os/nova-coda';

export interface CodaRuntimeSnapshot {
  packageName: '@aaes-os/coda-runtime';
  status: 'live' | 'mixed';
  corpus: {
    total: number;
    live: number;
    mixed: number;
    docForward: number;
  };
  liveSurfaces: string[];
  docForwardSurfaces: string[];
  novaCoda: NovaCodaRuntimeSnapshot;
}

export interface CodaRuntimeOptions {
  transport?: NovaCodaTransport;
  corpus?: readonly CodaCorpusRecord[];
}

export class CodaRuntime {
  private readonly corpus: readonly CodaCorpusRecord[];
  private readonly novaCoda: NovaCodaRuntime;

  constructor(options: CodaRuntimeOptions = {}) {
    this.corpus = options.corpus ?? buildCodaCorpus();
    this.novaCoda = new NovaCodaRuntime({ transport: options.transport });
  }

  async connect(): Promise<this> {
    await this.novaCoda.connect();
    return this;
  }

  async ping(): Promise<CodaRuntimeSnapshot> {
    await this.novaCoda.ping();
    return this.snapshot();
  }

  disconnect(): void {
    this.novaCoda.disconnect();
  }

  snapshot(): CodaRuntimeSnapshot {
    const liveSurfaces = this.corpus.filter((record) => record.status === 'live').map((record) => record.displayName);
    const docForwardSurfaces = this.corpus.filter((record) => record.status !== 'live').map((record) => record.displayName);

    return {
      packageName: '@aaes-os/coda-runtime',
      status: docForwardSurfaces.length > 0 ? 'mixed' : 'live',
      corpus: summarizeCodaCorpus(this.corpus),
      liveSurfaces,
      docForwardSurfaces,
      novaCoda: this.novaCoda.snapshot(),
    };
  }

  findSurface(query: string): CodaCorpusRecord | undefined {
    return findCodaCorpusRecord(query, this.corpus);
  }
}

export function createCodaRuntime(options: CodaRuntimeOptions = {}): CodaRuntime {
  return new CodaRuntime(options);
}

export function buildCodaRuntimeStatus(options: CodaRuntimeOptions = {}): string {
  const runtime = new CodaRuntime(options);
  const snapshot = runtime.snapshot();
  return `${snapshot.packageName} has ${snapshot.corpus.live} live surfaces and ${snapshot.corpus.docForward} doc-forward surfaces`;
}

export { buildCodaCorpus, findCodaCorpusRecord, summarizeCodaCorpus };
