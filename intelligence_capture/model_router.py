"""Model routing utilities to support round-robin + fallback chains."""
from __future__ import annotations

import threading
from itertools import cycle
from typing import Iterable, List, Optional

from .config import FALLBACK_CHAIN, ROUND_ROBIN_CHAIN


class ModelRouter:
    """Keeps a rotating pointer over configured models."""

    def __init__(
        self,
        round_robin_chain: Optional[Iterable[str]] = None,
        fallback_chain: Optional[Iterable[str]] = None,
    ) -> None:
        self.round_robin_chain = list(round_robin_chain or ROUND_ROBIN_CHAIN or ["gpt-4o-mini"])
        self.fallback_chain = list(fallback_chain or FALLBACK_CHAIN or self.round_robin_chain)

        if not self.round_robin_chain:
            raise ValueError("Round robin chain cannot be empty")

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

        ordered = [initial] + self.fallback_chain
        for model_name in ordered:
            if model_name in seen:
                continue
            seen.add(model_name)
            sequence.append(model_name)

        return sequence


MODEL_ROUTER = ModelRouter()
