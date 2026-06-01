import { ChatWindow } from "@/components/chat-window";
import type React from "react";
import type { SigilName } from "@/lib/memory-fragments";

type EchoFieldProps = React.ComponentProps<typeof ChatWindow> & {
  activeSigil: SigilName;
};

export function EchoField({ activeSigil, ...props }: EchoFieldProps) {
  return (
    <div className="sigil-surface sigil-echo-field flex min-h-0 flex-1 flex-col" data-sigil={activeSigil}>
      <ChatWindow {...props} activeSigil={activeSigil} />
    </div>
  );
}
