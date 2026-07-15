import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

type VerificationItem = {
  status?: string;
  evidence?: string[];
  notes?: string[];
};

type SliceStatus = {
  sliceId: string;
  name: string;
  version?: string;
  currentStatus: string;
  owningCisRequirements?: string[];
  companionSpecification?: string[];
  buildVerification?: VerificationItem;
  testVerification?: VerificationItem;
  runtimeVerification?: VerificationItem;
  conformanceVerification?: VerificationItem;
  replayVerification?: VerificationItem;
  evidencePackageReference?: string | null;
  constitutionalReceiptReference?: string | null;
  conformanceRecordReference?: string | null;
  replayVerificationRecordReference?: string | null;
  dependencies?: string[];
  acceptanceCriteria?: string[];
  lastVerificationTimestamp?: string | null;
};

type StatusSpec = {
  displayName: string;
  version: string;
  status: string;
  purpose: string;
  derivedFrom: string;
  statusModel: {
    states: string[];
    evidenceGates: string[];
  };
  slices: SliceStatus[];
};

function countByStatus(slices: SliceStatus[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const slice of slices) {
    counts.set(slice.currentStatus, (counts.get(slice.currentStatus) ?? 0) + 1);
  }
  return counts;
}

function formatList(values: string[] | undefined | null): string {
  if (!values || values.length === 0) {
    return 'None';
  }
  return values.join('; ');
}

function formatVerification(item: VerificationItem | undefined): string {
  if (!item) {
    return 'Not started';
  }
  const status = item.status ?? 'Not started';
  const evidence = formatList(item.evidence ?? []);
  return `${status} :: Evidence: ${evidence}`;
}

function renderDashboard(spec: StatusSpec): string {
  const counts = countByStatus(spec.slices);
  const generatedAt = new Date().toISOString();

  const summaryRows = spec.statusModel.states.map((state) => {
    return `| ${state} | ${String(counts.get(state) ?? 0)} |`;
  }).join('\n');

  const sliceRows = spec.slices.map((slice) => {
    return [
      `| ${slice.sliceId}-build | Build | ${slice.buildVerification?.status ?? 'Not started'} | ${formatList(slice.buildVerification?.evidence)} |`,
      `| ${slice.sliceId}-test | Test | ${slice.testVerification?.status ?? 'Not started'} | ${formatList(slice.testVerification?.evidence)} |`,
      `| ${slice.sliceId}-runtime | Runtime | ${slice.runtimeVerification?.status ?? 'Not started'} | ${formatList(slice.runtimeVerification?.evidence)} |`,
      `| ${slice.sliceId}-conformance | Conformance | ${slice.conformanceVerification?.status ?? 'Not started'} | ${formatList(slice.conformanceVerification?.evidence)} |`,
      `| ${slice.sliceId}-replay | Replay | ${slice.replayVerification?.status ?? 'Not started'} | ${formatList(slice.replayVerification?.evidence)} |`,
    ].join('\n');
  }).join('\n');

  return [
    '# CORI Alpha Minimal Runtime Dashboard',
    '',
    `**Source:** [CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json](CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json)`,
    `**Generated:** ${generatedAt}`,
    `**Purpose:** ${spec.purpose}`,
    `**Status:** ${spec.status}`,
    `**Derived from:** ${spec.derivedFrom}`,
    '',
    '## Status Model',
    '',
    `Allowed states: ${spec.statusModel.states.join(', ')}`,
    '',
    '| State | Count |',
    '|---|---|',
    summaryRows,
    '',
    '## Slice Overview',
    '',
    '| Slice ID | Slice Name | Current Status | Owning CIS Requirement(s) | Dependencies | Last Verification Timestamp |',
    '|---|---|---|---|---|---|',
    spec.slices
      .map((slice) => `| ${slice.sliceId} | ${slice.name} | ${slice.currentStatus} | ${formatList(slice.owningCisRequirements)} | ${formatList(slice.dependencies)} | ${slice.lastVerificationTimestamp ?? 'Not recorded'} |`)
      .join('\n'),
    '',
    '## Slice Artifacts',
    '',
    '| Slice ID | Constitutional Receipt | Evidence Package | Conformance Record | Replay Verification Record |',
    '|---|---|---|---|---|',
    spec.slices
      .map(
        (slice) =>
          `| ${slice.sliceId} | ${slice.constitutionalReceiptReference ?? 'Not recorded'} | ${slice.evidencePackageReference ?? 'Not recorded'} | ${slice.conformanceRecordReference ?? 'Not recorded'} | ${slice.replayVerificationRecordReference ?? 'Not recorded'} |`,
      )
      .join('\n'),
    '',
    '## Verification Details',
    '',
    '| Slice Key | Gate | Status | Evidence |',
    '|---|---|---|---|',
    sliceRows,
    '',
    '## Acceptance Notes',
    '',
    ...spec.slices.map((slice) => `- **${slice.name}**: ${formatList(slice.acceptanceCriteria)}`),
    '',
    '## Dashboard Rule',
    '',
    'This view is generated from the status companion and should be regenerated rather than edited by hand.',
    '',
  ].join('\n');
}

function main() {
  const specPath = resolve(process.cwd(), 'docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json');
  const outputPath = resolve(process.cwd(), 'docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_DASHBOARD.md');
  const spec = JSON.parse(readFileSync(specPath, 'utf8')) as StatusSpec;
  const markdown = renderDashboard(spec);
  writeFileSync(outputPath, `${markdown}\n`, 'utf8');
  console.log(`rendered CORI Alpha dashboard: ${outputPath}`);
}

main();
