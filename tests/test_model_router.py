from __future__ import annotations

import threading
from collections import Counter
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.model_router import ModelRouter


def test_round_robin_rotation() -> None:
    router = ModelRouter(round_robin_chain=["m1", "m2"], fallback_chain=["backup"])
    assert [router.next_model() for _ in range(4)] == ["m1", "m2", "m1", "m2"]


def test_fallback_chain_building_and_deduplication() -> None:
    router = ModelRouter(
        round_robin_chain=["gpt-4o-mini", "deepseek-r1"],
        fallback_chain=["deepseek-r1", "mistral-large", "gpt-4o-mini"],
    )
    sequence = router.build_sequence(initial="deepseek-r1")
    assert sequence == ["deepseek-r1", "mistral-large", "gpt-4o-mini"]


def test_build_sequence_rejects_invalid_initial_model() -> None:
    router = ModelRouter(round_robin_chain=["gpt-4o-mini"], fallback_chain=["mistral-large"])
    with pytest.raises(ValueError):
        router.build_sequence(initial="claude-3-opus")


def test_thread_safety_for_next_model() -> None:
    router = ModelRouter(round_robin_chain=["a", "b", "c"])
    results: list[str] = []
    write_lock = threading.Lock()

    def worker(calls: int) -> None:
        local = [router.next_model() for _ in range(calls)]
        with write_lock:
            results.extend(local)

    threads = [threading.Thread(target=worker, args=(50,)) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 150
    counts = Counter(results)
    assert counts == Counter({"a": 50, "b": 50, "c": 50})


def test_empty_round_robin_chain_is_invalid() -> None:
    with pytest.raises(ValueError):
        ModelRouter(round_robin_chain=[], fallback_chain=["fallback"])
