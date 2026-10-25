"""FIFO - First In, First Out page replacement."""
from collections import deque
from typing import Optional, Sequence

from .base import Decision, ReplacementPolicy


class FIFOPolicy(ReplacementPolicy):
    name = "FIFO"
    full_name = "First In, First Out"
    behavior = (
        "FIFO always removes the page that has been in RAM the longest. "
        "It ignores how often or how recently a page was used, so a page that is "
        "used constantly can still be removed just because it arrived early."
    )

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.order = deque()      # resident pages, oldest first
        self.arrival = {}         # page -> reference index at which it was loaded

    # A hit deliberately does NOT touch the arrival order (on_hit is inherited no-op).
    def on_load(self, page: int, index: int) -> None:
        self.order.append(page)
        self.arrival[page] = index

    def on_evict(self, page: int) -> None:
        self.order.remove(page)
        self.arrival.pop(page, None)

    def choose_victim(
        self, frames: Sequence[Optional[int]], refs: Sequence[int], index: int
    ) -> Decision:
        resident = {p for p in frames if p is not None}
        ordered = [p for p in self.order if p in resident]
        victim = ordered[0]
        details = []
        for rank, page in enumerate(ordered):
            tag = "  <- oldest, will be removed" if rank == 0 else ""
            details.append(
                f"Page {page} - entered RAM at reference {self.arrival[page] + 1}{tag}"
            )
        reason = (
            f"FIFO removes Page {victim} because it entered RAM before the other "
            f"resident pages."
        )
        return Decision(victim=victim, reason=reason, details=details)
