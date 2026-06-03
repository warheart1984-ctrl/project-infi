"""v3.0 cloud invariant families 9–11 + federated boundary extend."""

from __future__ import annotations

import unittest

from src.ugr.invariants.cloud_invariants import (
    check_cloud_forge_rail,
    check_cloud_federation_policy,
    check_cloud_observed_promotion,
    has_hard_fail,
)
from src.ugr.invariants.cloud_manifold import (
    CLOUD_INVARIANT_SET_VERSION,
    CloudManifoldState,
    build_boundary_set,
    extend_boundary_for_federation_step,
)


class TestFederatedBoundaryExtend(unittest.TestCase):
    def test_extend_adds_peer_rail_tuple(self):
        boundary = build_boundary_set(
            region_id="tenant-us",
            rail="NORMAL",
            organ_providers=[("organ-local-tiny", "local")],
        )
        manifold = CloudManifoldState(
            cloud_identity_hash="abc",
            boundary_digest="def",
            boundary_set=boundary,
            region_id="tenant-us",
            rail="NORMAL",
        )
        extended, did_extend = extend_boundary_for_federation_step(
            manifold,
            organ_id="organ-local-tiny",
            provider="local",
            region_id="tenant-us",
            peer_rail="EXPRESS",
        )
        self.assertTrue(did_extend)
        self.assertIn(("tenant-us", "local", "EXPRESS"), extended.boundary_tuples())
        self.assertEqual(extended.boundary_digest, manifold.boundary_digest)

    def test_cloud_forge_rail_passes_after_extend(self):
        boundary = build_boundary_set(
            region_id="tenant-us",
            rail="NORMAL",
            organ_providers=[("organ-local-tiny", "local")],
        )
        manifold = CloudManifoldState(
            cloud_identity_hash="abc",
            boundary_digest="def",
            boundary_set=boundary,
            region_id="tenant-us",
            rail="NORMAL",
        )
        extended, _ = extend_boundary_for_federation_step(
            manifold,
            organ_id="organ-local-tiny",
            provider="local",
            region_id="tenant-us",
            peer_rail="EXPRESS",
        )
        mission_state = {"region_id": "tenant-us", "cloud_manifold": extended.to_dict()}
        results = check_cloud_forge_rail(
            mission_state,
            {"organ_id": "organ-local-tiny", "provider": "local", "rail": "EXPRESS"},
            manifold=extended,
            home_rail="NORMAL",
            federation_peer_tenant="tenant:contoso",
            federation_grant_id="fed-1",
            grant_capabilities=("route_step",),
        )
        self.assertFalse(has_hard_fail(results))

    def test_invariant_version_is_3_0(self):
        self.assertEqual(CLOUD_INVARIANT_SET_VERSION, "3.0")

    def test_federation_policy_requires_accepted_grant(self):
        results = check_cloud_federation_policy(
            home_tenant_id="tenant:acme",
            peer_tenant_id="tenant:contoso",
            federation_grant_id="fed-1",
            grant_status="pending",
            grant_capabilities=("route_step",),
        )
        self.assertTrue(has_hard_fail(results))

    def test_observed_promotion_blocks_without_governance_apply(self):
        results = check_cloud_observed_promotion(submit_promotion=True)
        self.assertTrue(has_hard_fail(results))


if __name__ == "__main__":
    unittest.main()
