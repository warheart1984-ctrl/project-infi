import { randomUUID } from "crypto";
import { mkdir, readFile, unlink, writeFile } from "fs/promises";
import path from "path";
import type { MessageAttachment } from "@shared/schema";

const CHAT_ATTACHMENT_DIR = path.join(process.cwd(), ".local", "chat-attachments");
const CHAT_ATTACHMENT_MAX_BYTES = Math.max(
  256 * 1024,
  Number.parseInt(process.env.CHAT_ATTACHMENT_MAX_BYTES || String(8 * 1024 * 1024), 10) ||
    8 * 1024 * 1024,
);
const SUPPORTED_IMAGE_CONTENT_TYPES = new Set<string>([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
]);
const ATTACHMENT_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class ChatAttachmentError extends Error {
  statusCode: number;

  constructor(statusCode: number, message: string) {
    super(message);
    this.name = "ChatAttachmentError";
    this.statusCode = statusCode;
  }
}

function normalizeContentType(value: string | undefined): string {
  return (value || "")
    .split(";")[0]
    .trim()
    .toLowerCase();
}

function extensionFromContentType(contentType: string): string {
  switch (contentType) {
    case "image/jpeg":
      return "jpg";
    case "image/png":
      return "png";
    case "image/webp":
      return "webp";
    case "image/gif":
      return "gif";
    default:
      return "img";
  }
}

function sanitizeFilename(value: string | undefined, fallbackExtension: string): string {
  const decoded = (() => {
    const raw = (value || "").trim();
    if (!raw) return "";
    try {
      return decodeURIComponent(raw);
    } catch {
      return raw;
    }
  })();
  const baseName = path.basename(decoded);
  const cleaned = baseName
    .replace(/[\u0000-\u001F\u007F]/g, "")
    .replace(/[^a-zA-Z0-9._-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 180);
  if (!cleaned) {
    return `attachment.${fallbackExtension}`;
  }
  if (!/\.[a-z0-9]{2,6}$/i.test(cleaned)) {
    return `${cleaned}.${fallbackExtension}`;
  }
  return cleaned;
}

export function getChatAttachmentLimitBytes(): number {
  return CHAT_ATTACHMENT_MAX_BYTES;
}

export function isValidAttachmentId(value: string): boolean {
  return ATTACHMENT_ID_PATTERN.test(value);
}

export function getChatAttachmentPath(attachmentId: string): string {
  return path.join(CHAT_ATTACHMENT_DIR, `${attachmentId}.bin`);
}

export async function createImageAttachment(input: {
  contentType: string | undefined;
  filename: string | undefined;
  bytes: Buffer;
}): Promise<MessageAttachment> {
  const normalizedContentType = normalizeContentType(input.contentType);
  if (!SUPPORTED_IMAGE_CONTENT_TYPES.has(normalizedContentType)) {
    throw new ChatAttachmentError(
      415,
      "Unsupported image type. Allowed: image/jpeg, image/png, image/webp, image/gif.",
    );
  }

  if (!Buffer.isBuffer(input.bytes) || input.bytes.length === 0) {
    throw new ChatAttachmentError(400, "Attachment body is empty.");
  }

  if (input.bytes.length > CHAT_ATTACHMENT_MAX_BYTES) {
    throw new ChatAttachmentError(
      413,
      `Attachment exceeds max size of ${Math.floor(CHAT_ATTACHMENT_MAX_BYTES / (1024 * 1024))}MB.`,
    );
  }

  const attachmentId = randomUUID();
  const extension = extensionFromContentType(normalizedContentType);
  const filename = sanitizeFilename(input.filename, extension);
  const uploadedAt = Date.now();

  await mkdir(CHAT_ATTACHMENT_DIR, { recursive: true });
  await writeFile(getChatAttachmentPath(attachmentId), input.bytes);

  return {
    id: attachmentId,
    kind: "image",
    filename,
    contentType: normalizedContentType,
    bytes: input.bytes.length,
    url: `/api/attachments/${encodeURIComponent(attachmentId)}`,
    uploadedAt,
  };
}

export async function readMessageAttachmentBytes(
  attachment: MessageAttachment,
): Promise<Buffer | null> {
  if (!attachment || attachment.kind !== "image") return null;
  if (!isValidAttachmentId(attachment.id)) return null;
  try {
    return await readFile(getChatAttachmentPath(attachment.id));
  } catch {
    return null;
  }
}

export async function deleteAttachmentById(attachmentId: string): Promise<void> {
  if (!isValidAttachmentId(attachmentId)) return;
  try {
    await unlink(getChatAttachmentPath(attachmentId));
  } catch {
    // Ignore missing files during cleanup.
  }
}
