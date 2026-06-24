"""CRK-1 constitutional violations — insulation and continuity breaches."""


class ConstitutionalError(Exception):
    """Raised when an operation would violate CRK-1 invariants (K0–K3)."""
