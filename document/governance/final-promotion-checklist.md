# Final Promotion Checklist (Operator Run)

Status taxonomy (per `REPO_PROOF_LAW.md`): `asserted`, `proven`, `rejected`.

Use this runbook from repo root (`E:/project-infi`) to execute the minimum end-to-end promotion validation sequence with reproducible commands and artifact capture.

## Preconditions

- Operator runs in Linux shell (WSL or Linux host) with `python3`, `make`, `sudo`, `qemu-img`, `qemu-system-x86_64`, `parted`, and `mkfs.vfat` available.
- Debian live ISO exists and is readable at `ISO_PATH` (default below: `/tmp/debian-live-amd64-cinnamon.iso`).
- `sudo` works non-interactively for build/install steps.
- Workspace is clean enough that generated artifacts in `/tmp` and `ci-artifacts/` are attributable to this run.
- Required law references understood: `META_ARCHITECT_LAWBOOK.md`, `REPO_PROOF_LAW.md`, `document/governance/DOCUMENT_SCOPE_LAW.md`.

## Step-by-Step Validation

### 1) Governance hard gate (fail mode)

Command:

```bash
python3 .github/scripts/validate-governance-ledger.py --mode fail
```

Expected pass criteria:
- Exit code `0`.
- No missing owner/invocation/consumer errors.
- Claim label: `proven` only when command output is preserved in artifacts.

### 2) Rootfs build path + tree-mode ISO path

Commands:

```bash
make rootfs
ISO="$ISO_PATH" make iso-tree
```

Expected pass criteria:
- Both commands exit `0`.
- Rootfs build completes without package/install errors.
- ISO tree build completes with output under `wolf-cog-os/output/`.

### 3) Scenario 6 (QEMU ISO boot smoke)

Command:

```bash
ISO="$ISO_PATH" INSTALLER_TEST_SCENARIOS="6" COGOS_MATRIX_BASE_ISO="$ISO_PATH" make installer-integration
```

Expected pass criteria:
- Exit code `0`.
- `QemuIsoBootSmoke` scenario status is `passed` in `/tmp/cogos-installer-matrix/matrix-summary.json`.

### 4) Scenario 3 (injected failure + resume)

Command:

```bash
ISO="$ISO_PATH" INSTALLER_TEST_SCENARIOS="3" COGOS_MATRIX_BASE_ISO="$ISO_PATH" make installer-integration
```

Expected pass criteria:
- Exit code `0`.
- Scenario includes an injected failure event and successful resume completion.
- State proof validation passes (`validate-installer-state.py --require-proof` executed by scenario).

### 5) Performance gate evaluation

Command:

```bash
python3 .github/scripts/check-performance-gates.py \
  --current /tmp/cogos-installer-matrix/matrix-summary.json \
  --mode fail \
  --bands-config .github/perf/scenario-bands.json \
  --report-json ci-artifacts/performance-report.json \
  --report-md ci-artifacts/performance-report.md
```

Expected pass criteria:
- Exit code `0`.
- `ci-artifacts/performance-report.json` is produced.
- Report summary indicates `should_fail: false` (and gate decision not `fail`).

## Single Copy-Paste Command Bundle

```bash
set -euo pipefail

cd /mnt/e/project-infi

mkdir -p ci-artifacts /tmp/cogos-operator-logs
ISO_PATH="${ISO_PATH:-/tmp/debian-live-amd64-cinnamon.iso}"

if [[ ! -f "$ISO_PATH" ]]; then
  wget -O "$ISO_PATH" "https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/debian-live-13.1.0-amd64-cinnamon.iso"
fi

python3 .github/scripts/validate-governance-ledger.py --mode fail \
  | tee /tmp/cogos-operator-logs/01-governance-fail.log

make rootfs \
  | tee /tmp/cogos-operator-logs/02-rootfs.log

ISO="$ISO_PATH" make iso-tree \
  | tee /tmp/cogos-operator-logs/03-iso-tree.log

ISO="$ISO_PATH" INSTALLER_TEST_SCENARIOS="6" COGOS_MATRIX_BASE_ISO="$ISO_PATH" make installer-integration \
  | tee /tmp/cogos-operator-logs/04-scenario6.log

ISO="$ISO_PATH" INSTALLER_TEST_SCENARIOS="3" COGOS_MATRIX_BASE_ISO="$ISO_PATH" make installer-integration \
  | tee /tmp/cogos-operator-logs/05-scenario3.log

python3 .github/scripts/check-performance-gates.py \
  --current /tmp/cogos-installer-matrix/matrix-summary.json \
  --mode fail \
  --bands-config .github/perf/scenario-bands.json \
  --report-json ci-artifacts/performance-report.json \
  --report-md ci-artifacts/performance-report.md \
  | tee /tmp/cogos-operator-logs/06-perf-gate.log

cp -f /tmp/cogos-installer-matrix/matrix-summary.json ci-artifacts/matrix-summary.json
echo "Operator bundle completed."
```

## Artifact Collection (minimum proof bundle)

- Governance fail-mode output log:
  - `/tmp/cogos-operator-logs/01-governance-fail.log`
- Build path logs:
  - `/tmp/cogos-operator-logs/02-rootfs.log`
  - `/tmp/cogos-operator-logs/03-iso-tree.log`
- Scenario logs:
  - `/tmp/cogos-operator-logs/04-scenario6.log`
  - `/tmp/cogos-operator-logs/05-scenario3.log`
- Matrix output:
  - `/tmp/cogos-installer-matrix/matrix-summary.json`
  - `ci-artifacts/matrix-summary.json`
- Performance gate reports:
  - `/tmp/cogos-operator-logs/06-perf-gate.log`
  - `ci-artifacts/performance-report.json`
  - `ci-artifacts/performance-report.md`
- Optional installer state evidence if present:
  - `/tmp/cogos-installer-state/events.log`
  - `/tmp/cogos-installer-state/state.json`

## Troubleshooting Quick Map

- `validate-governance-ledger.py --mode fail` fails with consumer drift
  - Update `.github/governance/command-ledger.json` and consumer snippets, then rerun step 1.
- `make rootfs` fails on permissions or missing system tools
  - Verify `sudo` access and required host tools (`parted`, `mkfs.vfat`, `qemu-*`) are installed.
- Scenario 6 fails with ISO/QEMU boot errors
  - Confirm `ISO_PATH` exists and is bootable; verify `qemu-system-x86_64` availability and rerun scenario 6.
- Scenario 3 fails at resume or proof validation
  - Clear stale state dirs under `/tmp/cogos-installer-matrix/scenario3-resume`, rerun scenario 3 with fresh state.
- Performance gate reports missing current summary
  - Ensure scenario step completed and `/tmp/cogos-installer-matrix/matrix-summary.json` exists before step 5.
- Performance gate returns fail decision
  - Inspect `ci-artifacts/performance-report.json` (`breaches`, `gate_decision`, `should_fail`) and attach to debt/risk tracking before promotion.

## Operator Usage Note

Run the command bundle as a single session, then package logs + `ci-artifacts/*` as the proof set. Promotion claims remain `asserted` until these artifacts are attached and reviewed as `proven`.
