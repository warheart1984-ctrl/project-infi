import { lazy, Suspense, useState } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";

const ImportDialogContent = lazy(async () => {
  const module = await import("@/components/import-dialog");
  return { default: module.ImportDialog };
});

interface LazyImportDialogProps {
  onImportComplete?: () => void;
}

export function LazyImportDialog({ onImportComplete }: LazyImportDialogProps) {
  const [shouldMount, setShouldMount] = useState(false);
  const [open, setOpen] = useState(false);

  const handleOpen = () => {
    if (!shouldMount) {
      setShouldMount(true);
    }
    setOpen(true);
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-start gap-2 text-muted-foreground"
        onClick={handleOpen}
        data-testid="button-import-chats"
      >
        <Upload className="h-4 w-4" />
        Import from Archive
      </Button>
      {shouldMount ? (
        <Suspense fallback={null}>
          <ImportDialogContent
            onImportComplete={onImportComplete}
            open={open}
            onOpenChange={setOpen}
            showTrigger={false}
          />
        </Suspense>
      ) : null}
    </>
  );
}
