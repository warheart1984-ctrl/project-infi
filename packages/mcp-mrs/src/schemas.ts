import { z } from 'zod';

export const RenderRt4dPreviewInput = z.object({
  sceneSpec: z.record(z.unknown()),
  surface: z.string().min(1),
  seed: z.number().int().optional(),
  camera: z.object({
    fov: z.number().min(1).max(179),
    position: z.array(z.number()).min(3).max(3),
    target: z.array(z.number()).min(3).max(3),
    rotations: z.array(z.number()).min(3).max(3).optional(),
  }).optional(),
  quality: z.object({
    resolution: z.array(z.number().int().positive()).min(2).max(2),
    spp: z.number().int().positive().optional(),
    maxDepth: z.number().int().positive().optional(),
  }).optional(),
  trajectory: z.array(z.array(z.number())).optional(),
}).strict();

export type RenderRt4dPreviewInput = z.infer<typeof RenderRt4dPreviewInput>;

export const RuntimeFingerprint = z.object({
  node: z.string(),
  zlib: z.string(),
  platform: z.string(),
  arch: z.string(),
}).strict();

export const RenderRt4dPreviewOutput = z.object({
  renderId: z.string().regex(/^rt4d-render-[a-f0-9]{16}$/),
  sceneId: z.string().min(1),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  seed: z.number().int(),
  trajectoryRoot: z.string(),
  sceneSpecHash: z.string().regex(/^[a-f0-9]{64}$/),
  projectionHash: z.string().regex(/^[a-f0-9]{64}$/),
  pixelHash: z.string().regex(/^[a-f0-9]{64}$/),
  pngHash: z.string().regex(/^[a-f0-9]{64}$/),
  rendererVersion: z.string(),
  runtimeFingerprint: RuntimeFingerprint,
  evidenceStatus: z.literal('substrate_verified'),
  promotionStatus: z.literal('not_promoted_to_ciems'),
  pngBase64: z.string(),
}).strict();

export type RenderRt4dPreviewOutput = z.infer<typeof RenderRt4dPreviewOutput>;

export const EngineReceiptSchema = z.object({
  renderId: z.string(),
  sceneId: z.string(),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  seed: z.number().int(),
  trajectoryRoot: z.string(),
  sceneSpecHash: z.string().regex(/^[a-f0-9]{64}$/),
  projectionHash: z.string().regex(/^[a-f0-9]{64}$/),
  pixelHash: z.string().regex(/^[a-f0-9]{64}$/),
  pngHash: z.string().regex(/^[a-f0-9]{64}$/),
  rendererVersion: z.string(),
  runtimeFingerprint: RuntimeFingerprint,
  evidenceStatus: z.literal('substrate_verified'),
  promotionStatus: z.literal('not_promoted_to_ciems'),
  pngBase64: z.string().optional(),
}).strict();

export type EngineReceipt = z.infer<typeof EngineReceiptSchema>;