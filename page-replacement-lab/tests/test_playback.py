import unittest

from tests.helpers import REFS, FRAMES
from algorithms import ALGORITHMS
from ui.playback import PlaybackController, FULL_PHASES, SHORT_PHASES


class FakeScheduler:
    """Stands in for Tk's after()/after_cancel(); we fire callbacks by hand."""

    def __init__(self):
        self.pending = {}
        self.next_id = 1
        self.cancelled = []

    def after(self, ms, fn):
        i = self.next_id
        self.next_id += 1
        self.pending[i] = (ms, fn)
        return i

    def after_cancel(self, i):
        self.cancelled.append(i)
        self.pending.pop(i, None)

    def fire_next(self):
        if not self.pending:
            return False
        i = min(self.pending)
        _, fn = self.pending.pop(i)
        fn()
        return True

    def run_all(self, limit=10000):
        n = 0
        while self.fire_next():
            n += 1
            assert n < limit


def make(steps):
    sched = FakeScheduler()
    log, finished, resets, states = [], [], [], []
    ctl = PlaybackController(
        sched,
        phases_for=lambda i: FULL_PHASES if steps[i].replaced else SHORT_PHASES,
        on_phase=lambda i, p: log.append((i, p)),
        on_finish=lambda: finished.append(1),
        on_reset=lambda: resets.append(1),
        on_state=states.append)
    ctl.load(len(steps))
    return ctl, sched, log, finished, resets, states


class TestPlayback(unittest.TestCase):
    def setUp(self):
        self.steps = ALGORITHMS["FIFO"](REFS, FRAMES)

    def expected_log(self):
        out = []
        for i, s in enumerate(self.steps):
            for p in (FULL_PHASES if s.replaced else SHORT_PHASES):
                out.append((i, p))
        return out

    def test_auto_plays_whole_sequence_without_clicks(self):
        ctl, sched, log, finished, *_ = make(self.steps)
        ctl.start()
        sched.run_all()
        self.assertEqual(log, self.expected_log())
        self.assertEqual(finished, [1])
        self.assertEqual(ctl.state, "finished")
        self.assertFalse(sched.pending)

    def test_pause_stops_and_resume_continues(self):
        ctl, sched, log, finished, *_ = make(self.steps)
        ctl.start()
        for _ in range(4):
            sched.fire_next()
        ctl.pause()
        count = len(log)
        self.assertEqual(ctl.state, "paused")
        self.assertFalse(sched.pending)       # pending callback was cancelled
        self.assertFalse(sched.fire_next())
        self.assertEqual(len(log), count)
        ctl.resume()
        sched.run_all()
        self.assertEqual(log, self.expected_log())  # no phase lost or repeated
        self.assertEqual(finished, [1])

    def test_restart_during_playback(self):
        ctl, sched, log, finished, resets, _ = make(self.steps)
        ctl.start()
        for _ in range(5):
            sched.fire_next()
        ctl.restart()
        self.assertEqual(len(sched.pending), 1)     # old callback cancelled, one new queued
        self.assertTrue(sched.cancelled)
        del log[:]
        sched.run_all()
        self.assertEqual(log, self.expected_log())  # begins again from reference 1
        self.assertEqual(len(resets), 2)
        self.assertEqual(finished, [1])

    def test_replay_after_finish(self):
        ctl, sched, log, finished, *_ = make(self.steps)
        ctl.start()
        sched.run_all()
        del log[:]
        ctl.start()
        sched.run_all()
        self.assertEqual(log, self.expected_log())
        self.assertEqual(finished, [1, 1])

    def test_manual_mode_steps_phase_by_phase(self):
        ctl, sched, log, finished, *_ = make(self.steps)
        ctl.start(auto=False)
        self.assertFalse(sched.pending)
        ctl.step_once()
        ctl.step_once()
        self.assertEqual(log, self.expected_log()[:2])
        for _ in range(len(self.expected_log())):
            ctl.step_once()
        self.assertEqual(log, self.expected_log())
        self.assertEqual(finished, [1])

    def test_stop_cancels_pending_callbacks(self):
        ctl, sched, *_ = make(self.steps)
        ctl.start()
        sched.fire_next()
        ctl.stop()
        self.assertFalse(sched.pending)

    def test_speed_changes_delay(self):
        ctl, *_ = make(self.steps)
        base = ctl.delay_for("decide")
        ctl.set_speed(2.0)
        self.assertEqual(ctl.delay_for("decide"), base // 2)

    def test_pause_when_not_playing_is_harmless(self):
        ctl, *_ = make(self.steps)
        ctl.pause()
        ctl.resume()
        self.assertEqual(ctl.state, "idle")


if __name__ == "__main__":
    unittest.main()
