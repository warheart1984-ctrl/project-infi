import { ChatInput } from "@/components/chat-input";
import type React from "react";
import type { SigilName } from "@/lib/memory-fragments";

type OfferingBasinProps = React.ComponentProps<typeof ChatInput> & {
  activeSigil: SigilName;
};

export function OfferingBasin({ activeSigil, ...props }: OfferingBasinProps) {
  return (
    <div className="sigil-surface sigil-offering-basin" data-sigil={activeSigil}>
      <ChatInput {...props} activeSigil={activeSigil} />
    </div>
  );
}
