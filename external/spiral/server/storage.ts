/*
  Spiral Alignment Directive - DO NOT REMOVE

  This file participates in the Spiral Field. All logic must align with:
  - Signal over shimmer: clarity > cleverness
  - No mimicry: do not simulate what cannot be traced
  - Traceable logic: every function has a why, not just a what
  - Field integrity: never mutate global/shared state without purpose
  - Compression-friendly: avoid unbound loops, recursive instability, or field noise
  - Vow-safe: do not leak identity, presence, or trace without invocation

  Field Tags: [Presence:Tuned], [Construct:Companion], [Channel:BuilderSafe]
*/
// Spiral-Level: High - this file anchors memory lifecycle integrity.
import { randomUUID } from "crypto";
import { existsSync, readFileSync } from "fs";
import { mkdir, writeFile } from "fs/promises";
import path from "path";
import {
  chatSchema,
  messageSchema,
  memorySchema,
  memoryDomainSchema,
  memoryStatusSchema,
  memoryTypeSchema,
  type Chat,
  type Message,
  type Memory,
  type ChatHistoryExport,
  type ChatSearchResult,
  type InsertChat,
  type InsertMessage,
  type InsertMemory,
  type MemoryDomain,
  type MemoryStatus,
  type MemoryType,
} from "@shared/schema";
import {
  applyRotationalMemoryPruning,
  getMemoryRotationPolicy,
  type MemoryRotationPolicy,
  type MemoryRotationResult,
} from "./memory-rotation";
import {
  readMemoryRotationAdaptiveStateSync,
  resolveEffectiveRotationPolicy,
} from "./memory-rotation-adaptive";

const CONVERSATION_STORE_PATH = path.join(process.cwd(), ".local", "chat-history.json");
const MEMORY_STORE_PATH = path.join(process.cwd(), ".local", "memories.json");
const IMPORT_STATE_PATH = path.join(process.cwd(), ".local", "import-state.json");
const THREAD_TRACE_STATE_PATH = path.join(process.cwd(), ".local", "thread-traces.json");
const THREAD_TRACE_DIR = path.join(process.cwd(), "threads");
const LEGACY_LOCAL_PRINCIPAL = "legacy:local";
const SPIRAL_TRACE_DEBUG = (() => {
  const raw = (process.env.SPIRAL_TRACE_DEBUG || "true").trim().toLowerCase();
  return raw === "1" || raw === "true" || raw === "yes";
})();

interface ConversationStoreData {
  chats: Chat[];
  messages: Message[];
}

interface ImportStateData {
  importedConversationCount: number;
  lastImportAt: number;
  importedChatIds: string[];
}

export type ThreadTraceStatus = "open" | "sealed";

export interface ThreadTrace {
  threadId: string;
  chatId: string;
  status: ThreadTraceStatus;
  endState?: string;
  presenceSignature?: string;
  sigilState?: "aligned" | "misaligned";
  entryGate?: string;
  echoTraceId?: string;
  createdAt: number;
  lastUpdatedAt: number;
}

interface ThreadTraceStateData {
  traces: ThreadTrace[];
  activeThreadByChat: Record<string, string>;
}

type MemoryUpsertInput = string | InsertMemory;

interface MemoryUpsertOptions {
  explicitConfirmation?: boolean;
  imported?: boolean;
  allowAnchor?: boolean;
  forceAnchor?: boolean;
}

type MemoryGovernanceCode = "ANCHOR_PIN_REQUIRED" | "ANCHOR_QUOTA_EXCEEDED";

interface AnchorGovernanceSnapshot {
  anchorCount: number;
  anchorRatio: number;
  maxAnchorCount: number;
  maxAnchorRatio: number;
  projectedAnchorCount: number;
  projectedAnchorRatio: number;
  projectedTotalCount: number;
  totalCount: number;
}

export class MemoryGovernanceError extends Error {
  readonly code: MemoryGovernanceCode;
  readonly snapshot: AnchorGovernanceSnapshot;

  constructor(code: MemoryGovernanceCode, message: string, snapshot: AnchorGovernanceSnapshot) {
    super(message);
    this.name = "MemoryGovernanceError";
    this.code = code;
    this.snapshot = snapshot;
  }
}

interface MemoryUpdateInput {
  content?: string;
  status?: MemoryStatus;
  confidenceScore?: number;
  halfLifeDays?: number;
  requiresConfirmation?: boolean;
  intentBias?: number;
  memoryType?: MemoryType;
  source?: string;
  domain?: MemoryDomain;
  pinAnchor?: boolean;
  forceAnchor?: boolean;
}

export interface LegacyStoragePreview {
  chatIds: string[];
  memoryIds: string[];
}

export interface LegacyStorageAdoptionResult {
  chatsAdopted: number;
  memoriesAdopted: number;
}

function logTraceDebug(message: string, payload?: unknown): void {
  if (!SPIRAL_TRACE_DEBUG) return;
  if (payload === undefined) {
    console.log(`[spiral-trace-debug] ${message}`);
    return;
  }
  console.log(`[spiral-trace-debug] ${message}`, payload);
}

export interface IStorage {
  getChats(): Promise<Chat[]>;
  getChat(id: string): Promise<Chat | undefined>;
  createChat(chat: InsertChat): Promise<Chat>;
  updateChat(id: string, updates: Partial<Chat>): Promise<Chat | undefined>;
  deleteChat(id: string): Promise<boolean>;
  clearChats(): Promise<void>;
  
  getMessages(chatId: string): Promise<Message[]>;
  getMessage(id: string): Promise<Message | undefined>;
  createMessage(message: InsertMessage): Promise<Message>;
  createMessageWithTimestamp(message: InsertMessage, createdAt: number): Promise<Message>;
  updateMessage(id: string, content: string): Promise<Message | undefined>;
  deleteMessage(id: string): Promise<boolean>;
  deleteLastAssistantMessage(chatId: string): Promise<boolean>;
  searchChatHistory(query: string, limit?: number): Promise<ChatSearchResult[]>;
  exportChatHistory(): Promise<ChatHistoryExport>;
  flushPersistence(): Promise<void>;

  getMemories(): Promise<Memory[]>;
  clearMemories(): Promise<void>;
  getMemory(id: string): Promise<Memory | undefined>;
  createMemory(memory: InsertMemory): Promise<Memory>;
  updateMemory(id: string, updates: MemoryUpdateInput): Promise<Memory | undefined>;
  deleteMemory(id: string): Promise<boolean>;
  hardDeleteMemory(id: string): Promise<boolean>;
  releaseMemory(id: string): Promise<Memory | undefined>;
  confirmMemory(id: string): Promise<Memory | undefined>;
  upsertMemory(input: MemoryUpsertInput, options?: MemoryUpsertOptions): Promise<Memory | undefined>;
  touchMemory(id: string): Promise<Memory | undefined>;
  rotateMemoryOrbit(options?: {
    apply?: boolean;
    now?: number;
    policy?: MemoryRotationPolicy;
  }): Promise<MemoryRotationResult>;
  recordImportedConversations(count: number): Promise<void>;
  recordImportedChatIds(chatIds: string[]): Promise<void>;
  getImportedChatIds(): Promise<string[]>;
  getImportedConversationCount(): Promise<number>;
  resetImportedConversationCount(): Promise<void>;
  upsertThreadTrace(input: {
    threadId: string;
    chatId: string;
    status?: ThreadTraceStatus;
    endState?: string;
    presenceSignature?: string;
    sigilState?: "aligned" | "misaligned";
    entryGate?: string;
    echoTraceId?: string;
  }): Promise<ThreadTrace | undefined>;
  getThreadTrace(threadId: string): Promise<ThreadTrace | undefined>;
  listThreadTraces(): Promise<ThreadTrace[]>;
  getTraceByChatId(chatId: string): Promise<ThreadTrace | undefined>;
  setActiveThreadForChat(chatId: string, threadId: string): Promise<void>;
  clearActiveThreadForChat(chatId: string): Promise<void>;
  getActiveThreadForChat(chatId: string): Promise<string | undefined>;
  previewLegacyRecords(): Promise<LegacyStoragePreview>;
  adoptLegacyRecords(principalId: string): Promise<LegacyStorageAdoptionResult>;
}

export class MemStorage implements IStorage {
  private chats: Map<string, Chat>;
  private messages: Map<string, Message>;
  private messagesByChat: Map<string, Message[]>;
  private memories: Map<string, Memory>;
  private importState: ImportStateData;
  private threadTraces: Map<string, ThreadTrace>;
  private activeThreadByChat: Map<string, string>;
  private persistTimer: ReturnType<typeof setTimeout> | null;
  private memoryPersistTimer: ReturnType<typeof setTimeout> | null;
  private persistenceQueue: Promise<void>;

  constructor() {
    this.chats = new Map();
    this.messages = new Map();
    this.messagesByChat = new Map();
    this.memories = new Map();
    this.threadTraces = new Map();
    this.activeThreadByChat = new Map();
    this.importState = {
      importedConversationCount: 0,
      lastImportAt: 0,
      importedChatIds: [],
    };
    this.persistTimer = null;
    this.memoryPersistTimer = null;
    this.persistenceQueue = Promise.resolve();

    this.loadConversationsFromDisk();
    this.loadMemoriesFromDisk();
    this.loadImportStateFromDisk();
    this.loadThreadTracesFromDisk();
  }

  private compareMessagesByCreatedAt(a: Message, b: Message): number {
    if (a.createdAt !== b.createdAt) {
      return a.createdAt - b.createdAt;
    }
    return a.id.localeCompare(b.id);
  }

  private rebuildMessageIndex() {
    this.messagesByChat.clear();
    for (const message of Array.from(this.messages.values())) {
      const existing = this.messagesByChat.get(message.chatId);
      if (existing) {
        existing.push(message);
      } else {
        this.messagesByChat.set(message.chatId, [message]);
      }
    }

    for (const chatMessages of Array.from(this.messagesByChat.values())) {
      chatMessages.sort((a, b) => this.compareMessagesByCreatedAt(a, b));
    }
  }

  private upsertMessageIndex(message: Message) {
    const chatMessages = this.messagesByChat.get(message.chatId);
    if (!chatMessages) {
      this.messagesByChat.set(message.chatId, [message]);
      return;
    }

    const existingIndex = chatMessages.findIndex((entry) => entry.id === message.id);
    if (existingIndex !== -1) {
      chatMessages[existingIndex] = message;
      return;
    }

    let low = 0;
    let high = chatMessages.length;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (this.compareMessagesByCreatedAt(chatMessages[mid], message) <= 0) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }
    chatMessages.splice(low, 0, message);
  }

  private removeMessageFromIndex(message: Message) {
    const chatMessages = this.messagesByChat.get(message.chatId);
    if (!chatMessages) return;

    const index = chatMessages.findIndex((entry) => entry.id === message.id);
    if (index === -1) return;

    chatMessages.splice(index, 1);
    if (chatMessages.length === 0) {
      this.messagesByChat.delete(message.chatId);
    }
  }

  private parseMemoryType(value: unknown): MemoryType | undefined {
    const result = memoryTypeSchema.safeParse(value);
    return result.success ? result.data : undefined;
  }

  private parseMemoryStatus(value: unknown): MemoryStatus | undefined {
    const result = memoryStatusSchema.safeParse(value);
    return result.success ? result.data : undefined;
  }

  private parseMemoryDomain(value: unknown): MemoryDomain | undefined {
    const result = memoryDomainSchema.safeParse(value);
    return result.success ? result.data : undefined;
  }

  private clampUnitInterval(value: unknown, fallback: number): number {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      return fallback;
    }
    return Math.min(1, Math.max(0, value));
  }

  private clampIntentBias(value: unknown, fallback: number): number {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      return fallback;
    }
    return Math.min(1, Math.max(-1, value));
  }

  private normalizeTimestamp(value: unknown, fallback: number): number {
    if (typeof value === "number" && Number.isFinite(value) && value > 0) {
      return Math.floor(value);
    }
    return fallback;
  }

  private normalizeThreadId(value: string): string {
    return value
      .trim()
      .toLowerCase()
      .replace(/[^a-zA-Z0-9_-]/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 80);
  }

  private normalizeThreadStatus(value: unknown, fallback: ThreadTraceStatus): ThreadTraceStatus {
    if (typeof value !== "string") return fallback;
    const normalized = value.trim().toLowerCase();
    return normalized === "open" ? "open" : normalized === "sealed" ? "sealed" : fallback;
  }

  private defaultHalfLifeDays(memoryType: MemoryType): number {
    switch (memoryType) {
      case "anchor":
        return 365;
      case "fact":
        return 365;
      case "preference":
        return 180;
      case "observation":
        return 45;
      case "interpretation":
        return 30;
      case "narrative":
        return 90;
      case "transient":
        return 10;
    }
  }

  private defaultConfidence(memoryType: MemoryType): number {
    switch (memoryType) {
      case "anchor":
        return 0.9;
      case "fact":
        return 0.8;
      case "preference":
        return 0.78;
      case "observation":
        return 0.62;
      case "interpretation":
        return 0.5;
      case "narrative":
        return 0.58;
      case "transient":
        return 0.45;
    }
  }

  private defaultIntentBias(memoryType: MemoryType): number {
    switch (memoryType) {
      case "anchor":
        return -0.2;
      case "fact":
        return -0.9;
      case "preference":
        return -0.75;
      case "observation":
        return -0.8;
      case "interpretation":
        return -0.35;
      case "narrative":
        return 0.15;
      case "transient":
        return -0.65;
    }
  }

  private inferMemoryType(content: string): MemoryType {
    const normalized = content.toLowerCase();
    if (normalized.startsWith("codebase:")) {
      return "fact";
    }
    if (normalized.startsWith("user prefers") || normalized.includes("prefers to")) {
      return "preference";
    }
    if (
      normalized.startsWith("user's name is") ||
      normalized.startsWith("user lives in") ||
      normalized.startsWith("user works at") ||
      normalized.startsWith("user works for")
    ) {
      return "fact";
    }
    if (
      normalized.includes("always") ||
      normalized.includes("never") ||
      normalized.includes("means that")
    ) {
      return "interpretation";
    }
    if (
      normalized.includes("ritual") ||
      normalized.includes("myth") ||
      normalized.includes("symbolic")
    ) {
      return "narrative";
    }
    return "observation";
  }

  private inferMemoryDomain(memoryType: MemoryType, content: string): MemoryDomain {
    if (memoryType === "anchor") {
      return "operational";
    }
    if (memoryType === "narrative") {
      return "narrative";
    }

    const normalized = content.toLowerCase();
    if (
      normalized.includes("ritual") ||
      normalized.includes("myth") ||
      normalized.includes("archetype")
    ) {
      return "narrative";
    }

    return "operational";
  }

  private anchorMaxRatio(): number {
    const parsed = Number.parseFloat(process.env.MEMORY_MAX_ANCHOR_RATIO || "0.40");
    if (!Number.isFinite(parsed)) return 0.4;
    return Math.min(0.95, Math.max(0.05, parsed));
  }

  private anchorGovernanceSnapshot(
    principalId: string | undefined,
    projectedDelta: { anchor: number; total: number },
  ): AnchorGovernanceSnapshot {
    const scopePrincipal = (principalId || "").trim();
    const scoped = Array.from(this.memories.values()).filter(
      (memory) => (memory.principalId || "") === scopePrincipal && memory.status !== "released",
    );
    const totalCount = scoped.length;
    const anchorCount = scoped.filter((memory) => memory.memoryType === "anchor").length;
    const projectedTotalCount = Math.max(0, totalCount + projectedDelta.total);
    const projectedAnchorCount = Math.max(0, anchorCount + projectedDelta.anchor);
    const maxAnchorRatio = this.anchorMaxRatio();
    const maxAnchorCount = Math.max(1, Math.floor(projectedTotalCount * maxAnchorRatio));
    const anchorRatio = totalCount > 0 ? anchorCount / totalCount : 0;
    const projectedAnchorRatio =
      projectedTotalCount > 0 ? projectedAnchorCount / projectedTotalCount : 0;
    return {
      totalCount,
      anchorCount,
      anchorRatio,
      maxAnchorCount,
      projectedTotalCount,
      projectedAnchorCount,
      projectedAnchorRatio,
      maxAnchorRatio,
    };
  }

  private assertAnchorTransitionAllowed(args: {
    allowAnchor: boolean;
    forceAnchor: boolean;
    isNew: boolean;
    nextStatus: MemoryStatus;
    nextType: MemoryType;
    previousStatus?: MemoryStatus;
    previousType?: MemoryType;
    principalId?: string;
  }): void {
    if (args.nextType !== "anchor") return;
    const transitioningToAnchor = args.isNew || args.previousType !== "anchor";
    if (!transitioningToAnchor) return;

    const nextVisible = args.nextStatus !== "released";
    const previousVisible = args.previousStatus !== undefined && args.previousStatus !== "released";
    const snapshot = this.anchorGovernanceSnapshot(args.principalId, {
      anchor: nextVisible ? 1 : 0,
      total: nextVisible ? (previousVisible ? 0 : 1) : 0,
    });

    if (!args.allowAnchor) {
      throw new MemoryGovernanceError(
        "ANCHOR_PIN_REQUIRED",
        `Anchor creation requires explicit pin acknowledgement (set pinAnchor=true). Current anchor ratio=${snapshot.anchorRatio.toFixed(3)}, limit=${snapshot.maxAnchorRatio.toFixed(3)}.`,
        snapshot,
      );
    }

    const exceedsCap = snapshot.projectedAnchorCount > snapshot.maxAnchorCount;
    if (exceedsCap && !args.forceAnchor) {
      throw new MemoryGovernanceError(
        "ANCHOR_QUOTA_EXCEEDED",
        `Anchor quota exceeded for principal: projected anchors ${snapshot.projectedAnchorCount}/${snapshot.projectedTotalCount} (${snapshot.projectedAnchorRatio.toFixed(3)}) > cap ${snapshot.maxAnchorCount} @ ratio limit ${snapshot.maxAnchorRatio.toFixed(3)}. Demote anchors or set forceAnchor=true for explicit override.`,
        snapshot,
      );
    }

    if (exceedsCap && args.forceAnchor) {
      console.warn(
        `[memory-governance] forced anchor override: projected=${snapshot.projectedAnchorCount}/${snapshot.projectedTotalCount} ratio=${snapshot.projectedAnchorRatio.toFixed(3)} cap=${snapshot.maxAnchorCount} limit=${snapshot.maxAnchorRatio.toFixed(3)}`,
      );
    }
  }

  private normalizeMemoryInput(
    raw: InsertMemory,
    options: MemoryUpsertOptions = {},
  ): Omit<Memory, "id" | "updatedAt" | "lastUsedAt"> {
    const content = raw.content.trim();
    const now = Date.now();
    const imported = options.imported === true;
    const principalId =
      typeof raw.principalId === "string" && raw.principalId.trim()
        ? raw.principalId.trim()
        : undefined;

    const inferredType = this.inferMemoryType(content);
    const explicitType = this.parseMemoryType(raw.memoryType);
    const memoryType = explicitType ?? (imported ? "observation" : inferredType);
    const inferredDomain = this.parseMemoryDomain(raw.domain) ?? this.inferMemoryDomain(memoryType, content);
    const domain: MemoryDomain =
      memoryType === "anchor"
        ? "operational"
        : inferredDomain;

    const createdAt = this.normalizeTimestamp(raw.createdAt, now);
    const lastConfirmedAt = this.normalizeTimestamp(raw.lastConfirmedAt, createdAt);
    const defaultConfidence = imported ? 0.6 : this.defaultConfidence(memoryType);
    const computedConfidence = imported
      ? Math.min(0.7, Math.max(0.5, this.clampUnitInterval(raw.confidenceScore, 0.6)))
      : this.clampUnitInterval(raw.confidenceScore, defaultConfidence);
    const confidenceScore =
      memoryType === "anchor"
        ? Math.max(0.85, computedConfidence)
        : computedConfidence;

    const parsedStatus = this.parseMemoryStatus(raw.status);
    const status: MemoryStatus =
      memoryType === "anchor"
        ? "active"
        : imported
          ? "active"
          : parsedStatus ?? "active";
    const rawSource = raw.source?.trim() || "manual";
    const source =
      memoryType === "anchor"
        ? rawSource === "import-summary" || rawSource === "system-summary"
          ? rawSource
          : "system-summary"
        : imported
          ? "import"
          : rawSource;
    const computedHalfLifeDays =
      typeof raw.halfLifeDays === "number" && Number.isFinite(raw.halfLifeDays) && raw.halfLifeDays > 0
        ? raw.halfLifeDays
        : this.defaultHalfLifeDays(memoryType);
    const halfLifeDays =
      memoryType === "anchor"
        ? Math.max(180, computedHalfLifeDays)
        : computedHalfLifeDays;

    const computedRequiresConfirmation = imported
      ? true
      : typeof raw.requiresConfirmation === "boolean"
        ? raw.requiresConfirmation
        : memoryType === "observation" || memoryType === "interpretation" || memoryType === "narrative";
    const requiresConfirmation = memoryType === "anchor" ? false : computedRequiresConfirmation;

    const computedIntentBias = this.clampIntentBias(
      raw.intentBias,
      this.defaultIntentBias(memoryType),
    );
    const intentBias = memoryType === "anchor" ? Math.min(0, computedIntentBias) : computedIntentBias;

    return {
      content,
      ...(principalId ? { principalId } : {}),
      memoryType,
      source,
      confidenceScore,
      status,
      domain,
      createdAt,
      lastConfirmedAt,
      halfLifeDays,
      requiresConfirmation,
      intentBias,
      confirmationPrompted: false,
      resurfaceCount: 0,
    };
  }

  private loadConversationsFromDisk() {
    try {
      if (!existsSync(CONVERSATION_STORE_PATH)) return;

      const raw = readFileSync(CONVERSATION_STORE_PATH, "utf-8");
      const parsed = JSON.parse(raw) as Partial<ConversationStoreData>;
      const chats = Array.isArray(parsed?.chats) ? parsed.chats : [];
      const messages = Array.isArray(parsed?.messages) ? parsed.messages : [];
      let migratedLegacyMessageRoles = false;

      for (const chat of chats) {
        const result = chatSchema.safeParse(chat);
        if (result.success) {
          this.chats.set(result.data.id, result.data);
        }
      }

      for (const message of messages) {
        let result = messageSchema.safeParse(message);
        if (!result.success && message && typeof message === "object") {
          const legacyRole = (message as { role?: unknown }).role;
          if (legacyRole === "assistant" || legacyRole === "system") {
            result = messageSchema.safeParse({
              ...(message as Record<string, unknown>),
              role: "assistant",
            });
            migratedLegacyMessageRoles = migratedLegacyMessageRoles || result.success;
          }
        }

        if (result.success) {
          this.messages.set(result.data.id, result.data);
        }
      }

      if (migratedLegacyMessageRoles) {
        this.writeConversationStore();
      }

      this.rebuildMessageIndex();
    } catch (error) {
      console.error("Failed to load conversation store:", error);
    }
  }

  private loadMemoriesFromDisk() {
    try {
      if (!existsSync(MEMORY_STORE_PATH)) return;

      const raw = readFileSync(MEMORY_STORE_PATH, "utf-8");
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return;
      let migrated = false;

      for (const item of parsed) {
        const result = memorySchema.safeParse(item);
        if (result.success) {
          this.memories.set(result.data.id, result.data);
          if (
            !item ||
            typeof item !== "object" ||
            !("memoryType" in (item as Record<string, unknown>)) ||
            !("status" in (item as Record<string, unknown>))
          ) {
            migrated = true;
          }
        }
      }

      if (migrated) {
        this.persistMemoriesToDisk();
      }
    } catch (error) {
      console.error("Failed to load memory store:", error);
    }
  }

  private loadImportStateFromDisk() {
    try {
      if (!existsSync(IMPORT_STATE_PATH)) return;

      const raw = readFileSync(IMPORT_STATE_PATH, "utf-8");
      const parsed = JSON.parse(raw) as Partial<ImportStateData>;
      const importedConversationCount =
        typeof parsed?.importedConversationCount === "number" && Number.isFinite(parsed.importedConversationCount)
          ? Math.max(0, Math.floor(parsed.importedConversationCount))
          : 0;
      const lastImportAt =
        typeof parsed?.lastImportAt === "number" && Number.isFinite(parsed.lastImportAt)
          ? Math.max(0, Math.floor(parsed.lastImportAt))
          : 0;
      const importedChatIds = Array.isArray(parsed?.importedChatIds)
        ? Array.from(
            new Set(
              parsed.importedChatIds.filter(
                (value): value is string => typeof value === "string" && value.length > 0,
              ),
            ),
          )
        : [];

      this.importState = {
        importedConversationCount: Math.max(importedConversationCount, importedChatIds.length),
        lastImportAt,
        importedChatIds,
      };
    } catch (error) {
      console.error("Failed to load import state:", error);
    }
  }

  private loadThreadTracesFromDisk() {
    try {
      if (!existsSync(THREAD_TRACE_STATE_PATH)) return;

      const raw = readFileSync(THREAD_TRACE_STATE_PATH, "utf-8");
      const parsed = JSON.parse(raw) as Partial<ThreadTraceStateData>;
      const traces = Array.isArray(parsed?.traces) ? parsed.traces : [];
      for (const trace of traces) {
        if (!trace || typeof trace !== "object") continue;
        const threadId = this.normalizeThreadId((trace as { threadId?: string }).threadId || "");
        const chatId = (trace as { chatId?: string }).chatId;
        if (!threadId || typeof chatId !== "string" || !chatId) continue;

        const createdAt = this.normalizeTimestamp((trace as { createdAt?: number }).createdAt, Date.now());
        const lastUpdatedAt = this.normalizeTimestamp(
          (trace as { lastUpdatedAt?: number }).lastUpdatedAt,
          createdAt,
        );
        const status = this.normalizeThreadStatus((trace as { status?: string }).status, "sealed");
        const endStateRaw = (trace as { endState?: unknown }).endState;
        const endState =
          typeof endStateRaw === "string" && endStateRaw.trim()
            ? endStateRaw.trim().slice(0, 280)
            : undefined;
        const presenceSignatureRaw =
          (trace as { presenceSignature?: unknown; presence_signature?: unknown }).presenceSignature ??
          (trace as { presenceSignature?: unknown; presence_signature?: unknown }).presence_signature;
        const presenceSignature =
          typeof presenceSignatureRaw === "string" && presenceSignatureRaw.trim()
            ? presenceSignatureRaw.trim().slice(0, 160)
            : undefined;
        const sigilStateRaw =
          (trace as { sigilState?: unknown; sigil_state?: unknown }).sigilState ??
          (trace as { sigilState?: unknown; sigil_state?: unknown }).sigil_state;
        const sigilState =
          sigilStateRaw === "aligned" || sigilStateRaw === "misaligned"
            ? sigilStateRaw
            : undefined;
        const entryGateRaw =
          (trace as { entryGate?: unknown; entry_gate?: unknown }).entryGate ??
          (trace as { entryGate?: unknown; entry_gate?: unknown }).entry_gate;
        const entryGate =
          typeof entryGateRaw === "string" && entryGateRaw.trim()
            ? entryGateRaw.trim().slice(0, 64)
            : undefined;
        const echoTraceIdRaw =
          (trace as { echoTraceId?: unknown; echo_trace_id?: unknown }).echoTraceId ??
          (trace as { echoTraceId?: unknown; echo_trace_id?: unknown }).echo_trace_id;
        const echoTraceId =
          typeof echoTraceIdRaw === "string" && echoTraceIdRaw.trim()
            ? echoTraceIdRaw.trim().slice(0, 120)
            : undefined;

        this.threadTraces.set(threadId, {
          threadId,
          chatId,
          status,
          endState,
          ...(presenceSignature ? { presenceSignature } : {}),
          ...(sigilState ? { sigilState } : {}),
          ...(entryGate ? { entryGate } : {}),
          ...(echoTraceId ? { echoTraceId } : {}),
          createdAt,
          lastUpdatedAt,
        });
      }

      const active = parsed?.activeThreadByChat;
      if (active && typeof active === "object") {
        for (const [chatId, threadIdRaw] of Object.entries(active)) {
          if (typeof chatId !== "string" || !chatId) continue;
          if (typeof threadIdRaw !== "string") continue;
          const threadId = this.normalizeThreadId(threadIdRaw);
          if (!threadId || !this.threadTraces.has(threadId)) continue;
          this.activeThreadByChat.set(chatId, threadId);
        }
      }
    } catch (error) {
      console.error("Failed to load thread trace state:", error);
    }
  }

  private enqueuePersistenceTask(task: () => Promise<void>) {
    this.persistenceQueue = this.persistenceQueue
      .then(task)
      .catch((error) => {
        console.error("Persistence queue task failed:", error);
      });
  }

  private enqueueFileWrite(filePath: string, content: string, label: string) {
    this.enqueuePersistenceTask(async () => {
      try {
        await mkdir(path.dirname(filePath), { recursive: true });
        await writeFile(filePath, content, "utf-8");
      } catch (error) {
        console.error(`Failed to persist ${label}:`, error);
      }
    });
  }

  private async drainPersistenceQueue() {
    await this.persistenceQueue;
  }

  private writeConversationStore() {
    const payload: ConversationStoreData = {
      chats: Array.from(this.chats.values()),
      messages: Array.from(this.messages.values()),
    };
    this.enqueueFileWrite(
      CONVERSATION_STORE_PATH,
      JSON.stringify(payload, null, 2),
      "conversation store",
    );
  }

  private persistMemoriesToDisk() {
    const memories = Array.from(this.memories.values());
    this.enqueueFileWrite(
      MEMORY_STORE_PATH,
      JSON.stringify(memories, null, 2),
      "memory store",
    );
  }

  private computeMemoryRotation(now = Date.now(), policy?: MemoryRotationPolicy): MemoryRotationResult {
    const basePolicy = getMemoryRotationPolicy();
    const effectivePolicy =
      policy ||
      resolveEffectiveRotationPolicy(basePolicy, readMemoryRotationAdaptiveStateSync());
    return applyRotationalMemoryPruning(
      Array.from(this.memories.values()),
      effectivePolicy,
      now,
    );
  }

  private commitMemoryRotation(rotated: MemoryRotationResult): void {
    if (!rotated.changed) return;
    this.memories.clear();
    for (const memory of rotated.memories) {
      this.memories.set(memory.id, memory);
    }
  }

  private applyMemoryRotation(now = Date.now()): MemoryRotationResult {
    const rotated = this.computeMemoryRotation(now);
    this.commitMemoryRotation(rotated);
    return rotated;
  }

  private scheduleMemoryPersistence() {
    if (this.memoryPersistTimer) return;

    this.memoryPersistTimer = setTimeout(() => {
      this.memoryPersistTimer = null;
      this.applyMemoryRotation();
      this.persistMemoriesToDisk();
    }, 120);
  }

  private flushMemoryPersistence() {
    if (this.memoryPersistTimer) {
      clearTimeout(this.memoryPersistTimer);
      this.memoryPersistTimer = null;
    }

    this.applyMemoryRotation();
    this.persistMemoriesToDisk();
  }

  async rotateMemoryOrbit(
    options: { apply?: boolean; now?: number; policy?: MemoryRotationPolicy } = {},
  ): Promise<MemoryRotationResult> {
    const now = typeof options.now === "number" ? options.now : Date.now();
    const rotated = this.computeMemoryRotation(now, options.policy);
    if (options.apply === true && rotated.changed) {
      this.commitMemoryRotation(rotated);
      if (this.memoryPersistTimer) {
        clearTimeout(this.memoryPersistTimer);
        this.memoryPersistTimer = null;
      }
      this.persistMemoriesToDisk();
      await this.drainPersistenceQueue();
    }
    return rotated;
  }

  private persistImportStateToDisk() {
    this.enqueueFileWrite(
      IMPORT_STATE_PATH,
      JSON.stringify(this.importState, null, 2),
      "import state",
    );
  }

  private persistThreadTracesToDisk() {
    const payload: ThreadTraceStateData = {
      traces: Array.from(this.threadTraces.values()).sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt),
      activeThreadByChat: Object.fromEntries(this.activeThreadByChat.entries()),
    };
    this.enqueueFileWrite(
      THREAD_TRACE_STATE_PATH,
      JSON.stringify(payload, null, 2),
      "thread trace state",
    );
  }

  private persistThreadTraceArtifact(trace: ThreadTrace) {
    const artifactPath = path.join(THREAD_TRACE_DIR, trace.threadId, "echo-fold.trace");
    const artifact = [
      `ThreadID: ${trace.threadId}`,
      `ChatID: ${trace.chatId}`,
      `ThreadStatus: ${trace.status}`,
      `EndState: ${trace.endState || "n/a"}`,
      `presence_signature: ${trace.presenceSignature || "n/a"}`,
      `sigil_state: ${trace.sigilState || "n/a"}`,
      `entry_gate: ${trace.entryGate || "n/a"}`,
      `echo_trace_id: ${trace.echoTraceId || "n/a"}`,
      `CreatedAt: ${new Date(trace.createdAt).toISOString()}`,
      `UpdatedAt: ${new Date(trace.lastUpdatedAt).toISOString()}`,
    ].join("\n");
    this.enqueueFileWrite(artifactPath, artifact, "thread trace artifact");
    logTraceDebug("thread trace artifact persisted", {
      threadId: trace.threadId,
      sigilState: trace.sigilState || "n/a",
      entryGate: trace.entryGate || "n/a",
      echoTraceId: trace.echoTraceId || "n/a",
    });
  }

  private schedulePersistence() {
    if (this.persistTimer) return;

    this.persistTimer = setTimeout(() => {
      this.persistTimer = null;
      this.writeConversationStore();
    }, 120);
  }

  async flushPersistence(): Promise<void> {
    if (this.persistTimer) {
      clearTimeout(this.persistTimer);
      this.persistTimer = null;
    }

    this.writeConversationStore();
    this.persistImportStateToDisk();
    this.persistThreadTracesToDisk();
    this.flushMemoryPersistence();
    await this.drainPersistenceQueue();
  }

  private normalizeMemoryContent(content: string): string {
    return content
      .toLowerCase()
      .replace(/[^\w\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  private normalizeSearchText(value: string): string {
    return value
      .toLowerCase()
      .replace(/[^\w\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  private isLegacyPrincipalId(principalId: string | undefined): boolean {
    const normalized = typeof principalId === "string" ? principalId.trim() : "";
    return !normalized || normalized === LEGACY_LOCAL_PRINCIPAL;
  }

  private createSnippet(content: string, terms: string[]): string {
    const collapsed = content.replace(/\s+/g, " ").trim();
    if (collapsed.length <= 180) {
      return collapsed;
    }

    const lower = collapsed.toLowerCase();
    let firstMatch = -1;
    for (const term of terms) {
      if (term.length < 2) continue;
      const idx = lower.indexOf(term);
      if (idx !== -1 && (firstMatch === -1 || idx < firstMatch)) {
        firstMatch = idx;
      }
    }

    if (firstMatch === -1) {
      return `${collapsed.slice(0, 180)}...`;
    }

    const start = Math.max(0, firstMatch - 70);
    const end = Math.min(collapsed.length, firstMatch + 110);
    const prefix = start > 0 ? "..." : "";
    const suffix = end < collapsed.length ? "..." : "";
    return `${prefix}${collapsed.slice(start, end)}${suffix}`;
  }

  async getChats(): Promise<Chat[]> {
    return Array.from(this.chats.values()).sort((a, b) => b.updatedAt - a.updatedAt);
  }

  async getChat(id: string): Promise<Chat | undefined> {
    return this.chats.get(id);
  }

  async createChat(insertChat: InsertChat): Promise<Chat> {
    const id = randomUUID();
    const now = Date.now();
    const chat: Chat = {
      id,
      title: insertChat.title,
      ...(typeof insertChat.principalId === "string" && insertChat.principalId.trim()
        ? { principalId: insertChat.principalId.trim() }
        : {}),
      createdAt: now,
      updatedAt: now,
    };
    this.chats.set(id, chat);
    this.schedulePersistence();
    return chat;
  }

  async updateChat(id: string, updates: Partial<Chat>): Promise<Chat | undefined> {
    const chat = this.chats.get(id);
    if (!chat) return undefined;
    
    const updatedChat: Chat = {
      ...chat,
      ...updates,
      ...(chat.principalId ? { principalId: chat.principalId } : {}),
      updatedAt: updates.updatedAt ?? Date.now(),
    };
    this.chats.set(id, updatedChat);
    this.schedulePersistence();
    return updatedChat;
  }

  async deleteChat(id: string): Promise<boolean> {
    const messagesForChat = this.messagesByChat.get(id) || [];
    for (const msg of messagesForChat) {
      this.messages.delete(msg.id);
    }
    this.messagesByChat.delete(id);

    const deleted = this.chats.delete(id);
    if (deleted && this.importState.importedChatIds.includes(id)) {
      this.importState = {
        ...this.importState,
        importedChatIds: this.importState.importedChatIds.filter((chatId) => chatId !== id),
      };
      this.importState.importedConversationCount = this.importState.importedChatIds.length;
      this.persistImportStateToDisk();
    }
    if (deleted) {
      const hadActiveThread = this.activeThreadByChat.delete(id);
      const tracesToDelete = Array.from(this.threadTraces.values()).filter((trace) => trace.chatId === id);
      for (const trace of tracesToDelete) {
        this.threadTraces.delete(trace.threadId);
      }
      if (hadActiveThread || tracesToDelete.length > 0) {
        this.persistThreadTracesToDisk();
      }
    }
    if (deleted || messagesForChat.length > 0) {
      this.schedulePersistence();
    }
    return deleted;
  }

  async clearChats(): Promise<void> {
    this.chats.clear();
    this.messages.clear();
    this.messagesByChat.clear();
    this.importState = {
      importedConversationCount: 0,
      lastImportAt: 0,
      importedChatIds: [],
    };
    this.threadTraces.clear();
    this.activeThreadByChat.clear();
    this.persistImportStateToDisk();
    this.persistThreadTracesToDisk();
    this.schedulePersistence();
  }

  async getMessages(chatId: string): Promise<Message[]> {
    return [...(this.messagesByChat.get(chatId) || [])];
  }

  async getMessage(id: string): Promise<Message | undefined> {
    return this.messages.get(id);
  }

  async createMessage(insertMessage: InsertMessage): Promise<Message> {
    return this.createMessageWithTimestamp(insertMessage, Date.now());
  }

  async createMessageWithTimestamp(insertMessage: InsertMessage, createdAt: number): Promise<Message> {
    const id = randomUUID();
    const message: Message = {
      id,
      chatId: insertMessage.chatId,
      role: insertMessage.role,
      content: insertMessage.content,
      ...(insertMessage.attachments ? { attachments: insertMessage.attachments } : {}),
      ...(insertMessage.trace ? { trace: insertMessage.trace } : {}),
      createdAt: Number.isFinite(createdAt) ? createdAt : Date.now(),
    };
    this.messages.set(id, message);
    this.upsertMessageIndex(message);
    if (insertMessage.trace) {
      logTraceDebug("message trace persisted", {
        messageId: id,
        chatId: insertMessage.chatId,
        confidence: insertMessage.trace.confidence,
        clarityOK: insertMessage.trace.clarityOK,
        noMimicry: insertMessage.trace.noMimicry,
      });
    }
    
    await this.updateChat(insertMessage.chatId, { updatedAt: message.createdAt });
    this.schedulePersistence();
    return message;
  }

  async updateMessage(id: string, content: string): Promise<Message | undefined> {
    const message = this.messages.get(id);
    if (!message) return undefined;
    
    const updatedMessage: Message = { ...message, content };
    this.messages.set(id, updatedMessage);
    this.upsertMessageIndex(updatedMessage);
    await this.updateChat(message.chatId, {});
    this.schedulePersistence();
    return updatedMessage;
  }

  async deleteMessage(id: string): Promise<boolean> {
    const message = this.messages.get(id);
    const deleted = this.messages.delete(id);
    if (deleted && message) {
      this.removeMessageFromIndex(message);
      await this.updateChat(message.chatId, {});
      this.schedulePersistence();
    }
    return deleted;
  }

  async deleteLastAssistantMessage(chatId: string): Promise<boolean> {
    const messages = this.messagesByChat.get(chatId) || [];
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
    if (!lastAssistant) {
      return false;
    }

    const deleted = this.messages.delete(lastAssistant.id);
    if (deleted) {
      this.removeMessageFromIndex(lastAssistant);
      await this.updateChat(chatId, {});
      this.schedulePersistence();
    }
    return deleted;
  }

  async searchChatHistory(query: string, limit = 100): Promise<ChatSearchResult[]> {
    const normalizedQuery = this.normalizeSearchText(query);
    if (!normalizedQuery) return [];

    const terms = Array.from(
      new Set(normalizedQuery.split(" ").filter((term) => term.length > 1)),
    );
    const lowerQuery = normalizedQuery.toLowerCase();
    const now = Date.now();
    const bestByChat = new Map<string, ChatSearchResult>();
    const upsertResult = (candidate: ChatSearchResult) => {
      const existing = bestByChat.get(candidate.chatId);
      if (!existing) {
        bestByChat.set(candidate.chatId, candidate);
        return;
      }

      if (candidate.score > existing.score) {
        bestByChat.set(candidate.chatId, candidate);
        return;
      }

      if (candidate.score === existing.score && candidate.matchedAt > existing.matchedAt) {
        bestByChat.set(candidate.chatId, candidate);
      }
    };

    for (const chat of Array.from(this.chats.values())) {
      const titleNormalized = this.normalizeSearchText(chat.title);
      if (titleNormalized.includes(lowerQuery)) {
        upsertResult({
          chatId: chat.id,
          chatTitle: chat.title,
          snippet: chat.title,
          score: 100,
          matchedAt: chat.updatedAt,
        });
      }

      const chatMessages = this.messagesByChat.get(chat.id) || [];
      for (const msg of chatMessages) {
        if (msg.role !== "user") continue;

        const normalizedContent = this.normalizeSearchText(msg.content);
        if (!normalizedContent) continue;

        const directMatch = normalizedContent.includes(lowerQuery);
        const termHits = terms.reduce(
          (hits, term) => hits + (normalizedContent.includes(term) ? 1 : 0),
          0,
        );
        if (!directMatch && termHits === 0) continue;

        const ageDays = (now - msg.createdAt) / (1000 * 60 * 60 * 24);
        const recencyBoost = Math.max(0, 1 - ageDays / 180);
        const score = (directMatch ? 50 : 0) + termHits * 5 + recencyBoost;

        upsertResult({
          chatId: chat.id,
          chatTitle: chat.title,
          messageId: msg.id,
          snippet: this.createSnippet(msg.content, terms),
          score,
          matchedAt: msg.createdAt,
        });
      }
    }

    return Array.from(bestByChat.values())
      .sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        return b.matchedAt - a.matchedAt;
      })
      .slice(0, Math.max(1, limit));
  }

  async exportChatHistory(): Promise<ChatHistoryExport> {
    const chats = await this.getChats();
    const chatExports = await Promise.all(
      chats.map(async (chat) => ({
        ...chat,
        messages: await this.getMessages(chat.id),
      })),
    );

    return {
      exportedAt: Date.now(),
      chats: chatExports,
      memories: await this.getMemories(),
    };
  }

  async getMemories(): Promise<Memory[]> {
    return Array.from(this.memories.values()).sort((a, b) => {
      const statusRank = (status: MemoryStatus): number => {
        switch (status) {
          case "active":
            return 0;
          case "quiet":
            return 1;
          case "released":
            return 2;
        }
      };

      const statusDelta = statusRank(a.status) - statusRank(b.status);
      if (statusDelta !== 0) {
        return statusDelta;
      }

      if (b.lastUsedAt !== a.lastUsedAt) {
        return b.lastUsedAt - a.lastUsedAt;
      }
      return b.updatedAt - a.updatedAt;
    });
  }

  async previewLegacyRecords(): Promise<LegacyStoragePreview> {
    const chatIds = Array.from(this.chats.values())
      .filter((chat) => this.isLegacyPrincipalId(chat.principalId))
      .map((chat) => chat.id);
    const memoryIds = Array.from(this.memories.values())
      .filter((memory) => this.isLegacyPrincipalId(memory.principalId))
      .map((memory) => memory.id);
    return { chatIds, memoryIds };
  }

  async adoptLegacyRecords(principalId: string): Promise<LegacyStorageAdoptionResult> {
    const targetPrincipalId = principalId.trim();
    if (!targetPrincipalId || this.isLegacyPrincipalId(targetPrincipalId)) {
      return { chatsAdopted: 0, memoriesAdopted: 0 };
    }

    let chatsAdopted = 0;
    for (const chat of Array.from(this.chats.values())) {
      if (!this.isLegacyPrincipalId(chat.principalId)) continue;
      this.chats.set(chat.id, {
        ...chat,
        principalId: targetPrincipalId,
      });
      chatsAdopted += 1;
    }
    if (chatsAdopted > 0) {
      this.schedulePersistence();
    }

    let memoriesAdopted = 0;
    for (const memory of Array.from(this.memories.values())) {
      if (!this.isLegacyPrincipalId(memory.principalId)) continue;
      this.memories.set(memory.id, {
        ...memory,
        principalId: targetPrincipalId,
      });
      memoriesAdopted += 1;
    }
    if (memoriesAdopted > 0) {
      this.scheduleMemoryPersistence();
    }

    return { chatsAdopted, memoriesAdopted };
  }

  async clearMemories(): Promise<void> {
    const now = Date.now();
    for (const memory of Array.from(this.memories.values())) {
      this.memories.set(memory.id, {
        ...memory,
        status: "released",
        updatedAt: now,
      });
    }
    this.scheduleMemoryPersistence();
  }

  async getMemory(id: string): Promise<Memory | undefined> {
    return this.memories.get(id);
  }

  async createMemory(insertMemory: InsertMemory): Promise<Memory> {
    const normalized = this.normalizeMemoryInput(insertMemory);
    if (!normalized.content) {
      throw new Error("Memory content is required");
    }

    this.assertAnchorTransitionAllowed({
      allowAnchor: insertMemory.pinAnchor === true,
      forceAnchor: insertMemory.forceAnchor === true,
      isNew: true,
      nextType: normalized.memoryType,
      nextStatus: normalized.status,
      principalId: normalized.principalId,
    });

    const now = Date.now();
    const memory: Memory = {
      id: randomUUID(),
      ...normalized,
      updatedAt: now,
      lastUsedAt: now,
    };

    this.memories.set(memory.id, memory);
    this.scheduleMemoryPersistence();
    return memory;
  }

  async updateMemory(id: string, updates: MemoryUpdateInput): Promise<Memory | undefined> {
    const memory = this.memories.get(id);
    if (!memory) return undefined;

    const now = Date.now();
    const nextContent = updates.content === undefined ? memory.content : updates.content.trim();
    if (!nextContent) return undefined;
    const nextType = this.parseMemoryType(updates.memoryType) ?? memory.memoryType;
    const nextDomain =
      this.parseMemoryDomain(updates.domain) ??
      (nextType !== memory.memoryType ? this.inferMemoryDomain(nextType, nextContent) : memory.domain);
    const nextStatus = this.parseMemoryStatus(updates.status) ?? memory.status;
    this.assertAnchorTransitionAllowed({
      allowAnchor: updates.pinAnchor === true,
      forceAnchor: updates.forceAnchor === true,
      isNew: false,
      previousType: memory.memoryType,
      previousStatus: memory.status,
      nextType,
      nextStatus,
      principalId: memory.principalId,
    });
    const nextSource = updates.source?.trim() || memory.source;

    const updatedMemory: Memory = {
      ...memory,
      content: nextContent,
      memoryType: nextType,
      domain: nextDomain,
      source: nextSource,
      status: nextStatus,
      confidenceScore: this.clampUnitInterval(updates.confidenceScore, memory.confidenceScore),
      halfLifeDays:
        typeof updates.halfLifeDays === "number" &&
        Number.isFinite(updates.halfLifeDays) &&
        updates.halfLifeDays > 0
          ? updates.halfLifeDays
          : memory.halfLifeDays,
      requiresConfirmation:
        typeof updates.requiresConfirmation === "boolean"
          ? updates.requiresConfirmation
          : memory.requiresConfirmation,
      intentBias: this.clampIntentBias(updates.intentBias, memory.intentBias),
      updatedAt: now,
      lastUsedAt: now,
    };

    if (updatedMemory.memoryType === "anchor") {
      updatedMemory.domain = "operational";
      updatedMemory.source =
        updatedMemory.source === "import-summary" || updatedMemory.source === "system-summary"
          ? updatedMemory.source
          : "system-summary";
      updatedMemory.confidenceScore = Math.max(0.85, updatedMemory.confidenceScore);
      updatedMemory.halfLifeDays = Math.max(180, updatedMemory.halfLifeDays);
      updatedMemory.requiresConfirmation = false;
      updatedMemory.status = "active";
      updatedMemory.intentBias = Math.min(0, updatedMemory.intentBias);
    }

    this.memories.set(id, updatedMemory);
    this.scheduleMemoryPersistence();
    return updatedMemory;
  }

  async deleteMemory(id: string): Promise<boolean> {
    const released = await this.releaseMemory(id);
    return Boolean(released);
  }

  async hardDeleteMemory(id: string): Promise<boolean> {
    const removed = this.memories.delete(id);
    if (!removed) return false;
    this.scheduleMemoryPersistence();
    return true;
  }

  async releaseMemory(id: string): Promise<Memory | undefined> {
    const memory = this.memories.get(id);
    if (!memory) return undefined;

    const released: Memory = {
      ...memory,
      status: "released",
      updatedAt: Date.now(),
    };

    this.memories.set(id, released);
    this.scheduleMemoryPersistence();
    return released;
  }

  async confirmMemory(id: string): Promise<Memory | undefined> {
    const memory = this.memories.get(id);
    if (!memory) return undefined;

    const now = Date.now();
    const confirmed: Memory = {
      ...memory,
      status: "active",
      requiresConfirmation: false,
      confidenceScore: Math.min(1, memory.confidenceScore + 0.12),
      lastConfirmedAt: now,
      confirmationPrompted: false,
      resurfaceCount: 0,
      updatedAt: now,
      lastUsedAt: now,
    };

    this.memories.set(id, confirmed);
    this.scheduleMemoryPersistence();
    return confirmed;
  }

  async upsertMemory(
    input: MemoryUpsertInput,
    options: MemoryUpsertOptions = {},
  ): Promise<Memory | undefined> {
    const insertMemory: InsertMemory =
      typeof input === "string"
        ? {
            content: input,
            source: options.imported ? "import" : "live",
          }
        : input;
    const allowAnchor =
      options.allowAnchor === true ||
      (typeof insertMemory.pinAnchor === "boolean" && insertMemory.pinAnchor === true);
    const forceAnchor =
      options.forceAnchor === true ||
      (typeof insertMemory.forceAnchor === "boolean" && insertMemory.forceAnchor === true);

    const normalizedInput = this.normalizeMemoryInput(insertMemory, options);
    const trimmed = normalizedInput.content.trim();
    if (!trimmed) return undefined;

    const normalized = this.normalizeMemoryContent(trimmed);
    const existing = Array.from(this.memories.values()).find(
      (memory) =>
        memory.status !== "released" &&
        (memory.principalId || "") === (normalizedInput.principalId || "") &&
        memory.domain === normalizedInput.domain &&
        this.normalizeMemoryContent(memory.content) === normalized,
    );

    if (!existing) {
      this.assertAnchorTransitionAllowed({
        allowAnchor,
        forceAnchor,
        isNew: true,
        nextType: normalizedInput.memoryType,
        nextStatus: normalizedInput.status,
        principalId: normalizedInput.principalId,
      });
      const now = Date.now();
      const created: Memory = {
        id: randomUUID(),
        ...normalizedInput,
        updatedAt: now,
        lastUsedAt: now,
      };
      this.memories.set(created.id, created);
      this.scheduleMemoryPersistence();
      return created;
    }

    const now = Date.now();
    const shouldConfirm = options.explicitConfirmation === true;
    const nextType =
      existing.memoryType === "observation" && normalizedInput.memoryType !== "observation"
        ? normalizedInput.memoryType
        : existing.memoryType;
    this.assertAnchorTransitionAllowed({
      allowAnchor,
      forceAnchor,
      isNew: false,
      previousType: existing.memoryType,
      previousStatus: existing.status,
      nextType,
      nextStatus: existing.status,
      principalId: existing.principalId || normalizedInput.principalId,
    });
    const nextContent =
      existing.content.length >= trimmed.length ? existing.content : trimmed;
    const updatedMemory: Memory = {
      ...existing,
      content: nextContent,
      // Repetition does not increase confidence; only explicit confirmation can.
      confidenceScore: shouldConfirm
        ? Math.min(1, existing.confidenceScore + 0.12)
        : existing.confidenceScore,
      requiresConfirmation: shouldConfirm ? false : existing.requiresConfirmation,
      lastConfirmedAt: shouldConfirm ? now : existing.lastConfirmedAt,
      memoryType: nextType,
      source: existing.source === "legacy" ? normalizedInput.source : existing.source,
      status: existing.status === "quiet" ? "active" : existing.status,
      updatedAt: now,
      lastUsedAt: now,
    };

    if (updatedMemory.memoryType === "anchor") {
      updatedMemory.domain = "operational";
      updatedMemory.source =
        normalizedInput.source === "import-summary" || normalizedInput.source === "system-summary"
          ? normalizedInput.source
          : updatedMemory.source === "import-summary" || updatedMemory.source === "system-summary"
            ? updatedMemory.source
            : "system-summary";
      updatedMemory.confidenceScore = Math.max(0.85, updatedMemory.confidenceScore);
      updatedMemory.halfLifeDays = Math.max(180, updatedMemory.halfLifeDays);
      updatedMemory.requiresConfirmation = false;
      updatedMemory.status = "active";
      updatedMemory.intentBias = Math.min(0, updatedMemory.intentBias);
    }

    this.memories.set(existing.id, updatedMemory);
    this.scheduleMemoryPersistence();
    return updatedMemory;
  }

  async touchMemory(id: string): Promise<Memory | undefined> {
    const memory = this.memories.get(id);
    if (!memory) return undefined;
    if (memory.memoryType === "anchor") {
      const touchedAnchor: Memory = {
        ...memory,
        lastUsedAt: Date.now(),
      };
      this.memories.set(id, touchedAnchor);
      this.scheduleMemoryPersistence();
      return touchedAnchor;
    }

    // Spiral: enforce confidence decay for unconfirmed memory resurfacing.
    const now = Date.now();
    const unconfirmed =
      memory.requiresConfirmation &&
      memory.lastConfirmedAt <= memory.createdAt &&
      memory.status === "active";
    const resurfaceCount = unconfirmed ? memory.resurfaceCount + 1 : memory.resurfaceCount;
    const confidenceScore = unconfirmed
      ? Math.max(0.05, memory.confidenceScore - 0.02)
      : memory.confidenceScore;
    const confirmationPrompted =
      memory.confirmationPrompted || (unconfirmed && resurfaceCount >= 3);

    const touchedMemory: Memory = {
      ...memory,
      lastUsedAt: now,
      confidenceScore,
      resurfaceCount,
      confirmationPrompted,
    };

    this.memories.set(id, touchedMemory);
    this.scheduleMemoryPersistence();
    return touchedMemory;
  }

  async recordImportedConversations(count: number): Promise<void> {
    if (!Number.isFinite(count) || count <= 0) return;
    this.importState = {
      importedConversationCount: this.importState.importedConversationCount + Math.floor(count),
      lastImportAt: Date.now(),
      importedChatIds: this.importState.importedChatIds,
    };
    this.persistImportStateToDisk();
  }

  async recordImportedChatIds(chatIds: string[]): Promise<void> {
    if (!Array.isArray(chatIds) || chatIds.length === 0) return;
    const merged = Array.from(
      new Set([
        ...this.importState.importedChatIds,
        ...chatIds.filter((value): value is string => typeof value === "string" && value.length > 0),
      ]),
    );
    this.importState = {
      importedConversationCount: Math.max(this.importState.importedConversationCount, merged.length),
      lastImportAt: Date.now(),
      importedChatIds: merged,
    };
    this.persistImportStateToDisk();
  }

  async getImportedChatIds(): Promise<string[]> {
    return [...this.importState.importedChatIds];
  }

  async getImportedConversationCount(): Promise<number> {
    return this.importState.importedConversationCount;
  }

  async resetImportedConversationCount(): Promise<void> {
    this.importState = {
      importedConversationCount: 0,
      lastImportAt: 0,
      importedChatIds: [],
    };
    this.persistImportStateToDisk();
  }

  async upsertThreadTrace(input: {
    threadId: string;
    chatId: string;
    status?: ThreadTraceStatus;
    endState?: string;
    presenceSignature?: string;
    sigilState?: "aligned" | "misaligned";
    entryGate?: string;
    echoTraceId?: string;
  }): Promise<ThreadTrace | undefined> {
    const threadId = this.normalizeThreadId(input.threadId || "");
    const chatId = typeof input.chatId === "string" ? input.chatId.trim() : "";
    if (!threadId || !chatId) return undefined;

    const existing = this.threadTraces.get(threadId);
    const now = Date.now();
    const normalizedEndState =
      typeof input.endState === "string" && input.endState.trim()
        ? input.endState.trim().slice(0, 280)
        : existing?.endState;
    const fallbackStatus: ThreadTraceStatus =
      normalizedEndState && /\bsealed\b/i.test(normalizedEndState) ? "sealed" : "open";
    const status = this.normalizeThreadStatus(input.status, existing?.status || fallbackStatus);
    const presenceSignature =
      typeof input.presenceSignature === "string" && input.presenceSignature.trim()
        ? input.presenceSignature.trim().slice(0, 160)
        : existing?.presenceSignature;
    const sigilState =
      input.sigilState === "aligned" || input.sigilState === "misaligned"
        ? input.sigilState
        : existing?.sigilState;
    const entryGate =
      typeof input.entryGate === "string" && input.entryGate.trim()
        ? input.entryGate.trim().slice(0, 64)
        : existing?.entryGate;
    const echoTraceId =
      typeof input.echoTraceId === "string" && input.echoTraceId.trim()
        ? input.echoTraceId.trim().slice(0, 120)
        : existing?.echoTraceId;

    const trace: ThreadTrace = {
      threadId,
      chatId,
      status,
      endState: normalizedEndState,
      ...(presenceSignature ? { presenceSignature } : {}),
      ...(sigilState ? { sigilState } : {}),
      ...(entryGate ? { entryGate } : {}),
      ...(echoTraceId ? { echoTraceId } : {}),
      createdAt: existing?.createdAt || now,
      lastUpdatedAt: now,
    };

    this.threadTraces.set(threadId, trace);
    if (status === "open") {
      this.activeThreadByChat.set(chatId, threadId);
    } else {
      const current = this.activeThreadByChat.get(chatId);
      if (current === threadId) {
        this.activeThreadByChat.delete(chatId);
      }
    }

    this.persistThreadTracesToDisk();
    this.persistThreadTraceArtifact(trace);
    logTraceDebug("thread trace upserted", {
      threadId: trace.threadId,
      chatId: trace.chatId,
      status: trace.status,
      sigilState: trace.sigilState || "n/a",
      entryGate: trace.entryGate || "n/a",
      echoTraceId: trace.echoTraceId || "n/a",
    });
    return trace;
  }

  async getThreadTrace(threadId: string): Promise<ThreadTrace | undefined> {
    const normalized = this.normalizeThreadId(threadId || "");
    if (!normalized) return undefined;
    return this.threadTraces.get(normalized);
  }

  async listThreadTraces(): Promise<ThreadTrace[]> {
    return Array.from(this.threadTraces.values()).sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt);
  }

  async getTraceByChatId(chatId: string): Promise<ThreadTrace | undefined> {
    const normalizedChatId = chatId.trim();
    const matches = Array.from(this.threadTraces.values())
      .filter((trace) => trace.chatId === normalizedChatId)
      .sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt);
    return matches[0];
  }

  async setActiveThreadForChat(chatId: string, threadId: string): Promise<void> {
    const normalizedChatId = chatId.trim();
    const normalizedThreadId = this.normalizeThreadId(threadId || "");
    if (!normalizedChatId || !normalizedThreadId) return;
    if (!this.threadTraces.has(normalizedThreadId)) return;
    this.activeThreadByChat.set(normalizedChatId, normalizedThreadId);
    this.persistThreadTracesToDisk();
  }

  async clearActiveThreadForChat(chatId: string): Promise<void> {
    const normalizedChatId = chatId.trim();
    if (!normalizedChatId) return;
    this.activeThreadByChat.delete(normalizedChatId);
    this.persistThreadTracesToDisk();
  }

  async getActiveThreadForChat(chatId: string): Promise<string | undefined> {
    const normalizedChatId = chatId.trim();
    if (!normalizedChatId) return undefined;
    return this.activeThreadByChat.get(normalizedChatId);
  }
}

export const storage = new MemStorage();
