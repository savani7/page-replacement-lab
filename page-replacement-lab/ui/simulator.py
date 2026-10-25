"""Interactive Simulator: one algorithm, fully automatic playback."""
import customtkinter as ctk

from algorithms import ALGORITHMS, ValidationError, parse_reference_string, parse_frame_count
from algorithms.compare import compare_all
from . import styles as S
from .panel import AlgoPanel
from .playback import PlaybackController
from .widgets import big_button, soft_button, card, home_bar

EXAMPLE_REFS, EXAMPLE_FRAMES = "1, 2, 3, 1, 4, 2, 5", "3"


class SimulatorScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.BG)
        self.app = app
        self.refs, self.n, self.steps = [], 3, []

        home_bar(self, app, "Interactive Simulator").pack(fill="x", padx=24, pady=(16, 8))
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # ---------- left: controls
        left = card(body, width=330)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)
        self._label(left, "Page reference string")
        self.refs_entry = ctk.CTkEntry(left, height=42, corner_radius=12, font=S.font(15),
                                       placeholder_text="1, 2, 3, 1, 4, 2, 5")
        self.refs_entry.pack(fill="x", padx=18)
        self._label(left, "Number of RAM frames (1 - 8)")
        self.frames_entry = ctk.CTkEntry(left, height=42, corner_radius=12, font=S.font(15), width=100,
                                         placeholder_text="3")
        self.frames_entry.pack(anchor="w", padx=18)
        self._label(left, "Algorithm")
        self.algo_var = ctk.StringVar(value="FIFO")
        self.algo_seg = ctk.CTkSegmentedButton(left, values=list(ALGORITHMS), variable=self.algo_var,
                                               command=self._on_algo_change, height=38, font=S.font(13, "bold"),
                                               selected_color=S.BLUE_D, selected_hover_color=S.BLUE_D,
                                               unselected_color=S.BLUE_L, unselected_hover_color="#BFD9FA",
                                               text_color=S.TEXT)
        self.algo_seg.pack(fill="x", padx=18)
        soft_button(left, "Fill example", self._fill_example, width=140).pack(anchor="w", padx=18, pady=(12, 4))

        self.error = ctk.CTkLabel(left, text="", text_color=S.CORAL_D, font=S.font(12, "bold"),
                                  wraplength=290, justify="left")
        self.error.pack(anchor="w", padx=18, pady=(2, 2))

        self.start_btn = big_button(left, "▶  START SIMULATION", self.start, color=S.GREEN_D, width=290)
        self.start_btn.pack(padx=18, pady=(6, 8))
        row = ctk.CTkFrame(left, fg_color="transparent")
        row.pack(fill="x", padx=18)
        self.pause_btn = soft_button(row, "Pause", self.pause, width=88)
        self.pause_btn.pack(side="left")
        self.resume_btn = soft_button(row, "Resume", self.resume, width=88)
        self.resume_btn.pack(side="left", padx=6)
        self.restart_btn = soft_button(row, "Restart", self.restart, width=88)
        self.restart_btn.pack(side="left")

        self._label(left, "Animation speed")
        self.speed_lbl = ctk.CTkLabel(left, text="1.0×", font=S.font(13, "bold"), text_color=S.MUTED)
        self.speed_lbl.pack(anchor="w", padx=18)
        self.speed = ctk.CTkSlider(left, from_=0.25, to=4, number_of_steps=15, command=self._on_speed,
                                   button_color=S.BLUE_D, progress_color=S.BLUE_L)
        self.speed.set(1.0)
        self.speed.pack(fill="x", padx=18, pady=(0, 4))

        self.manual_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left, text="Manual-step mode", variable=self.manual_var, command=self._on_manual,
                        font=S.font(13), fg_color=S.BLUE_D).pack(anchor="w", padx=18, pady=(10, 4))
        self.next_btn = soft_button(left, "Next step ▶", self.next_step, width=290)
        self.next_btn.pack(padx=18, pady=(0, 14))

        # ---------- right: panel + results
        right = ctk.CTkScrollableFrame(body, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        self.panel = AlgoPanel(right, "FIFO", compact=False)
        self.panel.pack(fill="x", pady=(0, 12))
        self.summary = card(right, fg_color=S.GREEN_L, border_color=S.GREEN_D, border_width=2)
        self.sum_head = ctk.CTkLabel(self.summary, text="", font=S.font(20, "bold"), text_color=S.TEXT)
        self.sum_head.pack(anchor="w", padx=18, pady=(14, 2))
        self.sum_body = ctk.CTkLabel(self.summary, text="", font=S.font(14), text_color=S.TEXT,
                                     wraplength=760, justify="left")
        self.sum_body.pack(anchor="w", padx=18, pady=(0, 14))

        self.controller = PlaybackController(
            self, phases_for=self.panel.phases, on_phase=self.panel.render,
            on_finish=self._on_finish, on_reset=self._on_reset, on_state=self._on_state)
        self._fill_example()
        self._on_state("idle")

    # ------------------------------------------------------------ helpers
    def _label(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=S.font(13, "bold"), text_color=S.TEXT).pack(
            anchor="w", padx=18, pady=(14, 4))

    def _fill_example(self):
        self.refs_entry.delete(0, "end")
        self.refs_entry.insert(0, EXAMPLE_REFS)
        self.frames_entry.delete(0, "end")
        self.frames_entry.insert(0, EXAMPLE_FRAMES)
        self.error.configure(text="")

    def on_leave(self):
        self.controller.stop()
        self.panel.stop_animation()

    # ------------------------------------------------------------ actions
    def start(self):
        try:
            refs = parse_reference_string(self.refs_entry.get())
            n = parse_frame_count(self.frames_entry.get())
        except ValidationError as e:
            self.error.configure(text="⚠  " + str(e))
            return
        self.error.configure(text="")
        self.controller.stop()
        algo = self.algo_var.get()
        self.refs, self.n = refs, n
        self.steps = ALGORITHMS[algo](refs, n)
        self.panel.set_algorithm(algo)
        self.panel.load(refs, n, self.steps)
        self.controller.load(len(self.steps))
        self.controller.set_speed(self._speed_value())
        self.summary.pack_forget()
        self.controller.start(auto=not self.manual_var.get())

    def pause(self):
        self.controller.pause()

    def resume(self):
        self.controller.resume()

    def restart(self):
        if not self.steps:
            self.error.configure(text="Press START SIMULATION first.")
            return
        self.summary.pack_forget()
        self.controller.restart(auto=not self.manual_var.get())

    def next_step(self):
        if self.steps:
            self.controller.step_once()

    def _speed_value(self):
        return float(self.speed.get())

    def _on_speed(self, value):
        self.speed_lbl.configure(text=f"{float(value):.2g}×")
        self.controller.set_speed(float(value))

    def _on_manual(self):
        if self.manual_var.get():
            self.controller.pause()
        self._on_state(self.controller.state)

    def _on_algo_change(self, name):
        self.controller.stop()
        self.steps = []
        self.controller.load(0)
        self.panel.set_algorithm(name)
        self.panel.load(self.refs, self.n, [])
        self.summary.pack_forget()

    def _on_reset(self):
        self.panel.render_idle()

    def _on_state(self, state):
        playing, paused = state == "playing", state == "paused"
        self.pause_btn.configure(state="normal" if playing else "disabled")
        self.resume_btn.configure(state="normal" if paused and not self.manual_var.get() else "disabled")
        self.restart_btn.configure(state="normal" if self.steps else "disabled")
        self.next_btn.configure(state="normal" if (self.manual_var.get() and self.steps
                                                   and state != "finished") else "disabled")

    def _on_finish(self):
        algo = self.algo_var.get()
        last = self.steps[-1]
        total = len(self.steps)
        rate = last.faults / total * 100
        results = compare_all(self.refs, self.n)
        others = ", ".join(f"{k}: {r.faults}" for k, r in results.items())
        self.sum_head.configure(text=f"✅  Simulation complete - {algo}")
        self.sum_body.configure(text=(
            f"{total} references with {self.n} frame(s): {last.hits} page hits and {last.faults} page "
            f"faults (fault rate {rate:.1f}%).\n\nFor the same input, page faults were - {others}. "
            f"Try the Algorithm Battle Arena to watch all three side by side."))
        self.summary.pack(fill="x", pady=(0, 12))
