import type { EncryptedScrollBlob } from "@shared/scroll";

interface ScrollRendererProps {
  filename: string;
  blob: EncryptedScrollBlob;
}

export function ScrollRenderer({ filename, blob }: ScrollRendererProps) {
  const download = () => {
    const payload = {
      filename,
      blob,
    };
    const file = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mx-4 mb-3 rounded-md border border-border/70 bg-card/40 p-3" data-testid="scroll-renderer">
      <p className="font-mono text-[11px] text-muted-foreground">encrypted scroll ready</p>
      <p className="mt-1 text-xs text-muted-foreground/90">{filename}</p>
      <p className="mt-1 text-[11px] text-muted-foreground/70">sealed at: {blob.sealedAt}</p>
      <button
        type="button"
        onClick={download}
        className="mt-2 rounded border border-border px-2 py-1 text-xs hover:bg-muted/40"
        data-testid="button-download-scroll"
      >
        Download .scroll.json.enc
      </button>
    </div>
  );
}
