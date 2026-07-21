import {
  MAGIC,
  NovaCodaClient,
  NovaCodaMessageType,
  SOCKET_PATH,
  type NovaArenaHandle,
  type NovaArenaRequest,
  type NovaCodaClientOptions,
  type NovaCodaFrame,
  type NovaCodaPingResponse,
  type NovaConstitutionalCheckRequest,
  type NovaConstitutionalDecision,
  type NovaFiberReady,
  type NovaFiberRequest,
  type NovaInferRequest,
  type NovaInferResult,
  type NovaPluginLoadRequest,
  type NovaPluginLoadResult,
  type NovaSyscallRequest,
  type NovaSyscallResult,
  decodeJsonBody,
} from '@aaes-os/nova-substrate-client';

export interface NovaCodaTransport {
  connect(): Promise<void>;
  ping(): Promise<NovaCodaPingResponse>;
  request?(msgType: NovaCodaMessageType, body?: object | Buffer | string): Promise<NovaCodaFrame>;
  allocateArena?(request: NovaArenaRequest): Promise<NovaArenaHandle>;
  spawnFiber?(request: NovaFiberRequest): Promise<NovaFiberReady>;
  infer?(request: NovaInferRequest): Promise<NovaInferResult>;
  syscall?(request: NovaSyscallRequest): Promise<NovaSyscallResult>;
  constitutionalCheck?(request: NovaConstitutionalCheckRequest): Promise<NovaConstitutionalDecision>;
  loadPlugin?(request: NovaPluginLoadRequest): Promise<NovaPluginLoadResult>;
  disconnect(): void;
}

export interface NovaCodaRuntimeSnapshot {
  packageName: '@aaes-os/nova-coda';
  transport: 'NovaCodaClient' | 'custom';
  substrate: 'Rust socket substrate';
  socketPath: string;
  protocolMagic: string;
  lastOperation?: string;
  operations: {
    connect: number;
    ping: number;
    request: number;
    arena: number;
    fiber: number;
    inference: number;
    syscall: number;
    constitutional: number;
    plugin: number;
  };
}

export interface NovaCodaRuntimeOptions {
  transport?: NovaCodaTransport;
  socketPath?: string;
}

export class NovaCodaRuntime {
  private readonly transport: NovaCodaTransport;
  private readonly socketPath: string;
  private lastOperation: string | undefined;
  private readonly operations = {
    connect: 0,
    ping: 0,
    request: 0,
    arena: 0,
    fiber: 0,
    inference: 0,
    syscall: 0,
    constitutional: 0,
    plugin: 0,
  };

  constructor(options: NovaCodaRuntimeOptions = {}) {
    this.transport =
      options.transport ?? new NovaCodaClient({ socketPath: options.socketPath });
    this.socketPath = options.socketPath ?? SOCKET_PATH;
  }

  async connect(): Promise<this> {
    this.operations.connect += 1;
    this.lastOperation = 'connect';
    await this.transport.connect();
    return this;
  }

  async ping(): Promise<NovaCodaRuntimeSnapshot> {
    this.operations.ping += 1;
    this.lastOperation = 'ping';
    await this.transport.ping();
    return this.snapshot();
  }

  async request(msgType: NovaCodaMessageType, body?: object | Buffer | string): Promise<NovaCodaFrame> {
    this.operations.request += 1;
    this.lastOperation = `request:${msgType}`;
    const request = this.transport.request as
      | ((msgType: NovaCodaMessageType, body?: object | Buffer | string) => Promise<NovaCodaFrame>)
      | undefined;
    if (request) {
      return request.call(this.transport, msgType, body);
    }
    throw new Error('transport does not expose the generic request surface');
  }

  async allocateArena(request: NovaArenaRequest): Promise<NovaArenaHandle> {
    this.operations.arena += 1;
    this.lastOperation = 'allocateArena';
    return this.invoke<NovaArenaHandle>('allocateArena', NovaCodaMessageType.AllocArena, request, NovaCodaMessageType.ArenaHandle);
  }

  async spawnFiber(request: NovaFiberRequest): Promise<NovaFiberReady> {
    this.operations.fiber += 1;
    this.lastOperation = 'spawnFiber';
    return this.invoke<NovaFiberReady>('spawnFiber', NovaCodaMessageType.SpawnFiber, request, NovaCodaMessageType.FiberReady);
  }

  async infer(request: NovaInferRequest): Promise<NovaInferResult> {
    this.operations.inference += 1;
    this.lastOperation = 'infer';
    return this.invoke<NovaInferResult>('infer', NovaCodaMessageType.InferRequest, request, NovaCodaMessageType.InferDone);
  }

  async syscall(request: NovaSyscallRequest): Promise<NovaSyscallResult> {
    this.operations.syscall += 1;
    this.lastOperation = 'syscall';
    return this.invoke<NovaSyscallResult>('syscall', NovaCodaMessageType.SyscallRequest, request, NovaCodaMessageType.SyscallResult);
  }

  async constitutionalCheck(request: NovaConstitutionalCheckRequest): Promise<NovaConstitutionalDecision> {
    this.operations.constitutional += 1;
    this.lastOperation = 'constitutionalCheck';
    return this.invoke<NovaConstitutionalDecision>(
      'constitutionalCheck',
      NovaCodaMessageType.ConstitutionalCheck,
      request,
      NovaCodaMessageType.CenDecision,
    );
  }

  async loadPlugin(request: NovaPluginLoadRequest): Promise<NovaPluginLoadResult> {
    this.operations.plugin += 1;
    this.lastOperation = 'loadPlugin';
    return this.invoke<NovaPluginLoadResult>('loadPlugin', NovaCodaMessageType.PluginLoad, request, NovaCodaMessageType.PluginLoad);
  }

  disconnect(): void {
    this.lastOperation = 'disconnect';
    this.transport.disconnect();
  }

  snapshot(): NovaCodaRuntimeSnapshot {
    return {
      packageName: '@aaes-os/nova-coda',
      transport: this.transport instanceof NovaCodaClient ? 'NovaCodaClient' : 'custom',
      substrate: 'Rust socket substrate',
      socketPath: this.socketPath,
      protocolMagic: `0x${MAGIC.toString('hex')}`,
      lastOperation: this.lastOperation,
      operations: { ...this.operations },
    };
  }

  private async invoke<T>(
    methodName: keyof NovaCodaTransport,
    fallbackType: NovaCodaMessageType,
    body: object | Buffer | string,
    expectedType: NovaCodaMessageType,
  ): Promise<T> {
    const direct = this.transport[methodName] as
      | ((body: object | Buffer | string) => Promise<T>)
      | undefined;
    if (typeof direct === 'function') {
      return direct.call(this.transport, body);
    }

    const request = this.transport.request as
      | ((msgType: NovaCodaMessageType, body?: object | Buffer | string) => Promise<NovaCodaFrame>)
      | undefined;
    if (request) {
      const frame = await request.call(this.transport, fallbackType, body);
      if (frame.msgType !== expectedType) {
        throw new Error(`unexpected NovaCoda response type: ${frame.msgType}, expected ${expectedType}`);
      }
      return decodeJsonBody<T>(frame.body);
    }

    throw new Error(`transport does not expose ${String(methodName)} or the generic request surface`);
  }
}

export function createNovaCodaRuntime(options: NovaCodaRuntimeOptions = {}): NovaCodaRuntime {
  return new NovaCodaRuntime(options);
}

export {
  MAGIC,
  NovaCodaClient,
  NovaCodaMessageType,
  SOCKET_PATH,
  type NovaArenaHandle,
  type NovaArenaRequest,
  type NovaCodaClientOptions,
  type NovaCodaFrame,
  type NovaCodaPingResponse,
  type NovaConstitutionalCheckRequest,
  type NovaConstitutionalDecision,
  type NovaFiberReady,
  type NovaFiberRequest,
  type NovaInferRequest,
  type NovaInferResult,
  type NovaPluginLoadRequest,
  type NovaPluginLoadResult,
  type NovaSyscallRequest,
  type NovaSyscallResult,
};
