"""LRU - Least Recently Used."""
from __future__ import annotations

from typing import List

from .base import Policy, Step, run_simulation


class LRUPolicy(Policy):
    name = "LRU"

    def reset(self, n_frames):
        self.last_used = [None] * n_frames   # reference number (1-based) of last use

    def on_load(self, slot, page, i):
        self.last_used[slot] = i + 1

    def on_hit(self, slot, page, i):
        self.last_used[slot] = i + 1         # LRU updates recency on every hit

    def _lru_slot(self, frames):
        return min((s for s, p in enumerate(frames) if p is not None),
                   key=lambda s: self.last_used[s])

    def choose_victim(self, frames, refs, i):
        slot = self._lru_slot(frames)
        page = frames[slot]
        others = ", ".join(f"Page {frames[s]} (ref {self.last_used[s]})"
                           for s in range(len(frames)) if s != slot)
        why = (f"LRU removes the page that was used longest ago. Page {page} was last used at "
               f"reference {self.last_used[slot]}, which is earlier than {others if others else 'any other page'}. "
               f"So LRU removes Page {page}.")
        return slot, why

    def info(self, frames, refs, i):
        out = []
        full = None not in frames
        lru = self._lru_slot(frames) if any(p is not None for p in frames) else None
        for s, p in enumerate(frames):
            if p is None:
                out.append("")
            else:
                tag = "  <- LEAST RECENTLY USED" if (s == lru and full) else ""
                out.append(f"Last used: ref {self.last_used[s]}{tag}")
        return out

    def order_note(self, frames, refs, i):
        slots = sorted((s for s, p in enumerate(frames) if p is not None),
                       key=lambda s: self.last_used[s])
        if not slots:
            return "Recency order: RAM is empty."
        return ("Recency order (least -> most recently used): "
                + " -> ".join(str(frames[s]) for s in slots))

    def hit_note(self, page, slot, i):
        return (f"LRU updates Page {page}'s last-used time to reference {i + 1}, "
                f"so it becomes the most recently used page.")


def simulate(refs: List[int], n_frames: int) -> List[Step]:
    return run_simulation(refs, n_frames, LRUPolicy())
