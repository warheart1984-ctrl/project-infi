"""Artifact storage abstraction for the hosted Mechanic pilot."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any


class FilesystemArtifactStore:
    """Durable local artifact store with signed download tokens.

    This is the deployable local backend. Cloud stores can preserve the same
    read/write contract and swap the path implementation for object storage.
    """

    def __init__(self, *, root: str | Path, signing_secret: str) -> None:
        self.root = Path(root).expanduser().resolve()
        self.signing_secret = signing_secret
        self.root.mkdir(parents=True, exist_ok=True)

    def case_dir(self, customer_id: str, scan_id: str, case_id: str) -> Path:
        return self.root / _safe(customer_id) / _safe(scan_id) / _safe(case_id)

    def write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")

    def read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def sign_artifact_path(self, path: str | Path) -> str:
        rel = str(Path(path)).replace("\\", "/")
        digest = hmac.new(self.signing_secret.encode("utf-8"), rel.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"mechanic-artifact://{rel}?sig={digest}"

    def verify_signed_path(self, signed: str) -> bool:
        if not signed.startswith("mechanic-artifact://") or "?sig=" not in signed:
            return False
        rel, sig = signed.removeprefix("mechanic-artifact://").rsplit("?sig=", 1)
        expected = hmac.new(self.signing_secret.encode("utf-8"), rel.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)

    def publish_case_dir(self, case_dir: Path) -> dict[str, str]:
        return {}


class S3ArtifactStore:
    """S3-compatible durable artifact store.

    Works with AWS S3 and MinIO via endpoint_url. The worker still writes to a
    local scratch directory; this backend mirrors the finished bundle to object
    storage and signs object URLs.
    """

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "mechanic",
        endpoint_url: str = "",
        region_name: str = "us-east-1",
        expires_seconds: int = 3600,
    ) -> None:
        if not bucket:
            raise ValueError("S3 artifact backend requires bucket")
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3 artifact storage") from exc
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.expires_seconds = expires_seconds
        self.client = boto3.client("s3", endpoint_url=endpoint_url or None, region_name=region_name)

    def case_dir(self, customer_id: str, scan_id: str, case_id: str) -> Path:
        root = Path(os.environ.get("MECHANIC_LOCAL_SCRATCH_ROOT", ".runtime/mechanic-scratch"))
        return root / _safe(customer_id) / _safe(scan_id) / _safe(case_id)

    def publish_case_dir(self, case_dir: Path) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for path in sorted(case_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(case_dir)).replace("\\", "/")
            key = f"{self.prefix}/{case_dir.parent.parent.name}/{case_dir.parent.name}/{case_dir.name}/{rel}"
            self.client.upload_file(str(path), self.bucket, key)
            mapping[str(path)] = f"s3://{self.bucket}/{key}"
        return mapping

    def sign_artifact_path(self, path: str | Path) -> str:
        value = str(path)
        if value.startswith("s3://"):
            _, rest = value.split("s3://", 1)
            bucket, key = rest.split("/", 1)
        else:
            bucket, key = self.bucket, value
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=self.expires_seconds,
        )

    def verify_signed_path(self, signed: str) -> bool:
        return signed.startswith("http://") or signed.startswith("https://")


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)[:120]


def artifact_store_from_settings(settings: Any) -> FilesystemArtifactStore | S3ArtifactStore:
    if str(settings.artifact_backend).lower() == "s3":
        return S3ArtifactStore(
            bucket=settings.s3_bucket,
            prefix=settings.s3_prefix,
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
        )
    return FilesystemArtifactStore(root=settings.artifact_root, signing_secret=settings.artifact_signing_secret)
