export type ReferenceImage =
  | { kind: 'url'; url: string }
  | { kind: 'dataUrl'; dataUrl: string };

export interface ImageGenRequest {
  prompt: string;
  model?: string;
  width?: number;
  height?: number;
  seed?: number;
  nologo?: boolean;
  referenceImage?: ReferenceImage;
}

export interface ImageGenResult {
  provider: string;
  model: string;
  contentType: string;
  bytes: Buffer;
}

export interface ImageProvider {
  readonly name: string;
  readonly requiresApiKey: boolean;
  readonly configured: boolean;
  readonly configHelp?: string;
  listModels(options?: { signal?: AbortSignal }): Promise<string[]>;
  generate(request: ImageGenRequest, options?: { signal?: AbortSignal }): Promise<ImageGenResult>;
}

export interface ProviderEnv {
  [key: string]: string | undefined;
}
