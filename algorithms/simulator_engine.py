"""Simulation engine: validation, step-by-step simulation, animation phases, summaries.

Pure Python - no tkinter or customtkinter imports, so everything here is unit-testable.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from .fifo import FIFOPolicy
from .lru import LRUPolicy
from .optimal import OptimalPolicy

ALGORITHM_ORDER = ("FIFO", "LRU", "Optimal")
ALGORITHMS = {"FIFO": FIFOPolicy, "LRU": LRUPolicy, "Optimal": OptimalPolicy}
ALGORITHM_FULL_NAMES = {
    "FIFO": FIFOPolicy.full_name,
    "LRU": LRUPolicy.full_name,
    "Optimal": OptimalPolicy.full_name,
}

MIN_FRAMES = 1
MAX_FRAMES = 8
MAX_REFS = 100
MAX_PAGE = 99
MAX_INPUT_CHARS = 600

EXAMPLES = [
    ("7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1", 3),
    ("1, 2, 3, 1, 4, 2, 5", 3),
]


class InputError(ValueError):
    """Raised with a beginner-friendly message when user input is invalid."""


# --------------------------------------------------------------------------- input

def parse_reference_string(text) -> List[int]:
    if text is None or not str(text).strip():
        raise InputError(
            "The page reference string is empty. Type page numbers separated by "
            "commas, for example: 1, 2, 3, 1, 4, 2, 5"
        )
    text = str(text)
    if len(text) > MAX_INPUT_CHARS:
        raise InputError(
            f"The reference string is too long ({len(text)} characters). "
            f"Please keep it under {MAX_INPUT_CHARS} characters."
        )
    tokens = [t for t in re.split(r"[,\s]+", text.strip()) if t]
    refs: List[int] = []
    for tok in tokens:
        if re.fullmatch(r"-\d+", tok):
            raise InputError(
                f"Page numbers cannot be negative (found '{tok}'). "
                f"Use whole numbers from 0 to {MAX_PAGE}."
            )
        if not re.fullmatch(r"[0-9]+", tok):
            raise InputError(
                f"'{tok}' is not a valid page number. Use only whole numbers "
                f"separated by commas or spaces, for example: 1, 2, 3"
            )
        page = int(tok)
        if page > MAX_PAGE:
            raise InputError(
                f"Page number {page} is too large. Use numbers from 0 to {MAX_PAGE}."
            )
        refs.append(page)
    if not refs:
        raise InputError("No page numbers were found. Example: 1, 2, 3, 1, 4, 2, 5")
    if len(refs) > MAX_REFS:
        raise InputError(
            f"Too many references ({len(refs)}). The maximum is {MAX_REFS}."
        )
    return refs


def validate_frames(value) -> int:
    if isinstance(value, bool):
        raise InputError("The number of frames must be a whole number.")
    if isinstance(value, int):
        n = value
    else:
        s = str(value).strip() if value is not None else ""
        if not s:
            raise InputError(
                f"The number of frames is empty. Enter a whole number from "
                f"{MIN_FRAMES} to {MAX_FRAMES}."
            )
        if not re.fullmatch(r"-?[0-9]+", s):
            raise InputError(
                f"'{s}' is not a valid number of frames. Enter a whole number from "
                f"{MIN_FRAMES} to {MAX_FRAMES}."
            )
        n = int(s)
    if n < MIN_FRAMES or n > MAX_FRAMES:
        raise InputError(
            f"The number of frames must be between {MIN_FRAMES} and {MAX_FRAMES} "
            f"(you entered {n})."
        )
    return n


def validate_inputs(ref_text, frames_value):
    return parse_reference_string(ref_text), validate_frames(frames_value)


def validate_comparison_selection(names: Iterable[str]) -> List[str]:
    names = list(names)
    unknown = [n for n in names if n not in ALGORITHMS]
    if unknown:
        raise InputError(f"Unknown algorithm: {', '.join(unknown)}.")
    chosen = [n for n in ALGORITHM_ORDER if n in set(names)]
    if len(chosen) < 2:
        raise InputError("Please select at least two algorithms to compare.")
    return chosen


# --------------------------------------------------------------------- simulation

def fault_rate(faults: int, processed: int) -> float:
    return 0.0 if processed <= 0 else faults / processed * 100.0


def format_frames(frames: Sequence[Optional[int]]) -> str:
    return " | ".join(
        f"Frame {i + 1}: " + ("empty" if p is None else f"Page {p}")
        for i, p in enumerate(frames)
    )


@dataclass
class Step:
    index: int
    page: int
    hit: bool
    slot: int
    victim: Optional[int]
    frames_before: List[Optional[int]]
    frames_after: List[Optional[int]]
    hits: int
    faults: int
    processed: int
    fault_rate: float
    reason: str = ""
    details: List[str] = field(default_factory=list)
    note: str = ""


@dataclass(frozen=True)
class Phase:
    """One animation frame of a step. `kind` drives how the UI draws it."""

    kind: str      # request | hit | fault | select | evict | load | done
    status: str    # HIT | PAGE FAULT | LOADING | EVICTING | CHECKING
    title: str
    text: str


@dataclass
class SimulationResult:
    algorithm: str
    refs: List[int]
    num_frames: int
    steps: List[Step]
    phases: List[List[Phase]]

    @property
    def total(self) -> int:
        return len(self.refs)

    @property
    def hits(self) -> int:
        return self.steps[-1].hits if self.steps else 0

    @property
    def faults(self) -> int:
        return self.steps[-1].faults if self.steps else 0

    @property
    def fault_rate(self) -> float:
        return fault_rate(self.faults, self.total)

    @property
    def final_frames(self) -> List[Optional[int]]:
        return list(self.steps[-1].frames_after) if self.steps else [None] * self.num_frames


def simulate(algorithm: str, refs: Sequence[int], num_frames: int) -> SimulationResult:
    if algorithm not in ALGORITHMS:
        raise InputError(f"Unknown algorithm: {algorithm}.")
    refs = list(refs)
    num_frames = validate_frames(num_frames)
    policy = ALGORITHMS[algorithm]()
    policy.reset()
    frames: List[Optional[int]] = [None] * num_frames
    steps: List[Step] = []
    hits = faults = 0

    for i, page in enumerate(refs):
        before = list(frames)
        victim = None
        reason, details, note = "", [], ""
        if page in frames:
            hit = True
            hits += 1
            slot = frames.index(page)
            policy.on_hit(page, i)
        else:
            hit = False
            faults += 1
            if None in frames:
                slot = frames.index(None)
            else:
                decision = policy.choose_victim(frames, refs, i)
                victim = decision.victim
                reason, details, note = decision.reason, decision.details, decision.note
                slot = frames.index(victim)
                policy.on_evict(victim)
            frames[slot] = page
            policy.on_load(page, i)
        processed = i + 1
        steps.append(
            Step(
                index=i, page=page, hit=hit, slot=slot, victim=victim,
                frames_before=before, frames_after=list(frames),
                hits=hits, faults=faults, processed=processed,
                fault_rate=fault_rate(faults, processed),
                reason=reason, details=details, note=note,
            )
        )

    result = SimulationResult(algorithm, refs, num_frames, steps, [])
    result.phases = [build_phases(s, algorithm, len(refs)) for s in steps]
    return result


def build_phases(step: Step, algorithm: str, total: int) -> List[Phase]:
    p, k = step.page, step.slot + 1
    request = Phase(
        "request", "CHECKING", f"REQUEST - PAGE {p}",
        f"Reference {step.index + 1} of {total}: the process asks for Page {p}. "
        f"The operating system checks every frame in RAM.",
    )
    if step.hit:
        extra = {
            "LRU": f" LRU updates Page {p}'s last-used time to reference {step.index + 1}.",
            "FIFO": " FIFO does not change the arrival order on a hit.",
        }.get(algorithm, "")
        return [
            request,
            Phase("hit", "HIT", "HIT",
                  f"Page {p} is already in Frame {k}. No page fault, nothing is "
                  f"replaced.{extra}"),
        ]

    if step.victim is None:
        return [
            request,
            Phase("fault", "PAGE FAULT", "STEP 1 - PAGE FAULT",
                  f"Page {p} is not present in RAM. A free frame exists, so no page "
                  f"needs to be removed."),
            Phase("load", "LOADING", "STEP 2 - LOAD NEW PAGE",
                  f"Frame {k}: Page {p} -> LOADED"),
            Phase("done", "PAGE FAULT", "RESULT",
                  f"Frame {k} now holds Page {p}.\n{format_frames(step.frames_after)}"),
        ]

    select_text = step.reason
    if step.details:
        select_text += "\n" + "\n".join(step.details)
    if step.note:
        select_text += "\n" + step.note
    return [
        request,
        Phase("fault", "PAGE FAULT", "STEP 1 - PAGE FAULT",
              f"Page {p} is not present in RAM and all frames are full, so the "
              f"operating system must choose a victim using {algorithm}."),
        Phase("select", "PAGE FAULT", "STEP 2 - SELECT VICTIM", select_text),
        Phase("evict", "EVICTING", "STEP 3 - REMOVE VICTIM",
              f"Frame {k}: Page {step.victim} -> EVICTED"),
        Phase("load", "LOADING", "STEP 4 - LOAD NEW PAGE",
              f"Frame {k}: Page {p} -> LOADED"),
        Phase("done", "PAGE FAULT", "RESULT",
              f"Page {step.victim} was replaced by Page {p} in Frame {k}.\n"
              f"{format_frames(step.frames_after)}"),
    ]


# ----------------------------------------------------------------------- summaries

def result_summary(result: SimulationResult) -> str:
    policy = ALGORITHMS[result.algorithm]
    return (
        f"{result.algorithm} processed {result.total} references with "
        f"{result.num_frames} frame(s): {result.hits} hits and {result.faults} page "
        f"faults ({result.fault_rate:.1f}% fault rate).\n\n{policy.behavior}"
    )


def compare_summary(results: Dict[str, SimulationResult]):
    """Returns (best_names, explanation_text) for the selected algorithms only."""
    ordered = [n for n in ALGORITHM_ORDER if n in results]
    if not ordered:
        return [], ""
    min_faults = min(results[n].faults for n in ordered)
    best = [n for n in ordered if results[n].faults == min_faults]
    if len(best) == len(ordered):
        text = (
            f"All selected algorithms had the same number of page faults "
            f"({min_faults}) on this input."
        )
    elif len(best) == 1:
        text = (
            f"{best[0]} had the fewest page faults ({min_faults}) on this reference "
            f"string and frame count."
        )
    else:
        text = (
            f"{' and '.join(best)} tied for the fewest page faults ({min_faults}) on "
            f"this reference string and frame count."
        )
    text += (
        " This only describes this one input: no practical algorithm is best for "
        "every reference string."
    )
    if "Optimal" in results:
        text += (
            " Optimal is a theoretical benchmark that uses knowledge of future "
            "references, so its fault count is the minimum possible for this input."
        )
    return best, text
