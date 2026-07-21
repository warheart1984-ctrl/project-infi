import { SovereignXRouter } from './SovereignXRouter.js';
import type {
  CiemsIntentSpec,
  EvidenceRecord,
  GovernanceLimits,
  MeasurementHealth,
  RouteDecision,
  RouteEvaluation,
  RuntimeStats,
  WorkItem,
} from './types.js';
import type {
  ProofLevel,
  ProofSurfaceOperationalStatus,
  ProofSurfaceReplayStatus,
  ProofSurfaceVerificationStatus,
} from './proofSurface.js';

export type SovereignXBackend = 'reference' | 'cpu' | 'vulkan' | 'metal' | 'dx12' | 'opencl';
export type SovereignXQueueKind = 'graphics' | 'compute' | 'transfer';
export type SovereignXShaderStage = 'vertex' | 'fragment' | 'compute';
export type SovereignXPipelineKind = 'graphics' | 'compute';
export type SovereignXResourceUsage =
  | 'vertex'
  | 'index'
  | 'uniform'
  | 'storage'
  | 'sampled'
  | 'render_target'
  | 'depth_stencil'
  | 'transfer';
export type SovereignXReceiptOutcome = 'allow' | 'delay' | 'throttle' | 'quarantine' | 'deny';
export type SovereignXReceiptKind =
  | 'lifecycle'
  | 'resource'
  | 'shader'
  | 'pipeline'
  | 'command'
  | 'swapchain'
  | 'fence'
  | 'governance'
  | 'evidence';

export interface SovereignXRuntimeLimits {
  maxBuffers: number;
  maxTextures: number;
  maxShaders: number;
  maxPipelines: number;
  maxCommandLists: number;
  maxQueueDepth: number;
  maxVramBytes: number;
  maxGpuTempC: number;
  maxTokensPerAgentPerMin: number;
  maxFlopsPerAgentPerMin: number;
}

export interface SovereignXRuntimeConfig {
  applicationName?: string;
  backend?: SovereignXBackend;
  preferredDeviceId?: string;
  limits?: Partial<SovereignXRuntimeLimits>;
}

export interface SovereignXResourceGovernance {
  intentId: string;
  claimId?: string;
  proofSurfaceId?: string;
  allowance?: string;
  maxVramBytes?: number;
  maxFrameMs?: number;
  allowUntrustedShaders?: boolean;
}

export interface SovereignXExecutionEvidence {
  receipts: string[];
  artifacts: string[];
  summary: string;
}

export interface SovereignXExecutionVerification {
  method: string;
  validator: string;
  replayArtifacts: string[];
  replayable: boolean;
}

export interface SovereignXExecutionCompliance {
  requirements: string[];
  satisfied: boolean;
  issues: string[];
}

export interface SovereignXExecutionContract {
  operation: string;
  subjectId: string;
  intentId: string;
  authority: string;
  evidence: SovereignXExecutionEvidence;
  verification: SovereignXExecutionVerification;
  compliance: SovereignXExecutionCompliance;
  truthBoundary: string;
}

export interface SovereignXDevice {
  id: string;
  name: string;
  backend: SovereignXBackend;
  queueKinds: SovereignXQueueKind[];
  description: string;
}

export interface SovereignXQueue {
  id: string;
  deviceId: string;
  kind: SovereignXQueueKind;
  label: string;
}

export interface SovereignXBufferDesc {
  label?: string;
  sizeBytes: number;
  usage: SovereignXResourceUsage[];
  governance: SovereignXResourceGovernance;
  deviceId?: string;
}

export interface SovereignXTextureSize {
  width: number;
  height: number;
  depth?: number;
}

export interface SovereignXTextureDesc {
  label?: string;
  size: SovereignXTextureSize;
  format: string;
  usage: SovereignXResourceUsage[];
  mipLevels?: number;
  governance: SovereignXResourceGovernance;
  deviceId?: string;
}

export interface SovereignXShaderDesc {
  label?: string;
  stage: SovereignXShaderStage;
  source: string;
  entryPoint?: string;
  governance: SovereignXResourceGovernance;
  deviceId?: string;
}

export interface SovereignXGraphicsPipelineDesc {
  label?: string;
  vertexShaderId: string;
  fragmentShaderId: string;
  renderPassId?: string;
  topology?: 'triangle-list' | 'triangle-strip' | 'line-list' | 'line-strip';
  governance: SovereignXResourceGovernance;
  deviceId?: string;
}

export interface SovereignXComputePipelineDesc {
  label?: string;
  computeShaderId: string;
  workgroupSize?: [number, number, number];
  governance: SovereignXResourceGovernance;
  deviceId?: string;
}

export interface SovereignXSwapchainDesc {
  label?: string;
  deviceId?: string;
  width: number;
  height: number;
  format: string;
  imageCount?: number;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXRenderPassDesc {
  label?: string;
  colorFormats: string[];
  depthFormat?: string;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXFramebufferDesc {
  label?: string;
  renderPassId: string;
  attachments: string[];
  width: number;
  height: number;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXCommandList {
  id: string;
  queueId: string;
  label?: string;
  commands: string[];
  closed: boolean;
  presentSwapchainId?: string;
  record(command: string): void;
  close(): void;
}

export interface SovereignXFence {
  id: string;
  queueId: string;
  label?: string;
  targetValue: number;
  signaledValue: number;
}

export interface SovereignXBuffer {
  id: string;
  deviceId: string;
  label?: string;
  sizeBytes: number;
  usage: SovereignXResourceUsage[];
  governance: SovereignXResourceGovernance;
}

export interface SovereignXTexture {
  id: string;
  deviceId: string;
  label?: string;
  size: SovereignXTextureSize;
  format: string;
  usage: SovereignXResourceUsage[];
  mipLevels: number;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXShader {
  id: string;
  deviceId: string;
  label?: string;
  stage: SovereignXShaderStage;
  entryPoint: string;
  source: string;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXPipeline {
  id: string;
  deviceId: string;
  kind: SovereignXPipelineKind;
  label?: string;
  governance: SovereignXResourceGovernance;
  shaderIds: string[];
  proofSurfaceId?: string;
  claimId?: string;
}

export interface SovereignXSwapchain {
  id: string;
  deviceId: string;
  label?: string;
  width: number;
  height: number;
  format: string;
  imageCount: number;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXRenderPass {
  id: string;
  label?: string;
  colorFormats: string[];
  depthFormat?: string;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXFramebuffer {
  id: string;
  label?: string;
  renderPassId: string;
  attachments: string[];
  width: number;
  height: number;
  governance: SovereignXResourceGovernance;
}

export interface SovereignXClaim {
  id: string;
  role: string;
  statement: string;
  proofSurfaceId: string;
  evidenceIds: string[];
  status: 'verified' | 'pending' | 'rejected';
}

export interface SovereignXProofSurface {
  id: string;
  label: string;
  kind:
    | 'resource'
    | 'shader'
    | 'pipeline'
    | 'swapchain'
    | 'command'
    | 'render-pass'
    | 'framebuffer'
    | 'lifecycle'
    | 'execution';
  claimId: string;
  evidenceIds: string[];
  proofLevel: ProofLevel;
  verificationStatus: ProofSurfaceVerificationStatus;
  replayStatus: ProofSurfaceReplayStatus;
  operationalStatus: ProofSurfaceOperationalStatus;
  truthBoundary: string;
  sourceId: string;
  executionContract?: SovereignXExecutionContract;
}

export interface SovereignXExecutionProofSurface extends SovereignXProofSurface {
  executionContract: SovereignXExecutionContract;
}

export interface SovereignXEvidenceGraphResolver {
  resolveClaim(claimId: string): SovereignXClaim | null;
  resolveProofSurface(proofSurfaceId: string): SovereignXProofSurface | null;
  resolveReceipt(receiptId: string): SovereignXReceipt | null;
}

export interface SovereignXGovernanceObserver {
  onReceipt?(receipt: SovereignXReceipt): void;
  onViolation?(receipt: SovereignXReceipt): void;
}

export interface SovereignXReceipt {
  id: string;
  kind: SovereignXReceiptKind;
  operation: string;
  subjectId: string;
  timestamp: string;
  intentId: string;
  outcome: SovereignXReceiptOutcome;
  reason: string;
  routeDecision: RouteDecision;
  routeEvaluation: RouteEvaluation;
  validationIssues: string[];
  governance: SovereignXResourceGovernance;
  claimId?: string;
  proofSurfaceId?: string;
  executionProofSurfaceId: string;
  executionContract: SovereignXExecutionContract;
  metadata: Record<string, unknown>;
}

export interface SovereignXStateSnapshot {
  initialized: boolean;
  applicationName: string;
  backend: SovereignXBackend;
  deviceCount: number;
  bufferCount: number;
  textureCount: number;
  shaderCount: number;
  pipelineCount: number;
  commandListCount: number;
  receiptCount: number;
  proofSurfaceCount: number;
  limits: SovereignXRuntimeLimits;
}

export class SovereignXViolationError extends Error {
  readonly receipt: SovereignXReceipt;

  constructor(receipt: SovereignXReceipt) {
    super(receipt.reason);
    this.name = 'SovereignXViolationError';
    this.receipt = receipt;
  }
}

const DEFAULT_LIMITS: SovereignXRuntimeLimits = {
  maxBuffers: 64,
  maxTextures: 64,
  maxShaders: 64,
  maxPipelines: 32,
  maxCommandLists: 64,
  maxQueueDepth: 128,
  maxVramBytes: 8_589_934_592,
  maxGpuTempC: 82,
  maxTokensPerAgentPerMin: 1_000,
  maxFlopsPerAgentPerMin: 1_000_000_000_000,
};

const DEFAULT_DEVICE: SovereignXDevice = {
  id: 'sx-reference-device',
  name: 'SovereignX Reference Device',
  backend: 'reference',
  queueKinds: ['graphics', 'compute', 'transfer'],
  description: 'Backend-neutral scaffold device used until a native GPU backend is wired.',
};

function clone<T>(value: T): T {
  return structuredClone(value);
}

function defaultRuntimeStats(): RuntimeStats {
  return {
    activeGpuJobs: 0,
    activeCpuJobs: 0,
    gpuUtil: 0,
    cpuUtil: 0,
    gpuTempC: 0,
    vramUsedBytes: 0,
    vramTotalBytes: DEFAULT_LIMITS.maxVramBytes,
  };
}

function validatePositiveInteger(value: number, field: string): string[] {
  return Number.isInteger(value) && value > 0 ? [] : [`${field} must be a positive integer`];
}

function validateGovernance(governance: SovereignXResourceGovernance | undefined, operation: string): string[] {
  if (!governance) {
    return [`${operation} requires a governance section`];
  }
  const issues: string[] = [];
  if (!String(governance.intentId || '').trim()) {
    issues.push(`${operation}.governance.intentId is required`);
  }
  if (governance.maxVramBytes != null && governance.maxVramBytes <= 0) {
    issues.push(`${operation}.governance.maxVramBytes must be positive`);
  }
  if (governance.maxFrameMs != null && governance.maxFrameMs <= 0) {
    issues.push(`${operation}.governance.maxFrameMs must be positive`);
  }
  return issues;
}

function operationTokens(size: number): number {
  return Math.max(1, Math.ceil(size / 1024));
}

export class SovereignXScaffold {
  private readonly clock = () => Date.now();
  private readonly router: SovereignXRouter;
  private readonly observers = new Set<SovereignXGovernanceObserver>();
  private readonly receipts: SovereignXReceipt[] = [];
  private readonly proofSurfaces: SovereignXProofSurface[] = [];
  private readonly claims: SovereignXClaim[] = [];
  private readonly devices: SovereignXDevice[] = [];
  private readonly queues: SovereignXQueue[] = [];
  private readonly buffers: SovereignXBuffer[] = [];
  private readonly textures: SovereignXTexture[] = [];
  private readonly shaders: SovereignXShader[] = [];
  private readonly pipelines: SovereignXPipeline[] = [];
  private readonly commandLists: SovereignXCommandList[] = [];
  private readonly fences: SovereignXFence[] = [];
  private readonly swapchains: SovereignXSwapchain[] = [];
  private readonly renderPasses: SovereignXRenderPass[] = [];
  private readonly framebuffers: SovereignXFramebuffer[] = [];
  private limits: SovereignXRuntimeLimits = { ...DEFAULT_LIMITS };
  private initialized = false;
  private config: SovereignXRuntimeConfig = {};
  private evidenceResolver: SovereignXEvidenceGraphResolver | null = null;
  private sequence = 0;

  constructor(config: SovereignXRuntimeConfig = {}) {
    this.router = new SovereignXRouter();
    this.configure(config);
    this.registerIntents();
  }

  initialize(config: SovereignXRuntimeConfig = {}): SovereignXStateSnapshot {
    this.configure(config);
    if (!this.initialized) {
      this.devices.splice(0, this.devices.length, this.makeDevice());
      this.queues.splice(0, this.queues.length, ...this.makeQueues(this.devices[0]));
      this.initialized = true;
      this.recordLifecycleReceipt('initialize', 'runtime', 'sx.initialize', 'runtime initialized', {
        backend: this.config.backend ?? DEFAULT_DEVICE.backend,
      });
    }
    return this.snapshot();
  }

  shutdown(): SovereignXStateSnapshot {
    this.ensureInitialized();
    this.recordLifecycleReceipt('shutdown', 'runtime', 'sx.shutdown', 'runtime shutdown', {});
    this.initialized = false;
    this.devices.splice(0);
    this.queues.splice(0);
    this.buffers.splice(0);
    this.textures.splice(0);
    this.shaders.splice(0);
    this.pipelines.splice(0);
    this.commandLists.splice(0);
    this.fences.splice(0);
    this.swapchains.splice(0);
    this.renderPasses.splice(0);
    this.framebuffers.splice(0);
    return this.snapshot();
  }

  enumerateDevices(): SovereignXDevice[] {
    this.ensureInitialized();
    return clone(this.devices);
  }

  getDefaultDevice(): SovereignXDevice {
    this.ensureInitialized();
    const device = this.devices[0];
    if (!device) {
      throw new SovereignXViolationError(this.makeViolationReceipt('getDefaultDevice', 'runtime', ['no device available']));
    }
    return clone(device);
  }

  getGraphicsQueue(deviceId?: string): SovereignXQueue {
    return this.getQueue('graphics', deviceId);
  }

  getComputeQueue(deviceId?: string): SovereignXQueue {
    return this.getQueue('compute', deviceId);
  }

  getTransferQueue(deviceId?: string): SovereignXQueue {
    return this.getQueue('transfer', deviceId);
  }

  createBuffer(desc: SovereignXBufferDesc): SovereignXBuffer {
    this.ensureInitialized();
    const issues = [
      ...validatePositiveInteger(desc.sizeBytes, 'buffer.sizeBytes'),
      ...validateGovernance(desc.governance, 'createBuffer'),
      ...(desc.usage.length === 0 ? ['buffer.usage requires at least one usage flag'] : []),
    ];
    return this.commitResource<SovereignXBuffer>('resource', 'createBuffer', 'buffer', desc.governance, issues, {
      create: () => {
        const device = this.resolveDevice(desc.deviceId);
        const buffer: SovereignXBuffer = {
          id: this.nextId('buffer'),
          deviceId: device.id,
          label: desc.label,
          sizeBytes: desc.sizeBytes,
          usage: [...desc.usage],
          governance: clone(desc.governance),
        };
        this.buffers.push(buffer);
        this.registerProofSurface(buffer.id, desc.governance, `Buffer ${buffer.id}`, 'resource');
        return buffer;
      },
      tokenCost: operationTokens(desc.sizeBytes),
      flopCost: Math.max(1, Math.ceil(desc.sizeBytes / 2048)),
    });
  }

  createTexture(desc: SovereignXTextureDesc): SovereignXTexture {
    this.ensureInitialized();
    const size = desc.size;
    const issues = [
      ...validatePositiveInteger(size.width, 'texture.size.width'),
      ...validatePositiveInteger(size.height, 'texture.size.height'),
      ...(size.depth != null ? validatePositiveInteger(size.depth, 'texture.size.depth') : []),
      ...validateGovernance(desc.governance, 'createTexture'),
      ...(desc.usage.length === 0 ? ['texture.usage requires at least one usage flag'] : []),
      ...(String(desc.format || '').trim() ? [] : ['texture.format is required']),
    ];
    return this.commitResource<SovereignXTexture>('resource', 'createTexture', 'texture', desc.governance, issues, {
      create: () => {
        const device = this.resolveDevice(desc.deviceId);
        const texture: SovereignXTexture = {
          id: this.nextId('texture'),
          deviceId: device.id,
          label: desc.label,
          size: clone(size),
          format: desc.format,
          usage: [...desc.usage],
          mipLevels: Math.max(1, desc.mipLevels ?? 1),
          governance: clone(desc.governance),
        };
        this.textures.push(texture);
        this.registerProofSurface(texture.id, desc.governance, `Texture ${texture.id}`, 'resource');
        return texture;
      },
      tokenCost: operationTokens(size.width * size.height * Math.max(1, size.depth ?? 1)),
      flopCost: Math.max(1, Math.ceil(size.width * size.height / 2)),
    });
  }

  createShader(desc: SovereignXShaderDesc): SovereignXShader {
    this.ensureInitialized();
    const issues = [
      ...validateGovernance(desc.governance, 'createShader'),
      ...(String(desc.source || '').trim() ? [] : ['shader.source is required']),
      ...(String(desc.stage || '').trim() ? [] : ['shader.stage is required']),
    ];
    return this.commitResource<SovereignXShader>('shader', 'createShader', 'shader', desc.governance, issues, {
      create: () => {
        const device = this.resolveDevice(desc.deviceId);
        const shader: SovereignXShader = {
          id: this.nextId('shader'),
          deviceId: device.id,
          label: desc.label,
          stage: desc.stage,
          entryPoint: desc.entryPoint ?? 'main',
          source: desc.source,
          governance: clone(desc.governance),
        };
        this.shaders.push(shader);
        this.registerProofSurface(shader.id, desc.governance, `Shader ${shader.id}`, 'shader');
        return shader;
      },
      tokenCost: operationTokens(desc.source.length),
      flopCost: Math.max(1, desc.source.length * 8),
    });
  }

  createGraphicsPipeline(desc: SovereignXGraphicsPipelineDesc): SovereignXPipeline {
    this.ensureInitialized();
    const issues = [
      ...validateGovernance(desc.governance, 'createGraphicsPipeline'),
      ...(this.findShader(desc.vertexShaderId, 'vertex') ? [] : [`vertex shader ${desc.vertexShaderId} not found`]),
      ...(this.findShader(desc.fragmentShaderId, 'fragment') ? [] : [`fragment shader ${desc.fragmentShaderId} not found`]),
    ];
    return this.commitResource<SovereignXPipeline>('pipeline', 'createGraphicsPipeline', 'pipeline', desc.governance, issues, {
      create: () => {
        const device = this.resolveDevice(desc.deviceId);
        this.ensureEvidenceLinks(desc.governance, desc);
        const pipeline: SovereignXPipeline = {
          id: this.nextId('graphics-pipeline'),
          deviceId: device.id,
          kind: 'graphics',
          label: desc.label,
          governance: clone(desc.governance),
          shaderIds: [desc.vertexShaderId, desc.fragmentShaderId],
          proofSurfaceId: desc.governance.proofSurfaceId,
          claimId: desc.governance.claimId,
        };
        this.pipelines.push(pipeline);
        this.registerProofSurface(pipeline.id, desc.governance, `Graphics pipeline ${pipeline.id}`, 'pipeline');
        return pipeline;
      },
      tokenCost: 64,
      flopCost: 512,
    });
  }

  createComputePipeline(desc: SovereignXComputePipelineDesc): SovereignXPipeline {
    this.ensureInitialized();
    const issues = [
      ...validateGovernance(desc.governance, 'createComputePipeline'),
      ...(this.findShader(desc.computeShaderId, 'compute') ? [] : [`compute shader ${desc.computeShaderId} not found`]),
    ];
    return this.commitResource<SovereignXPipeline>('pipeline', 'createComputePipeline', 'pipeline', desc.governance, issues, {
      create: () => {
        const device = this.resolveDevice(desc.deviceId);
        this.ensureEvidenceLinks(desc.governance, desc);
        const pipeline: SovereignXPipeline = {
          id: this.nextId('compute-pipeline'),
          deviceId: device.id,
          kind: 'compute',
          label: desc.label,
          governance: clone(desc.governance),
          shaderIds: [desc.computeShaderId],
          proofSurfaceId: desc.governance.proofSurfaceId,
          claimId: desc.governance.claimId,
        };
        this.pipelines.push(pipeline);
        this.registerProofSurface(pipeline.id, desc.governance, `Compute pipeline ${pipeline.id}`, 'pipeline');
        return pipeline;
      },
      tokenCost: 48,
      flopCost: 256,
    });
  }

  createSwapchain(desc: SovereignXSwapchainDesc): SovereignXSwapchain {
    this.ensureInitialized();
    const issues = [
      ...validatePositiveInteger(desc.width, 'swapchain.width'),
      ...validatePositiveInteger(desc.height, 'swapchain.height'),
      ...validateGovernance(desc.governance, 'createSwapchain'),
    ];
    return this.commitResource<SovereignXSwapchain>('swapchain', 'createSwapchain', 'swapchain', desc.governance, issues, {
      create: () => {
        const device = this.resolveDevice(desc.deviceId);
        const swapchain: SovereignXSwapchain = {
          id: this.nextId('swapchain'),
          deviceId: device.id,
          label: desc.label,
          width: desc.width,
          height: desc.height,
          format: desc.format,
          imageCount: Math.max(2, desc.imageCount ?? 2),
          governance: clone(desc.governance),
        };
        this.swapchains.push(swapchain);
        this.registerProofSurface(swapchain.id, desc.governance, `Swapchain ${swapchain.id}`, 'swapchain');
        return swapchain;
      },
      tokenCost: 32,
      flopCost: 64,
    });
  }

  createRenderPass(desc: SovereignXRenderPassDesc): SovereignXRenderPass {
    this.ensureInitialized();
    const issues = [
      ...validateGovernance(desc.governance, 'createRenderPass'),
      ...(desc.colorFormats.length === 0 ? ['renderPass.colorFormats requires at least one format'] : []),
    ];
    return this.commitResource<SovereignXRenderPass>('pipeline', 'createRenderPass', 'render-pass', desc.governance, issues, {
      create: () => {
        const renderPass: SovereignXRenderPass = {
          id: this.nextId('render-pass'),
          label: desc.label,
          colorFormats: [...desc.colorFormats],
          depthFormat: desc.depthFormat,
          governance: clone(desc.governance),
        };
        this.renderPasses.push(renderPass);
        this.registerProofSurface(renderPass.id, desc.governance, `Render pass ${renderPass.id}`, 'render-pass');
        return renderPass;
      },
      tokenCost: 16,
      flopCost: 32,
    });
  }

  createFramebuffer(desc: SovereignXFramebufferDesc): SovereignXFramebuffer {
    this.ensureInitialized();
    const issues = [
      ...validatePositiveInteger(desc.width, 'framebuffer.width'),
      ...validatePositiveInteger(desc.height, 'framebuffer.height'),
      ...validateGovernance(desc.governance, 'createFramebuffer'),
      ...(String(desc.renderPassId || '').trim() ? [] : ['framebuffer.renderPassId is required']),
      ...(desc.attachments.length === 0 ? ['framebuffer.attachments requires at least one attachment'] : []),
    ];
    return this.commitResource<SovereignXFramebuffer>('resource', 'createFramebuffer', 'framebuffer', desc.governance, issues, {
      create: () => {
        const framebuffer: SovereignXFramebuffer = {
          id: this.nextId('framebuffer'),
          label: desc.label,
          renderPassId: desc.renderPassId,
          attachments: [...desc.attachments],
          width: desc.width,
          height: desc.height,
          governance: clone(desc.governance),
        };
        this.framebuffers.push(framebuffer);
        this.registerProofSurface(framebuffer.id, desc.governance, `Framebuffer ${framebuffer.id}`, 'framebuffer');
        return framebuffer;
      },
      tokenCost: 24,
      flopCost: 48,
    });
  }

  beginCommands(queue: SovereignXQueue | string, label?: string): SovereignXCommandList {
    this.ensureInitialized();
    const queueId = typeof queue === 'string' ? queue : queue.id;
    const resolvedQueue = this.resolveQueue(queueId);
    const commandList: SovereignXCommandList = {
      id: this.nextId('command-list'),
      queueId: resolvedQueue.id,
      label,
      commands: [],
      closed: false,
      record: (command: string) => {
        if (commandList.closed) {
          throw new SovereignXViolationError(this.makeViolationReceipt('beginCommands', commandList.id, ['command list is already closed']));
        }
        commandList.commands.push(command);
      },
      close: () => {
        commandList.closed = true;
      },
    };
    this.commitOperation<SovereignXCommandList>({
      kind: 'command',
      operation: 'beginCommands',
      subjectId: commandList.id,
      intentId: 'sx.begin_commands',
      governance: {
        intentId: 'sx.begin_commands',
      },
      tokenCost: 8,
      flopCost: 8,
      create: () => {
        this.commandLists.push(commandList);
        this.registerProofSurface(commandList.id, { intentId: 'sx.begin_commands' }, `Command list ${commandList.id}`, 'command');
        return commandList;
      },
      metadata: { queueId: resolvedQueue.id },
      allowReturn: true,
    });
    return commandList;
  }

  submitCommands(commandList: SovereignXCommandList, queue?: SovereignXQueue | string, presentSwapchainId?: string): SovereignXReceipt {
    this.ensureInitialized();
    const resolvedQueue = queue ? this.resolveQueue(typeof queue === 'string' ? queue : queue.id) : this.resolveQueue(commandList.queueId);
    commandList.close();
    return this.commitOperation<SovereignXReceipt>({
      kind: 'command',
      operation: 'submitCommands',
      subjectId: commandList.id,
      intentId: 'sx.submit_commands',
      governance: { intentId: 'sx.submit_commands', proofSurfaceId: presentSwapchainId ? `${presentSwapchainId}-proof` : undefined },
      tokenCost: Math.max(8, commandList.commands.length * 4),
      flopCost: Math.max(16, commandList.commands.length * 16),
      metadata: {
        queueId: resolvedQueue.id,
        presentSwapchainId,
        commandCount: commandList.commands.length,
      },
    });
  }

  presentSwapchainFrame(swapchain: SovereignXSwapchain | string): SovereignXReceipt {
    this.ensureInitialized();
    const swapchainId = typeof swapchain === 'string' ? swapchain : swapchain.id;
    return this.commitOperation<SovereignXReceipt>({
      kind: 'swapchain',
      operation: 'presentSwapchainFrame',
      subjectId: swapchainId,
      intentId: 'sx.present_frame',
      governance: { intentId: 'sx.present_frame', proofSurfaceId: `${swapchainId}-proof` },
      tokenCost: 8,
      flopCost: 16,
      metadata: { swapchainId },
    });
  }

  waitForFence(fence: SovereignXFence | string, targetValue?: number): SovereignXFence {
    this.ensureInitialized();
    const resolved = this.resolveFence(fence);
    const target = targetValue ?? resolved.targetValue;
    this.commitOperation<SovereignXFence>({
      kind: 'fence',
      operation: 'waitForFence',
      subjectId: resolved.id,
      intentId: 'sx.wait_for_fence',
      governance: { intentId: 'sx.wait_for_fence' },
      tokenCost: 4,
      flopCost: 4,
      metadata: { targetValue: target },
    });
    resolved.targetValue = target;
    resolved.signaledValue = Math.max(resolved.signaledValue, target);
    return clone(resolved);
  }

  waitIdle(): SovereignXReceipt {
    this.ensureInitialized();
    return this.commitOperation<SovereignXReceipt>({
      kind: 'lifecycle',
      operation: 'waitIdle',
      subjectId: 'runtime',
      intentId: 'sx.wait_idle',
      governance: { intentId: 'sx.wait_idle' },
      tokenCost: 4,
      flopCost: 4,
      metadata: {},
    });
  }

  registerGovernanceObserver(observer: SovereignXGovernanceObserver): void {
    this.observers.add(observer);
  }

  setRuntimeLimits(limits: Partial<SovereignXRuntimeLimits>): SovereignXRuntimeLimits {
    this.limits = {
      ...this.limits,
      ...limits,
    };
    return clone(this.limits);
  }

  setEvidenceGraphResolver(resolver: SovereignXEvidenceGraphResolver | null): void {
    this.evidenceResolver = resolver;
  }

  resolveClaim(claimId: string): SovereignXClaim | null {
    return clone(this.claims.find((claim) => claim.id === claimId) || this.evidenceResolver?.resolveClaim(claimId) || null);
  }

  resolveProofSurface(proofSurfaceId: string): SovereignXProofSurface | null {
    return clone(this.proofSurfaces.find((surface) => surface.id === proofSurfaceId) || this.evidenceResolver?.resolveProofSurface(proofSurfaceId) || null);
  }

  resolveReceipt(receiptId: string): SovereignXReceipt | null {
    return clone(this.receipts.find((receipt) => receipt.id === receiptId) || this.evidenceResolver?.resolveReceipt(receiptId) || null);
  }

  listReceipts(): SovereignXReceipt[] {
    return clone(this.receipts);
  }

  listProofSurfaces(): SovereignXProofSurface[] {
    return clone(this.proofSurfaces);
  }

  snapshot(): SovereignXStateSnapshot {
    return {
      initialized: this.initialized,
      applicationName: this.config.applicationName ?? 'SovereignX Scaffold',
      backend: this.config.backend ?? DEFAULT_DEVICE.backend,
      deviceCount: this.devices.length,
      bufferCount: this.buffers.length,
      textureCount: this.textures.length,
      shaderCount: this.shaders.length,
      pipelineCount: this.pipelines.length,
      commandListCount: this.commandLists.length,
      receiptCount: this.receipts.length,
      proofSurfaceCount: this.proofSurfaces.length,
      limits: clone(this.limits),
    };
  }

  private configure(config: SovereignXRuntimeConfig): void {
    this.config = {
      ...this.config,
      ...config,
      backend: config.backend ?? this.config.backend ?? DEFAULT_DEVICE.backend,
    };
    this.limits = {
      ...DEFAULT_LIMITS,
      ...this.limits,
      ...(config.limits || {}),
    };
  }

  private registerIntents(): void {
    const operations: Array<{ id: string; domain: CiemsIntentSpec['domain']; maxTokens: number; maxFlops: number }> = [
      { id: 'runtime.initialize', domain: 'governance', maxTokens: 16, maxFlops: 16 },
      { id: 'runtime.shutdown', domain: 'governance', maxTokens: 16, maxFlops: 16 },
      { id: 'sx.initialize', domain: 'governance', maxTokens: 16, maxFlops: 16 },
      { id: 'sx.shutdown', domain: 'governance', maxTokens: 16, maxFlops: 16 },
      { id: 'sx.create_buffer', domain: 'tool_call', maxTokens: 4_096, maxFlops: 2_000_000 },
      { id: 'sx.create_texture', domain: 'render_frame', maxTokens: 8_192, maxFlops: 4_000_000 },
      { id: 'sx.create_shader', domain: 'tool_call', maxTokens: 2_048, maxFlops: 1_000_000 },
      { id: 'sx.create_graphics_pipeline', domain: 'render_frame', maxTokens: 2_048, maxFlops: 1_000_000 },
      { id: 'sx.create_compute_pipeline', domain: 'mlp', maxTokens: 2_048, maxFlops: 1_000_000 },
      { id: 'sx.create_swapchain', domain: 'render_frame', maxTokens: 2_048, maxFlops: 64_000 },
      { id: 'sx.create_render_pass', domain: 'render_frame', maxTokens: 2_048, maxFlops: 32_000 },
      { id: 'sx.create_framebuffer', domain: 'render_frame', maxTokens: 2_048, maxFlops: 64_000 },
      { id: 'sx.begin_commands', domain: 'tool_call', maxTokens: 2_048, maxFlops: 64_000 },
      { id: 'sx.submit_commands', domain: 'tool_call', maxTokens: 2_048, maxFlops: 128_000 },
      { id: 'sx.present_frame', domain: 'render_frame', maxTokens: 2_048, maxFlops: 64_000 },
      { id: 'sx.wait_for_fence', domain: 'tool_call', maxTokens: 128, maxFlops: 16_000 },
      { id: 'sx.wait_idle', domain: 'tool_call', maxTokens: 128, maxFlops: 16_000 },
    ];
    for (const operation of operations) {
      this.router.registerIntent({
        id: operation.id,
        domain: operation.domain,
        rules: `SovereignX ${operation.id} remains governed by the scaffold contract`,
        allowedTargets: ['CPU', 'DELAY'],
        maxTokensPerAgentPerMin: operation.maxTokens,
        maxFlopsPerAgentPerMin: operation.maxFlops,
      });
    }
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      this.initialize(this.config);
    }
  }

  private makeDevice(): SovereignXDevice {
    return clone({
      ...DEFAULT_DEVICE,
      backend: this.config.backend ?? DEFAULT_DEVICE.backend,
      description: `${this.config.applicationName ?? DEFAULT_DEVICE.name} scaffold device`,
    });
  }

  private makeQueues(device: SovereignXDevice): SovereignXQueue[] {
    return device.queueKinds.map((kind) => ({
      id: this.nextId(`${kind}-queue`),
      deviceId: device.id,
      kind,
      label: `${device.name} ${kind} queue`,
    }));
  }

  private resolveDevice(deviceId?: string): SovereignXDevice {
    this.ensureInitialized();
    const device = deviceId ? this.devices.find((entry) => entry.id === deviceId) : this.devices[0];
    if (!device) {
      throw new SovereignXViolationError(this.makeViolationReceipt('resolveDevice', 'runtime', ['device not found']));
    }
    return device;
  }

  private getQueue(kind: SovereignXQueueKind, deviceId?: string): SovereignXQueue {
    this.ensureInitialized();
    const queue = this.queues.find((entry) => entry.kind === kind && (!deviceId || entry.deviceId === deviceId));
    if (!queue) {
      throw new SovereignXViolationError(this.makeViolationReceipt('getQueue', kind, ['queue not found']));
    }
    return queue;
  }

  private resolveQueue(queueId: string): SovereignXQueue {
    const queue = this.queues.find((entry) => entry.id === queueId);
    if (!queue) {
      throw new SovereignXViolationError(this.makeViolationReceipt('resolveQueue', queueId, ['queue not found']));
    }
    return queue;
  }

  private resolveFence(fence: SovereignXFence | string): SovereignXFence {
    const resolved = typeof fence === 'string' ? this.fences.find((entry) => entry.id === fence) : fence;
    if (!resolved) {
      throw new SovereignXViolationError(this.makeViolationReceipt('resolveFence', typeof fence === 'string' ? fence : fence.id, ['fence not found']));
    }
    return resolved;
  }

  private findShader(shaderId: string, stage?: SovereignXShaderStage): SovereignXShader | undefined {
    return this.shaders.find((shader) => shader.id === shaderId && (!stage || shader.stage === stage));
  }

  private ensureEvidenceLinks(governance: SovereignXResourceGovernance, desc: { label?: string }): void {
    const proofSurface = governance.proofSurfaceId ? this.resolveProofSurface(governance.proofSurfaceId) : null;
    const claim = governance.claimId ? this.resolveClaim(governance.claimId) : null;
    if (governance.proofSurfaceId && !proofSurface) {
      throw new SovereignXViolationError(this.makeViolationReceipt('resolveProofSurface', governance.proofSurfaceId, ['proof surface not found']));
    }
    if (governance.claimId && !claim) {
      throw new SovereignXViolationError(this.makeViolationReceipt('resolveClaim', governance.claimId, ['claim not found']));
    }
    void desc;
  }

  private registerProofSurface(
    sourceId: string,
    governance: SovereignXResourceGovernance,
    label: string,
    proofKind: SovereignXProofSurface['kind'],
  ): SovereignXProofSurface {
    const proofSurface: SovereignXProofSurface = {
      id: governance.proofSurfaceId ?? `${sourceId}-proof`,
      label,
      kind: proofKind,
      claimId: governance.claimId ?? `${sourceId}-claim`,
      evidenceIds: [],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
      truthBoundary: 'SovereignX scaffold truth boundary',
      sourceId,
    };
    this.proofSurfaces.push(proofSurface);
    const claim: SovereignXClaim = {
      id: proofSurface.claimId,
      role: governance.intentId,
      statement: `${label} is governed by ${governance.intentId}`,
      proofSurfaceId: proofSurface.id,
      evidenceIds: [],
      status: 'verified',
    };
    this.claims.push(claim);
    return proofSurface;
  }

  private registerExecutionProofSurface(input: {
    receiptId: string;
    operation: string;
    subjectId: string;
    intentId: string;
    outcome: SovereignXReceiptOutcome;
    routeEvaluation: RouteEvaluation;
    validationIssues: string[];
    governance: SovereignXResourceGovernance;
  }): SovereignXExecutionProofSurface {
    const executionContract = this.buildExecutionContract(input);
    const proofSurfaceId = `${input.receiptId}-execution-proof`;
    const claimId = `${input.receiptId}-execution-claim`;
    const evidenceIds = [input.receiptId, input.routeEvaluation.evidence.id];
    const proofSurface: SovereignXExecutionProofSurface = {
      id: proofSurfaceId,
      label: `Execution ${input.operation}`,
      kind: 'execution',
      claimId,
      evidenceIds,
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
      truthBoundary: executionContract.truthBoundary,
      sourceId: input.receiptId,
      executionContract,
    };
    this.proofSurfaces.push(proofSurface);
    const claim: SovereignXClaim = {
      id: claimId,
      role: input.intentId,
      statement: `${input.operation} executed for ${input.subjectId} under ${input.intentId}`,
      proofSurfaceId: proofSurface.id,
      evidenceIds,
      status: input.outcome === 'allow' ? 'verified' : 'pending',
    };
    this.claims.push(claim);
    return proofSurface;
  }

  private buildExecutionContract(input: {
    receiptId: string;
    operation: string;
    subjectId: string;
    intentId: string;
    outcome: SovereignXReceiptOutcome;
    routeEvaluation: RouteEvaluation;
    validationIssues: string[];
    governance: SovereignXResourceGovernance;
  }): SovereignXExecutionContract {
    const authority = input.governance.claimId
      ? `claim ${input.governance.claimId} authorized by intent ${input.intentId}`
      : `intent ${input.intentId} authorized by AAES governance`;
    const evidenceIds = [input.receiptId, input.routeEvaluation.evidence.id];
    const artifacts = [
      `receipt:${input.receiptId}`,
      `evidence:${input.routeEvaluation.evidence.id}`,
      `route:${input.routeEvaluation.localDecision.target}`,
    ];
    const complianceRequirements = [
      'Intent must be registered before execution',
      'Authority must resolve through governed intent',
      'Evidence must exist for the execution path',
      'Verification must remain replayable',
      'Truth boundary must be declared',
    ];
    const complianceIssues = input.validationIssues.length > 0 ? [...input.validationIssues] : [];
    const allowed = input.outcome === 'allow' && complianceIssues.length === 0;

    return {
      operation: input.operation,
      subjectId: input.subjectId,
      intentId: input.intentId,
      authority,
      evidence: {
        receipts: [input.receiptId],
        artifacts,
        summary: `Execution receipt ${input.receiptId} and routed evidence ${input.routeEvaluation.evidence.id} prove ${input.operation}.`,
      },
      verification: {
        method: 'Replay the routed work item, validate the execution proof surface, and inspect the emitted receipt.',
        validator: 'SovereignX scaffold execution contract',
        replayArtifacts: evidenceIds,
        replayable: true,
      },
      compliance: {
        requirements: complianceRequirements,
        satisfied: allowed,
        issues: complianceIssues,
      },
      truthBoundary: allowed
        ? `SovereignX proves governed execution for ${input.subjectId}, not full cluster orchestration.`
        : `SovereignX proves the execution request was evaluated and denied or constrained, not unrestricted GPU/runtime access.`,
    };
  }

  private recordReceipt(receipt: SovereignXReceipt): SovereignXReceipt {
    this.receipts.push(receipt);
    this.notifyReceipt(receipt);
    return receipt;
  }

  private notifyReceipt(receipt: SovereignXReceipt): void {
    for (const observer of this.observers) {
      observer.onReceipt?.(clone(receipt));
      if (receipt.outcome !== 'allow') {
        observer.onViolation?.(clone(receipt));
      }
    }
  }

  private recordLifecycleReceipt(
    operation: 'initialize' | 'shutdown',
    subjectId: string,
    intentId: string,
    reason: string,
    metadata: Record<string, unknown>,
  ): SovereignXReceipt {
    const now = Date.now();
    const workItem: WorkItem = {
      id: this.nextId(`lifecycle-${operation}`),
      agentId: 'sovereignx-scaffold',
      kind: 'governance',
      intentId,
      costEstimateTokens: 0,
      costEstimateFlops: 0,
      priority: 0,
      tenantId: this.config.applicationName ?? 'SovereignX',
    };
    const runtime = defaultRuntimeStats();
    const limits = this.mapGovernanceLimits();
    const measurementHealth: MeasurementHealth = {
      trusted: true,
      stale: false,
      sampleCount: 0,
      windowMs: 60_000,
      temperatureVarianceC: 0,
      notes: ['lifecycle receipt'],
    };
    const routeDecision: RouteDecision = {
      target: 'CPU',
      reason,
      mode: 'Normal',
    };
    const evidence: EvidenceRecord = {
      id: `evidence-${workItem.id}-${now}`,
      workItemId: workItem.id,
      agentId: workItem.agentId,
      kind: workItem.kind,
      intentId,
      estTokens: 0,
      estFlops: 0,
      runtime: clone(runtime),
      limits: clone(limits),
      localDecision: routeDecision,
      timestamp: new Date(now).toISOString(),
    };
    const receiptId = this.nextId('receipt');
    const executionProofSurface = this.registerExecutionProofSurface({
      receiptId,
      operation,
      subjectId,
      intentId,
      outcome: 'allow',
      routeEvaluation: {
        workItem: clone(workItem),
        runtime,
        limits,
        measurementHealth,
        localDecision: routeDecision,
        ciemsDecisions: [],
        effectiveDecision: routeDecision,
        evidence,
      },
      validationIssues: [],
      governance: { intentId },
    });
    const receipt: SovereignXReceipt = {
      id: receiptId,
      kind: 'lifecycle',
      operation,
      subjectId,
      timestamp: new Date(now).toISOString(),
      intentId,
      outcome: 'allow',
      reason,
      routeDecision,
      routeEvaluation: {
        workItem: clone(workItem),
        runtime,
        limits,
        measurementHealth,
        localDecision: routeDecision,
        ciemsDecisions: [],
        effectiveDecision: routeDecision,
        evidence,
      },
      validationIssues: [],
      governance: { intentId },
      executionProofSurfaceId: executionProofSurface.id,
      executionContract: executionProofSurface.executionContract,
      metadata: { ...metadata },
    };
    return this.recordReceipt(receipt);
  }

  private commitResource<T>(
    kind: SovereignXReceiptKind,
    operation: string,
    subjectId: string,
    governance: SovereignXResourceGovernance,
    validationIssues: string[],
    options: {
      create: () => T;
      tokenCost: number;
      flopCost: number;
    },
  ): T {
    return this.commitOperation<T>({
      kind,
      operation,
      subjectId,
      intentId: governance.intentId,
      governance,
      validationIssues,
      tokenCost: options.tokenCost,
      flopCost: options.flopCost,
      metadata: {},
      create: options.create,
      allowReturn: true,
    }) as T;
  }

  private commitOperation<T>(options: {
    kind: SovereignXReceiptKind;
    operation: string;
    subjectId: string;
    intentId: string;
    governance: SovereignXResourceGovernance;
    validationIssues?: string[];
    tokenCost: number;
    flopCost: number;
    metadata: Record<string, unknown>;
    create?: () => T;
    allowReturn?: boolean;
  }): T | SovereignXReceipt {
    const validationIssues = [...(options.validationIssues || [])];
    const workItem: WorkItem = {
      id: this.nextId(options.operation),
      agentId: 'sovereignx-scaffold',
      kind: 'tool_call',
      intentId: options.intentId,
      costEstimateTokens: options.tokenCost,
      costEstimateFlops: options.flopCost,
      costEstimateMs: Math.max(1, Math.ceil(options.flopCost / 10_000)),
      priority: 1,
      tenantId: this.config.applicationName ?? 'SovereignX',
    };
    const runtime = defaultRuntimeStats();
    runtime.vramUsedBytes = this.estimateVramUsage();
    runtime.vramTotalBytes = this.limits.maxVramBytes;
    const routeEvaluation = this.router.evaluate(workItem, runtime, this.mapGovernanceLimits());
    const outcome = this.mapOutcome(routeEvaluation, validationIssues);
    const receiptId = this.nextId('receipt');
    const executionProofSurface = this.registerExecutionProofSurface({
      receiptId,
      operation: options.operation,
      subjectId: options.subjectId,
      intentId: options.intentId,
      outcome,
      routeEvaluation,
      validationIssues,
      governance: options.governance,
    });
    const receipt: SovereignXReceipt = {
      id: receiptId,
      kind: options.kind,
      operation: options.operation,
      subjectId: options.subjectId,
      timestamp: new Date().toISOString(),
      intentId: options.intentId,
      outcome,
      reason: validationIssues[0] || routeEvaluation.effectiveDecision.reason || routeEvaluation.localDecision.reason,
      routeDecision: routeEvaluation.effectiveDecision,
      routeEvaluation,
      validationIssues,
      governance: clone(options.governance),
      claimId: options.governance.claimId,
      proofSurfaceId: options.governance.proofSurfaceId,
      executionProofSurfaceId: executionProofSurface.id,
      executionContract: executionProofSurface.executionContract,
      metadata: { ...options.metadata },
    };
    this.recordReceipt(receipt);
    if (outcome !== 'allow') {
      throw new SovereignXViolationError(receipt);
    }
    if (!options.create) {
      return receipt;
    }
    return options.create();
  }

  private mapGovernanceLimits(): GovernanceLimits {
    return {
      maxGpuJobs: 8,
      maxCpuJobs: 16,
      maxConcurrentJobs: 24,
      maxGpuTempC: this.limits.maxGpuTempC,
      maxVramBytes: this.limits.maxVramBytes,
      maxTokensPerAgentPerMin: this.limits.maxTokensPerAgentPerMin,
      maxFlopsPerAgentPerMin: this.limits.maxFlopsPerAgentPerMin,
      gpuKindThreshold: 0,
    };
  }

  private mapOutcome(routeEvaluation: RouteEvaluation, validationIssues: string[]): SovereignXReceiptOutcome {
    if (validationIssues.length > 0) {
      return 'deny';
    }
    if (routeEvaluation.ciemsDecisions.some((decision) => decision.action === 'quarantine')) {
      return 'quarantine';
    }
    if (routeEvaluation.ciemsDecisions.some((decision) => decision.action === 'throttle')) {
      return 'throttle';
    }
    if (routeEvaluation.effectiveDecision.target === 'DELAY') {
      return 'delay';
    }
    if (routeEvaluation.effectiveDecision.target === 'DROP') {
      return 'deny';
    }
    return 'allow';
  }

  private estimateVramUsage(): number {
    const totalResourceBytes = this.buffers.reduce((sum, buffer) => sum + buffer.sizeBytes, 0);
    const totalTextureBytes = this.textures.reduce((sum, texture) => sum + texture.size.width * texture.size.height * Math.max(1, texture.size.depth ?? 1) * 4, 0);
    return totalResourceBytes + totalTextureBytes;
  }

  private makeViolationReceipt(operation: string, subjectId: string, issues: string[]): SovereignXReceipt {
    const routeEvaluation = this.router.evaluate(
      {
        id: this.nextId(operation),
        agentId: 'sovereignx-scaffold',
        kind: 'tool_call',
        intentId: `sx.${operation}`,
        costEstimateTokens: 1,
        costEstimateFlops: 1,
        costEstimateMs: 1,
        priority: 1,
        tenantId: this.config.applicationName ?? 'SovereignX',
      },
      defaultRuntimeStats(),
      this.mapGovernanceLimits(),
    );
    const receiptId = this.nextId('receipt');
    const executionProofSurface = this.registerExecutionProofSurface({
      receiptId,
      operation,
      subjectId,
      intentId: `sx.${operation}`,
      outcome: 'deny',
      routeEvaluation,
      validationIssues: [...issues],
      governance: { intentId: `sx.${operation}` },
    });
    return {
      id: receiptId,
      kind: 'governance',
      operation,
      subjectId,
      timestamp: new Date().toISOString(),
      intentId: `sx.${operation}`,
      outcome: 'deny',
      reason: issues[0] || `${operation} denied`,
      routeDecision: routeEvaluation.effectiveDecision,
      routeEvaluation,
      validationIssues: [...issues],
      governance: { intentId: `sx.${operation}` },
      executionProofSurfaceId: executionProofSurface.id,
      executionContract: executionProofSurface.executionContract,
      metadata: { issues: [...issues] },
    };
  }

  private nextId(prefix: string): string {
    this.sequence += 1;
    return `${prefix}-${this.sequence}`;
  }
}

export function createSovereignXScaffold(config: SovereignXRuntimeConfig = {}): SovereignXScaffold {
  return new SovereignXScaffold(config);
}

const defaultScaffold = new SovereignXScaffold();

export function initialize(config: SovereignXRuntimeConfig = {}): SovereignXStateSnapshot {
  return defaultScaffold.initialize(config);
}

export function shutdown(): SovereignXStateSnapshot {
  return defaultScaffold.shutdown();
}

export function enumerateDevices(): SovereignXDevice[] {
  return defaultScaffold.enumerateDevices();
}

export function getDefaultDevice(): SovereignXDevice {
  return defaultScaffold.getDefaultDevice();
}

export function getGraphicsQueue(deviceId?: string): SovereignXQueue {
  return defaultScaffold.getGraphicsQueue(deviceId);
}

export function getComputeQueue(deviceId?: string): SovereignXQueue {
  return defaultScaffold.getComputeQueue(deviceId);
}

export function getTransferQueue(deviceId?: string): SovereignXQueue {
  return defaultScaffold.getTransferQueue(deviceId);
}

export function createBuffer(desc: SovereignXBufferDesc): SovereignXBuffer {
  return defaultScaffold.createBuffer(desc);
}

export function createTexture(desc: SovereignXTextureDesc): SovereignXTexture {
  return defaultScaffold.createTexture(desc);
}

export function createShader(desc: SovereignXShaderDesc): SovereignXShader {
  return defaultScaffold.createShader(desc);
}

export function createGraphicsPipeline(desc: SovereignXGraphicsPipelineDesc): SovereignXPipeline {
  return defaultScaffold.createGraphicsPipeline(desc);
}

export function createComputePipeline(desc: SovereignXComputePipelineDesc): SovereignXPipeline {
  return defaultScaffold.createComputePipeline(desc);
}

export function createSwapchain(desc: SovereignXSwapchainDesc): SovereignXSwapchain {
  return defaultScaffold.createSwapchain(desc);
}

export function createRenderPass(desc: SovereignXRenderPassDesc): SovereignXRenderPass {
  return defaultScaffold.createRenderPass(desc);
}

export function createFramebuffer(desc: SovereignXFramebufferDesc): SovereignXFramebuffer {
  return defaultScaffold.createFramebuffer(desc);
}

export function beginCommands(queue: SovereignXQueue | string, label?: string): SovereignXCommandList {
  return defaultScaffold.beginCommands(queue, label);
}

export function submitCommands(commandList: SovereignXCommandList, queue?: SovereignXQueue | string, presentSwapchainId?: string): SovereignXReceipt {
  return defaultScaffold.submitCommands(commandList, queue, presentSwapchainId);
}

export function presentSwapchainFrame(swapchain: SovereignXSwapchain | string): SovereignXReceipt {
  return defaultScaffold.presentSwapchainFrame(swapchain);
}

export function waitForFence(fence: SovereignXFence | string, targetValue?: number): SovereignXFence {
  return defaultScaffold.waitForFence(fence, targetValue);
}

export function waitIdle(): SovereignXReceipt {
  return defaultScaffold.waitIdle();
}

export function registerGovernanceObserver(observer: SovereignXGovernanceObserver): void {
  defaultScaffold.registerGovernanceObserver(observer);
}

export function setRuntimeLimits(limits: Partial<SovereignXRuntimeLimits>): SovereignXRuntimeLimits {
  return defaultScaffold.setRuntimeLimits(limits);
}

export function setEvidenceGraphResolver(resolver: SovereignXEvidenceGraphResolver | null): void {
  defaultScaffold.setEvidenceGraphResolver(resolver);
}

export function resolveClaim(claimId: string): SovereignXClaim | null {
  return defaultScaffold.resolveClaim(claimId);
}

export function resolveProofSurface(proofSurfaceId: string): SovereignXProofSurface | null {
  return defaultScaffold.resolveProofSurface(proofSurfaceId);
}

export function resolveReceipt(receiptId: string): SovereignXReceipt | null {
  return defaultScaffold.resolveReceipt(receiptId);
}

export function listReceipts(): SovereignXReceipt[] {
  return defaultScaffold.listReceipts();
}

export function listProofSurfaces(): SovereignXProofSurface[] {
  return defaultScaffold.listProofSurfaces();
}

export const SovereignX = {
  initialize,
  shutdown,
  enumerateDevices,
  getDefaultDevice,
  getGraphicsQueue,
  getComputeQueue,
  getTransferQueue,
  createBuffer,
  createTexture,
  createShader,
  createGraphicsPipeline,
  createComputePipeline,
  createSwapchain,
  createRenderPass,
  createFramebuffer,
  beginCommands,
  submitCommands,
  presentSwapchainFrame,
  waitForFence,
  waitIdle,
  registerGovernanceObserver,
  setRuntimeLimits,
  setEvidenceGraphResolver,
  resolveClaim,
  resolveProofSurface,
  resolveReceipt,
  listReceipts,
  listProofSurfaces,
  createSovereignXScaffold,
};
