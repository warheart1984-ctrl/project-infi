import { User, Eye, Copy, Check, Pencil } from "lucide-react";
import { useMemo, useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { Message } from "@shared/schema";
import { cn } from "@/lib/utils";
import { spiralModeEnabled } from "@/lib/spiral-mode";
import { dreamRecall } from "@/lib/spiral-presence";

interface ChatMessageProps {
  message: Message;
  onEdit?: (id: string, newContent: string) => void;
  hushEcho?: boolean;
}

const USER_MARKDOWN_SIGNAL =
  /(```[\s\S]*?```|`[^`\n]+`|\*\*[^*\n]+\*\*|__[^_\n]+__|(^|\n)\s{0,3}([-*+]\s+|\d+\.\s+|>\s+|#{1,6}\s)|\[[^\]]+\]\([^)]+\))/m;

function shouldRenderUserMarkdown(content: string): boolean {
  return USER_MARKDOWN_SIGNAL.test(content);
}

function getDisplayRole(role: string): string {
  switch (role) {
    case "user":
      return "Witness";
    case "assistant":
      return "Echo";
    case "system":
      return "SpiralTrace";
    default:
      return role;
  }
}

function formatWhisperTimestamp(createdAt: number): string {
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function imageAttachmentsForMessage(message: Message) {
  if (!Array.isArray(message.attachments)) return [];
  return message.attachments.filter((attachment) => attachment.kind === "image");
}

export function ChatMessage({ message, onEdit, hushEcho = false }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isUser = message.role === "user";
  const isEcho = message.role === "assistant";
  const imageAttachments = imageAttachmentsForMessage(message);
  const hasImageAttachments = imageAttachments.length > 0;
  const isVeilSilence = isEcho && message.content.trim().length === 0 && !hasImageAttachments;
  const showHushEcho = hushEcho && isEcho && !isVeilSilence;
  const hushedContent = useMemo(() => {
    if (!showHushEcho) return message.content;
    return dreamRecall(message.content, 0.12);
  }, [message.content, showHushEcho]);
  const displayRole = getDisplayRole(message.role);
  const renderUserMarkdown = isUser && shouldRenderUserMarkdown(message.content);
  const whisperTimestamp = isEcho ? formatWhisperTimestamp(message.createdAt) : "";

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      textareaRef.current.focus();
    }
  }, [isEditing]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveEdit = () => {
    if (editContent.trim() !== message.content) {
      onEdit?.(message.id, editContent);
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditContent(message.content);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSaveEdit();
    } else if (e.key === "Escape") {
      handleCancelEdit();
    }
  };

  return (
    <div
      className={cn(
        "group flex gap-4 px-4 py-6",
        isUser ? "bg-transparent" : "bg-card/50"
      )}
      data-testid={`message-${message.id}`}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </div>

      <div className="flex-1 min-w-0 space-y-2">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="font-medium">{displayRole}</span>
          {isEcho && whisperTimestamp && (
            <span className="font-mono text-[11px]" data-testid={`text-whisper-timestamp-${message.id}`}>
              ⟡ {whisperTimestamp}
            </span>
          )}
        </div>
        <div
          className={cn(
            "prose-chat text-foreground",
            !isUser && spiralModeEnabled && "bg-sigil rounded-md px-3 py-2"
          )}
        >
          {hasImageAttachments && (
            <div className="mb-2 grid grid-cols-1 gap-2 sm:grid-cols-2" data-testid={`image-attachments-${message.id}`}>
              {imageAttachments.map((attachment) => (
                <a
                  key={attachment.id}
                  href={attachment.url}
                  target="_blank"
                  rel="noreferrer"
                  className="group/image block overflow-hidden rounded-md border border-border/70 bg-muted/20"
                >
                  <img
                    src={attachment.url}
                    alt={attachment.filename}
                    className="max-h-72 w-full object-cover transition-transform duration-200 group-hover/image:scale-[1.01]"
                    loading="lazy"
                  />
                  <div className="flex items-center justify-between gap-2 px-2 py-1 text-[10px] text-muted-foreground">
                    <span className="truncate">{attachment.filename}</span>
                    <span className="shrink-0">{Math.max(1, Math.round(attachment.bytes / 1024))}KB</span>
                  </div>
                </a>
              ))}
            </div>
          )}
          {isEditing ? (
            <div className="space-y-2">
              <Textarea
                ref={textareaRef}
                value={editContent}
                onChange={(e) => {
                  setEditContent(e.target.value);
                  e.target.style.height = "auto";
                  e.target.style.height = `${e.target.scrollHeight}px`;
                }}
                onKeyDown={handleKeyDown}
                className="min-h-[60px] resize-none bg-background"
              />
              <div className="flex gap-2 justify-end">
                <Button size="sm" variant="outline" onClick={handleCancelEdit}>
                  Cancel
                </Button>
                <Button size="sm" onClick={handleSaveEdit}>
                  Save & Submit
                </Button>
              </div>
            </div>
          ) : isVeilSilence ? (
            <p className="font-mono text-xs tracking-[0.18em] text-muted-foreground/80" data-testid={`text-veil-silence-${message.id}`}>
              ∅
            </p>
          ) : showHushEcho ? (
            <p className="font-mono text-xs text-muted-foreground/80" data-testid={`text-echo-hush-${message.id}`}>
              ∿ {hushedContent}
            </p>
          ) : message.content.trim().length === 0 && hasImageAttachments ? (
            <p className="font-mono text-xs text-muted-foreground/80">image attachment</p>
          ) : isUser && !renderUserMarkdown ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  const isInline = !match && !className;
                  
                  if (isInline) {
                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }

                  return (
                    <div className="relative group/code">
                      {match && (
                        <div className="absolute top-0 right-0 px-2 py-1 text-xs text-muted-foreground bg-muted rounded-bl-md rounded-tr-md">
                          {match[1]}
                        </div>
                      )}
                      <pre className="overflow-x-auto">
                        <code className={className} {...props}>
                          {children}
                        </code>
                      </pre>
                    </div>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        {spiralModeEnabled && message.trace && (
          <div className="text-xs text-muted-foreground mt-1">
            SpiralTrace - clarity: {message.trace.confidence.toFixed(2)}, mimicry:{" "}
            {message.trace.noMimicry ? "none" : "detected"}
          </div>
        )}
      </div>

      {!isEditing && (
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
          {isUser && onEdit && !hasImageAttachments && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setIsEditing(true)}
              data-testid={`button-edit-message-${message.id}`}
            >
              <Pencil className="h-4 w-4 text-muted-foreground" />
            </Button>
          )}
          {message.content.trim().length > 0 && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleCopy}
              data-testid={`button-copy-message-${message.id}`}
            >
              {copied ? (
                <Check className="h-4 w-4 text-primary" />
              ) : (
                <Copy className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export function StreamingMessage() {
  return (
    <div className="group flex gap-4 px-4 py-6 bg-card/50" data-testid="streaming-message">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
        <Eye className="h-4 w-4" />
      </div>

      <div className="flex-1 min-w-0 space-y-2">
        <div className="font-medium text-sm text-muted-foreground">{getDisplayRole("assistant")}</div>
        <div
          className={cn(
            "prose-chat text-foreground",
            spiralModeEnabled && "bg-sigil rounded-md px-3 py-2"
          )}
        >
          <p className="font-mono text-xs tracking-[0.14em] text-muted-foreground">listening</p>
        </div>
      </div>
    </div>
  );
}
