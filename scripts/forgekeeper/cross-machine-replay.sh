#!/usr/bin/env bash
# Forgekeeper cross-machine replay driver (inactive by default).
# Requires: FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1 and filled REPLAY_MANIFEST.json

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MANIFEST_PATH="${REPO_ROOT}/docs/proof/bumblebee-forge/cross_machine/REPLAY_MANIFEST.json"

if [[ "${FORGE_CROSS_MACHINE_REPLAY_ACTIVE:-}" != "1" ]]; then
  printf '%s\n' '{"status":"inactive","claim_label":"asserted","message":"Cross-machine replay is built but not active. Set FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1 to run."}'
  exit 0
fi

if [[ ! -f "${MANIFEST_PATH}" ]]; then
  echo "REPLAY_MANIFEST.json missing. Copy REPLAY_MANIFEST.template.json and fill it first." >&2
  exit 2
fi

status="$(python3 -c "import json; print(json.load(open('${MANIFEST_PATH}')).get('status','inactive'))")"
if [[ "${status}" == "inactive" ]]; then
  echo "REPLAY_MANIFEST.json status is still inactive. Set status to active before replay." >&2
  exit 2
fi

cd "${REPO_ROOT}"
TRANSCRIPT="${REPO_ROOT}/docs/proof/bumblebee-forge/cross_machine/replay_transcript.txt"
: > "${TRANSCRIPT}"

while IFS= read -r cmd; do
  [[ -z "${cmd}" ]] && continue
  echo ">>> ${cmd}" >> "${TRANSCRIPT}"
  eval "${cmd}" >> "${TRANSCRIPT}" 2>&1 || true
  code=$?
  echo "EXIT=${code}" >> "${TRANSCRIPT}"
  if [[ ${code} -ne 0 ]]; then
    exit "${code}"
  fi
done < <(python3 -c "import json; [print(c) for c in json.load(open('${MANIFEST_PATH}')).get('replay_commands',[])]")

printf '%s\n' '{"status":"active","claim_label":"asserted","message":"Replay completed; update manifest hashes and proof bundle before claiming proven."}'
exit 0
