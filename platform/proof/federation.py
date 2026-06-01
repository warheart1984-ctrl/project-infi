"""Proof attestation registry (v19+)."""



from __future__ import annotations



import os

from datetime import datetime

from typing import Any



from src.datetime_compat import UTC



from platform.common import new_id

from platform.proof.runners import is_runner_enrolled
from platform.proof.witnesses import witness_policy_satisfied

from platform.proof.signing import default_signature_alg, sign_attestation, verify_attestation_signature

from platform.store import PlatformStore



ATTESTATION_VERSION = "platform.proof_attestation.v1"





def register_attestation(

    *,

    store: PlatformStore,

    job_id: str,

    runner_id: str,

    result_hash: str,

    region: str = "us",

    machine_label: str = "",

    manifest_ref: str = "",

    signature: str = "",

    signature_alg: str = "",

    witness_id: str = "",

) -> dict[str, Any]:

    if witness_id:

        if not store.get_proof_witness(witness_id):

            raise PermissionError(f"witness {witness_id} not enrolled")

        runner_id = f"witness:{witness_id}"

        runner: dict[str, Any] = {}

    else:

        if not is_runner_enrolled(store=store, runner_id=runner_id):

            raise PermissionError(f"runner {runner_id} not enrolled")

        runner = store.get_proof_runner(runner_id) or {}

    alg = signature_alg or default_signature_alg()

    pub_pem = str(runner.get("public_key_pem") or "")

    if signature:

        sig = signature

    else:

        sig, alg = sign_attestation(

            job_id=job_id,

            runner_id=runner_id,

            result_hash=result_hash,

            signature_alg=alg,

            private_key_pem=os.environ.get("PLATFORM_RUNNER_PRIVATE_KEY_PEM", ""),

        )

    if not verify_attestation_signature(

        job_id=job_id,

        runner_id=runner_id,

        result_hash=result_hash,

        signature=sig,

        signature_alg=alg,

        public_key_pem=pub_pem,

    ):

        raise PermissionError("invalid attestation signature")

    record = {

        "attestation_version": ATTESTATION_VERSION,

        "attestation_id": new_id("att"),

        "job_id": job_id,

        "runner_id": runner_id,

        "region": region,

        "machine_label": machine_label or runner_id,

        "result_hash": result_hash,

        "manifest_ref": manifest_ref,

        "signed_at": datetime.now(UTC).isoformat(),

        "signature": sig,

        "signature_alg": alg,

        "public_key_ref": str(runner.get("public_key_ref") or ""),

        "witness_id": witness_id,

        "claim_label": "asserted",

    }

    att = store.upsert_attestation(record)

    job = store.get_job(job_id)

    if job and job.get("org_id"):

        from platform.ledger.hooks import ledger_attestation



        ledger_attestation(store=store, org_id=str(job["org_id"]), attestation=att)

    return att





def federation_status(*, store: PlatformStore, job: dict[str, Any]) -> dict[str, Any]:

    job_id = str(job.get("job_id"))

    attestations = store.list_attestations(job_id=job_id)

    hashes = {str(a.get("result_hash") or "") for a in attestations if a.get("result_hash")}

    runners = {str(a.get("runner_id") or "") for a in attestations}

    quorum = int(job.get("attestation_quorum") or os.environ.get("PLATFORM_PROOF_QUORUM", "2"))

    hash_consensus = len(hashes) == 1 and len(hashes) > 0

    return {

        "federation_id": job.get("federation_id") or job_id,

        "job_id": job_id,

        "attestations": attestations,

        "distinct_runners": len(runners),

        "quorum_required": quorum,

        "hash_consensus": hash_consensus,

        "hash_mismatch": len(hashes) > 1,

        "quorum_met": len(runners) >= quorum
        and hash_consensus
        and witness_policy_satisfied(store=store, job_id=job_id),

    }

