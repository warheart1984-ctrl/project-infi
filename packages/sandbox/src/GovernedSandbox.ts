import vm from 'node:vm';
import { createRequire } from 'node:module';

export interface SandboxResult {
  logs: string[];
  error: string | null;
}

export interface GovernedSandboxOptions {
  allowedModules?: string[];
  timeoutMs?: number;
}

export class GovernedSandbox {
  private readonly allowedModules: Set<string>;
  private readonly timeoutMs: number;

  constructor(options: GovernedSandboxOptions = {}) {
    this.allowedModules = new Set(options.allowedModules ?? []);
    this.timeoutMs = options.timeoutMs ?? 2000;
  }

  execute(code: string): SandboxResult {
    const logs: string[] = [];
    const requireFn = createRequire(import.meta.url);

    const sandbox: Record<string, unknown> = {
      console: {
        log: (...args: unknown[]) => {
          logs.push(args.map(String).join(' '));
        },
      },
      require: (mod: string) => {
        if (!this.allowedModules.has(mod)) {
          throw new Error(`Module not allowed: ${mod}`);
        }
        return requireFn(mod);
      },
    };

    const context = vm.createContext(sandbox);

    try {
      vm.runInContext(code, context, { timeout: this.timeoutMs });
      return { logs, error: null };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { logs, error: message };
    }
  }
}
