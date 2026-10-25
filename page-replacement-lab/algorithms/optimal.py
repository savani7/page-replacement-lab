"""Optimal page replacement (Belady's MIN) - a theoretical benchmark."""
from __future__ import annotations

from typing import List, Optional

from .base import Policy, Step, run_simulation


def next_use(page: int, refs: List[int], i: int) -> Optional[int]:
    """0-based index of the next reference to ``page`` after position i, or None."""
    for j in range(i + 1, len(refs)):
        if refs[j] == page:
            return j
    return None


class OptimalPolicy(Policy):
    name = "Optimal"

    def reset(self, n_frames):
        pass

    def _victim(self, frames, refs, i):
        """Return (slot, never_used_slots). Ties among never-used pages -> lowest frame."""
        never = [s for s, p in enumerate(frames) if p is not None and next_use(p, refs, i) is None]
        if never:
            return never[0], never
        slot = max((s for s, p in enumerate(frames) if p is not None),
                   key=lambda s: next_use(frames[s], refs, i))
        return slot, never

    def choose_victim(self, frames, refs, i):
        slot, never = self._victim(frames, refs, i)
        page = frames[slot]
        bench = " (Optimal needs to know the future, so it is only a theoretical benchmark.)"
        if never:
            if len(never) == 1:
                why = (f"Optimal looks ahead: Page {page} is never used again in the remaining "
                       f"references, so removing it costs nothing later. Optimal removes Page {page}.")
            else:
                names = ", ".join(f"Page {frames[s]}" for s in never)
                why = (f"Optimal looks ahead: {names} are never used again - a tie. This simulator "
                       f"breaks ties by choosing the page in the lowest-numbered frame, so Optimal "
                       f"removes Page {page} (Frame {slot + 1}).")
        else:
            uses = ", ".join(f"Page {frames[s]} at ref {next_use(frames[s], refs, i) + 1}"
                             for s in range(len(frames)))
            why = (f"Optimal looks ahead: next uses are {uses}. Page {page} is needed the furthest "
                   f"in the future, so Optimal removes it.")
        return slot, why + bench

    def info(self, frames, refs, i):
        out = []
        full = None not in frames
        victim = self._victim(frames, refs, i)[0] if any(p is not None for p in frames) else None
        for s, p in enumerate(frames):
            if p is None:
                out.append("")
                continue
            nu = next_use(p, refs, i)
            text = "Never used again" if nu is None else f"Next use: ref {nu + 1}"
            if full and s == victim:
                text += "  <- FARTHEST (leaves first)"
            out.append(text)
        return out

    def order_note(self, frames, refs, i):
        rest = refs[i + 1:]
        if not rest:
            return "Remaining references: none (this is the last reference)."
        return "Remaining references: " + ", ".join(str(p) for p in rest)


def simulate(refs: List[int], n_frames: int) -> List[Step]:
    return run_simulation(refs, n_frames, OptimalPolicy())
