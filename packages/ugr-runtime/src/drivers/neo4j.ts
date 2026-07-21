import neo4j, { type Driver, type Session } from 'neo4j-driver';

import { CypherNeo4jUgrAdapter, type UgrNeo4jAdapterOptions, type UgrNeo4jQueryRunner } from '../adapters/neo4j.js';

export interface UgrNeo4jQueryLike {
  session(config?: { database?: string }): Session;
}

export function createUgrNeo4jDriver(
  uri: string,
  auth: Parameters<typeof neo4j.driver>[1],
  config?: Parameters<typeof neo4j.driver>[2],
): Driver {
  return neo4j.driver(uri, auth, config);
}

export function createUgrNeo4jQueryRunner(client: UgrNeo4jQueryLike, database?: string): UgrNeo4jQueryRunner {
  return {
    async run(cypher: string, params?: Record<string, unknown>) {
      const session = client.session(database ? { database } : undefined);
      try {
        const result = await session.run(cypher, params);
        return {
          records: result.records.map((record) => record.toObject() as Record<string, unknown>),
        };
      } finally {
        await session.close();
      }
    },
  };
}

export function createUgrNeo4jAdapter(
  client: UgrNeo4jQueryLike,
  options: UgrNeo4jAdapterOptions = {},
): CypherNeo4jUgrAdapter {
  return new CypherNeo4jUgrAdapter(createUgrNeo4jQueryRunner(client, options.database), options);
}
