import type { AddressInfo, Server } from 'node:net';

import { createUgrHttpServer, UgrApi, type UgrApiDependencies, type UgrReplayRepeatCheck, type UgrReplayRepeatDecision } from './api.js';
import type { UgrPersistenceAdapters } from './adapters.js';
import { InMemoryUgrGraphStorage, type UgrGraphStorage } from './storage/graph.js';
import { InMemoryUgrSqlStorage, type UgrSqlStorage } from './storage/sql.js';
import { InMemoryUgrVectorStorage, type UgrVectorStorage } from './storage/vector.js';

export interface UgrRuntimeConfig {
  host: string;
  port: number;
  adapters?: Partial<UgrPersistenceAdapters>;
  shutdown?: () => Promise<void>;
}

export interface UgrRuntimeServices {
  sql: UgrSqlStorage;
  graph: UgrGraphStorage;
  vector: UgrVectorStorage;
  api: UgrApi;
  server: Server;
}

export interface UgrRuntimeStartResult {
  host: string;
  port: number;
  url: string;
}

export interface UgrRuntimeService {
  readonly config: UgrRuntimeConfig;
  readonly api: UgrApi;
  readonly sql: UgrSqlStorage;
  readonly graph: UgrGraphStorage;
  readonly vector: UgrVectorStorage;
  readonly server: Server;
  start(): Promise<UgrRuntimeStartResult>;
  stop(): Promise<void>;
  hasReplayableResult(check: UgrReplayRepeatCheck): Promise<boolean>;
  shouldRepeatExperiment(check: UgrReplayRepeatCheck): Promise<UgrReplayRepeatDecision>;
  assertExperimentMayRun(check: UgrReplayRepeatCheck): Promise<void>;
  snapshot(): Promise<{
    routes: number;
    grpcMethods: number;
    glyphs: number;
    health: string;
  }>;
}

const DEFAULT_CONFIG: UgrRuntimeConfig = {
  host: '127.0.0.1',
  port: 0,
};

function createRuntimeServices(adapters: Partial<UgrPersistenceAdapters> = {}): UgrRuntimeServices {
  const sql = new InMemoryUgrSqlStorage({ adapter: adapters.postgres });
  const graph = new InMemoryUgrGraphStorage({ adapter: adapters.neo4j });
  const vector = new InMemoryUgrVectorStorage({ adapter: adapters.pgvector });
  const api = new UgrApi({ sql, graph, vector });
  const server = createUgrHttpServer(api);

  return {
    sql,
    graph,
    vector,
    api,
    server,
  };
}

function createRuntimeDependencies(adapters: Partial<UgrPersistenceAdapters> = {}): UgrApiDependencies {
  const sql = new InMemoryUgrSqlStorage({ adapter: adapters.postgres });
  const graph = new InMemoryUgrGraphStorage({ adapter: adapters.neo4j });
  const vector = new InMemoryUgrVectorStorage({ adapter: adapters.pgvector });
  return {
    sql,
    graph,
    vector,
  };
}

export function createUgrRuntimeService(config: Partial<UgrRuntimeConfig> = {}): UgrRuntimeService {
  const resolvedConfig: UgrRuntimeConfig = {
    ...DEFAULT_CONFIG,
    ...config,
  };
  const components = createRuntimeServices(resolvedConfig.adapters ?? {});

  return {
    config: resolvedConfig,
    api: components.api,
    sql: components.sql,
    graph: components.graph,
    vector: components.vector,
    server: components.server,
    async start(): Promise<UgrRuntimeStartResult> {
      await new Promise<void>((resolve) => {
        components.server.listen(resolvedConfig.port, resolvedConfig.host, resolve);
      });
      const address = components.server.address();
      if (!address || typeof address === 'string') {
        return {
          host: resolvedConfig.host,
          port: resolvedConfig.port,
          url: `http://${resolvedConfig.host}:${resolvedConfig.port}`,
        };
      }
      const resolvedAddress = address as AddressInfo;
      return {
        host: resolvedAddress.address,
        port: resolvedAddress.port,
        url: `http://${resolvedAddress.address}:${resolvedAddress.port}`,
      };
    },
    async stop(): Promise<void> {
      await new Promise<void>((resolve, reject) => {
        components.server.close((error?: Error) => {
          if (error) {
            reject(error);
            return;
          }
          resolve();
        });
      });
      await resolvedConfig.shutdown?.();
    },
    async hasReplayableResult(check: UgrReplayRepeatCheck): Promise<boolean> {
      return components.api.hasReplayableResult(check);
    },
    async shouldRepeatExperiment(check: UgrReplayRepeatCheck): Promise<UgrReplayRepeatDecision> {
      return components.api.shouldRepeatExperiment(check);
    },
    async assertExperimentMayRun(check: UgrReplayRepeatCheck): Promise<void> {
      await components.api.assertExperimentMayRun(check);
    },
    async snapshot() {
      const glyphs = await components.sql.fetch_all_glyphs();
      return {
        routes: components.api.getRoutes().length,
        grpcMethods: components.api.getGrpcService().length,
        glyphs: glyphs.length,
        health: '/health',
      };
    },
  };
}

export function createUgrRuntimeServices(config: Partial<UgrRuntimeConfig> = {}): UgrRuntimeServices {
  return createRuntimeServices(config.adapters ?? {});
}

export function createUgrRuntimeDependencies(config: Partial<UgrRuntimeConfig> = {}): UgrApiDependencies {
  return createRuntimeDependencies(config.adapters ?? {});
}
