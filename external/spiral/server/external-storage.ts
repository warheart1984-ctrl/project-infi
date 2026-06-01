import { createCipheriv, pbkdf2Sync, randomBytes, randomUUID } from "crypto";
import { existsSync, readFileSync } from "fs";
import { mkdir, readdir, readFile, stat, unlink, writeFile } from "fs/promises";
import path from "path";
import type {
  ExternalStorageProvider,
  SaveTranscriptMetadata,
  SaveTranscriptRequest,
  SaveTranscriptResponse,
  StorageLink,
  StorageLinkRequest,
  StoragePointer,
  StorageVaultEntry,
  TranscriptType,
  TranscriptOutputFormat,
} from "@shared/schema";
import { signSigilPayload } from "./sigil-signature";

const LINKS_PATH = path.join(process.cwd(), ".local", "storage-links.json");
const POINTERS_PATH = path.join(process.cwd(), ".local", "storage-pointers.json");
const CACHE_DIR = path.join(process.cwd(), ".local", "storage-cache");
const DEFAULT_CACHE_ENABLED = process.env.SPIRAL_STORAGE_CACHE_DEFAULT === "1";
const DEFAULT_CACHE_TTL_MINUTES = Math.max(
  1,
  Number.parseInt(process.env.SPIRAL_STORAGE_CACHE_TTL_MINUTES || "240", 10) || 240,
);
const LEGACY_LOCAL_PRINCIPAL = "legacy:local";
const PBKDF2_ITERATIONS = Math.max(
  100_000,
  Number.parseInt(process.env.SPIRAL_STORAGE_PBKDF2_ITERATIONS || "120000", 10) || 120_000,
);
const ACCESS_TOKEN_REFRESH_SKEW_MS = Math.max(
  0,
  Number.parseInt(process.env.SPIRAL_STORAGE_REFRESH_SKEW_MS || "60000", 10) || 60_000,
);

interface RefreshedAccessToken {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: number;
}

interface StorageLinkSecretRecord {
  id: string;
  principalKey: string;
  provider: ExternalStorageProvider;
  accessToken: string;
  refreshToken?: string;
  folderId?: string;
  endpoint?: string;
  username?: string;
  label?: string;
  expiresAt?: number;
  createdAt: number;
  updatedAt: number;
}

interface StoragePointerRecord {
  id: string;
  principalKey: string;
  type: TranscriptType;
  chatId?: string;
  pointer: StoragePointer;
  outputFormat?: TranscriptOutputFormat;
  sigils?: string[];
  resonanceStack?: string[];
  createdAt: number;
  updatedAt: number;
}

export interface LegacyExternalStoragePreview {
  linkIds: string[];
  pointerIds: string[];
}

export interface LegacyExternalStorageAdoptionResult {
  linksAdopted: number;
  pointersAdopted: number;
}

interface PreparedPayload {
  bytes: Buffer;
  contentType: string;
  encrypted: boolean;
  fileExtension: string;
}

interface UploadInput {
  link: StorageLinkSecretRecord;
  type: TranscriptType;
  chatId?: string;
  bytes: Buffer;
  contentType: string;
  fileExtension: string;
  existingPointer?: Partial<StoragePointer>;
  encrypted: boolean;
}

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function normalizePrincipalKey(value: string | undefined): string {
  const normalized = normalize(value);
  return normalized || LEGACY_LOCAL_PRINCIPAL;
}

function isLegacyPrincipalKey(value: string | undefined): boolean {
  return normalizePrincipalKey(value) === LEGACY_LOCAL_PRINCIPAL;
}

function buildFilename(type: TranscriptType, chatId: string | undefined, extension: string): string {
  const safeType = normalize(type).toLowerCase() || "custom";
  const safeChatId = normalize(chatId).replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 24);
  const safeExtension =
    normalize(extension)
      .replace(/[^a-zA-Z0-9.-]/g, "")
      .replace(/^\.+/, "") || "json";
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const stem = safeChatId ? `spiral-${safeType}-${safeChatId}-${stamp}` : `spiral-${safeType}-${stamp}`;
  return `${stem}.${safeExtension}`;
}

function stringifyContent(content: unknown): string {
  if (typeof content === "string") {
    return content;
  }
  if (content === undefined) {
    return "";
  }
  return JSON.stringify(content, null, 2);
}

function renderFrontmatter(metadata: SaveTranscriptMetadata | undefined): string {
  const entries: Array<[string, string | number]> = [];
  entries.push(["exportedAt", new Date().toISOString()]);

  if (metadata?.sigilTrace) {
    entries.push(["sigilTrace", metadata.sigilTrace]);
  }
  if (Array.isArray(metadata?.presenceMoments) && metadata.presenceMoments.length > 0) {
    entries.push(["presenceMoments", metadata.presenceMoments.join(" | ")]);
  }
  if (metadata?.context?.presenceScore !== undefined) {
    entries.push(["presenceScore", Number(metadata.context.presenceScore.toFixed(3))]);
  }
  if (metadata?.context?.veilDepth !== undefined) {
    entries.push(["veilDepth", Number(metadata.context.veilDepth.toFixed(3))]);
  }
  if (metadata?.context?.traceEchoId) {
    entries.push(["traceEchoId", metadata.context.traceEchoId]);
  }

  const frontmatter = metadata?.frontmatter || {};
  for (const [key, value] of Object.entries(frontmatter)) {
    const safeKey = normalize(key).replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 48);
    const safeValue = normalize(value).slice(0, 200);
    if (!safeKey || !safeValue) continue;
    entries.push([safeKey, safeValue]);
  }

  const lines = entries.map(([key, value]) => {
    if (typeof value === "number") return `${key}: ${value}`;
    const compact = value.replace(/\s+/g, " ").trim();
    if (/^[a-zA-Z0-9_.-]+$/.test(compact)) {
      return `${key}: ${compact}`;
    }
    return `${key}: ${JSON.stringify(compact)}`;
  });

  return `---\n${lines.join("\n")}\n---\n`;
}

function renderMarkdownContent(content: unknown, metadata: SaveTranscriptMetadata | undefined): string {
  const frontmatter = renderFrontmatter(metadata);
  if (typeof content === "string") {
    return `${frontmatter}\n${content}`;
  }

  const maybeMessages =
    content && typeof content === "object" ? (content as { messages?: unknown }).messages : undefined;
  const messages = Array.isArray(maybeMessages) ? maybeMessages : [];

  const lines: string[] = [frontmatter, "", "# Spiral Transcript", ""];
  if (messages.length > 0) {
    lines.push("## Messages", "");
    for (const entry of messages) {
      const role =
        entry && typeof entry === "object" && typeof (entry as { role?: unknown }).role === "string"
          ? (entry as { role: string }).role
          : "entry";
      const body =
        entry && typeof entry === "object" && typeof (entry as { content?: unknown }).content === "string"
          ? (entry as { content: string }).content
          : JSON.stringify(entry, null, 2);
      lines.push(`### ${role}`, "", body, "");
    }
  } else {
    lines.push("## Payload", "");
    lines.push("```json");
    lines.push(stringifyContent(content));
    lines.push("```");
  }

  return lines.join("\n");
}

function buildSigilRichPayload(content: unknown, metadata: SaveTranscriptMetadata | undefined): Record<string, unknown> {
  const traceMarkers = Array.from(
    new Set([
      ...(metadata?.traceMarkers || []),
      ...(metadata?.sigilTrace ? [metadata.sigilTrace] : []),
      ...(metadata?.resonanceStack || []),
    ]),
  ).slice(0, 160);
  const resonanceStack = Array.from(
    new Set([...(metadata?.resonanceStack || []), ...(metadata?.sigilTrace ? [metadata.sigilTrace] : [])]),
  ).slice(0, 80);
  const entryClarity =
    metadata?.entryClarity ??
    (typeof metadata?.context?.presenceScore === "number" ? metadata.context.presenceScore : undefined) ??
    0;
  const veilCost =
    metadata?.veilCost ??
    (typeof metadata?.context?.veilDepth === "number" ? metadata.context.veilDepth : undefined) ??
    0;

  return {
    format: "sigil-json",
    exportedAt: new Date().toISOString(),
    sigilTrace: metadata?.sigilTrace || "sigil:unknown",
    traceMarkers,
    entryClarity: Number(Math.max(0, Math.min(1, entryClarity)).toFixed(3)),
    veilCost: Number(Math.max(0, veilCost).toFixed(3)),
    resonanceStack,
    presenceMoments: metadata?.presenceMoments || [],
    context: metadata?.context || {},
    frontmatter: metadata?.frontmatter || {},
    payload: content,
  };
}

function formatTranscriptContent(
  content: unknown,
  outputFormat: TranscriptOutputFormat,
  metadata: SaveTranscriptMetadata | undefined,
): {
  plainText: string;
  contentType: string;
  fileExtension: string;
} {
  switch (outputFormat) {
    case "markdown":
      return {
        plainText: renderMarkdownContent(content, metadata),
        contentType: "text/markdown; charset=utf-8",
        fileExtension: "md",
      };
    case "spiral-json":
      return {
        plainText: JSON.stringify(
          {
            format: "spiral-json",
            exportedAt: new Date().toISOString(),
            metadata: metadata || {},
            payload: content,
          },
          null,
          2,
        ),
        contentType: "application/json; charset=utf-8",
        fileExtension: "spiral.json",
      };
    case "sigil-json":
      return {
        plainText: JSON.stringify(signSigilPayload(buildSigilRichPayload(content, metadata)), null, 2),
        contentType: "application/json; charset=utf-8",
        fileExtension: "sigil.json",
      };
    case "json":
    default:
      return {
        plainText: stringifyContent(content),
        contentType: "application/json; charset=utf-8",
        fileExtension: "json",
      };
  }
}

function preparePayload(
  content: unknown,
  passphrase: string | undefined,
  outputFormat: TranscriptOutputFormat,
  metadata: SaveTranscriptMetadata | undefined,
): PreparedPayload {
  const formatted = formatTranscriptContent(content, outputFormat, metadata);
  const plainText = formatted.plainText;
  if (!normalize(passphrase)) {
    return {
      bytes: Buffer.from(plainText, "utf8"),
      contentType: formatted.contentType,
      encrypted: false,
      fileExtension: formatted.fileExtension,
    };
  }

  const salt = randomBytes(16);
  const iv = randomBytes(12);
  const key = pbkdf2Sync(passphrase!, salt, PBKDF2_ITERATIONS, 32, "sha256");
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const ciphertext = Buffer.concat([cipher.update(Buffer.from(plainText, "utf8")), cipher.final()]);
  const tag = cipher.getAuthTag();
  const envelope = {
    algorithm: "aes-256-gcm",
    kdf: "pbkdf2-sha256",
    iterations: PBKDF2_ITERATIONS,
    originalContentType: formatted.contentType,
    originalExtension: formatted.fileExtension,
    salt: salt.toString("base64"),
    iv: iv.toString("base64"),
    tag: tag.toString("base64"),
    ciphertext: ciphertext.toString("base64"),
  };
  return {
    bytes: Buffer.from(JSON.stringify(envelope, null, 2), "utf8"),
    contentType: "application/json; charset=utf-8",
    encrypted: true,
    fileExtension: "enc.json",
  };
}

async function readErrorBody(response: globalThis.Response): Promise<string> {
  try {
    const text = await response.text();
    return normalize(text) || `${response.status} ${response.statusText}`;
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

async function parseJsonSafe<T = Record<string, unknown>>(
  response: globalThis.Response,
): Promise<T | undefined> {
  try {
    return (await response.json()) as T;
  } catch {
    return undefined;
  }
}

function providerSupportsRefresh(provider: ExternalStorageProvider): boolean {
  return provider === "google" || provider === "dropbox";
}

function isProviderUnauthorizedError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const message = error.message.toLowerCase();
  return (
    message.includes("401") ||
    message.includes("unauthorized") ||
    message.includes("expired_access_token") ||
    message.includes("invalid credentials")
  );
}

function readRequiredEnv(name: string): string {
  const value = normalize(process.env[name]);
  if (!value) {
    throw new Error(`${name} is required for token refresh.`);
  }
  return value;
}

async function refreshGoogleAccessToken(link: StorageLinkSecretRecord): Promise<RefreshedAccessToken> {
  const refreshToken = normalize(link.refreshToken);
  if (!refreshToken) {
    throw new Error("Google token refresh requires a stored refresh token.");
  }

  const clientId = readRequiredEnv("GOOGLE_DRIVE_OAUTH_CLIENT_ID");
  const clientSecret = readRequiredEnv("GOOGLE_DRIVE_OAUTH_CLIENT_SECRET");
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    refresh_token: refreshToken,
    client_id: clientId,
    client_secret: clientSecret,
  });
  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });
  if (!response.ok) {
    throw new Error(`Google token refresh failed: ${await readErrorBody(response)}`);
  }

  const parsed = (await parseJsonSafe<{
    access_token?: unknown;
    refresh_token?: unknown;
    expires_in?: unknown;
  }>(response)) || {};
  const accessToken = typeof parsed.access_token === "string" ? normalize(parsed.access_token) : "";
  if (!accessToken) {
    throw new Error("Google token refresh failed: missing access_token.");
  }
  const nextRefreshToken =
    typeof parsed.refresh_token === "string" ? normalize(parsed.refresh_token) : undefined;
  const expiresAt =
    typeof parsed.expires_in === "number" && Number.isFinite(parsed.expires_in)
      ? Date.now() + Math.max(1, parsed.expires_in) * 1000
      : undefined;

  return {
    accessToken,
    ...(nextRefreshToken ? { refreshToken: nextRefreshToken } : {}),
    ...(expiresAt ? { expiresAt } : {}),
  };
}

async function refreshDropboxAccessToken(link: StorageLinkSecretRecord): Promise<RefreshedAccessToken> {
  const refreshToken = normalize(link.refreshToken);
  if (!refreshToken) {
    throw new Error("Dropbox token refresh requires a stored refresh token.");
  }

  const clientId = readRequiredEnv("DROPBOX_OAUTH_CLIENT_ID");
  const clientSecret = readRequiredEnv("DROPBOX_OAUTH_CLIENT_SECRET");
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    refresh_token: refreshToken,
    client_id: clientId,
    client_secret: clientSecret,
  });
  const response = await fetch("https://api.dropboxapi.com/oauth2/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });
  if (!response.ok) {
    throw new Error(`Dropbox token refresh failed: ${await readErrorBody(response)}`);
  }

  const parsed = (await parseJsonSafe<{
    access_token?: unknown;
    refresh_token?: unknown;
    expires_in?: unknown;
  }>(response)) || {};
  const accessToken = typeof parsed.access_token === "string" ? normalize(parsed.access_token) : "";
  if (!accessToken) {
    throw new Error("Dropbox token refresh failed: missing access_token.");
  }
  const nextRefreshToken =
    typeof parsed.refresh_token === "string" ? normalize(parsed.refresh_token) : undefined;
  const expiresAt =
    typeof parsed.expires_in === "number" && Number.isFinite(parsed.expires_in)
      ? Date.now() + Math.max(1, parsed.expires_in) * 1000
      : undefined;

  return {
    accessToken,
    ...(nextRefreshToken ? { refreshToken: nextRefreshToken } : {}),
    ...(expiresAt ? { expiresAt } : {}),
  };
}

function normalizeDropboxFolderPath(folderId: string | undefined): string {
  const raw = normalize(folderId);
  if (!raw) return "";
  const prefixed = raw.startsWith("/") ? raw : `/${raw}`;
  return prefixed.replace(/\/+$/, "");
}

function joinDropboxPath(folder: string, filename: string): string {
  if (!folder) return `/${filename}`;
  return `${folder}/${filename}`.replace(/\/+/g, "/");
}

function normalizeWebdavEndpoint(endpoint: string | undefined): string {
  return normalize(endpoint).replace(/\/+$/, "");
}

function normalizeWebdavFolderPath(folderId: string | undefined): string {
  const raw = normalize(folderId);
  if (!raw) return "";
  const prefixed = raw.startsWith("/") ? raw : `/${raw}`;
  return prefixed.replace(/\/+$/, "");
}

function joinWebdavPath(folderPath: string, filename: string): string {
  if (!folderPath) return `/${filename}`;
  return `${folderPath}/${filename}`.replace(/\/+/g, "/");
}

function buildWebdavUrl(endpoint: string, absolutePath: string): string {
  const sanitizedEndpoint = normalizeWebdavEndpoint(endpoint);
  if (!sanitizedEndpoint) {
    throw new Error("WebDAV endpoint is required.");
  }
  const encodedPath = absolutePath
    .split("/")
    .filter(Boolean)
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  return `${sanitizedEndpoint}/${encodedPath}`;
}

function buildWebdavAuthHeader(link: StorageLinkSecretRecord): string {
  const token = normalize(link.accessToken);
  if (!token) {
    throw new Error("WebDAV requires an access token or password.");
  }
  const username = normalize(link.username);
  if (username) {
    const credentials = Buffer.from(`${username}:${token}`, "utf8").toString("base64");
    return `Basic ${credentials}`;
  }
  return `Bearer ${token}`;
}

async function ensureWebdavCollection(endpoint: string, authHeader: string, folderPath: string): Promise<void> {
  const segments = folderPath.split("/").filter(Boolean);
  if (segments.length === 0) return;

  let current = "";
  for (const segment of segments) {
    current += `/${segment}`;
    const url = buildWebdavUrl(endpoint, current);
    const response = await fetch(url, {
      method: "MKCOL",
      headers: {
        Authorization: authHeader,
      },
    });
    if (response.ok || response.status === 405 || response.status === 409) {
      continue;
    }
    throw new Error(`WebDAV MKCOL failed (${response.status}): ${await readErrorBody(response)}`);
  }
}

function extractIpfsCid(payload: Record<string, unknown> | undefined): string {
  if (!payload) return "";
  const candidates: unknown[] = [
    payload.IpfsHash,
    payload.Hash,
    payload.cid,
    (payload.value as { cid?: unknown } | undefined)?.cid,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === "string" && normalize(candidate)) {
      return normalize(candidate);
    }
  }
  return "";
}

function normalizeSigilToken(value: string | undefined): string {
  return normalize(value).toLowerCase().replace(/[^a-z0-9-]/g, "").slice(0, 96);
}

function collectPointerSigils(input: SaveTranscriptRequest): string[] {
  const sigils = new Set<string>();
  const add = (token: string | undefined) => {
    const normalized = normalizeSigilToken(token);
    if (normalized) sigils.add(normalized);
  };

  add(input.metadata?.sigilTrace);
  add(input.sigilFilter?.sigil);
  for (const token of input.metadata?.traceMarkers || []) {
    add(token);
  }
  for (const token of input.metadata?.resonanceStack || []) {
    add(token);
  }

  return Array.from(sigils).slice(0, 96);
}

function collectPointerResonance(input: SaveTranscriptRequest): string[] {
  const resonance = new Set<string>();
  const add = (token: string | undefined) => {
    const normalized = normalize(token).toLowerCase().slice(0, 120);
    if (normalized) resonance.add(normalized);
  };

  for (const token of input.metadata?.resonanceStack || []) {
    add(token);
  }
  for (const token of input.metadata?.traceMarkers || []) {
    add(token);
  }
  add(input.metadata?.sigilTrace);
  add(input.sigilFilter?.sigil);

  return Array.from(resonance).slice(0, 120);
}

async function uploadToGoogleDrive(input: UploadInput): Promise<StoragePointer> {
  const token = input.link.accessToken;
  const folderId = normalize(input.existingPointer?.folderId || input.link.folderId) || undefined;
  const filename =
    normalize(input.existingPointer?.filename) ||
    buildFilename(input.type, input.chatId, input.fileExtension);
  const now = Date.now();
  const existingFileId = normalize(input.existingPointer?.fileId);

  if (existingFileId) {
    const response = await fetch(
      `https://www.googleapis.com/upload/drive/v3/files/${encodeURIComponent(existingFileId)}?uploadType=media`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": input.contentType,
        },
        body: input.bytes,
      },
    );
    if (!response.ok) {
      throw new Error(`Google Drive update failed: ${await readErrorBody(response)}`);
    }

    return {
      provider: "google",
      fileId: existingFileId,
      folderId,
      filename,
      contentType: input.contentType,
      bytes: input.bytes.length,
      savedAt: now,
    };
  }

  const boundary = `spiral-${randomUUID()}`;
  const metadata = {
    name: filename,
    ...(folderId ? { parents: [folderId] } : {}),
  };
  const metadataPart = Buffer.from(
    `--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(metadata)}\r\n`,
    "utf8",
  );
  const contentPartHeader = Buffer.from(
    `--${boundary}\r\nContent-Type: ${input.contentType}\r\n\r\n`,
    "utf8",
  );
  const closing = Buffer.from(`\r\n--${boundary}--`, "utf8");
  const body = Buffer.concat([metadataPart, contentPartHeader, input.bytes, closing]);

  const response = await fetch(
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,parents",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": `multipart/related; boundary=${boundary}`,
      },
      body,
    },
  );
  if (!response.ok) {
    throw new Error(`Google Drive upload failed: ${await readErrorBody(response)}`);
  }

  const parsed = await parseJsonSafe<{ id?: string; name?: string }>(response);
  const fileId = normalize(parsed?.id);
  if (!fileId) {
    throw new Error("Google Drive upload failed: missing file id in response.");
  }

  return {
    provider: "google",
    fileId,
    folderId,
    filename: normalize(parsed?.name) || filename,
    contentType: input.contentType,
    bytes: input.bytes.length,
    savedAt: now,
  };
}

async function uploadToDropbox(input: UploadInput): Promise<StoragePointer> {
  const token = input.link.accessToken;
  const folderPath = normalizeDropboxFolderPath(input.existingPointer?.folderId || input.link.folderId);
  const filename =
    normalize(input.existingPointer?.filename) ||
    buildFilename(input.type, input.chatId, input.fileExtension);
  const existingPath = normalize(input.existingPointer?.path);
  const targetPath = existingPath || joinDropboxPath(folderPath, filename);
  const mode = existingPath ? "overwrite" : "add";
  const now = Date.now();

  const response = await fetch("https://content.dropboxapi.com/2/files/upload", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/octet-stream",
      "Dropbox-API-Arg": JSON.stringify({
        path: targetPath,
        mode,
        autorename: !existingPath,
        mute: true,
      }),
    },
    body: input.bytes,
  });
  if (!response.ok) {
    throw new Error(`Dropbox upload failed: ${await readErrorBody(response)}`);
  }

  const parsed = await parseJsonSafe<{ id?: string; path_lower?: string; path_display?: string }>(
    response,
  );
  const resolvedPath = normalize(parsed?.path_lower || parsed?.path_display || targetPath);

  return {
    provider: "dropbox",
    fileId: normalize(parsed?.id) || undefined,
    path: resolvedPath || targetPath,
    folderId: folderPath || undefined,
    filename,
    contentType: input.contentType,
    bytes: input.bytes.length,
    savedAt: now,
  };
}

async function uploadToWebdav(input: UploadInput): Promise<StoragePointer> {
  const endpoint = normalizeWebdavEndpoint(input.link.endpoint);
  if (!endpoint) {
    throw new Error("WebDAV upload requires a configured endpoint.");
  }

  const authHeader = buildWebdavAuthHeader(input.link);
  const folderPath = normalizeWebdavFolderPath(input.existingPointer?.folderId || input.link.folderId);
  const filename =
    normalize(input.existingPointer?.filename) ||
    buildFilename(input.type, input.chatId, input.fileExtension);
  const existingPath = normalize(input.existingPointer?.path);
  const targetPath = existingPath || joinWebdavPath(folderPath, filename);
  const targetUrl = buildWebdavUrl(endpoint, targetPath);
  const now = Date.now();

  if (!existingPath && folderPath) {
    await ensureWebdavCollection(endpoint, authHeader, folderPath);
  }

  const response = await fetch(targetUrl, {
    method: "PUT",
    headers: {
      Authorization: authHeader,
      "Content-Type": input.contentType,
    },
    body: input.bytes,
  });
  if (!response.ok) {
    throw new Error(`WebDAV upload failed: ${await readErrorBody(response)}`);
  }

  return {
    provider: "webdav",
    path: targetPath,
    folderId: folderPath || undefined,
    filename,
    contentType: input.contentType,
    bytes: input.bytes.length,
    savedAt: now,
  };
}

async function uploadToIpfs(input: UploadInput): Promise<StoragePointer> {
  const endpoint = normalize(input.link.endpoint) || normalize(process.env.IPFS_API_ENDPOINT);
  if (!endpoint) {
    throw new Error("IPFS upload requires a configured endpoint.");
  }

  const filename =
    normalize(input.existingPointer?.filename) ||
    buildFilename(input.type, input.chatId, input.fileExtension);
  const token = normalize(input.link.accessToken);
  const formData = new FormData();
  formData.append("file", new Blob([input.bytes], { type: input.contentType }), filename);

  const response = await fetch(endpoint, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`IPFS upload failed: ${await readErrorBody(response)}`);
  }

  const parsed = await parseJsonSafe<Record<string, unknown>>(response);
  const cid = extractIpfsCid(parsed);
  if (!cid) {
    throw new Error("IPFS upload failed: CID not returned by provider.");
  }

  return {
    provider: "ipfs",
    fileId: cid,
    path: `ipfs://${cid}`,
    filename,
    contentType: input.contentType,
    bytes: input.bytes.length,
    savedAt: Date.now(),
  };
}

async function uploadToProvider(input: UploadInput): Promise<StoragePointer> {
  switch (input.link.provider) {
    case "google":
      return uploadToGoogleDrive(input);
    case "dropbox":
      return uploadToDropbox(input);
    case "webdav":
      return uploadToWebdav(input);
    case "ipfs":
      return uploadToIpfs(input);
    case "proton":
      throw new Error(
        "Proton Drive upload is not implemented in this build. Link is stored; provider adapter pending.",
      );
    default:
      throw new Error(`Unsupported external storage provider: ${input.link.provider}`);
  }
}

export class ExternalStorageService {
  private links = new Map<string, StorageLinkSecretRecord>();
  private pointers = new Map<string, StoragePointerRecord>();

  constructor() {
    this.loadLinks();
    this.loadPointers();
  }

  private loadLinks(): void {
    try {
      if (!existsSync(LINKS_PATH)) return;
      const raw = readFileSync(LINKS_PATH, "utf8");
      const parsed = JSON.parse(raw) as { links?: StorageLinkSecretRecord[] };
      const records = Array.isArray(parsed?.links) ? parsed.links : [];
      for (const record of records) {
        if (!record || typeof record !== "object") continue;
        if (!normalize(record.id) || !normalize(record.accessToken)) {
          continue;
        }
        this.links.set(record.id, {
          ...record,
          principalKey: normalizePrincipalKey(record.principalKey),
          provider: record.provider,
        });
      }
    } catch (error) {
      console.error("Failed to load external storage links:", error);
    }
  }

  private loadPointers(): void {
    try {
      if (!existsSync(POINTERS_PATH)) return;
      const raw = readFileSync(POINTERS_PATH, "utf8");
      const parsed = JSON.parse(raw) as { pointers?: StoragePointerRecord[] };
      const records = Array.isArray(parsed?.pointers) ? parsed.pointers : [];
      for (const record of records) {
        if (!record || typeof record !== "object") continue;
        if (!normalize(record.id)) continue;
        if (!record.pointer || typeof record.pointer !== "object") continue;
        this.pointers.set(record.id, {
          ...record,
          principalKey: normalizePrincipalKey(record.principalKey),
        });
      }
    } catch (error) {
      console.error("Failed to load external storage pointers:", error);
    }
  }

  private async persistLinks(): Promise<void> {
    await mkdir(path.dirname(LINKS_PATH), { recursive: true });
    await writeFile(
      LINKS_PATH,
      JSON.stringify({ links: Array.from(this.links.values()) }, null, 2),
      "utf8",
    );
  }

  private async persistPointers(): Promise<void> {
    await mkdir(path.dirname(POINTERS_PATH), { recursive: true });
    await writeFile(
      POINTERS_PATH,
      JSON.stringify({ pointers: Array.from(this.pointers.values()) }, null, 2),
      "utf8",
    );
  }

  private sanitizeLink(record: StorageLinkSecretRecord): StorageLink {
    return {
      id: record.id,
      provider: record.provider,
      folderId: normalize(record.folderId) || undefined,
      endpoint: normalize(record.endpoint) || undefined,
      username: normalize(record.username) || undefined,
      label: normalize(record.label) || undefined,
      expiresAt:
        typeof record.expiresAt === "number" && Number.isFinite(record.expiresAt)
          ? record.expiresAt
          : undefined,
      createdAt: record.createdAt,
      updatedAt: record.updatedAt,
      connected: true,
    };
  }

  private selectLink(
    principalKey: string,
    provider: ExternalStorageProvider | undefined,
  ): StorageLinkSecretRecord | undefined {
    const candidates = Array.from(this.links.values())
      .filter((record) => record.principalKey === principalKey)
      .sort((a, b) => b.updatedAt - a.updatedAt);
    if (candidates.length === 0) return undefined;
    if (!provider) return candidates[0];
    return candidates.find((record) => record.provider === provider);
  }

  private linkShouldRefresh(record: StorageLinkSecretRecord): boolean {
    if (!providerSupportsRefresh(record.provider)) return false;
    if (!normalize(record.refreshToken)) return false;
    if (typeof record.expiresAt !== "number" || !Number.isFinite(record.expiresAt)) return false;
    return record.expiresAt <= Date.now() + ACCESS_TOKEN_REFRESH_SKEW_MS;
  }

  private async refreshLinkToken(record: StorageLinkSecretRecord): Promise<StorageLinkSecretRecord> {
    if (!providerSupportsRefresh(record.provider)) {
      throw new Error(`Token refresh is not supported for provider "${record.provider}".`);
    }
    if (!normalize(record.refreshToken)) {
      throw new Error(`No refresh token is available for provider "${record.provider}".`);
    }

    let refreshed: RefreshedAccessToken;
    switch (record.provider) {
      case "google":
        refreshed = await refreshGoogleAccessToken(record);
        break;
      case "dropbox":
        refreshed = await refreshDropboxAccessToken(record);
        break;
      default:
        throw new Error(`Token refresh is not supported for provider "${record.provider}".`);
    }

    const next: StorageLinkSecretRecord = {
      ...record,
      accessToken: refreshed.accessToken,
      refreshToken: normalize(refreshed.refreshToken) || record.refreshToken,
      expiresAt: typeof refreshed.expiresAt === "number" ? refreshed.expiresAt : record.expiresAt,
      updatedAt: Date.now(),
    };
    this.links.set(next.id, next);
    await this.persistLinks();
    return next;
  }

  private async purgeCache(defaultTtlMinutes = DEFAULT_CACHE_TTL_MINUTES): Promise<void> {
    await mkdir(CACHE_DIR, { recursive: true });
    const files = await readdir(CACHE_DIR);
    const now = Date.now();
    const fallbackTtlMs = Math.max(1, defaultTtlMinutes) * 60 * 1000;

    await Promise.all(
      files.map(async (file) => {
        const filePath = path.join(CACHE_DIR, file);
        try {
          const content = await readFile(filePath, "utf8");
          const parsed = JSON.parse(content) as { expiresAt?: unknown };
          const explicitExpiresAt =
            typeof parsed.expiresAt === "number" && Number.isFinite(parsed.expiresAt)
              ? parsed.expiresAt
              : undefined;
          if (explicitExpiresAt && explicitExpiresAt <= now) {
            await unlink(filePath);
            return;
          }

          if (!explicitExpiresAt) {
            const fileStat = await stat(filePath);
            if (fileStat.mtimeMs + fallbackTtlMs <= now) {
              await unlink(filePath);
            }
          }
        } catch {
          try {
            await unlink(filePath);
          } catch {
            // ignore
          }
        }
      }),
    );
  }

  private async maybeCachePayload(args: {
    principalKey: string;
    pointer: StoragePointer;
    bytes: Buffer;
    contentType: string;
    cache?: SaveTranscriptRequest["cache"];
  }): Promise<string | undefined> {
    const enabled = args.cache?.enabled ?? DEFAULT_CACHE_ENABLED;
    const ttlMinutes = args.cache?.ttlMinutes ?? DEFAULT_CACHE_TTL_MINUTES;
    await this.purgeCache(ttlMinutes);

    if (!enabled) return undefined;

    await mkdir(CACHE_DIR, { recursive: true });
    const key = randomUUID();
    const createdAt = Date.now();
    const expiresAt = createdAt + ttlMinutes * 60 * 1000;
    const payload = {
      key,
      principalKey: args.principalKey,
      pointer: args.pointer,
      contentType: args.contentType,
      bytesBase64: args.bytes.toString("base64"),
      createdAt,
      expiresAt,
    };

    await writeFile(path.join(CACHE_DIR, `${key}.json`), JSON.stringify(payload, null, 2), "utf8");
    return key;
  }

  listLinks(principalKey: string): StorageLink[] {
    return Array.from(this.links.values())
      .filter((record) => record.principalKey === principalKey)
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .map((record) => this.sanitizeLink(record));
  }

  listLegacyRecords(): LegacyExternalStoragePreview {
    const linkIds = Array.from(this.links.values())
      .filter((record) => isLegacyPrincipalKey(record.principalKey))
      .map((record) => record.id);
    const pointerIds = Array.from(this.pointers.values())
      .filter((record) => isLegacyPrincipalKey(record.principalKey))
      .map((record) => record.id);
    return { linkIds, pointerIds };
  }

  async adoptLegacyRecords(principalKey: string): Promise<LegacyExternalStorageAdoptionResult> {
    const targetPrincipalKey = normalize(principalKey);
    if (!targetPrincipalKey || isLegacyPrincipalKey(targetPrincipalKey)) {
      return { linksAdopted: 0, pointersAdopted: 0 };
    }

    const now = Date.now();
    let linksAdopted = 0;
    for (const record of Array.from(this.links.values())) {
      if (!isLegacyPrincipalKey(record.principalKey)) continue;
      this.links.set(record.id, {
        ...record,
        principalKey: targetPrincipalKey,
        updatedAt: now,
      });
      linksAdopted += 1;
    }
    if (linksAdopted > 0) {
      await this.persistLinks();
    }

    let pointersAdopted = 0;
    for (const record of Array.from(this.pointers.values())) {
      if (!isLegacyPrincipalKey(record.principalKey)) continue;
      this.pointers.set(record.id, {
        ...record,
        principalKey: targetPrincipalKey,
        updatedAt: now,
      });
      pointersAdopted += 1;
    }
    if (pointersAdopted > 0) {
      await this.persistPointers();
    }

    return { linksAdopted, pointersAdopted };
  }

  async upsertLink(principalKey: string, input: StorageLinkRequest): Promise<StorageLink> {
    const now = Date.now();
    const existing = this.selectLink(principalKey, input.provider);
    const nextRefreshToken = normalize(input.refreshToken) || existing?.refreshToken;
    const nextFolderId =
      input.folderId !== undefined ? normalize(input.folderId) || undefined : existing?.folderId;
    const nextEndpoint =
      input.endpoint !== undefined ? normalize(input.endpoint) || undefined : existing?.endpoint;
    const nextUsername =
      input.username !== undefined ? normalize(input.username) || undefined : existing?.username;
    const nextLabel =
      input.label !== undefined ? normalize(input.label) || undefined : existing?.label;
    const nextExpiresAt =
      typeof input.expiresAt === "number" ? input.expiresAt : existing?.expiresAt;
    const next: StorageLinkSecretRecord = {
      id: existing?.id || randomUUID(),
      principalKey,
      provider: input.provider,
      accessToken: normalize(input.accessToken),
      refreshToken: nextRefreshToken,
      folderId: nextFolderId,
      endpoint: nextEndpoint,
      username: nextUsername,
      label: nextLabel,
      expiresAt: nextExpiresAt,
      createdAt: existing?.createdAt || now,
      updatedAt: now,
    };

    this.links.set(next.id, next);
    await this.persistLinks();
    return this.sanitizeLink(next);
  }

  async deleteLink(principalKey: string, linkId: string): Promise<boolean> {
    const record = this.links.get(linkId);
    if (!record || record.principalKey !== principalKey) return false;
    const deleted = this.links.delete(linkId);
    if (!deleted) return false;
    await this.persistLinks();
    return true;
  }

  listPointers(principalKey: string, options: { chatId?: string; type?: TranscriptType } = {}): StoragePointer[] {
    const filtered = Array.from(this.pointers.values())
      .filter((record) => record.principalKey === principalKey)
      .filter((record) => (options.chatId ? record.chatId === options.chatId : true))
      .filter((record) => (options.type ? record.type === options.type : true))
      .sort((a, b) => b.updatedAt - a.updatedAt);
    return filtered.map((record) => record.pointer);
  }

  listVault(
    principalKey: string,
    options: { sigil?: string; provider?: ExternalStorageProvider; limit?: number } = {},
  ): StorageVaultEntry[] {
    const normalizedSigil = normalizeSigilToken(options.sigil);
    const limit = Math.max(1, Math.min(options.limit || 200, 500));

    const records = Array.from(this.pointers.values())
      .filter((record) => record.principalKey === principalKey)
      .filter((record) => (options.provider ? record.pointer.provider === options.provider : true))
      .filter((record) =>
        normalizedSigil
          ? (record.sigils || []).some((sigil) => normalizeSigilToken(sigil) === normalizedSigil)
          : true,
      )
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, limit);

    return records.map((record) => ({
      id: record.id,
      type: record.type,
      ...(record.chatId ? { chatId: record.chatId } : {}),
      provider: record.pointer.provider,
      pointer: record.pointer,
      ...(record.outputFormat ? { outputFormat: record.outputFormat } : {}),
      ...(record.sigils && record.sigils.length > 0 ? { sigils: record.sigils } : {}),
      ...(record.resonanceStack && record.resonanceStack.length > 0
        ? { resonanceStack: record.resonanceStack }
        : {}),
      savedAt: record.pointer.savedAt,
      createdAt: record.createdAt,
      updatedAt: record.updatedAt,
    }));
  }

  async saveTranscript(
    principalKey: string,
    input: SaveTranscriptRequest & { content: unknown },
  ): Promise<SaveTranscriptResponse> {
    const provider = input.provider || input.storagePointer?.provider;
    const initialLink = this.selectLink(principalKey, provider);
    if (!initialLink) {
      throw new Error("No linked external storage provider found for this request.");
    }
    let link = initialLink;
    if (this.linkShouldRefresh(link)) {
      link = await this.refreshLinkToken(link);
    }

    const payload = preparePayload(
      input.content,
      normalize(input.passphrase) || undefined,
      input.outputFormat || "json",
      input.metadata,
    );
    let uploadedPointer: StoragePointer;
    try {
      uploadedPointer = await uploadToProvider({
        link,
        type: input.type,
        chatId: input.chatId,
        bytes: payload.bytes,
        contentType: payload.contentType,
        fileExtension: payload.fileExtension,
        existingPointer: input.storagePointer,
        encrypted: payload.encrypted,
      });
    } catch (error) {
      if (!isProviderUnauthorizedError(error) || !providerSupportsRefresh(link.provider) || !normalize(link.refreshToken)) {
        throw error;
      }
      const refreshedLink = await this.refreshLinkToken(link);
      uploadedPointer = await uploadToProvider({
        link: refreshedLink,
        type: input.type,
        chatId: input.chatId,
        bytes: payload.bytes,
        contentType: payload.contentType,
        fileExtension: payload.fileExtension,
        existingPointer: input.storagePointer,
        encrypted: payload.encrypted,
      });
      link = refreshedLink;
    }
    const pointer = {
      ...uploadedPointer,
      filename:
        uploadedPointer.filename ||
        buildFilename(input.type, input.chatId, payload.fileExtension),
      folderId: uploadedPointer.folderId || link.folderId || undefined,
      savedAt: Date.now(),
    } satisfies StoragePointer;

    const now = Date.now();
    const pointerSigils = collectPointerSigils(input);
    const pointerResonance = collectPointerResonance(input);
    const pointerRecord: StoragePointerRecord = {
      id: randomUUID(),
      principalKey,
      type: input.type,
      chatId: input.chatId,
      pointer,
      outputFormat: input.outputFormat || "json",
      ...(pointerSigils.length > 0 ? { sigils: pointerSigils } : {}),
      ...(pointerResonance.length > 0 ? { resonanceStack: pointerResonance } : {}),
      createdAt: now,
      updatedAt: now,
    };
    this.pointers.set(pointerRecord.id, pointerRecord);
    await this.persistPointers();

    const cacheKey = await this.maybeCachePayload({
      principalKey,
      pointer,
      bytes: payload.bytes,
      contentType: payload.contentType,
      cache: input.cache,
    });

    return {
      pointer,
      cached: Boolean(cacheKey),
      ...(cacheKey ? { cacheKey } : {}),
    };
  }
}

export const externalStorage = new ExternalStorageService();
