"""Timer-driven playback (no widgets here, so it can be unit-tested).

The controller never sleeps.  It renders one (step, phase) pair, then asks the
scheduler (any object with ``after(ms, fn)`` / ``after_cancel(id)``, e.g. a
Tk widget) to call it again later.  Pause/restart simply cancel the pending call.
"""
from __future__ import annotations

from typing import Callable, List, Optional

PHASE_DELAYS = {"incoming": 800, "decide": 1700, "remove": 1000, "enter": 1000, "done": 800}
FULL_PHASES = ["incoming", "decide", "remove", "enter", "done"]
SHORT_PHASES = ["incoming", "enter", "done"]


class PlaybackController:
    IDLE, PLAYING, PAUSED, FINISHED = "idle", "playing", "paused", "finished"

    def __init__(self, scheduler, phases_for: Callable[[int], List[str]],
                 on_phase: Callable[[int, str], None],
                 on_finish: Optional[Callable[[], None]] = None,
                 on_reset: Optional[Callable[[], None]] = None,
                 on_state: Optional[Callable[[str], None]] = None):
        self.sched = scheduler
        self.phases_for = phases_for
        self.on_phase = on_phase
        self.on_finish = on_finish
        self.on_reset = on_reset
        self.on_state = on_state
        self.total = 0
        self.speed = 1.0
        self.state = self.IDLE
        self.step_i = 0
        self.phase_i = 0
        self._after_id = None

    # ---- public API -------------------------------------------------
    def load(self, total_steps: int) -> None:
        self._cancel()
        self.total = total_steps
        self._rewind()
        self._set_state(self.IDLE)

    def start(self, auto: bool = True) -> None:
        """(Re)start from the first reference."""
        if self.total <= 0:
            return
        self._cancel()
        self._rewind()
        if self.on_reset:
            self.on_reset()
        if auto:
            self._set_state(self.PLAYING)
            self._schedule(0)
        else:
            self._set_state(self.PAUSED)

    restart = start

    def pause(self) -> None:
        if self.state == self.PLAYING:
            self._cancel()
            self._set_state(self.PAUSED)

    def resume(self) -> None:
        if self.state == self.PAUSED:
            self._set_state(self.PLAYING)
            self._schedule(0)

    def stop(self) -> None:
        """Cancel pending callbacks (used when leaving the screen)."""
        self._cancel()
        if self.state == self.PLAYING:
            self._set_state(self.PAUSED)

    def step_once(self) -> None:
        """Manual mode: show the next phase."""
        if self.state == self.PLAYING:
            self.pause()
        if self.state == self.PAUSED:
            self._render_and_advance()

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.1, float(speed))

    def delay_for(self, phase: str) -> int:
        return max(1, int(PHASE_DELAYS.get(phase, 800) / self.speed))

    # ---- internals --------------------------------------------------
    def _rewind(self):
        self.step_i = 0
        self.phase_i = 0

    def _set_state(self, state):
        self.state = state
        if self.on_state:
            self.on_state(state)

    def _schedule(self, delay):
        self._after_id = self.sched.after(delay, self._tick)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.sched.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _tick(self):
        self._after_id = None
        if self.state != self.PLAYING:
            return
        delay = self._render_and_advance()
        if self.state == self.PLAYING:
            self._schedule(delay)

    def _render_and_advance(self) -> int:
        if self.state == self.FINISHED or self.step_i >= self.total:
            return 0
        phases = self.phases_for(self.step_i)
        phase = phases[self.phase_i]
        self.on_phase(self.step_i, phase)
        delay = self.delay_for(phase)
        self.phase_i += 1
        if self.phase_i >= len(phases):
            self.phase_i = 0
            self.step_i += 1
            if self.step_i >= self.total:
                self._cancel()
                self._set_state(self.FINISHED)
                if self.on_finish:
                    self.on_finish()
        return delay
