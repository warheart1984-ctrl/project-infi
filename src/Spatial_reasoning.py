"""Local spatial reasoning tool for maps, scenes, and layout checks.

This stays dependency-free so it can plug into AAIS without adding another
runtime requirement. It supports simple graph builds, entity placement, shortest
path, and visibility checks that can be used for writing, coding, or training
examples.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from typing import Any


@dataclass
class _ResolvedPoint:
    """One normalized point inside a named spatial graph."""

    node_id: str
    source: str
    point_type: str


class SpatialReasoningPlug:
    """Stateful graph-based spatial reasoning for the local AAIS runtime."""

    EARTH_RADIUS_METERS = 6_371_000.0

    def __init__(self):
        self.spaces: dict[str, dict[str, Any]] = {}
        self.entities: dict[str, dict[str, Any]] = {}

    def build_space(self, space_id: str, nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
        """Create or replace one named spatial graph."""
        normalized_space_id = self._require_text(space_id, "space_id")
        normalized_nodes: dict[str, dict[str, Any]] = {}

        for node in nodes or []:
            node_id = self._require_text((node or {}).get("id"), "node.id")
            if node_id in normalized_nodes:
                raise ValueError(f"Duplicate node id '{node_id}' in space '{normalized_space_id}'")
            normalized_nodes[node_id] = self._normalize_node_attributes(
                {key: value for key, value in (node or {}).items() if key != "id"}
            )

        adjacency = {node_id: {} for node_id in normalized_nodes}
        normalized_edges: list[dict[str, Any]] = []

        for edge in edges or []:
            source = self._require_text((edge or {}).get("from"), "edge.from")
            target = self._require_text((edge or {}).get("to"), "edge.to")
            if source not in normalized_nodes or target not in normalized_nodes:
                raise ValueError(
                    f"Edge '{source}' -> '{target}' must reference nodes that already exist in '{normalized_space_id}'"
                )

            source_node = normalized_nodes[source]
            target_node = normalized_nodes[target]
            geo_distance = None
            if self._has_coordinates(source_node) and self._has_coordinates(target_node):
                geo_distance = self._geo_distance_between_points(source_node, target_node)

            if "weight" in (edge or {}):
                weight = self._coerce_weight((edge or {}).get("weight"))
            elif geo_distance is not None:
                weight = geo_distance
            else:
                weight = 1.0
            payload = {
                key: value
                for key, value in (edge or {}).items()
                if key not in {"from", "to"}
            }
            payload["weight"] = weight
            payload["distance_meters"] = self._coerce_weight(
                payload.get("distance_meters", geo_distance if geo_distance is not None else weight)
            )
            payload["obstacle"] = bool(payload.get("obstacle", False))
            adjacency[source][target] = dict(payload)
            adjacency[target][source] = dict(payload)
            normalized_edges.append({"from": source, "to": target, **payload})

        overwritten = normalized_space_id in self.spaces
        self.spaces[normalized_space_id] = {
            "nodes": normalized_nodes,
            "adjacency": adjacency,
            "edges": normalized_edges,
        }

        self.entities = {
            entity_id: entity
            for entity_id, entity in self.entities.items()
            if entity.get("space") != normalized_space_id
        }

        summary = (
            f"Space '{normalized_space_id}' built with {len(normalized_nodes)} nodes and "
            f"{len(normalized_edges)} connections."
        )
        if overwritten:
            summary = (
                f"Space '{normalized_space_id}' was rebuilt with {len(normalized_nodes)} nodes and "
                f"{len(normalized_edges)} connections."
            )

        return {
            "space_id": normalized_space_id,
            "node_count": len(normalized_nodes),
            "edge_count": len(normalized_edges),
            "node_ids": list(normalized_nodes.keys()),
            "geo_enabled": any(self._has_coordinates(node) for node in normalized_nodes.values()),
            "summary": summary,
        }

    def add_real_world_node(
        self,
        space_id: str,
        node_id: str,
        lat: float,
        lon: float,
        elevation: float = 0,
        **attrs,
    ) -> dict[str, Any]:
        """Add one coordinate-aware node to a new or existing space."""
        normalized_space_id = self._require_text(space_id, "space_id")
        normalized_node_id = self._require_text(node_id, "node_id")
        attrs = dict(attrs or {})
        attrs["lat"] = lat
        attrs["lon"] = lon
        attrs["z"] = elevation

        if normalized_space_id not in self.spaces:
            self.spaces[normalized_space_id] = {
                "nodes": {},
                "adjacency": {},
                "edges": [],
            }

        normalized_attrs = self._normalize_node_attributes(attrs)
        self.spaces[normalized_space_id]["nodes"][normalized_node_id] = normalized_attrs
        self.spaces[normalized_space_id]["adjacency"].setdefault(normalized_node_id, {})

        return {
            "space_id": normalized_space_id,
            "node_id": normalized_node_id,
            "lat": normalized_attrs["lat"],
            "lon": normalized_attrs["lon"],
            "z": normalized_attrs["z"],
            "summary": f"Real-world node '{normalized_node_id}' added to '{normalized_space_id}'.",
        }

    def place_entity(self, entity_id: str, space_id: str, node_id: str, **attrs) -> dict[str, Any]:
        """Place a named entity on one node inside a space."""
        normalized_entity_id = self._require_text(entity_id, "entity_id")
        normalized_space_id = self._require_text(space_id, "space_id")
        normalized_node_id = self._require_text(node_id, "node")
        self._require_node(normalized_space_id, normalized_node_id)

        payload = {
            "space": normalized_space_id,
            "node": normalized_node_id,
            **attrs,
        }
        self.entities[normalized_entity_id] = payload
        return {
            "entity_id": normalized_entity_id,
            "space_id": normalized_space_id,
            "node": normalized_node_id,
            "attributes": attrs,
            "summary": f"Entity '{normalized_entity_id}' placed at '{normalized_node_id}' in '{normalized_space_id}'.",
        }

    def shortest_path(self, space_id: str, start: str, end: str) -> dict[str, Any]:
        """Return the shortest weighted path between two points."""
        normalized_space_id = self._require_text(space_id, "space_id")
        resolved_start = self._resolve_point(normalized_space_id, start)
        resolved_end = self._resolve_point(normalized_space_id, end)

        if resolved_start is None or resolved_end is None:
            missing = start if resolved_start is None else end
            return {"error": f"Point '{missing}' does not exist in '{normalized_space_id}'."}

        if resolved_start.node_id == resolved_end.node_id:
            return {
                "path": [resolved_start.node_id],
                "distance": 0.0,
                "from": resolved_start.source,
                "to": resolved_end.source,
            }

        path, distance = self._dijkstra(normalized_space_id, resolved_start.node_id, resolved_end.node_id)
        if not path:
            return {
                "error": f"No path exists between '{resolved_start.source}' and '{resolved_end.source}' in '{normalized_space_id}'.",
            }

        return {
            "path": path,
            "distance": distance,
            "distance_meters": self._path_distance_meters(normalized_space_id, path),
            "from": resolved_start.source,
            "to": resolved_end.source,
        }

    def geo_distance(self, space_id: str, a: str, b: str, unit: str = "meters") -> dict[str, Any]:
        """Return straight-line geo distance between two coordinate-aware points."""
        normalized_space_id = self._require_text(space_id, "space_id")
        resolved_a = self._resolve_point(normalized_space_id, a)
        resolved_b = self._resolve_point(normalized_space_id, b)
        if resolved_a is None or resolved_b is None:
            missing = a if resolved_a is None else b
            return {"error": f"Point '{missing}' does not exist in '{normalized_space_id}'."}

        point_a = self._point_coordinates(normalized_space_id, resolved_a)
        point_b = self._point_coordinates(normalized_space_id, resolved_b)
        if point_a is None or point_b is None:
            missing = a if point_a is None else b
            return {"error": f"Point '{missing}' has no real-world coordinates in '{normalized_space_id}'."}

        meters = self._geo_distance_between_points(point_a, point_b)
        normalized_unit = self._normalize_unit(unit)
        converted = self._convert_distance(meters, normalized_unit)
        return {
            "from": resolved_a.source,
            "to": resolved_b.source,
            "unit": normalized_unit,
            "distance_meters": meters,
            "distance": converted,
        }

    def bearing(self, space_id: str, a: str, b: str) -> dict[str, Any]:
        """Return initial bearing in degrees between two coordinate-aware points."""
        normalized_space_id = self._require_text(space_id, "space_id")
        resolved_a = self._resolve_point(normalized_space_id, a)
        resolved_b = self._resolve_point(normalized_space_id, b)
        if resolved_a is None or resolved_b is None:
            missing = a if resolved_a is None else b
            return {"error": f"Point '{missing}' does not exist in '{normalized_space_id}'."}

        point_a = self._point_coordinates(normalized_space_id, resolved_a)
        point_b = self._point_coordinates(normalized_space_id, resolved_b)
        if point_a is None or point_b is None:
            missing = a if point_a is None else b
            return {"error": f"Point '{missing}' has no real-world coordinates in '{normalized_space_id}'."}

        degrees = self._bearing_between_points(point_a, point_b)
        return {
            "from": resolved_a.source,
            "to": resolved_b.source,
            "bearing_degrees": degrees,
            "bearing_label": self._bearing_label(degrees),
        }

    def adjacent(self, space_id: str, a: str, b: str) -> dict[str, Any]:
        """Return whether two resolved points share a direct edge."""
        normalized_space_id = self._require_text(space_id, "space_id")
        resolved_a = self._resolve_point(normalized_space_id, a)
        resolved_b = self._resolve_point(normalized_space_id, b)
        if resolved_a is None or resolved_b is None:
            missing = a if resolved_a is None else b
            return {"error": f"Point '{missing}' does not exist in '{normalized_space_id}'."}

        edge = self._space(normalized_space_id)["adjacency"].get(resolved_a.node_id, {}).get(resolved_b.node_id)
        return {
            "from": resolved_a.source,
            "to": resolved_b.source,
            "adjacent": edge is not None,
            "edge": dict(edge) if edge is not None else None,
        }

    def travel_time(
        self,
        space_id: str,
        a: str,
        b: str,
        speed_kmh: float = 5.0,
        route_mode: str = "path",
    ) -> dict[str, Any]:
        """Estimate travel time using either graph distance or straight-line geo distance."""
        normalized_speed = self._coerce_weight(speed_kmh)
        if normalized_speed <= 0:
            raise ValueError("speed_kmh must be greater than zero")

        normalized_route_mode = self._require_text(route_mode, "route_mode").lower().replace("-", "_")
        if normalized_route_mode not in {"path", "direct"}:
            raise ValueError("route_mode must be 'path' or 'direct'")

        if normalized_route_mode == "path":
            path_result = self.shortest_path(space_id, a, b)
            if path_result.get("error"):
                return path_result
            distance_meters = path_result.get("distance_meters") or path_result.get("distance") or 0.0
            path = path_result.get("path", [])
        else:
            distance_result = self.geo_distance(space_id, a, b, unit="meters")
            if distance_result.get("error"):
                return distance_result
            distance_meters = distance_result["distance_meters"]
            path = None

        meters_per_minute = (normalized_speed * 1000.0) / 60.0
        minutes = distance_meters / meters_per_minute if meters_per_minute else 0.0
        return {
            "from": a,
            "to": b,
            "route_mode": normalized_route_mode,
            "speed_kmh": normalized_speed,
            "distance_meters": distance_meters,
            "travel_minutes": minutes,
            "travel_hours": minutes / 60.0,
            "path": path,
        }

    def visibility(self, space_id: str, a: str, b: str, line_of_sight: bool = True) -> dict[str, Any]:
        """Estimate whether two points can see each other through the graph."""
        normalized_space_id = self._require_text(space_id, "space_id")
        resolved_a = self._resolve_point(normalized_space_id, a)
        resolved_b = self._resolve_point(normalized_space_id, b)

        if resolved_a is None or resolved_b is None:
            missing = a if resolved_a is None else b
            return {
                "visible": False,
                "blocked_by": ["the realm itself"],
                "reason": f"Point '{missing}' does not exist in '{normalized_space_id}'.",
            }

        adjacency = self._space(normalized_space_id)["adjacency"]
        direct_edge = adjacency.get(resolved_a.node_id, {}).get(resolved_b.node_id)
        if direct_edge is not None:
            if direct_edge.get("obstacle"):
                blocker = direct_edge.get("name") or "unnamed obstacle"
                return {
                    "visible": False,
                    "blocked_by": [blocker],
                    "distance": float(direct_edge.get("weight", 1)),
                    "reason": "A direct edge exists, but an obstacle blocks the line-of-sight.",
                }

            return {
                "visible": True,
                "blocked_by": [],
                "distance": float(direct_edge.get("weight", 1)),
                "path": [resolved_a.node_id, resolved_b.node_id],
                "reason": "Direct connection with no obstacle in the way.",
            }

        if line_of_sight:
            path, distance = self._dijkstra(normalized_space_id, resolved_a.node_id, resolved_b.node_id)
            if path:
                blockers = []
                for index in range(len(path) - 1):
                    edge = adjacency[path[index]][path[index + 1]]
                    if edge.get("obstacle"):
                        blockers.append(edge.get("name") or "unnamed obstacle")

                if blockers:
                    return {
                        "visible": False,
                        "blocked_by": blockers,
                        "distance": distance,
                        "distance_meters": self._path_distance_meters(normalized_space_id, path),
                        "path": path,
                        "reason": "A route exists, but one or more obstacles interrupt the gaze.",
                    }

                return {
                    "visible": True,
                    "blocked_by": [],
                    "distance": distance,
                    "distance_meters": self._path_distance_meters(normalized_space_id, path),
                    "path": path,
                    "reason": "Indirect visibility through open linked space.",
                }

        return {
            "visible": False,
            "blocked_by": ["shadows", "distance", "topology"],
            "reason": "No clear path or line-of-sight exists between those points.",
        }

    def real_world_visibility(
        self,
        space_id: str,
        a: str,
        b: str,
        max_distance_meters: float | None = None,
    ) -> dict[str, Any]:
        """Check straight-line visibility between coordinate-aware points."""
        normalized_space_id = self._require_text(space_id, "space_id")
        resolved_a = self._resolve_point(normalized_space_id, a)
        resolved_b = self._resolve_point(normalized_space_id, b)
        if resolved_a is None or resolved_b is None:
            missing = a if resolved_a is None else b
            return {"error": f"Point '{missing}' does not exist in '{normalized_space_id}'."}

        point_a = self._point_coordinates(normalized_space_id, resolved_a)
        point_b = self._point_coordinates(normalized_space_id, resolved_b)
        if point_a is None or point_b is None:
            missing = a if point_a is None else b
            return {"error": f"Point '{missing}' has no real-world coordinates in '{normalized_space_id}'."}

        distance_meters = self._geo_distance_between_points(point_a, point_b)
        bearing_degrees = self._bearing_between_points(point_a, point_b)
        if max_distance_meters is not None:
            max_distance_meters = self._coerce_weight(max_distance_meters)
            if distance_meters > max_distance_meters:
                return {
                    "visible": False,
                    "blocked_by": ["distance"],
                    "distance_meters": distance_meters,
                    "bearing_degrees": bearing_degrees,
                    "reason": f"Target is beyond the maximum visibility range of {max_distance_meters:.2f} meters.",
                }

        blockers, penalties = self._collect_real_world_blockers(
            normalized_space_id,
            start_node_id=resolved_a.node_id,
            end_node_id=resolved_b.node_id,
            point_a=point_a,
            point_b=point_b,
        )

        if blockers:
            return {
                "visible": False,
                "blocked_by": blockers,
                "terrain_penalties": penalties,
                "distance_meters": distance_meters,
                "bearing_degrees": bearing_degrees,
                "reason": "Straight-line visibility is blocked by mapped obstacles.",
            }

        penalty_total = sum(item["penalty"] for item in penalties)
        if penalty_total >= 1.0:
            return {
                "visible": False,
                "blocked_by": [item["name"] for item in penalties],
                "terrain_penalties": penalties,
                "distance_meters": distance_meters,
                "bearing_degrees": bearing_degrees,
                "reason": "Terrain penalties make the direct line-of-sight effectively opaque.",
            }

        reason = "Straight-line visibility is clear."
        if penalties:
            reason = "Straight-line visibility is clear, but terrain along the line reduces clarity."
        return {
            "visible": True,
            "blocked_by": [],
            "terrain_penalties": penalties,
            "distance_meters": distance_meters,
            "bearing_degrees": bearing_degrees,
            "reason": reason,
        }

    def _wrap_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(dict(payload))

    def query(self, mode: str, **kwargs) -> dict[str, Any]:
        """Universal entrypoint for AAIS tool-calling."""
        normalized_mode = self._require_text(mode, "mode").lower().replace("-", "_")
        if normalized_mode in {"path", "shortest_path"}:
            return self._wrap_result(
                self.shortest_path(kwargs["space_id"], kwargs["from"], kwargs["to"])
            )
        if normalized_mode in {"distance", "geo_distance"}:
            return self._wrap_result(
                self.geo_distance(
                    kwargs["space_id"],
                    kwargs["from"],
                    kwargs["to"],
                    kwargs.get("unit", "meters"),
                )
            )
        if normalized_mode in {"bearing", "heading"}:
            return self._wrap_result(
                self.bearing(kwargs["space_id"], kwargs["from"], kwargs["to"])
            )
        if normalized_mode in {"adjacent", "adjacency", "direct_connection"}:
            return self._wrap_result(
                self.adjacent(kwargs["space_id"], kwargs["from"], kwargs["to"])
            )
        if normalized_mode in {"travel_time", "travel"}:
            return self._wrap_result(
                self.travel_time(
                    kwargs["space_id"],
                    kwargs["from"],
                    kwargs["to"],
                    kwargs.get("speed_kmh", 5.0),
                    kwargs.get("route_mode", "path"),
                )
            )
        if normalized_mode in {"visibility", "line_of_sight"}:
            return self._wrap_result(
                self.visibility(
                    kwargs["space_id"],
                    kwargs["from"],
                    kwargs["to"],
                    kwargs.get("line_of_sight", True),
                )
            )
        if normalized_mode in {"real_world_visibility", "geo_visibility"}:
            return self._wrap_result(
                self.real_world_visibility(
                    kwargs["space_id"],
                    kwargs["from"],
                    kwargs["to"],
                    kwargs.get("max_distance_meters"),
                )
            )
        if normalized_mode == "place":
            return self._wrap_result(
                self.place_entity(
                    kwargs["entity_id"],
                    kwargs["space_id"],
                    kwargs["node"],
                    **kwargs.get("attrs", {}),
                )
            )
        if normalized_mode in {"add_real_world_node", "geo_node"}:
            return self._wrap_result(
                self.add_real_world_node(
                    kwargs["space_id"],
                    kwargs["node_id"],
                    kwargs["lat"],
                    kwargs["lon"],
                    kwargs.get("elevation", kwargs.get("z", 0)),
                    **kwargs.get("attrs", {}),
                )
            )
        if normalized_mode == "build":
            return self._wrap_result(
                self.build_space(
                    kwargs["space_id"],
                    kwargs.get("nodes", []),
                    kwargs.get("edges", []),
                )
            )
        return self._wrap_result({"error": f"Unknown mode '{normalized_mode}'."})

    def _space(self, space_id: str) -> dict[str, Any]:
        if space_id not in self.spaces:
            raise ValueError(f"Space '{space_id}' has not been built yet.")
        return self.spaces[space_id]

    def _require_node(self, space_id: str, node_id: str) -> None:
        space = self._space(space_id)
        if node_id not in space["nodes"]:
            raise ValueError(f"Node '{node_id}' does not exist in '{space_id}'.")

    def _resolve_point(self, space_id: str, name: str) -> _ResolvedPoint | None:
        normalized_name = self._require_text(name, "point")
        if normalized_name in self.entities:
            entity = self.entities[normalized_name]
            if entity.get("space") != space_id:
                return None
            return _ResolvedPoint(
                node_id=self._require_text(entity.get("node"), "entity.node"),
                source=normalized_name,
                point_type="entity",
            )

        space = self.spaces.get(space_id)
        if not space:
            raise ValueError(f"Space '{space_id}' has not been built yet.")
        if normalized_name not in space["nodes"]:
            return None
        return _ResolvedPoint(node_id=normalized_name, source=normalized_name, point_type="node")

    def _point_coordinates(self, space_id: str, resolved_point: _ResolvedPoint) -> dict[str, Any] | None:
        node = self._space(space_id)["nodes"].get(resolved_point.node_id)
        if not node or not self._has_coordinates(node):
            return None
        return node

    def _path_distance_meters(self, space_id: str, path: list[str]) -> float | None:
        if len(path or []) < 2:
            return 0.0
        adjacency = self._space(space_id)["adjacency"]
        total = 0.0
        for index in range(len(path) - 1):
            edge = adjacency[path[index]][path[index + 1]]
            total += float(edge.get("distance_meters", edge.get("weight", 0.0)))
        return total

    def _collect_real_world_blockers(
        self,
        space_id: str,
        *,
        start_node_id: str,
        end_node_id: str,
        point_a: dict[str, Any],
        point_b: dict[str, Any],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        space = self._space(space_id)
        blockers: list[str] = []
        penalties: list[dict[str, Any]] = []

        direct_edge = space["adjacency"].get(start_node_id, {}).get(end_node_id)
        if direct_edge and direct_edge.get("obstacle"):
            blockers.append(direct_edge.get("name") or "direct obstacle")

        segment_length = self._planar_distance_meters(point_a, point_b)
        for node_id, node in space["nodes"].items():
            if node_id in {start_node_id, end_node_id} or not self._has_coordinates(node):
                continue

            distance_to_line = self._point_to_segment_distance(point_a, point_b, node)
            base_radius = float(node.get("radius_meters", 0.0) or 0.0)
            if base_radius <= 0 and (node.get("obstacle") or node.get("type") == "obstacle"):
                base_radius = max(12.0, float(node.get("height", 0.0) or 0.0) * 0.3)
            if base_radius <= 0 and node.get("terrain"):
                base_radius = 20.0

            if base_radius <= 0 or distance_to_line > base_radius:
                continue

            if node.get("obstacle") or node.get("type") == "obstacle" or float(node.get("height", 0.0) or 0.0) >= 20.0:
                blockers.append(str(node.get("name") or node_id))
                continue

            visibility_penalty = float(node.get("visibility_penalty", 0.0) or 0.0)
            terrain_name = str(node.get("terrain") or node.get("name") or node_id)
            if visibility_penalty > 0:
                penalties.append(
                    {
                        "name": terrain_name,
                        "penalty": visibility_penalty,
                        "distance_to_line_meters": distance_to_line,
                        "segment_length_meters": segment_length,
                    }
                )

        return blockers, penalties

    def _normalize_node_attributes(self, attrs: dict[str, Any]) -> dict[str, Any]:
        payload = dict(attrs or {})
        lat_present = "lat" in payload
        lon_present = "lon" in payload
        if lat_present != lon_present:
            raise ValueError("Real-world nodes must provide both lat and lon together")

        if lat_present and lon_present:
            payload["lat"] = self._coerce_float(payload["lat"], "lat", minimum=-90.0, maximum=90.0)
            payload["lon"] = self._coerce_float(payload["lon"], "lon", minimum=-180.0, maximum=180.0)

        if "elevation" in payload and "z" not in payload:
            payload["z"] = payload["elevation"]
        payload["z"] = self._coerce_float(payload.get("z", 0.0), "z")

        if "height" in payload:
            payload["height"] = self._coerce_float(payload["height"], "height", minimum=0.0)
        if "visibility_penalty" in payload:
            payload["visibility_penalty"] = self._coerce_float(
                payload["visibility_penalty"],
                "visibility_penalty",
                minimum=0.0,
            )

        if "obstacle" in payload:
            payload["obstacle"] = bool(payload["obstacle"])

        return payload

    def _dijkstra(self, space_id: str, start: str, end: str) -> tuple[list[str], float | None]:
        adjacency = self._space(space_id)["adjacency"]
        queue: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
        best: dict[str, float] = {start: 0.0}

        while queue:
            distance, node_id, path = heapq.heappop(queue)
            if node_id == end:
                return path, distance
            if distance > best.get(node_id, float("inf")):
                continue

            for neighbor, edge in adjacency.get(node_id, {}).items():
                weight = float(edge.get("weight", 1))
                candidate = distance + max(0.0, weight)
                if candidate >= best.get(neighbor, float("inf")):
                    continue
                best[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor, [*path, neighbor]))

        return [], None

    @staticmethod
    def _require_text(value: Any, field_name: str) -> str:
        cleaned = " ".join(str(value or "").split()).strip()
        if not cleaned:
            raise ValueError(f"{field_name} is required")
        return cleaned

    @staticmethod
    def _coerce_weight(value: Any) -> float:
        try:
            weight = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("edge.weight must be numeric") from exc
        if weight < 0:
            raise ValueError("edge.weight must be non-negative")
        return weight

    @staticmethod
    def _coerce_float(
        value: Any,
        field_name: str,
        *,
        minimum: float | None = None,
        maximum: float | None = None,
    ) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
        if minimum is not None and number < minimum:
            raise ValueError(f"{field_name} must be at least {minimum}")
        if maximum is not None and number > maximum:
            raise ValueError(f"{field_name} must be at most {maximum}")
        return number

    @staticmethod
    def _has_coordinates(node: dict[str, Any]) -> bool:
        return "lat" in (node or {}) and "lon" in (node or {})

    def _geo_distance_between_points(self, point_a: dict[str, Any], point_b: dict[str, Any]) -> float:
        lat1 = math.radians(float(point_a["lat"]))
        lon1 = math.radians(float(point_a["lon"]))
        lat2 = math.radians(float(point_b["lat"]))
        lon2 = math.radians(float(point_b["lon"]))

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        hav = (
            math.sin(delta_lat / 2.0) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2.0) ** 2
        )
        horizontal = 2.0 * self.EARTH_RADIUS_METERS * math.asin(min(1.0, math.sqrt(hav)))
        vertical = float(point_b.get("z", 0.0) or 0.0) - float(point_a.get("z", 0.0) or 0.0)
        return math.sqrt(horizontal ** 2 + vertical ** 2)

    @staticmethod
    def _bearing_between_points(point_a: dict[str, Any], point_b: dict[str, Any]) -> float:
        lat1 = math.radians(float(point_a["lat"]))
        lon1 = math.radians(float(point_a["lon"]))
        lat2 = math.radians(float(point_b["lat"]))
        lon2 = math.radians(float(point_b["lon"]))
        delta_lon = lon2 - lon1

        x = math.sin(delta_lon) * math.cos(lat2)
        y = (
            math.cos(lat1) * math.sin(lat2)
            - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        )
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360.0) % 360.0

    @staticmethod
    def _bearing_label(degrees: float) -> str:
        directions = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
        index = int(((degrees + 22.5) % 360.0) // 45.0)
        return directions[index]

    @staticmethod
    def _normalize_unit(unit: Any) -> str:
        normalized = " ".join(str(unit or "meters").split()).strip().lower()
        if normalized in {"m", "meter", "meters"}:
            return "meters"
        if normalized in {"km", "kilometer", "kilometers"}:
            return "kilometers"
        if normalized in {"mi", "mile", "miles"}:
            return "miles"
        raise ValueError("unit must be meters, kilometers, or miles")

    @staticmethod
    def _convert_distance(distance_meters: float, unit: str) -> float:
        if unit == "meters":
            return distance_meters
        if unit == "kilometers":
            return distance_meters / 1000.0
        if unit == "miles":
            return distance_meters / 1609.344
        raise ValueError(f"Unsupported distance unit '{unit}'")

    @staticmethod
    def _point_to_segment_distance(point_a: dict[str, Any], point_b: dict[str, Any], point_c: dict[str, Any]) -> float:
        ax, ay = SpatialReasoningPlug._project_to_local_xy(point_a, origin=point_a)
        bx, by = SpatialReasoningPlug._project_to_local_xy(point_b, origin=point_a)
        cx, cy = SpatialReasoningPlug._project_to_local_xy(point_c, origin=point_a)

        abx = bx - ax
        aby = by - ay
        ab_length_sq = abx ** 2 + aby ** 2
        if ab_length_sq == 0:
            return math.sqrt((cx - ax) ** 2 + (cy - ay) ** 2)

        projection = ((cx - ax) * abx + (cy - ay) * aby) / ab_length_sq
        projection = max(0.0, min(1.0, projection))
        closest_x = ax + projection * abx
        closest_y = ay + projection * aby
        return math.sqrt((cx - closest_x) ** 2 + (cy - closest_y) ** 2)

    @staticmethod
    def _planar_distance_meters(point_a: dict[str, Any], point_b: dict[str, Any]) -> float:
        ax, ay = SpatialReasoningPlug._project_to_local_xy(point_a, origin=point_a)
        bx, by = SpatialReasoningPlug._project_to_local_xy(point_b, origin=point_a)
        return math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)

    @staticmethod
    def _project_to_local_xy(point: dict[str, Any], *, origin: dict[str, Any]) -> tuple[float, float]:
        lat_scale = 111_320.0
        mean_lat = math.radians((float(point["lat"]) + float(origin["lat"])) / 2.0)
        lon_scale = math.cos(mean_lat) * 111_320.0
        x = (float(point["lon"]) - float(origin["lon"])) * lon_scale
        y = (float(point["lat"]) - float(origin["lat"])) * lat_scale
        return x, y
