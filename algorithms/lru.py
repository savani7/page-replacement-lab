"""LRU - Least Recently Used page replacement."""
from typing import Optional, Sequence

from .base import Decision, ReplacementPolicy


class LRUPolicy(ReplacementPolicy):
    name = "LRU"
    full_name = "Least Recently Used"
    behavior = (
        "LRU removes the page that has not been used for the longest time, assuming "
        "that pages used recently are likely to be used again soon. Every hit "
        "refreshes a page, so frequently used pages tend to stay in RAM."
    )

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.last_used = {}   # resident page -> index of its most recent reference

    def on_hit(self, page: int, index: int) -> None:
        self.last_used[page] = index

    def on_load(self, page: int, index: int) -> None:
        self.last_used[page] = index

    def on_evict(self, page: int) -> None:
        self.last_used.pop(page, None)

    def choose_victim(
        self, frames: Sequence[Optional[int]], refs: Sequence[int], index: int
    ) -> Decision:
        resident = [p for p in frames if p is not None]
        ordered = sorted(resident, key=lambda p: self.last_used[p])
        victim = ordered[0]
        details = []
        for rank, page in enumerate(ordered):
            tag = "  <- least recently used, will be removed" if rank == 0 else ""
            details.append(
                f"Page {page} - last used at reference {self.last_used[page] + 1}{tag}"
            )
        reason = f"LRU removes Page {victim} because it was used least recently."
        return Decision(victim=victim, reason=reason, details=details)
