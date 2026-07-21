import type { ConformanceReport } from './types.js';

export class CorpusAdmitter {
  private corpus: ConformanceReport[] = [];

  admit(artifact: ConformanceReport): void {
    if (!artifact.admitted) {
      throw new Error('CORPUS: cannot admit non-admitted artifact');
    }
    this.corpus.push(artifact);
  }

  getCorpus(): ConformanceReport[] {
    return [...this.corpus];
  }
}
