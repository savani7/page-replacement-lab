"""Shared simulation engine for page replacement (no GUI code in here).

Every algorithm is a small ``Policy`` object.  ``run_simulation`` walks through
the reference string once and records a ``Step`` for every reference.  The GUI
only *replays* these steps, so what you see on screen always comes from the
real algorithm calculation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

MAX_REFERENCES = 40
MAX_FRAMES = 8
MAX_PAGE = 99


class ValidationError(ValueError):
    """Raised with a friendly message when the user's input is not usable."""


def parse_reference_string(text) -> List[int]:
    """Turn '1, 2, 3, 1' into [1, 2, 3, 1] or raise ValidationError."""
    if text is None or not str(text).strip():
        raise ValidationError(
            "The page reference string is empty. Try something like: 1, 2, 3, 1, 4, 2, 5")
    tokens = [t for t in re.split(r"[,\s;]+", str(text).strip()) if t]
    pages: List[int] = []
    for token in tokens:
        if not re.fullmatch(r"\d+", token):
            raise ValidationError(
                f"'{token}' is not a valid page number. Use whole numbers "
                f"separated by commas, for example: 1, 2, 3.")
        value = int(token)
        if value > MAX_PAGE:
            raise ValidationError(
                f"Page number {value} is too large. Please use pages 0 to {MAX_PAGE}.")
        pages.append(value)
    if not pages:
        raise ValidationError("No page numbers were found. Try: 1, 2, 3, 1, 4, 2, 5")
    if len(pages) > MAX_REFERENCES:
        raise ValidationError(
            f"That is {len(pages)} references. Please use at most {MAX_REFERENCES} "
            f"so the animation stays readable.")
    return pages


def parse_frame_count(text) -> int:
    """Validate the number of RAM frames (1 to MAX_FRAMES)."""
    raw = str(text).strip() if text is not None else ""
    if not raw:
        raise ValidationError("Please enter the number of RAM frames, for example: 3")
    if not re.fullmatch(r"\d+", raw):
        raise ValidationError(f"'{raw}' is not a valid frame count. Enter a whole number such as 3.")
    value = int(raw)
    if value < 1:
        raise ValidationError("RAM needs at least 1 frame.")
    if value > MAX_FRAMES:
        raise ValidationError(f"Please use at most {MAX_FRAMES} frames so the boxes fit on screen.")
    return value


@dataclass
class Step:
    """Everything that happened for one page reference."""
    index: int                      # 0-based position in the reference string
    page: int                       # page requested
    kind: str                       # "hit", "load" (free frame) or "replace"
    frames_before: List[Optional[int]]
    frames_after: List[Optional[int]]
    slot: int                       # frame touched (hit frame / loaded frame)
    victim: Optional[int]           # page removed (replace only)
    victim_slot: Optional[int]
    hits: int                       # running totals after this step
    faults: int
    headline: str
    reason: str                     # the decision, explained
    explanation: str                # decision + result
    info_before: List[str]          # per-frame helper text (arrival / last used / next use)
    info_after: List[str]
    order_note: str                 # one line describing the algorithm's bookkeeping

    @property
    def hit(self) -> bool:
        return self.kind == "hit"

    @property
    def replaced(self) -> bool:
        return self.kind == "replace"

    @property
    def fault_rate(self) -> float:
        return self.faults / (self.index + 1)


class Policy:
    """Interface every algorithm implements."""
    name = "BASE"

    def reset(self, n_frames: int) -> None: ...

    def on_load(self, slot: int, page: int, i: int) -> None: ...

    def on_hit(self, slot: int, page: int, i: int) -> None: ...

    def choose_victim(self, frames, refs, i) -> Tuple[int, str]:
        raise NotImplementedError

    def info(self, frames, refs, i) -> List[str]:
        return ["" for _ in frames]

    def order_note(self, frames, refs, i) -> str:
        return ""

    def hit_note(self, page: int, slot: int, i: int) -> str:
        return ""


def run_simulation(refs: List[int], n_frames: int, policy: Policy) -> List[Step]:
    if not refs:
        raise ValidationError("The page reference string is empty.")
    if n_frames < 1:
        raise ValidationError("RAM needs at least 1 frame.")
    policy.reset(n_frames)
    frames: List[Optional[int]] = [None] * n_frames
    hits = faults = 0
    steps: List[Step] = []
    for i, page in enumerate(refs):
        before = list(frames)
        info_before = policy.info(frames, refs, i)
        note = policy.order_note(frames, refs, i)
        victim = victim_slot = None
        if page in frames:
            kind = "hit"
            slot = frames.index(page)
            hits += 1
            policy.on_hit(slot, page, i)
            headline = "PAGE HIT"
            reason = (f"Page {page} is already in RAM (Frame {slot + 1}). "
                      f"No page replacement is needed.")
            extra = policy.hit_note(page, slot, i)
            explanation = reason + (" " + extra if extra else "")
        elif None in frames:
            kind = "load"
            slot = frames.index(None)
            faults += 1
            frames[slot] = page
            policy.on_load(slot, page, i)
            headline = "PAGE FAULT"
            reason = (f"Page {page} is not in RAM, so this is a page fault. Frame {slot + 1} "
                      f"is still empty, so the page is simply loaded there. Nothing is removed.")
            explanation = reason
        else:
            kind = "replace"
            faults += 1
            slot, why = policy.choose_victim(frames, refs, i)
            victim = frames[slot]
            victim_slot = slot
            headline = "PAGE FAULT - REPLACEMENT"
            reason = f"Page {page} is not in RAM (page fault) and every frame is full. {why}"
            frames[slot] = page
            policy.on_load(slot, page, i)
            explanation = (reason + f" Page {victim} leaves Frame {slot + 1} and "
                           f"Page {page} takes its place.")
        steps.append(Step(
            index=i, page=page, kind=kind, frames_before=before, frames_after=list(frames),
            slot=slot, victim=victim, victim_slot=victim_slot, hits=hits, faults=faults,
            headline=headline, reason=reason, explanation=explanation,
            info_before=info_before, info_after=policy.info(frames, refs, i), order_note=note))
    return steps


def summarize(steps: List[Step]) -> dict:
    last = steps[-1]
    total = len(steps)
    return {"total": total, "hits": last.hits, "faults": last.faults,
            "fault_rate": last.faults / total}


def trace_text(steps: List[Step]) -> str:
    """Plain-text table of a simulation (used for worked examples)."""
    n = len(steps[0].frames_after)
    head = f"{'Ref':>3} {'Page':>4}  {'RAM (frames 1..' + str(n) + ')':<{max(3 * n + 1, 14)}} Result"
    lines = [head, "-" * len(head) + "-" * 18]
    for s in steps:
        ram = " ".join(f"{(p if p is not None else '-'):>2}" for p in s.frames_after)
        if s.kind == "hit":
            res = "HIT"
        elif s.kind == "load":
            res = "FAULT (free frame)"
        else:
            res = f"FAULT (removed {s.victim})"
        lines.append(f"{s.index + 1:>3} {s.page:>4}  {ram:<{max(3 * n + 1, 14)}} {res}")
    t = summarize(steps)
    lines.append(f"Total: {t['faults']} faults, {t['hits']} hits "
                 f"({t['fault_rate'] * 100:.1f}% fault rate)")
    return "\n".join(lines)
