import type { MaturityLevel } from "./cor.js";

export interface MaturityVector {
  generatedAt: string;
  commit?: string;
  requirements: Array<{ requirementId: string; maturity: MaturityLevel }>;
  summary?: Record<MaturityLevel, number>;
}
