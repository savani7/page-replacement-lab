"""Optimal (Belady's MIN) page replacement - a theoretical benchmark."""
from typing import List, Optional, Sequence

from .base import Decision, ReplacementPolicy


def next_use(refs: Sequence[int], page: int, after_index: int) -> Optional[int]:
    """Index of the next reference to `page` after `after_index`, or None."""
    for j in range(after_index + 1, len(refs)):
        if refs[j] == page:
            return j
    return None


class OptimalPolicy(ReplacementPolicy):
    name = "Optimal"
    full_name = "Optimal (farthest future use)"
    behavior = (
        "Optimal removes the page whose next use is farthest in the future (or that "
        "is never used again). It gives the fewest possible page faults for a given "
        "input, but it needs to know future references, so real systems cannot use "
        "it. It is a theoretical benchmark."
    )

    def choose_victim(
        self, frames: Sequence[Optional[int]], refs: Sequence[int], index: int
    ) -> Decision:
        infos = []  # (slot, page, next_use_index_or_None)
        for slot, page in enumerate(frames):
            if page is not None:
                infos.append((slot, page, next_use(refs, page, index)))

        # Deterministic choice: farthest next use wins; "never" counts as infinity;
        # on a tie the page in the lowest-numbered frame is chosen.
        best = None
        best_dist = -1.0
        for slot, page, nxt in infos:
            dist = float("inf") if nxt is None else float(nxt)
            if dist > best_dist:
                best, best_dist = (slot, page, nxt), dist
        _, victim, victim_next = best

        remaining = refs[index + 1:]
        remaining_text = ", ".join(str(p) for p in remaining) if remaining else "none"
        details: List[str] = [f"Remaining references: {remaining_text}"]
        for slot, page, nxt in infos:
            if nxt is None:
                text = f"Page {page} - never used again"
            else:
                text = f"Page {page} - next used at reference {nxt + 1} (in {nxt - index} steps)"
            if page == victim:
                text += "  <- farthest, will be removed"
            details.append(text)

        never = [p for _, p, nxt in infos if nxt is None]
        if victim_next is None:
            reason = f"Optimal removes Page {victim} because it is never used again."
            if len(never) > 1:
                others = ", ".join(str(p) for p in never)
                reason += (
                    f" (Pages {others} are never used again; the one in the "
                    f"lowest-numbered frame is chosen.)"
                )
        else:
            reason = (
                f"Optimal removes Page {victim} because its next use (reference "
                f"{victim_next + 1}) is farther in the future than the other "
                f"resident pages."
            )
        note = (
            "Optimal is a theoretical benchmark: it needs to know future page "
            "references, so a real operating system cannot use it."
        )
        return Decision(victim=victim, reason=reason, details=details, note=note)
