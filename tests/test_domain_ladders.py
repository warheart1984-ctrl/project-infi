from __future__ import annotations

from nova.law_kernel.capability_ladders import DOMAIN_LADDERS, next_capability


def test_domain_ladders_have_max_levels_and_steps():
    assert "cognition" in DOMAIN_LADDERS
    assert "planning" in DOMAIN_LADDERS
    assert "governance" in DOMAIN_LADDERS
    assert "substrate" in DOMAIN_LADDERS

    for _domain, cfg in DOMAIN_LADDERS.items():
        assert "max_level" in cfg
        assert "base_step" in cfg
        assert cfg["max_level"] >= 1
        assert cfg["base_step"] > 0.0


def test_next_capability_respects_bounds():
    for domain, cfg in DOMAIN_LADDERS.items():
        max_level = cfg["max_level"]
        assert next_capability(domain, 0, -10.0) == 1
        assert next_capability(domain, max_level, 10.0) == min(max_level, 10)


def test_next_capability_monotone_in_delta():
    domain = "cognition"
    base = 3

    low = next_capability(domain, base, 0.1)
    mid = next_capability(domain, base, 0.5)
    high = next_capability(domain, base, 1.0)

    assert low <= mid <= high
