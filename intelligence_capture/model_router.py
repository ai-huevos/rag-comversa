"""Model routing utilities to support round-robin + fallback chains."""
from __future__ import annotations

import threading
from itertools import cycle
from typing import Iterable, List, Optional

from .config import FALLBACK_CHAIN, ROUND_ROBIN_CHAIN


class ModelRouter:
    """
    Keeps a rotating pointer over configured models.

    Thread-safe: a shared lock protects the underlying cycle iterator so
    multiple workers can call `next_model` concurrently.
    """

    def __init__(
        self,
        round_robin_chain: Optional[Iterable[str]] = None,
        fallback_chain: Optional[Iterable[str]] = None,
    ) -> None:
        if round_robin_chain is None:
            self.round_robin_chain = list(ROUND_ROBIN_CHAIN or ["gpt-4o-mini"])
        else:
            self.round_robin_chain = list(round_robin_chain)

        if not self.round_robin_chain:
            raise ValueError("Round robin chain cannot be empty")

        if fallback_chain is None:
            fallback_source = FALLBACK_CHAIN or self.round_robin_chain
        else:
            fallback_source = fallback_chain or self.round_robin_chain

        self.fallback_chain = list(fallback_source)
        self._lock = threading.Lock()
        self._cycle = cycle(self.round_robin_chain)

    def next_model(self) -> str:
        """Return the next model in the round-robin chain."""
        with self._lock:
            return next(self._cycle)

    def build_sequence(self, initial: Optional[str] = None) -> List[str]:
        """Build the ordered sequence of models to attempt."""
        sequence: List[str] = []
        seen = set()

        if initial is None:
            initial = self.next_model()
        elif initial not in self.round_robin_chain and initial not in self.fallback_chain:
            raise ValueError(f"Model '{initial}' not in configured chains")

        ordered = [initial] + self.fallback_chain
        for model_name in ordered:
            if model_name in seen:
                continue
            seen.add(model_name)
            sequence.append(model_name)

        return sequence


MODEL_ROUTER = ModelRouter()
