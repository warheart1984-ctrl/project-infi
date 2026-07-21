import * as net from 'node:net';

import CRC32 from 'crc-32';

export const MAGIC = Buffer.from([0xc0, 0xda]);
export const SOCKET_PATH = '/tmp/nova.sock';
export const PROTOCOL_VERSION = 1;

export enum NovaCodaMessageType {
  Ping = 0x01,
  Pong = 0x02,
  AllocArena = 0x10,
  ArenaHandle = 0x11,
  SpawnFiber = 0x20,
  FiberReady = 0x21,
  InferRequest = 0x30,
  InferToken = 0x31,
  InferDone = 0x32,
  SyscallRequest = 0x40,
  SyscallResult = 0x41,
  PluginLoad = 0x50,
  ConstitutionalCheck = 0x60,
  CenDecision = 0x61,
  IveResult = 0x62,
}

export interface NovaCodaFrame {
  version: number;
  msgType: NovaCodaMessageType;
  body: Buffer;
}

export type NovaCodaResponse = NovaCodaFrame;

export interface NovaCodaPingResponse {
  ok: boolean;
  message: string;
  protocol: string;
  arenaCapacity: number;
}

export type NovaPong = NovaCodaPingResponse;

export interface NovaArenaRequest {
  capacity: number;
  label?: string;
}

export interface NovaArenaHandle {
  protocol: string;
  arenaId: string;
  requestedCapacity: number;
  grantedCapacity: number;
  remainingCapacity: number;
  label?: string;
}

export interface NovaFiberRequest {
  entryPoint: string;
  label?: string;
}

export interface NovaFiberReady {
  protocol: string;
  fiberId: string;
  entryPoint: string;
  ready: boolean;
  scheduledAt: string;
  label?: string;
}

export interface NovaInferRequest {
  prompt: string;
  maxTokens?: number;
  mode?: string;
}

export interface NovaInferResult {
  protocol: string;
  inferenceId: string;
  prompt: string;
  completion: string;
  tokens: string[];
  done: boolean;
  mode?: string;
}

export interface NovaSyscallRequest {
  syscall: string;
  args?: Record<string, unknown>;
}

export interface NovaSyscallResult {
  protocol: string;
  syscall: string;
  status: 'ok' | 'error';
  result: unknown;
}

export interface NovaConstitutionalCheckRequest {
  intentId: string;
  authority: string;
  evidence: string[];
}

export interface NovaConstitutionalDecision {
  protocol: string;
  intentId: string;
  decision: 'allow' | 'deny';
  reason: string;
}

export interface NovaPluginLoadRequest {
  plugin: string;
}

export interface NovaPluginLoadResult {
  protocol: string;
  plugin: string;
  loaded: boolean;
}

export interface NovaCodaClientOptions {
  socketPath?: string;
}

type RequestBody = Buffer | string | object | undefined;

type PendingRead = {
  length: number;
  resolve: (value: Buffer) => void;
  reject: (reason: Error) => void;
};

export class NovaCodaClient {
  private client: net.Socket | undefined;
  private incoming = Buffer.alloc(0);
  private readonly pendingReads: PendingRead[] = [];
  private readonly socketPath: string;
  private serial = Promise.resolve();

  constructor(options: NovaCodaClientOptions = {}) {
    this.socketPath = options.socketPath ?? SOCKET_PATH;
  }

  connect(): Promise<void> {
    if (this.client && !this.client.destroyed) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      const socket = net.createConnection(this.socketPath);
      this.client = socket;

      const fail = (error: Error) => {
        this.failPending(error);
        if (!socket.destroyed) {
          socket.destroy();
        }
        reject(error);
      };

      const settle = () => {
        socket.off('error', fail);
        socket.on('error', (error) => this.failPending(error));
        socket.on('data', (chunk) => this.consume(chunk));
        socket.on('close', () => this.failPending(new Error('NovaCoda socket closed')));
        resolve();
      };

      socket.once('connect', settle);
      socket.once('error', fail);
    });
  }

  ping(): Promise<NovaCodaPingResponse> {
    return this.requestAndDecode<NovaCodaPingResponse>(NovaCodaMessageType.Ping, undefined, NovaCodaMessageType.Pong);
  }

  allocateArena(request: NovaArenaRequest): Promise<NovaArenaHandle> {
    return this.requestAndDecode<NovaArenaHandle>(
      NovaCodaMessageType.AllocArena,
      request,
      NovaCodaMessageType.ArenaHandle,
    );
  }

  spawnFiber(request: NovaFiberRequest): Promise<NovaFiberReady> {
    return this.requestAndDecode<NovaFiberReady>(
      NovaCodaMessageType.SpawnFiber,
      request,
      NovaCodaMessageType.FiberReady,
    );
  }

  infer(request: NovaInferRequest): Promise<NovaInferResult> {
    return this.requestAndDecode<NovaInferResult>(
      NovaCodaMessageType.InferRequest,
      request,
      NovaCodaMessageType.InferDone,
    );
  }

  syscall(request: NovaSyscallRequest): Promise<NovaSyscallResult> {
    return this.requestAndDecode<NovaSyscallResult>(
      NovaCodaMessageType.SyscallRequest,
      request,
      NovaCodaMessageType.SyscallResult,
    );
  }

  constitutionalCheck(request: NovaConstitutionalCheckRequest): Promise<NovaConstitutionalDecision> {
    return this.requestAndDecode<NovaConstitutionalDecision>(
      NovaCodaMessageType.ConstitutionalCheck,
      request,
      NovaCodaMessageType.CenDecision,
    );
  }

  loadPlugin(request: NovaPluginLoadRequest): Promise<NovaPluginLoadResult> {
    return this.requestAndDecode<NovaPluginLoadResult>(
      NovaCodaMessageType.PluginLoad,
      request,
      NovaCodaMessageType.PluginLoad,
    );
  }

  request(msgType: NovaCodaMessageType, body: RequestBody = undefined): Promise<NovaCodaFrame> {
    const operation = this.serial.then(() => this.sendFrame(msgType, body));
    this.serial = operation.then(
      () => undefined,
      () => undefined,
    );
    return operation;
  }

  disconnect(): void {
    this.failPending(new Error('NovaCoda socket disconnected'));
    this.incoming = Buffer.alloc(0);
    this.client?.destroy();
    this.client = undefined;
    this.serial = Promise.resolve();
  }

  private async requestAndDecode<T>(msgType: NovaCodaMessageType, body: RequestBody, expectedType: NovaCodaMessageType): Promise<T> {
    const frame = await this.request(msgType, body);
    if (frame.msgType !== expectedType) {
      throw new Error(`unexpected response type: ${frame.msgType}, expected ${expectedType}`);
    }
    return decodeJsonBody<T>(frame.body);
  }

  private async sendFrame(msgType: NovaCodaMessageType, body: RequestBody): Promise<NovaCodaFrame> {
    await this.ensureConnected();
    const socket = this.requireSocket();
    const payload = encodeBody(body);
    const header = encodeHeader(msgType, payload);

    await writeSocket(socket, Buffer.concat([header, payload]));
    return this.readFrame();
  }

  private async readFrame(): Promise<NovaCodaFrame> {
    const header = await this.readExact(12);
    const decoded = decodeHeader(header);
    const body = await this.readExact(decoded.bodyLength);
    const actualCrc = CRC32.buf(body) >>> 0;
    if (actualCrc !== decoded.crc32) {
      throw new Error('invalid NovaCoda frame checksum');
    }

    return {
      version: decoded.version,
      msgType: decoded.msgType,
      body,
    };
  }

  private readExact(length: number): Promise<Buffer> {
    if (length === 0) {
      return Promise.resolve(Buffer.alloc(0));
    }

    if (this.incoming.length >= length) {
      const chunk = this.incoming.subarray(0, length);
      this.incoming = this.incoming.subarray(length);
      return Promise.resolve(Buffer.from(chunk));
    }

    return new Promise((resolve, reject) => {
      this.pendingReads.push({ length, resolve, reject });
      this.flushReads();
    });
  }

  private consume(chunk: Buffer): void {
    this.incoming = this.incoming.length === 0 ? Buffer.from(chunk) : Buffer.concat([this.incoming, chunk]);
    this.flushReads();
  }

  private flushReads(): void {
    while (this.pendingReads.length > 0) {
      const pending = this.pendingReads[0];
      if (!pending || this.incoming.length < pending.length) {
        return;
      }

      this.pendingReads.shift();
      const chunk = this.incoming.subarray(0, pending.length);
      this.incoming = this.incoming.subarray(pending.length);
      pending.resolve(Buffer.from(chunk));
    }
  }

  private failPending(error: Error): void {
    while (this.pendingReads.length > 0) {
      const pending = this.pendingReads.shift();
      pending?.reject(error);
    }
  }

  private async ensureConnected(): Promise<void> {
    if (!this.client || this.client.destroyed) {
      await this.connect();
    }
  }

  private requireSocket(): net.Socket {
    if (!this.client || this.client.destroyed) {
      throw new Error('NovaCoda client is not connected');
    }
    return this.client;
  }
}

export function encodeHeader(msgType: NovaCodaMessageType, body: Buffer): Buffer {
  const header = Buffer.alloc(12);
  MAGIC.copy(header, 0);
  header[2] = PROTOCOL_VERSION;
  header[3] = msgType;
  header.writeUInt32BE(body.length, 4);
  header.writeUInt32BE(CRC32.buf(body) >>> 0, 8);
  return header;
}

export function decodeHeader(header: Buffer): {
  version: number;
  msgType: NovaCodaMessageType;
  bodyLength: number;
  crc32: number;
} {
  if (header.length !== 12) {
    throw new Error('invalid NovaCoda header length');
  }
  if (header[0] !== MAGIC[0] || header[1] !== MAGIC[1]) {
    throw new Error('invalid NovaCoda magic bytes');
  }
  if (header[2] !== PROTOCOL_VERSION) {
    throw new Error(`unsupported NovaCoda protocol version: ${header[2]}`);
  }

  const msgType = header[3] as NovaCodaMessageType;
  const bodyLength = header.readUInt32BE(4);
  const crc32 = header.readUInt32BE(8);

  return { version: header[2], msgType, bodyLength, crc32 };
}

export function encodeBody(body: RequestBody): Buffer {
  if (body === undefined) {
    return Buffer.alloc(0);
  }
  if (Buffer.isBuffer(body)) {
    return body;
  }
  if (typeof body === 'string') {
    return Buffer.from(body, 'utf8');
  }
  return Buffer.from(stableStringify(body), 'utf8');
}

export function decodeJsonBody<T>(body: Buffer): T {
  if (body.length === 0) {
    return {} as T;
  }
  return JSON.parse(body.toString('utf8')) as T;
}

function writeSocket(socket: net.Socket, payload: Buffer): Promise<void> {
  return new Promise((resolve, reject) => {
    socket.write(payload, (error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });
}

function stableStringify(value: unknown): string {
  return JSON.stringify(stableValue(value));
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => stableValue(entry));
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => [key, stableValue(entry)] as const);
    return Object.fromEntries(entries);
  }
  return value;
}
