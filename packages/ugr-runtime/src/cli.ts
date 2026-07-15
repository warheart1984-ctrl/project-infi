export interface UgrRuntimeCliOptions {
  mode: 'snapshot' | 'serve';
  pretty: boolean;
  host: string;
  port: number;
}

export interface UgrRuntimeCanonicalJson {
  package: string;
  version: string;
  runtime: {
    config: {
      host: string;
      port: number;
    };
    api: {
      routes: readonly {
        method: 'GET' | 'POST';
        path: string;
        description: string;
      }[];
      grpcMethods: readonly {
        name: string;
        requestType: string;
        responseType: string;
      }[];
    };
    snapshot: {
      routes: number;
      grpcMethods: number;
      glyphs: number;
      health: string;
    };
    records: {
      glyphs: readonly unknown[];
      artifacts: readonly unknown[];
      lineageEvents: readonly unknown[];
      organisms: readonly unknown[];
    };
  };
}

import { createUgrRuntimeService } from './runtime.js';
import { createUgrRuntimeResourcesFromEnv, loadUgrRuntimeEnvConfig } from './runtime-env.js';

const PACKAGE_NAME = '@aaes-os/ugr-runtime';
const PACKAGE_VERSION = '0.1.0';

export async function buildCanonicalUgrRuntimeJson(): Promise<UgrRuntimeCanonicalJson> {
  const service = createUgrRuntimeService();
  const snapshot = await service.snapshot();
  return {
    package: PACKAGE_NAME,
    version: PACKAGE_VERSION,
    runtime: {
      config: {
        host: service.config.host,
        port: service.config.port,
      },
      api: {
        routes: service.api.getRoutes(),
        grpcMethods: service.api.getGrpcService(),
      },
      snapshot,
      records: {
        glyphs: await service.sql.fetch_all_glyphs(),
        artifacts: await service.sql.fetch_all_artifacts(),
        lineageEvents: await service.sql.fetch_all_lineage(),
        organisms: await service.sql.fetch_all_organisms(),
      },
    },
  };
}

export function parseUgrRuntimeCliArgs(argv: readonly string[]): UgrRuntimeCliOptions {
  const mode = argv.includes('serve') ? 'serve' : 'snapshot';
  const host = valueAfterFlag(argv, '--host') ?? '127.0.0.1';
  const portValue = valueAfterFlag(argv, '--port');
  return {
    mode,
    pretty: argv.includes('--pretty'),
    host,
    port: portValue ? Number(portValue) : 0,
  };
}

export async function runUgrRuntimeCli(argv: readonly string[]): Promise<number> {
  const options = parseUgrRuntimeCliArgs(argv);
  const payload = await buildCanonicalUgrRuntimeJson();
  const output = options.pretty ? JSON.stringify(payload, null, 2) : JSON.stringify(payload);
  process.stdout.write(`${output}\n`);
  return 0;
}

export async function runUgrRuntimeServe(argv: readonly string[]): Promise<number> {
  const options = parseUgrRuntimeCliArgs(argv);
  const envConfig = loadUgrRuntimeEnvConfig(process.env);
  const resources = await createUgrRuntimeResourcesFromEnv(process.env);
  const service = createUgrRuntimeService({
    host: options.host === '127.0.0.1' ? envConfig.host : options.host,
    port: options.port === 0 ? envConfig.port : options.port,
    adapters: resources.adapters,
    shutdown: resources.shutdown,
  });

  const stop = async (): Promise<void> => {
    await service.stop();
  };

  const onSignal = async (): Promise<void> => {
    await stop();
    process.exit(0);
  };

  process.once('SIGINT', onSignal);
  process.once('SIGTERM', onSignal);

  try {
    const started = await service.start();
    process.stdout.write(`${JSON.stringify({ ok: true, url: started.url }, null, 2)}\n`);
    await new Promise<void>(() => {
      // keep the process alive until signaled
    });
    return 0;
  } finally {
    process.off('SIGINT', onSignal);
    process.off('SIGTERM', onSignal);
  }
}

function valueAfterFlag(argv: readonly string[], flag: string): string | undefined {
  const index = argv.indexOf(flag);
  if (index < 0) {
    return undefined;
  }
  const next = argv[index + 1];
  if (!next || next.startsWith('--') || next === 'serve') {
    return undefined;
  }
  return next;
}
