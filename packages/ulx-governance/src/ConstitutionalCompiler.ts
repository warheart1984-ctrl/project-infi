export class ConstitutionalCompiler {
  compile(source: string): string {
    const normalized = source.trim().replace(/\s+/g, ' ');
    return `ULX::${normalized}`;
  }
}
