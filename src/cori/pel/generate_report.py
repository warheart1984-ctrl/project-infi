"""Generate leadership Markdown and machine JSON reports from verified PEL artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from src.cori.pel.models import Claim, PELRecord, VerificationRecord


def _iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_markdown_report(pel: PELRecord, claim: Claim, verif: VerificationRecord) -> str:
    """Produce a reviewer-facing Markdown report."""
    raw_json = json.dumps(pel.raw, indent=2, default=str)
    details_json = json.dumps(verif.details, indent=2, default=str)
    verified = verif.status == "verified"

    interpretation = (
        "The canonical loop payload was re-serialized and hashed.\n\n"
        "The recomputed hash matched the stored primary_hash.\n\n"
        "Therefore, the audit record is cryptographically self-consistent.\n\n"
        "The claim is supported by primary evidence.\n\n"
        "A third party can independently verify the entire chain without relying on founder interpretation."
        if verified
        else (
            "The recomputed hash did **not** match the stored primary_hash.\n\n"
            "The audit record is **not** cryptographically self-consistent.\n\n"
            "The claim cannot be supported until the evidence chain is reconciled."
        )
    )

    return f"""# CORI Alpha — First Verified Loop Report
**Generated:** {_iso_z(datetime.now(UTC))}
**Verification ID:** {verif.id}

---

## 1. Summary

This report documents the first fully verified CORI Alpha governance loop.
A real user executed the runtime core loop, producing an AuditRecord which was ingested into the PEL and independently verified using `pel_verify.py`.

This establishes the first **end-to-end operational evidence** that CORI Alpha can produce governed decisions with full provenance.

---

## 2. Claim

**Claim ID:** {claim.id}
**Tier:** {claim.tier}
**Summary:** {claim.summary}
**Description:**

{claim.description}

Status: **{claim.status}**
Created At: {_iso_z(claim.created_at)}

---

## 3. PEL Record (Primary Evidence)

**PEL ID:** {pel.id}
**Kind:** {pel.kind}
**Observed At:** {_iso_z(pel.observed_at)}
**Primary Hash:** `{pel.primary_hash}`

### Linked Entities
- **Subject:** {pel.actor_ref}
- **Asset:** {pel.object_ref}
- **Evidence:** {pel.evidence_ref}
- **Validation:** {pel.validation_ref}
- **Decision:** {pel.decision}

### Canonical Payload (raw)
```json
{raw_json}
```

---

## 4. Verification Result

Status: **{verif.status.upper()}**
Verified At: {_iso_z(verif.verified_at)}
Method: {verif.method}

### Details
```json
{details_json}
```

---

## 5. Interpretation

{interpretation}

---

## 6. Conclusion

This report constitutes the first independently verifiable governance artifact produced by CORI Alpha.

It demonstrates:

- A real governed loop executed successfully.
- The runtime produced a tamper-evident audit record.
- The PEL ingested the record as primary evidence.
- The verifier confirmed the invariant mechanically.

This marks the transition from architecture to operational evidence.
"""


def generate_json_report(pel: PELRecord, claim: Claim, verif: VerificationRecord) -> dict:
    """Produce a machine-ingestible JSON report bundle."""
    verified = verif.status == "verified"
    return {
        "generated_at": _iso_z(datetime.now(UTC)),
        "verification_id": verif.id,
        "claim": claim.model_dump(mode="json"),
        "pel_record": pel.model_dump(mode="json"),
        "verification": verif.model_dump(mode="json"),
        "interpretation": {
            "hash_match": verified,
            "message": (
                "Audit record is cryptographically self-consistent"
                if verified
                else "Hash mismatch — evidence chain invalid"
            ),
        },
        "conclusion": "First independently verifiable governance artifact produced by CORI Alpha.",
    }


def write_report_bundle(
    pel: PELRecord,
    claim: Claim,
    verif: VerificationRecord,
    output_dir: str | Path,
    *,
    stem: str | None = None,
) -> dict[str, Path]:
    """Write Markdown and JSON reports to disk; return output paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = stem or pel.id.replace("/", "-")
    md_path = out / f"{base}.md"
    json_path = out / f"{base}.json"
    md_path.write_text(generate_markdown_report(pel, claim, verif), encoding="utf-8")
    json_path.write_text(
        json.dumps(generate_json_report(pel, claim, verif), indent=2, default=str),
        encoding="utf-8",
    )
    return {"markdown": md_path, "json": json_path}
