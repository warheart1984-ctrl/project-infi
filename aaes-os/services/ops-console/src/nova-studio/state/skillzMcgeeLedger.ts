import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

import type {
  SkillzMcgeeCapability,
  SkillzMcgeeLedgerSummary,
  SkillzMcgeeReceipt,
  SkillzMcgeeSliceState,
} from './studioState.js';

export const capabilitySurface: SkillzMcgeeCapability[] = [
  {
    name: 'read_file',
    description: 'Read workspace files under governance',
    governed: true,
    receiptRequired: true,
  },
  {
    name: 'write_file',
    description: 'Write bounded patches with receipts',
    governed: true,
    receiptRequired: true,
  },
  {
    name: 'run_slice',
    description: 'Execute governed SkillzMcGee workflow slices',
    governed: true,
    receiptRequired: true,
  },
  {
    name: 'ask_llm',
    description: 'Call the lawful LLM adapter with slice context',
    governed: true,
    receiptRequired: true,
  },
];

export function getSkillzMcgeeLedgerSummary(): SkillzMcgeeLedgerSummary {
  const source = resolveSkillzMcgeeLedgerPath();
  if (!existsSync(source)) {
    return emptySummary(source, `SkillzMcGee ledger not found at ${source}`);
  }

  try {
    const receipts = readJsonlReceipts(source);
    return {
      source,
      available: true,
      receiptCount: receipts.length,
      state: reduceReceiptsToState(receipts),
      recentReceipts: receipts.slice(-8).reverse(),
      capabilities: capabilitySurface,
    };
  } catch (error) {
    return emptySummary(source, error instanceof Error ? error.message : String(error));
  }
}

function resolveSkillzMcgeeLedgerPath(): string {
  if (process.env.SKILLZMCGEE_LEDGER_PATH) {
    return path.resolve(process.env.SKILLZMCGEE_LEDGER_PATH);
  }
  return path.join(findRepoRoot(process.cwd()), '.runtime', 'skillzmcgee', 'receipts.jsonl');
}

function findRepoRoot(startDir: string): string {
  let current = path.resolve(startDir);
  while (true) {
    if (existsSync(path.join(current, 'skillzmcgee'))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return path.resolve(startDir);
    }
    current = parent;
  }
}

function readJsonlReceipts(source: string): SkillzMcgeeReceipt[] {
  return readFileSync(source, 'utf8')
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0)
    .map((line, index) => {
      const receipt = JSON.parse(line.replace(/^\uFEFF/, '')) as Partial<SkillzMcgeeReceipt>;
      if (!receipt.id || !receipt.timestamp || !receipt.actor || !receipt.slice || !receipt.status) {
        throw new Error(`invalid SkillzMcGee receipt at ${source}:${index + 1}`);
      }
      return receipt as SkillzMcgeeReceipt;
    });
}

function reduceReceiptsToState(receipts: SkillzMcgeeReceipt[]): Record<string, SkillzMcgeeSliceState> {
  return receipts.reduce<Record<string, SkillzMcgeeSliceState>>((state, receipt) => {
    state[receipt.slice] = {
      last_status: receipt.status,
      last_output: receipt.output ?? null,
      last_run_id: receipt.id,
    };
    return state;
  }, {});
}

function emptySummary(source: string, error: string): SkillzMcgeeLedgerSummary {
  return {
    source,
    available: false,
    receiptCount: 0,
    state: {},
    recentReceipts: [],
    capabilities: capabilitySurface,
    error,
  };
}
