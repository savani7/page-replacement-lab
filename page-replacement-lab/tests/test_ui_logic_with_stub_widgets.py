"""Runs the REAL screen/panel code against fake widgets.

This is NOT a real GUI test (nothing is drawn).  It only proves that the screen
code - input validation, start/pause/resume/restart wiring, per-phase rendering,
final results - runs end-to-end without exceptions.  Always also launch
`python main.py` yourself.
"""
import sys
import types
import unittest

from tests.helpers import REFS  # noqa: F401  (adds project root to sys.path)


class _W:
    """Permissive stand-in for any tkinter / customtkinter widget."""
    _afters = []

    def __init__(self, *a, **k):
        self._value = None
        self._cfg = dict(k)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: 0

    def configure(self, **k):
        self._cfg.update(k)

    cget = lambda self, k: self._cfg.get(k)
    insert = lambda self, i, t: setattr(self, "_value", (self._value or "") + t)
    delete = lambda self, *a: setattr(self, "_value", "")
    set = lambda self, v: setattr(self, "_value", v)

    def get(self):
        return self._value

    def winfo_children(self):
        return []

    def winfo_ismapped(self):
        return False

    def after(self, ms, fn=None):
        _W._afters.append(fn)
        return len(_W._afters)

    def after_cancel(self, i):
        pass


class _Var:
    def __init__(self, value=None):
        self.v = value

    def get(self):
        return self.v

    def set(self, v):
        self.v = v


def _install():
    saved = {k: sys.modules.get(k) for k in ("customtkinter", "tkinter")}
    ctk = types.ModuleType("customtkinter")
    for name in ("CTk CTkFrame CTkLabel CTkButton CTkEntry CTkSlider CTkCheckBox CTkScrollbar "
                 "CTkScrollableFrame CTkSegmentedButton CTkTabview").split():
        setattr(ctk, name, type(name, (_W,), {}))
    ctk.StringVar, ctk.BooleanVar = _Var, _Var
    tk = types.ModuleType("tkinter")
    tk.Canvas = type("Canvas", (_W,), {})
    tk.LAST = "last"
    sys.modules["customtkinter"], sys.modules["tkinter"] = ctk, tk
    for m in [m for m in sys.modules if m == "ui" or m.startswith("ui.")]:
        if m not in ("ui", "ui.playback"):
            del sys.modules[m]
    return saved


def _restore(saved):
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v
    for m in [m for m in sys.modules if m.startswith("ui.") and m != "ui.playback"]:
        del sys.modules[m]


def _drain():
    guard = 0
    while _W._afters and guard < 5000:
        fn = _W._afters.pop(0)
        if fn:
            fn()
        guard += 1
    return guard


class TestScreensWithStubs(unittest.TestCase):
    def setUp(self):
        self.saved = _install()
        _W._afters.clear()

    def tearDown(self):
        _restore(self.saved)

    def _fill(self, screen, refs, frames):
        screen.refs_entry.delete(0, "end")
        screen.refs_entry.insert(0, refs)
        screen.frames_entry.delete(0, "end")
        screen.frames_entry.insert(0, frames)

    def test_simulator_runs_every_algorithm_to_the_end(self):
        from ui.simulator import SimulatorScreen
        s = SimulatorScreen(None, types.SimpleNamespace(show=lambda n: None))
        for algo in ("FIFO", "LRU", "Optimal"):
            s.algo_var.set(algo)
            s.start()
            _drain()
            self.assertEqual(s.controller.state, "finished", algo)
            self.assertEqual(s.panel.stats["faults"].cget("text"), str(s.steps[-1].faults))

    def test_simulator_bad_input_shows_message_not_crash(self):
        from ui.simulator import SimulatorScreen
        s = SimulatorScreen(None, types.SimpleNamespace(show=lambda n: None))
        self._fill(s, "1, x, 3", "3")
        s.start()
        self.assertIn("'x'", s.error.cget("text"))
        self._fill(s, "1, 2", "0")
        s.start()
        self.assertIn("at least 1", s.error.cget("text"))
        self._fill(s, "", "3")
        s.start()
        self.assertIn("empty", s.error.cget("text"))

    def test_pause_resume_restart_and_replay(self):
        from ui.simulator import SimulatorScreen
        s = SimulatorScreen(None, types.SimpleNamespace(show=lambda n: None))
        s.start()
        for _ in range(3):
            _W._afters.pop(0)()
        s.pause()
        self.assertEqual(s.controller.state, "paused")
        s.resume()
        self.assertEqual(s.controller.state, "playing")
        s.restart()
        _drain()
        self.assertEqual(s.controller.state, "finished")
        s.start()                       # replay
        _drain()
        self.assertEqual(s.controller.state, "finished")

    def test_manual_mode(self):
        from ui.simulator import SimulatorScreen
        s = SimulatorScreen(None, types.SimpleNamespace(show=lambda n: None))
        s.manual_var.set(True)
        s.start()
        self.assertEqual(s.controller.state, "paused")
        for _ in range(60):
            s.next_step()
        self.assertEqual(s.controller.state, "finished")

    def test_leaving_cancels_playback(self):
        from ui.simulator import SimulatorScreen
        s = SimulatorScreen(None, types.SimpleNamespace(show=lambda n: None))
        s.start()
        s.on_leave()
        self.assertNotEqual(s.controller.state, "playing")

    def test_battle_arena_synchronised_and_summary(self):
        from ui.battle_arena import BattleArenaScreen
        a = BattleArenaScreen(None, types.SimpleNamespace(show=lambda n: None))
        self._fill(a, "1, 2, 3, 1, 4, 2, 5", "3")
        a.start()
        _drain()
        self.assertEqual(a.controller.state, "finished")
        self.assertEqual({n: r.faults for n, r in a.results.items()},
                         {"FIFO": 5, "LRU": 6, "Optimal": 5})
        self.assertIn("FIFO (5) beat LRU (6)", a.res_text.cget("text"))

    def test_learning_and_quiz_content_build(self):
        from ui.learning_content import TABS
        for name, fn in TABS:
            blocks = fn()
            self.assertGreater(len(blocks), 4, name)
        from ui.quiz_data import build_questions, VIVA
        qs = build_questions()
        self.assertGreaterEqual(len(qs), 15)
        for q in qs:
            self.assertNotIn(q["correct"], q["wrong"])
            self.assertGreaterEqual(len(q["wrong"]), 2)
        calc = [q for q in qs if "page faults does" in q["question"]]
        answers = sorted(q["correct"] for q in calc[:3])
        self.assertEqual(answers, ["5", "5", "6"])
        self.assertGreaterEqual(len(VIVA), 10)


if __name__ == "__main__":
    unittest.main()
