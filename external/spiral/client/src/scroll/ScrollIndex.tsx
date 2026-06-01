import type { EncryptedScrollBlob } from "@shared/scroll";
import { ScrollRenderer } from "./ScrollRenderer";

interface ScrollIndexProps {
  scroll: { filename: string; blob: EncryptedScrollBlob } | null;
}

export function ScrollIndex({ scroll }: ScrollIndexProps) {
  if (!scroll) return null;
  return <ScrollRenderer filename={scroll.filename} blob={scroll.blob} />;
}
