from algorithms.simulator_engine import simulate
from ui.playback import (FINISHED, IDLE, PAUSED, RUNNING, PlaybackController,
                         delay_for_speed)

SPEC = [1, 2, 3, 1, 4, 2, 5]


class FakeScheduler:
    """Stands in for tkinter's after()/after_cancel() so no window is needed."""

    def __init__(self):
        self.jobs = {}
        self.next_id = 1

    def after(self, ms, fn):
        job_id = self.next_id
        self.next_id += 1
        self.jobs[job_id] = (ms, fn)
        return job_id

    def after_cancel(self, job_id):
        self.jobs.pop(job_id, None)

    def run_next(self):
        if not self.jobs:
            return False
        job_id = min(self.jobs)
        _, fn = self.jobs.pop(job_id)
        fn()
        return True

    def run_all(self, limit=5000):
        n = 0
        while self.run_next():
            n += 1
            assert n < limit, "runaway scheduling"
        return n


def make(algos=("FIFO", "LRU", "Optimal"), refs=SPEC, frames=3, manual=False):
    sched = FakeScheduler()
    log = {"events": [], "complete": 0, "resets": 0, "states": []}
    ctl = PlaybackController(
        sched,
        on_phase=lambda r, p: log["events"].append((r, p)),
        on_complete=lambda: log.__setitem__("complete", log["complete"] + 1),
        on_reset=lambda: log.__setitem__("resets", log["resets"] + 1),
        on_state=log["states"].append,
    )
    ctl.manual = manual
    runs = [simulate(a, refs, frames) for a in algos]
    ctl.load(runs)
    return ctl, sched, log, runs


def expected_events(runs):
    out = []
    for ref in range(len(runs[0].steps)):
        for ph in range(max(len(r.phases[ref]) for r in runs)):
            out.append((ref, ph))
    return out


def test_autoplay_runs_to_completion_without_next_clicks():
    ctl, sched, log, runs = make()
    assert ctl.start()
    sched.run_all()
    assert ctl.state == FINISHED
    assert log["complete"] == 1
    assert log["events"] == expected_events(runs)
    assert not sched.jobs


def test_pause_really_stops_and_resume_continues_from_same_place():
    ctl, sched, log, runs = make()
    ctl.start()
    for _ in range(5):
        sched.run_next()
    shown = list(log["events"])
    ctl.pause()
    assert ctl.state == PAUSED
    assert not sched.jobs              # nothing left scheduled
    assert sched.run_next() is False
    assert log["events"] == shown      # nothing advanced while paused
    ctl.resume()
    assert ctl.state == RUNNING
    sched.run_all()
    assert log["events"] == expected_events(runs)   # no repeats, no skips
    assert log["complete"] == 1


def test_resume_when_not_paused_is_ignored():
    ctl, sched, log, runs = make()
    ctl.start()
    ctl.resume()
    assert len(sched.jobs) == 1        # still only one pending callback


def test_restart_during_playback_resets_and_does_not_duplicate_callbacks():
    ctl, sched, log, runs = make()
    ctl.start()
    for _ in range(6):
        sched.run_next()
    resets_before = log["resets"]
    ctl.restart()
    assert log["resets"] == resets_before + 1
    assert (ctl.ref, ctl.phase) == (0, 0)
    assert len(sched.jobs) == 1        # old callback cancelled
    log["events"].clear()
    sched.run_all()
    assert log["events"] == expected_events(runs)
    assert log["complete"] == 1


def test_restart_after_finish_and_while_paused():
    ctl, sched, log, runs = make()
    ctl.start()
    sched.run_all()
    ctl.restart()
    assert ctl.state == RUNNING
    sched.run_all()
    assert log["complete"] == 2
    ctl.restart()
    sched.run_next()
    ctl.pause()
    ctl.restart()
    assert ctl.state == RUNNING and len(sched.jobs) == 1


def test_cancel_when_leaving_screen():
    ctl, sched, log, runs = make()
    ctl.start()
    sched.run_next()
    ctl.cancel()
    assert ctl.state == IDLE and not sched.jobs
    sched.run_all()
    assert log["complete"] == 0


def test_manual_mode_steps_one_phase_at_a_time():
    ctl, sched, log, runs = make(manual=True)
    ctl.start()
    assert ctl.state == PAUSED and not sched.jobs
    ctl.step()
    assert log["events"] == [(0, 0)]
    ctl.step()
    assert log["events"] == [(0, 0), (0, 1)]
    for _ in range(len(expected_events(runs)) - 2):
        ctl.step()
    assert log["events"] == expected_events(runs)
    assert ctl.state == PAUSED
    ctl.step()                          # one more click reveals the final result
    assert ctl.state == FINISHED and log["complete"] == 1


def test_manual_mode_can_switch_to_autoplay_with_resume():
    ctl, sched, log, runs = make(manual=True)
    ctl.start()
    ctl.step()
    ctl.resume()
    sched.run_all()
    assert log["events"] == expected_events(runs)


def test_two_and_three_algorithm_runs_stay_synchronized():
    for algos in (("FIFO", "LRU"), ("LRU", "Optimal"), ("FIFO", "Optimal"),
                  ("FIFO", "LRU", "Optimal")):
        ctl, sched, log, runs = make(algos)
        ctl.start()
        sched.run_all()
        assert log["events"] == expected_events(runs)
        # every algorithm is asked to show the same (ref, phase) at each tick
        refs_seen = [e[0] for e in log["events"]]
        assert refs_seen == sorted(refs_seen)


def test_switching_selection_mid_playback_cancels_old_run():
    ctl, sched, log, runs = make(("FIFO", "LRU", "Optimal"))
    ctl.start()
    sched.run_next()
    new_runs = [simulate(a, SPEC, 3) for a in ("FIFO", "LRU")]
    ctl.load(new_runs)
    assert ctl.state == IDLE and not sched.jobs
    log["events"].clear()
    ctl.start()
    sched.run_all()
    assert log["events"] == expected_events(new_runs)


def test_start_without_runs_does_nothing():
    ctl, sched, log, _ = make()
    ctl.clear()
    assert ctl.start() is False
    assert not sched.jobs


def test_single_frame_and_single_reference_finish():
    for frames, refs in ((1, SPEC), (8, [3]), (2, [5, 5, 5])):
        ctl, sched, log, runs = make(refs=refs, frames=frames)
        ctl.start()
        sched.run_all()
        assert ctl.state == FINISHED and log["events"] == expected_events(runs)


def test_speed_mapping_is_monotonic_and_positive():
    delays = [delay_for_speed(v) for v in range(1, 11)]
    assert delays == sorted(delays, reverse=True)
    assert min(delays) > 0
