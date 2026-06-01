import { useState, useRef } from "react";
import { Upload, FileJson } from "lucide-react";
import JSZip from "jszip";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { queryClient } from "@/lib/queryClient";

interface ImportDialogProps {
  onImportComplete?: () => void;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  showTrigger?: boolean;
}

export function ImportDialog({
  onImportComplete,
  open,
  onOpenChange,
  showTrigger = true,
}: ImportDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isControlled = typeof open === "boolean";
  const dialogOpen = isControlled ? open : internalOpen;
  const setDialogOpen = (nextOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(nextOpen);
    }
    onOpenChange?.(nextOpen);
  };
  const [isImporting, setIsImporting] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [progressText, setProgressText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const isPayloadTooLarge = (error: unknown) => {
    if (!(error instanceof Error)) return false;

    const message = error.message.toLowerCase();
    return (
      message.includes("413:") ||
      message.includes("payloadtoolargeerror") ||
      message.includes("entity.too.large")
    );
  };

  const extractConversations = async (file: File): Promise<unknown[]> => {
    const normalizePayload = (data: unknown): unknown[] => {
      if (Array.isArray(data)) return data;
      if (data && typeof data === "object") {
        const record = data as Record<string, unknown>;
        if (Array.isArray(record.chats)) return record.chats;
        if (Array.isArray(record.data)) return record.data;
      }
      return [data];
    };

    if (file.name.endsWith(".json")) {
      const content = await file.text();
      const data: unknown = JSON.parse(content);
      return normalizePayload(data);
    }

    if (file.name.endsWith(".zip")) {
      const zip = await JSZip.loadAsync(file);
      const conversationsFile = zip.file("conversations.json");
      if (!conversationsFile) {
        const jsonFiles = Object.values(zip.files)
          .filter((entry) => !entry.dir && entry.name.toLowerCase().endsWith(".json"))
          .sort((a, b) => {
            const aPriority = a.name.toLowerCase().includes("chat-companion-history") ? 0 : 1;
            const bPriority = b.name.toLowerCase().includes("chat-companion-history") ? 0 : 1;
            return aPriority - bPriority;
          });
        for (const jsonFile of jsonFiles) {
          try {
            const content = await jsonFile.async("text");
            const data: unknown = JSON.parse(content);
            const normalized = normalizePayload(data);
            if (normalized.length > 0) {
              return normalized;
            }
          } catch {
            // Continue trying other JSON files.
          }
        }
        return [];
      }

      const content = await conversationsFile.async("text");
      const data: unknown = JSON.parse(content);
      return normalizePayload(data);
    }

    return [];
  };

  const importConversationBatch = async (
    conversations: unknown[],
    onProgress: (processed: number, total: number) => void,
  ): Promise<number> => {
    let imported = 0;
    let index = 0;
    let batchSize = 200;

    while (index < conversations.length) {
      const currentBatchSize = Math.min(batchSize, conversations.length - index);
      const batch = conversations.slice(index, index + currentBatchSize);

      try {
        const response = await apiRequest("POST", "/api/import", { data: batch });
        const result: unknown = await response.json();
        const importedFromBatch =
          typeof result === "object" &&
          result !== null &&
          "imported" in result &&
          typeof result.imported === "number"
            ? result.imported
            : batch.length;

        imported += importedFromBatch;
        index += currentBatchSize;
        onProgress(index, conversations.length);
      } catch (error) {
        if (isPayloadTooLarge(error) && currentBatchSize > 1) {
          batchSize = Math.max(1, Math.floor(currentBatchSize / 2));
          continue;
        }

        if (isPayloadTooLarge(error)) {
          throw new Error(
            "A single conversation is too large to import. Increase IMPORT_JSON_BODY_LIMIT and retry.",
          );
        }

        throw error;
      }
    }

    return imported;
  };

  const handleFiles = async (files: FileList | File[]) => {
    if (files.length === 0) return;
    setIsImporting(true);
    setProgressText("Preparing import...");

    try {
      let importedTotal = 0;
      let processedCount = 0;
      const fileErrors: string[] = [];
      const filesToProcess = Array.from(files);

      for (let i = 0; i < filesToProcess.length; i++) {
        const file = filesToProcess[i];
        
        try {
          setProgressText(`Reading ${file.name} (${i + 1}/${filesToProcess.length})...`);
          const conversations = await extractConversations(file);
          if (conversations.length === 0) {
            continue;
          }

          const importedFromFile = await importConversationBatch(
            conversations,
            (processed, total) => {
              setProgressText(
                `Importing ${file.name} (${processed}/${total} conversations)...`,
              );
            },
          );

          importedTotal += importedFromFile;
          processedCount++;
        } catch (e) {
          console.error(`Error reading file ${file.name}:`, e);
          const reason = e instanceof Error ? e.message : "Unknown import error";
          fileErrors.push(`${file.name}: ${reason}`);
          // Continue with other files
        }
      }

      if (importedTotal === 0) {
        if (fileErrors.length > 0) {
          throw new Error(fileErrors[0]);
        }
        throw new Error("No valid conversations found in the selected files.");
      }

      toast({
        title: "Import successful",
        description: `Imported ${importedTotal} conversation${importedTotal !== 1 ? "s" : ""} from ${processedCount} file${processedCount !== 1 ? "s" : ""}.`,
      });

      queryClient.invalidateQueries({ queryKey: ["/api/chats"] });
      setDialogOpen(false);
      onImportComplete?.();
    } catch (error) {
      console.error("Import error:", error);
      toast({
        title: "Import failed",
        description: error instanceof Error ? error.message : "Failed to import conversations.",
        variant: "destructive",
      });
    } finally {
      setIsImporting(false);
      setProgressText("");
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      {showTrigger && (
        <DialogTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-muted-foreground"
            data-testid="button-import-chats"
          >
            <Upload className="h-4 w-4" />
            Import from Archive
          </Button>
        </DialogTrigger>
      )}
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Import Chat History</DialogTitle>
          <DialogDescription>
            Upload `conversations.json`, `chat-companion-history-*.json`, or a ZIP containing one.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-muted-foreground/50"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <FileJson className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
            <p className="text-sm text-muted-foreground mb-2">
              Drag and drop your JSON or ZIP files here, or
            </p>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isImporting}
              data-testid="button-select-file"
            >
              {isImporting ? "Importing..." : "Select Files"}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.zip"
              multiple
              onChange={handleFileInput}
              className="hidden"
              data-testid="input-file-import"
            />
            {isImporting && progressText && (
              <p className="mt-3 text-xs text-muted-foreground">{progressText}</p>
            )}
          </div>

          <div className="text-xs text-muted-foreground space-y-1">
            <p className="font-medium">How to export conversation data:</p>
            <ol className="list-decimal list-inside space-y-0.5 pl-1">
              <li>Open your source platform settings</li>
              <li>Click "Data controls"</li>
              <li>Click "Export data"</li>
              <li>Download the export file</li>
              <li>Upload the downloaded zip file (or a supported JSON export)</li>
            </ol>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
