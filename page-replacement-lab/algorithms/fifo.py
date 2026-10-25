"""FIFO - First In, First Out."""
from __future__ import annotations

from typing import List

from .base import Policy, Step, run_simulation


class FIFOPolicy(Policy):
    name = "FIFO"

    def reset(self, n_frames):
        self.arrival = [None] * n_frames   # arrival number of the page in each frame
        self.counter = 0

    def on_load(self, slot, page, i):
        self.counter += 1
        self.arrival[slot] = self.counter

    def on_hit(self, slot, page, i):
        pass  # a hit never changes FIFO's arrival order

    def _oldest_slot(self, frames):
        return min((s for s, p in enumerate(frames) if p is not None),
                   key=lambda s: self.arrival[s])

    def choose_victim(self, frames, refs, i):
        slot = self._oldest_slot(frames)
        page = frames[slot]
        order = sorted((s for s, p in enumerate(frames) if p is not None),
                       key=lambda s: self.arrival[s])
        order_txt = " -> ".join(f"Page {frames[s]}" for s in order)
        why = (f"FIFO removes the page that entered RAM first. Page {page} arrived earliest "
               f"(arrival #{self.arrival[slot]}). Arrival order, oldest first: {order_txt}. "
               f"So FIFO removes Page {page}.")
        return slot, why

    def info(self, frames, refs, i):
        out = []
        oldest = self._oldest_slot(frames) if any(p is not None for p in frames) else None
        full = None not in frames
        for s, p in enumerate(frames):
            if p is None:
                out.append("")
            else:
                tag = "  <- OLDEST (leaves first)" if (s == oldest and full) else ""
                out.append(f"Arrived #{self.arrival[s]}{tag}")
        return out

    def order_note(self, frames, refs, i):
        slots = sorted((s for s, p in enumerate(frames) if p is not None),
                       key=lambda s: self.arrival[s])
        if not slots:
            return "Arrival order: RAM is empty."
        return "Arrival order (oldest -> newest): " + " -> ".join(str(frames[s]) for s in slots)

    def hit_note(self, page, slot, i):
        return "FIFO does not change the arrival order on a hit."


def simulate(refs: List[int], n_frames: int) -> List[Step]:
    return run_simulation(refs, n_frames, FIFOPolicy())
