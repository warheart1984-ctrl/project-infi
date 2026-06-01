import { Button } from "@/components/ui/button";

interface CutTheThreadProps {
  disabled?: boolean;
  onClick: () => void;
}

export function CutTheThread({ disabled, onClick }: CutTheThreadProps) {
  return (
    <Button size="sm" onClick={onClick} disabled={disabled} data-testid="button-cut-the-thread">
      Cut The Thread
    </Button>
  );
}
