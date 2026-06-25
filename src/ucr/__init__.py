"""Ultima Cognitive Runtime (UCR) kernel package."""

from src.ucr.authority_envelope import AuthorityEnvelope, PermissionSet, build_test_envelope
from src.ucr.binary_law_key import CANONICAL_U128, BinaryLawKey, parse_and_validate, validate_law_key
from src.ucr.boot_manifest import BootManifest, build_boot_manifest, parse_boot_manifest, write_boot_manifest
from src.ucr.cog_act_commit import CommitOutcome, CommitResult, cog_act_commit
from src.ucr.corridor import Corridor, LaneProfile, build_nova_dev_corridor, build_prod_ops_corridor
from src.ucr.corridor_loader import CorridorLoader, get_trusted_corridors, is_sealed
from src.ucr.corridor_serialize import TrustedCorridorSet, compute_h_corridors
from src.ucr.kernel_boot import get_trust_root_syscall, run_early_boot
from src.ucr.trust_root import TrustRoot, UCRTrustContext, get_trust_root, to_ucr_context
from src.ucr.ucr_attestation import (
    RegisterOutcome,
    UCR_NOT_REGISTERED,
    UCRAttestationToken,
    UCRRegisterResult,
    get_registered_ucr_handle,
    issue_attestation_from_sealed_trust,
    issue_attestation_token,
    reset_ucr_registration_for_tests,
    ucr_register,
)
from src.ucr.ucr_governed import require_governed_mode

__all__ = [
    "AuthorityEnvelope",
    "BinaryLawKey",
    "BootManifest",
    "CANONICAL_U128",
    "CommitOutcome",
    "CommitResult",
    "Corridor",
    "CorridorLoader",
    "LaneProfile",
    "PermissionSet",
    "RegisterOutcome",
    "UCR_NOT_REGISTERED",
    "TrustedCorridorSet",
    "TrustRoot",
    "UCRAttestationToken",
    "UCRRegisterResult",
    "UCRTrustContext",
    "build_boot_manifest",
    "build_nova_dev_corridor",
    "build_prod_ops_corridor",
    "build_test_envelope",
    "cog_act_commit",
    "compute_h_corridors",
    "get_registered_ucr_handle",
    "get_trust_root",
    "get_trust_root_syscall",
    "get_trusted_corridors",
    "is_sealed",
    "issue_attestation_from_sealed_trust",
    "issue_attestation_token",
    "parse_and_validate",
    "parse_boot_manifest",
    "require_governed_mode",
    "reset_ucr_registration_for_tests",
    "run_early_boot",
    "to_ucr_context",
    "ucr_register",
    "validate_law_key",
    "write_boot_manifest",
]
