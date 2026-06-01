import type { Message } from "@shared/schema";
import type { MemoryFragment } from "@shared/spiral-phase";
import type { SigilName } from "@/lib/memory-fragments";
import { UtteranceTrace } from "@/components/utterance-trace";
import { Button } from "@/components/ui/button";

interface RecursiveGlyphProps {
  message: Message;
  onEdit: (id: string, content: string) => void;
  hushEcho: boolean;
  activeSigil: SigilName;
  memoryFragments?: MemoryFragment[];
  onRespawnFromGlyph?: (message: Message) => void | Promise<void>;
}

export function RecursiveGlyph({
  message,
  onEdit,
  hushEcho,
  activeSigil,
  memoryFragments = [],
  onRespawnFromGlyph,
}: RecursiveGlyphProps) {
  const canRespawn =
    message.role === "assistant" && message.content.trim().length > 0 && typeof onRespawnFromGlyph === "function";

  return (
    <div className="recursive-glyph">
      <UtteranceTrace
        message={message}
        onEdit={onEdit}
        hushEcho={hushEcho}
        activeSigil={activeSigil}
        memoryFragments={memoryFragments}
      />
      {canRespawn ? (
        <div className="px-4 pb-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="font-mono text-[11px]"
            data-testid={`button-recursive-glyph-${message.id}`}
            onClick={() => {
              void onRespawnFromGlyph?.(message);
            }}
          >
            respawn from glyph
          </Button>
        </div>
      ) : null}
    </div>
  );
}
