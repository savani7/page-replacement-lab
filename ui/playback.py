"""Playback controller driven by tkinter's after() - never blocks, never sleeps.

The controller only needs an object with `after(ms, fn)` and `after_cancel(id)`,
so it can be unit-tested with a fake scheduler (see tests/test_playback.py).

Position model: (ref, phase) is the NEXT phase to show. Every selected algorithm
advances through the same reference at the same tick, which keeps comparison panels
synchronized. When one algorithm has fewer phases for a reference (e.g. a hit), its
panel simply holds its last phase while the others finish.
"""
from typing import Callable, List, Optional

IDLE, RUNNING, PAUSED, FINISHED = "idle", "running", "paused", "finished"


def delay_for_speed(speed: float) -> int:
    """Slider value 1..10 -> milliseconds per animation phase."""
    speed = max(1.0, min(10.0, float(speed)))
    return int(1750 - speed * 150)


class PlaybackController:
    def __init__(
        self,
        scheduler,
        on_phase: Callable[[int, int], None],
        on_complete: Callable[[], None],
        on_reset: Optional[Callable[[], None]] = None,
        on_state: Optional[Callable[[str], None]] = None,
        delay_ms: int = 700,
    ) -> None:
        self.sched = scheduler
        self.on_phase = on_phase
        self.on_complete = on_complete
        self.on_reset = on_reset or (lambda: None)
        self.on_state = on_state or (lambda s: None)
        self.delay_ms = delay_ms
        self.manual = False
        self.runs: List = []
        self.total = 0
        self.ref = 0
        self.phase = 0
        self.state = IDLE
        self._job = None

    # ------------------------------------------------------------------ setup
    @property
    def has_runs(self) -> bool:
        return bool(self.runs)

    def load(self, runs) -> None:
        self.cancel()
        self.runs = list(runs)
        self.total = max((len(r.steps) for r in self.runs), default=0)
        self._reset_position()

    def clear(self) -> None:
        self.cancel()
        self.runs = []
        self.total = 0
        self._reset_position()

    def set_delay(self, ms: int) -> None:
        self.delay_ms = max(1, int(ms))

    # --------------------------------------------------------------- controls
    def start(self) -> bool:
        if not self.runs:
            return False
        self._cancel_job()
        self._reset_position()
        self.on_reset()
        if self.manual:
            self._set_state(PAUSED)
        else:
            self._set_state(RUNNING)
            self._schedule(50)
        return True

    def pause(self) -> None:
        if self.state == RUNNING:
            self._cancel_job()
            self._set_state(PAUSED)

    def resume(self) -> None:
        if self.state == PAUSED:
            self._set_state(RUNNING)
            self._schedule(50)

    def restart(self) -> bool:
        if not self.runs:
            return False
        return self.start()

    def step(self) -> None:
        """Manual mode: advance exactly one animation phase."""
        if self.state != PAUSED:
            return
        self._do_tick()

    def cancel(self) -> None:
        """Stop any pending callback (used when leaving a screen or changing inputs)."""
        self._cancel_job()
        if self.state != IDLE:
            self._set_state(IDLE)

    # --------------------------------------------------------------- internals
    def _reset_position(self) -> None:
        self.ref = 0
        self.phase = 0
        self._set_state(IDLE)

    def _set_state(self, state: str) -> None:
        self.state = state
        self.on_state(state)

    def _cancel_job(self) -> None:
        if self._job is not None:
            try:
                self.sched.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _schedule(self, ms: int) -> None:
        self._cancel_job()
        self._job = self.sched.after(ms, self._tick)

    def _phase_count(self, ref: int) -> int:
        return max(len(r.phases[ref]) for r in self.runs)

    def _do_tick(self) -> None:
        if self.ref >= self.total:
            self._finish()
            return
        count = self._phase_count(self.ref)
        self.on_phase(self.ref, self.phase)
        self.phase += 1
        if self.phase >= count:
            self.ref += 1
            self.phase = 0

    def _tick(self) -> None:
        self._job = None
        if self.state != RUNNING:
            return
        self._do_tick()
        if self.state == RUNNING:
            self._schedule(self.delay_ms)

    def _finish(self) -> None:
        self._cancel_job()
        self._set_state(FINISHED)
        self.on_complete()
