"""Common interface for page replacement policies."""
from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass
class Decision:
    """The result of asking a policy which resident page to evict."""

    victim: int
    reason: str
    details: List[str] = field(default_factory=list)
    note: str = ""


class ReplacementPolicy:
    """Base class. The engine calls the hooks below in this order:

    * hit            -> on_hit(page, index)
    * fault, free    -> on_load(page, index)
    * fault, full    -> choose_victim(...), on_evict(victim), on_load(page, index)
    """

    name = "BASE"
    full_name = "Base policy"
    behavior = ""

    def reset(self) -> None:
        pass

    def on_hit(self, page: int, index: int) -> None:
        pass

    def on_load(self, page: int, index: int) -> None:
        pass

    def on_evict(self, page: int) -> None:
        pass

    def choose_victim(
        self, frames: Sequence[Optional[int]], refs: Sequence[int], index: int
    ) -> Decision:
        raise NotImplementedError
