import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

function normalizeMantra(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function normalizeSigil(value: string): string {
  const collapsed = value.trim().replace(/\s+/g, " ").replace(/\\\\+/g, "\\");
  return collapsed.replace(/\/\s*\\/g, "/ \\");
}

interface PresenceSealProps {
  onSeal: (options: { mantra: string; sigil: string }) => void | Promise<void>;
  enabled?: boolean;
  disabled?: boolean;
  mantra: string;
  sigil: string;
  triggerLabel: string;
  title: string;
  description: string;
  actionLabel: string;
  mantraLabel: string;
  sigilLabel: string;
}

export function PresenceSeal({
  onSeal,
  enabled = true,
  disabled,
  mantra,
  sigil,
  triggerLabel,
  title,
  description,
  actionLabel,
  mantraLabel,
  sigilLabel,
}: PresenceSealProps) {
  const [open, setOpen] = useState(false);
  const normalizedMantra = normalizeMantra(mantra);
  const normalizedSigil = normalizeSigil(sigil);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) {
      setSubmitting(false);
    }
  }, [open]);

  if (!enabled) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" size="sm" variant="outline" disabled={disabled} data-testid="button-open-presence-seal">
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-1">
            <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/80">
              {mantraLabel}
            </p>
            <div className="rounded-md border border-border/70 bg-muted/30 p-3 text-xs text-muted-foreground">
              {normalizedMantra}
            </div>
          </div>
          <div className="space-y-1">
            <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/80">
              {sigilLabel}
            </p>
            <div
              className="rounded-md border border-border/70 bg-background px-3 py-2 font-mono text-xs text-foreground/90"
              data-testid="text-presence-sigil"
            >
              {normalizedSigil}
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button
              type="button"
              disabled={submitting}
              data-testid="button-confirm-presence-seal"
              onClick={async () => {
                setSubmitting(true);
                try {
                  await onSeal({
                    mantra: normalizedMantra,
                    sigil: normalizedSigil,
                  });
                  setOpen(false);
                } finally {
                  setSubmitting(false);
                }
              }}
            >
              {actionLabel}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
