"""Lawful brain planner errors."""


class PlannerError(RuntimeError):
    """Raised when both frontier and JSON fallback planners fail."""
