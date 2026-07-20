import express, { Request, Response } from 'express';

/**
 * Shared health check middleware for all services
 */

export interface HealthCheckOptions {
  /** Custom check functions to run before returning ready */
  checks?: Record<string, () => Promise<boolean>>;
  /** Timeout for each check in ms */
  checkTimeout?: number;
}

export function createHealthCheckHandler(options: HealthCheckOptions = {}) {
  const { checks = {}, checkTimeout = 5000 } = options;

  return {
    /**
     * GET /health - Liveness probe (is the service alive?)
     * Returns 200 if the service is running, even if dependencies are down
     */
    liveness: async (_req: Request, res: Response) => {
      try {
        res.status(200).json({
          status: 'alive',
          timestamp: new Date().toISOString(),
          uptime: process.uptime(),
        });
      } catch (error) {
        res.status(500).json({
          status: 'error',
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    },

    /**
     * GET /ready - Readiness probe (is the service ready to serve traffic?)
     * Returns 200 only if all dependencies are healthy
     */
    readiness: async (_req: Request, res: Response) => {
      const results: Record<string, boolean> = {};
      let allHealthy = true;

      // Run all checks with timeout
      await Promise.all(
        Object.entries(checks).map(async ([name, checkFn]) => {
          try {
            const checkPromise = checkFn();
            const timeoutPromise = new Promise<boolean>((resolve) =>
              setTimeout(() => resolve(false), checkTimeout)
            );
            results[name] = await Promise.race([checkPromise, timeoutPromise]);
            if (!results[name]) allHealthy = false;
          } catch (error) {
            results[name] = false;
            allHealthy = false;
          }
        })
      );

      if (!allHealthy) {
        res.status(503).json({
          status: 'not_ready',
          checks: results,
          timestamp: new Date().toISOString(),
        });
        return;
      }

      res.status(200).json({
        status: 'ready',
        checks: results,
        timestamp: new Date().toISOString(),
      });
    },

    /**
     * GET /health/detailed - Detailed health status
     * Returns comprehensive health information
     */
    detailed: async (_req: Request, res: Response) => {
      const results: Record<string, { status: string; latency?: number; error?: string }> = {};

      await Promise.all(
        Object.entries(checks).map(async ([name, checkFn]) => {
          const start = Date.now();
          try {
            const checkPromise = checkFn();
            const timeoutPromise = new Promise<boolean>((resolve) =>
              setTimeout(() => resolve(false), checkTimeout)
            );
            const healthy = await Promise.race([checkPromise, timeoutPromise]);
            results[name] = {
              status: healthy ? 'healthy' : 'unhealthy',
              latency: Date.now() - start,
            };
          } catch (error) {
            results[name] = {
              status: 'error',
              latency: Date.now() - start,
              error: error instanceof Error ? error.message : 'Unknown error',
            };
          }
        })
      );

      const allHealthy = Object.values(results).every((r) => r.status === 'healthy');

      res.status(allHealthy ? 200 : 503).json({
        status: allHealthy ? 'healthy' : 'unhealthy',
        checks: results,
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
      });
    },
  };
}

/**
 * Mount healthcheck endpoints on an Express app
 */
export function mountHealthChecks(
  app: Express,
  options: HealthCheckOptions = {}
) {
  const handlers = createHealthCheckHandler(options);

  app.get('/health', handlers.liveness);
  app.get('/ready', handlers.readiness);
  app.get('/health/detailed', handlers.detailed);

  // Kubernetes-style probes
  app.get('/healthz', handlers.liveness);
  app.get('/readyz', handlers.readiness);

  return app;
}
