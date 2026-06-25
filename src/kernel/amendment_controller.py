"""CRK-T2 amendment controller — hysteresis and persistence window."""

from __future__ import annotations

DEFAULT_THETA_HIGH = 0.65
DEFAULT_THETA_LOW = 0.40
DEFAULT_PERSISTENCE_EPOCHS = 3


class KernelAmendmentController:
    """Discrete u(t) with hysteresis and N-epoch persistence above theta_high."""

    def __init__(
        self,
        *,
        theta_high: float = DEFAULT_THETA_HIGH,
        theta_low: float = DEFAULT_THETA_LOW,
        persistence_epochs: int = DEFAULT_PERSISTENCE_EPOCHS,
    ) -> None:
        if theta_low >= theta_high:
            raise ValueError("theta_low must be less than theta_high")
        if persistence_epochs < 1:
            raise ValueError("persistence_epochs must be >= 1")
        self.theta_high = theta_high
        self.theta_low = theta_low
        self.persistence_epochs = persistence_epochs
        self.high_count = 0
        self.last_u = 0

    def decide(self, insufficiency_value: float) -> int:
        if insufficiency_value <= self.theta_low:
            self.high_count = 0
            self.last_u = 0
            return 0

        if insufficiency_value >= self.theta_high:
            self.high_count += 1
        else:
            self.high_count = 0

        if self.high_count >= self.persistence_epochs:
            self.last_u = 1
            return 1

        return 0

    def reset_after_ratification(self) -> None:
        self.high_count = 0
        self.last_u = 0
