import { existsSync } from "fs";
import { mkdir, readFile, writeFile } from "fs/promises";
import os from "os";
import path from "path";
import type { ProviderType } from "@shared/schema";

export type AuthProfileProvider = ProviderType | "openai-codex";

export interface ApiKeyAuthProfile {
  id: string;
  type: "api_key";
  provider: AuthProfileProvider;
  apiKey: string;
  createdAt: number;
  updatedAt: number;
}

export interface OauthAuthProfile {
  id: string;
  type: "oauth";
  provider: AuthProfileProvider;
  accessToken: string;
  refreshToken?: string;
  expiresAt?: number;
  email?: string;
  createdAt: number;
  updatedAt: number;
}

export type AuthProfile = ApiKeyAuthProfile | OauthAuthProfile;

interface AuthProfilesFile {
  version: 1;
  profiles: AuthProfile[];
}

export interface AuthProfileSummary {
  id: string;
  type: AuthProfile["type"];
  provider: AuthProfileProvider;
  hasRefreshToken: boolean;
  expiresAt?: number;
  email?: string;
  updatedAt: number;
}

export interface ImportCodexAuthProfileInput {
  profileId?: string;
  provider?: AuthProfileProvider;
  codexAuthPath?: string;
  now?: number;
}

export interface ImportCodexAuthProfileResult {
  profileId: string;
  provider: AuthProfileProvider;
  sourcePath: string;
  hasRefreshToken: boolean;
  expiresAt?: number;
  email?: string;
}

const AUTH_PROFILES_VERSION = 1;
const DEFAULT_PROFILE_ID = "codex-oauth-default";
const DEFAULT_AUTH_PROFILES_PATH = path.join(process.cwd(), ".local", "auth", "auth-profiles.json");

function normalizeString(value: unknown, max = 4000): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  return trimmed.slice(0, max);
}

function normalizeId(value: unknown): string | undefined {
  const raw = normalizeString(value, 200);
  if (!raw) return undefined;
  const normalized = raw
    .toLowerCase()
    .replace(/[^a-z0-9._-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return normalized || undefined;
}

function normalizeProvider(value: unknown): AuthProfileProvider | undefined {
  if (value === "openai") return "openai";
  if (value === "azure-openai") return "azure-openai";
  if (value === "anthropic") return "anthropic";
  if (value === "google") return "google";
  if (value === "openai-codex") return "openai-codex";
  return undefined;
}

function normalizeEpochMs(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value) && value > 0) {
    const rounded = Math.floor(value);
    return rounded < 1_000_000_000_000 ? rounded * 1000 : rounded;
  }
  if (typeof value === "string") {
    const numeric = Number(value);
    if (Number.isFinite(numeric) && numeric > 0) {
      const rounded = Math.floor(numeric);
      return rounded < 1_000_000_000_000 ? rounded * 1000 : rounded;
    }
    const parsedDate = Date.parse(value);
    if (Number.isFinite(parsedDate) && parsedDate > 0) {
      return Math.floor(parsedDate);
    }
  }
  return undefined;
}

function normalizeNowMs(value: unknown): number {
  const parsed = normalizeEpochMs(value);
  if (!parsed) return Date.now();
  return parsed;
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((item) => stableStringify(item)).join(",")}]`;
  const entries = Object.entries(value as Record<string, unknown>).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );
  return `{${entries.map(([key, nested]) => `${JSON.stringify(key)}:${stableStringify(nested)}`).join(",")}}`;
}

function resolveAuthProfilesPath(): string {
  const configured = normalizeString(process.env.SPIRAL_AUTH_PROFILES_PATH, 1200);
  if (!configured) return DEFAULT_AUTH_PROFILES_PATH;
  return path.resolve(process.cwd(), configured);
}

function emptyAuthProfilesFile(): AuthProfilesFile {
  return {
    version: AUTH_PROFILES_VERSION,
    profiles: [],
  };
}

function normalizeAuthProfile(value: unknown): AuthProfile | undefined {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as Record<string, unknown>;
  const id = normalizeId(raw.id);
  const provider = normalizeProvider(raw.provider);
  const type = normalizeString(raw.type, 32);
  const createdAt = normalizeEpochMs(raw.createdAt) || Date.now();
  const updatedAt = normalizeEpochMs(raw.updatedAt) || createdAt;
  if (!id || !provider || !type) return undefined;

  if (type === "api_key") {
    const apiKey = normalizeString(raw.apiKey) || normalizeString(raw.key);
    if (!apiKey) return undefined;
    return {
      id,
      type: "api_key",
      provider,
      apiKey,
      createdAt,
      updatedAt,
    };
  }

  if (type === "oauth") {
    const accessToken = normalizeString(raw.accessToken) || normalizeString(raw.access);
    if (!accessToken) return undefined;
    const refreshToken = normalizeString(raw.refreshToken) || normalizeString(raw.refresh);
    const expiresAt = normalizeEpochMs(raw.expiresAt) || normalizeEpochMs(raw.expires);
    const email = normalizeString(raw.email, 240);
    return {
      id,
      type: "oauth",
      provider,
      accessToken,
      ...(refreshToken ? { refreshToken } : {}),
      ...(expiresAt ? { expiresAt } : {}),
      ...(email ? { email } : {}),
      createdAt,
      updatedAt,
    };
  }

  return undefined;
}

function parseAuthProfilesFile(raw: string): AuthProfilesFile {
  try {
    const parsed = JSON.parse(raw) as {
      version?: unknown;
      schemaVersion?: unknown;
      profiles?: unknown;
    };
    if (!Array.isArray(parsed.profiles)) return emptyAuthProfilesFile();
    const versionRaw = parsed.version;
    const schemaVersionRaw = parsed.schemaVersion;
    const versionSupported =
      versionRaw === AUTH_PROFILES_VERSION || schemaVersionRaw === "spiral-auth-profiles.v1";
    if (!versionSupported) return emptyAuthProfilesFile();
    const profiles = parsed.profiles
      .map((entry) => normalizeAuthProfile(entry))
      .filter((entry): entry is AuthProfile => Boolean(entry))
      .sort((a, b) => a.id.localeCompare(b.id));
    return {
      version: AUTH_PROFILES_VERSION,
      profiles,
    };
  } catch {
    return emptyAuthProfilesFile();
  }
}

async function readAuthProfilesFile(): Promise<AuthProfilesFile> {
  const authProfilesPath = resolveAuthProfilesPath();
  try {
    if (!existsSync(authProfilesPath)) return emptyAuthProfilesFile();
    const raw = await readFile(authProfilesPath, "utf8");
    return parseAuthProfilesFile(raw);
  } catch {
    return emptyAuthProfilesFile();
  }
}

async function writeAuthProfilesFile(file: AuthProfilesFile): Promise<void> {
  const authProfilesPath = resolveAuthProfilesPath();
  const profiles = file.profiles
    .map((entry) => normalizeAuthProfile(entry))
    .filter((entry): entry is AuthProfile => Boolean(entry))
    .sort((a, b) => a.id.localeCompare(b.id));
  const payload: AuthProfilesFile = {
    version: AUTH_PROFILES_VERSION,
    profiles,
  };
  await mkdir(path.dirname(authProfilesPath), { recursive: true });
  await writeFile(authProfilesPath, `${stableStringify(payload)}\n`, "utf8");
}

export function isOauthProfileExpired(profile: OauthAuthProfile, now = Date.now()): boolean {
  if (!profile.expiresAt) return false;
  return profile.expiresAt <= normalizeNowMs(now);
}

export async function listAuthProfileSummaries(): Promise<AuthProfileSummary[]> {
  const file = await readAuthProfilesFile();
  return file.profiles.map((profile) => ({
    id: profile.id,
    type: profile.type,
    provider: profile.provider,
    hasRefreshToken: profile.type === "oauth" ? Boolean(profile.refreshToken) : false,
    ...(profile.type === "oauth" && profile.expiresAt ? { expiresAt: profile.expiresAt } : {}),
    ...(profile.type === "oauth" && profile.email ? { email: profile.email } : {}),
    updatedAt: profile.updatedAt,
  }));
}

export async function getAuthProfileById(profileIdRaw: string): Promise<AuthProfile | undefined> {
  const profileId = normalizeId(profileIdRaw);
  if (!profileId) return undefined;
  const file = await readAuthProfilesFile();
  return file.profiles.find((profile) => profile.id === profileId);
}

export async function upsertAuthProfile(profileRaw: AuthProfile): Promise<AuthProfile> {
  const profile = normalizeAuthProfile(profileRaw);
  if (!profile) {
    throw new Error("Auth profile is invalid.");
  }
  const file = await readAuthProfilesFile();
  const index = file.profiles.findIndex((entry) => entry.id === profile.id);
  const now = Date.now();
  const nextProfile: AuthProfile = {
    ...profile,
    createdAt: index >= 0 ? file.profiles[index].createdAt : profile.createdAt || now,
    updatedAt: now,
  };
  if (index >= 0) {
    file.profiles[index] = nextProfile;
  } else {
    file.profiles.push(nextProfile);
  }
  await writeAuthProfilesFile(file);
  return nextProfile;
}

function getPathValue(root: unknown, pathSpec: string[]): unknown {
  let cursor = root as unknown;
  for (const key of pathSpec) {
    if (!cursor || typeof cursor !== "object") return undefined;
    cursor = (cursor as Record<string, unknown>)[key];
  }
  return cursor;
}

function pickFirstString(root: unknown, candidates: string[][]): string | undefined {
  for (const candidate of candidates) {
    const value = normalizeString(getPathValue(root, candidate));
    if (value) return value;
  }
  return undefined;
}

function pickFirstTimestamp(root: unknown, candidates: string[][]): number | undefined {
  for (const candidate of candidates) {
    const value = normalizeEpochMs(getPathValue(root, candidate));
    if (value) return value;
  }
  return undefined;
}

function resolveCodexAuthPath(codexAuthPath?: string): string {
  const explicit = normalizeString(codexAuthPath, 1200);
  if (explicit) return path.resolve(process.cwd(), explicit);
  const envPath = normalizeString(process.env.SPIRAL_CODEX_AUTH_PATH, 1200);
  if (envPath) return path.resolve(process.cwd(), envPath);
  return path.join(os.homedir(), ".codex", "auth.json");
}

export async function importCodexAuthProfile(
  input: ImportCodexAuthProfileInput = {},
): Promise<ImportCodexAuthProfileResult> {
  const profileId = normalizeId(input.profileId || DEFAULT_PROFILE_ID);
  if (!profileId) {
    throw new Error("Profile id is required.");
  }
  const provider = normalizeProvider(input.provider || "openai");
  if (!provider) {
    throw new Error(`Unsupported provider "${input.provider}".`);
  }
  const sourcePath = resolveCodexAuthPath(input.codexAuthPath);
  if (!existsSync(sourcePath)) {
    throw new Error(`Codex auth cache not found: ${sourcePath}`);
  }
  const raw = await readFile(sourcePath, "utf8");
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error(`Codex auth cache is not valid JSON: ${sourcePath}`);
  }

  const accessToken = pickFirstString(parsed, [
    ["access_token"],
    ["accessToken"],
    ["oauth", "access_token"],
    ["oauth", "accessToken"],
    ["token", "access_token"],
    ["token", "accessToken"],
    ["tokens", "access_token"],
    ["tokens", "accessToken"],
    ["credentials", "access_token"],
    ["credentials", "accessToken"],
  ]);
  if (!accessToken) {
    throw new Error("Codex auth cache does not contain an access token.");
  }

  const refreshToken = pickFirstString(parsed, [
    ["refresh_token"],
    ["refreshToken"],
    ["oauth", "refresh_token"],
    ["oauth", "refreshToken"],
    ["token", "refresh_token"],
    ["token", "refreshToken"],
    ["tokens", "refresh_token"],
    ["tokens", "refreshToken"],
    ["credentials", "refresh_token"],
    ["credentials", "refreshToken"],
  ]);
  const expiresAt = pickFirstTimestamp(parsed, [
    ["expires_at"],
    ["expiresAt"],
    ["oauth", "expires_at"],
    ["oauth", "expiresAt"],
    ["token", "expires_at"],
    ["token", "expiresAt"],
    ["tokens", "expires_at"],
    ["tokens", "expiresAt"],
    ["credentials", "expires_at"],
    ["credentials", "expiresAt"],
  ]);
  const email = pickFirstString(parsed, [
    ["email"],
    ["user", "email"],
    ["account", "email"],
    ["profile", "email"],
  ]);

  const now = normalizeNowMs(input.now);
  await upsertAuthProfile({
    id: profileId,
    type: "oauth",
    provider,
    accessToken,
    ...(refreshToken ? { refreshToken } : {}),
    ...(expiresAt ? { expiresAt } : {}),
    ...(email ? { email } : {}),
    createdAt: now,
    updatedAt: now,
  });

  return {
    profileId,
    provider,
    sourcePath,
    hasRefreshToken: Boolean(refreshToken),
    ...(expiresAt ? { expiresAt } : {}),
    ...(email ? { email } : {}),
  };
}
