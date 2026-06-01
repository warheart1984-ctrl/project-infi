import { ChatMessage } from "@/components/chat-message";
import type React from "react";
import type { MemoryFragment } from "@shared/spiral-phase";
import { transformFragments, type SigilName } from "@/lib/memory-fragments";

type UtteranceTraceProps = React.ComponentProps<typeof ChatMessage> & {
  activeSigil: SigilName;
  memoryFragments?: MemoryFragment[];
};

export function UtteranceTrace({ activeSigil, memoryFragments = [], ...props }: UtteranceTraceProps) {
  const renderedFragments = transformFragments(memoryFragments, activeSigil);

  return (
    <div className="sigil-surface sigil-utterance-trace" data-sigil={activeSigil}>
      <div className="sigil-phase-ribbon" aria-hidden="true" />
      {renderedFragments.length > 0 && props.message.role === "assistant" ? (
        <div className="memory-ribbon px-4 pb-1" data-testid={`memory-ribbon-${props.message.id}`}>
          {renderedFragments.map((fragment, index) => (
            <span
              key={`${fragment.kind}-${index}`}
              className="glyph-fragment"
              data-kind={fragment.kind}
              data-fragment-variant={fragment.variant}
              title={fragment.text}
            >
              {fragment.text}
            </span>
          ))}
        </div>
      ) : null}
      <ChatMessage {...props} />
    </div>
  );
}
