from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture import rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiters() -> None:
    rate_limiter._rate_limiters.clear()
    yield
    rate_limiter._rate_limiters.clear()


def test_get_rate_limiter_returns_keyed_instances() -> None:
    limiter_a = rate_limiter.get_rate_limiter(max_calls_per_minute=10, key="model-a")
    limiter_a_repeat = rate_limiter.get_rate_limiter(key="model-a")
    limiter_b = rate_limiter.get_rate_limiter(key="model-b")

    assert limiter_a is limiter_a_repeat
    assert limiter_a is not limiter_b
    assert limiter_a.max_calls == 10


def test_rate_limiters_track_calls_independently() -> None:
    limiter_a = rate_limiter.get_rate_limiter(max_calls_per_minute=1000, key="model-a")
    limiter_b = rate_limiter.get_rate_limiter(max_calls_per_minute=1000, key="model-b")

    for _ in range(3):
        limiter_a.wait_if_needed()
    for _ in range(2):
        limiter_b.wait_if_needed()

    assert len(limiter_a.calls) == 3
    assert len(limiter_b.calls) == 2
    assert set(rate_limiter._rate_limiters.keys()) == {"model-a", "model-b"}
