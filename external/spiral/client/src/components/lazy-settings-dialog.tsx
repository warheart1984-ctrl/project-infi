import { lazy, Suspense, useState, type ComponentProps } from "react";
import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ExecutorProviderSettings, ProviderSettings } from "@shared/schema";

const SettingsDialogContent = lazy(async () => {
  const module = await import("@/components/settings-dialog");
  return { default: module.SettingsDialog };
});

interface LazySettingsDialogProps {
  runtimeSettings: ProviderSettings | null;
  executorSettings: ExecutorProviderSettings | null;
  onSave: (settings: {
    runtimeProviderSettings: ProviderSettings;
    executorProviderSettings: ExecutorProviderSettings | null;
  }) => void;
  triggerLabel?: string;
  triggerVariant?: ComponentProps<typeof Button>["variant"];
  triggerSize?: ComponentProps<typeof Button>["size"];
  triggerClassName?: string;
}

export function LazySettingsDialog({
  runtimeSettings,
  executorSettings,
  onSave,
  triggerLabel,
  triggerVariant,
  triggerSize,
  triggerClassName,
}: LazySettingsDialogProps) {
  const [shouldMount, setShouldMount] = useState(false);
  const [open, setOpen] = useState(false);
  const iconOnly = !triggerLabel;

  const handleOpen = () => {
    if (!shouldMount) {
      setShouldMount(true);
    }
    setOpen(true);
  };

  return (
    <>
      <Button
        variant={triggerVariant || "ghost"}
        size={triggerSize || (iconOnly ? "icon" : "sm")}
        onClick={handleOpen}
        className={[triggerLabel ? "gap-2" : "", triggerClassName || ""].filter(Boolean).join(" ")}
        data-testid="button-settings"
      >
        <Settings className="h-5 w-5" />
        {triggerLabel ? <span>{triggerLabel}</span> : null}
      </Button>
      {shouldMount ? (
        <Suspense fallback={null}>
          <SettingsDialogContent
            runtimeSettings={runtimeSettings}
            executorSettings={executorSettings}
            onSave={onSave}
            open={open}
            onOpenChange={setOpen}
            showTrigger={false}
          />
        </Suspense>
      ) : null}
    </>
  );
}
