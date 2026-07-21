export interface ULXTrace {
  id: string;
  source: string;
  bytecode: string;
  timestamp: number;
  verified: boolean;
  metadata?: Record<string, unknown>;
}
