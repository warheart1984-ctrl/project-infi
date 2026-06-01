"""Tests for the local spatial reasoning plug."""

import unittest

from src.Spatial_reasoning import SpatialReasoningPlug


class TestSpatialReasoningPlug(unittest.TestCase):
    """Verify coordinate-aware and graph-aware spatial reasoning behavior."""

    def test_real_world_distance_bearing_and_travel_time(self):
        """Geo distance, bearing, and travel time should work for coordinate-aware nodes."""
        plug = SpatialReasoningPlug()
        plug.add_real_world_node("map", "west", 0.0, 0.0)
        plug.add_real_world_node("map", "east", 0.0, 1.0)

        distance = plug.geo_distance("map", "west", "east")
        bearing = plug.bearing("map", "west", "east")
        travel = plug.travel_time("map", "west", "east", speed_kmh=60.0, route_mode="direct")

        self.assertGreater(distance["distance_meters"], 111_000)
        self.assertLess(distance["distance_meters"], 112_500)
        self.assertAlmostEqual(distance["distance"], distance["distance_meters"], places=5)
        self.assertAlmostEqual(bearing["bearing_degrees"], 90.0, delta=0.5)
        self.assertEqual(bearing["bearing_label"], "E")
        self.assertGreater(travel["travel_minutes"], 110.0)
        self.assertLess(travel["travel_minutes"], 113.0)

    def test_build_space_auto_uses_geo_distance_for_unweighted_edges(self):
        """Edges between coordinate-aware nodes should get a real-world distance when weight is omitted."""
        plug = SpatialReasoningPlug()
        plug.build_space(
            "towns",
            nodes=[
                {"id": "Grayling", "lat": 44.661, "lon": -84.714},
                {"id": "TraverseCity", "lat": 44.763, "lon": -85.62},
            ],
            edges=[
                {"from": "Grayling", "to": "TraverseCity"},
            ],
        )

        path = plug.shortest_path("towns", "Grayling", "TraverseCity")
        self.assertEqual(path["path"], ["Grayling", "TraverseCity"])
        self.assertGreater(path["distance"], 70_000)
        self.assertEqual(path["distance"], path["distance_meters"])

    def test_real_world_visibility_detects_obstacle_node_on_line(self):
        """Obstacle nodes near the straight path should block real-world visibility."""
        plug = SpatialReasoningPlug()
        plug.build_space(
            "street",
            nodes=[
                {"id": "observer", "lat": 0.0, "lon": 0.0},
                {"id": "target", "lat": 0.0, "lon": 0.02},
                {"id": "building", "lat": 0.0, "lon": 0.01, "type": "obstacle", "height": 30, "name": "building"},
            ],
            edges=[],
        )

        visibility = plug.real_world_visibility("street", "observer", "target")

        self.assertFalse(visibility["visible"])
        self.assertIn("building", visibility["blocked_by"])

    def test_real_world_visibility_tracks_terrain_penalties(self):
        """Terrain penalties should be reported even when visibility remains technically open."""
        plug = SpatialReasoningPlug()
        plug.build_space(
            "trail",
            nodes=[
                {"id": "a", "lat": 0.0, "lon": 0.0},
                {"id": "b", "lat": 0.0, "lon": 0.01},
                {"id": "forest", "lat": 0.0, "lon": 0.005, "terrain": "forest", "visibility_penalty": 0.4},
            ],
            edges=[],
        )

        visibility = plug.real_world_visibility("trail", "a", "b")

        self.assertTrue(visibility["visible"])
        self.assertEqual(len(visibility["terrain_penalties"]), 1)
        self.assertEqual(visibility["terrain_penalties"][0]["name"], "forest")

    def test_query_supports_real_world_node_mode(self):
        """The universal query entrypoint should expose geo node adds and geo distance."""
        plug = SpatialReasoningPlug()
        added = plug.query("add_real_world_node", space_id="campus", node_id="hall", lat=44.0, lon=-85.0, z=12)
        plug.query("add_real_world_node", space_id="campus", node_id="lab", lat=44.0005, lon=-85.0005)
        distance = plug.query("geo_distance", space_id="campus", **{"from": "hall", "to": "lab"})

        self.assertEqual(added["node_id"], "hall")
        self.assertGreater(distance["distance_meters"], 0)


if __name__ == "__main__":
    unittest.main()
