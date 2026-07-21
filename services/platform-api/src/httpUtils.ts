import type { Request, Response, NextFunction } from 'express';

import { resolveContext } from './state.js';

export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<void>,
) {
  return (req: Request, res: Response, next: NextFunction) => {
    void fn(req, res, next).catch(next);
  };
}

export function authRequired(req: Request, res: Response, next: NextFunction): void {
  try {
    req.platformCtx = resolveContext(req);
    next();
  } catch {
    res.status(401).json({ error: 'AUTH: missing or invalid credentials' });
  }
}

declare module 'express-serve-static-core' {
  interface Request {
    platformCtx?: import('@aaes-os/platform-core').PlatformContext;
  }
}
