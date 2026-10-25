"""Algorithm Battle Arena: FIFO | LRU | Optimal running in lock-step."""
import customtkinter as ctk

from algorithms import ALGORITHMS, ValidationError, parse_reference_string, parse_frame_count
from algorithms.compare import compare_all, best_algorithms, explain_comparison
from . import styles as S
from .panel import AlgoPanel
from .playback import PlaybackController, FULL_PHASES, SHORT_PHASES
from .widgets import big_button, soft_button, card, home_bar

EXAMPLE_REFS, EXAMPLE_FRAMES = "1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5", "3"


class BattleArenaScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.BG)
        self.app = app
        self.refs, self.n = [], 3
        self.results = {}

        home_bar(self, app, "Algorithm Battle Arena").pack(fill="x", padx=24, pady=(16, 8))
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # ---- controls
        bar = card(scroll)
        bar.pack(fill="x", padx=8, pady=(0, 10))
        r1 = ctk.CTkFrame(bar, fg_color="transparent")
        r1.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(r1, text="Reference string", font=S.font(13, "bold")).pack(side="left")
        self.refs_entry = ctk.CTkEntry(r1, width=380, height=38, corner_radius=12, font=S.font(14))
        self.refs_entry.pack(side="left", padx=(8, 18))
        ctk.CTkLabel(r1, text="Frames", font=S.font(13, "bold")).pack(side="left")
        self.frames_entry = ctk.CTkEntry(r1, width=60, height=38, corner_radius=12, font=S.font(14))
        self.frames_entry.pack(side="left", padx=(8, 18))
        soft_button(r1, "Fill example", self._fill_example, width=120).pack(side="left")
        self.error = ctk.CTkLabel(bar, text="", text_color=S.CORAL_D, font=S.font(12, "bold"), anchor="w")
        self.error.pack(fill="x", padx=16)

        r2 = ctk.CTkFrame(bar, fg_color="transparent")
        r2.pack(fill="x", padx=14, pady=(2, 12))
        big_button(r2, "▶  START BATTLE", self.start, color=S.GREEN_D, width=200).pack(side="left")
        self.pause_btn = soft_button(r2, "Pause", self.controller_pause, width=90)
        self.pause_btn.pack(side="left", padx=(12, 4))
        self.resume_btn = soft_button(r2, "Resume", self.controller_resume, width=90)
        self.resume_btn.pack(side="left", padx=4)
        self.restart_btn = soft_button(r2, "Restart", self.restart, width=90)
        self.restart_btn.pack(side="left", padx=4)
        ctk.CTkLabel(r2, text="Speed", font=S.font(13, "bold")).pack(side="left", padx=(18, 6))
        self.speed = ctk.CTkSlider(r2, from_=0.25, to=4, number_of_steps=15, width=150,
                                   command=self._on_speed, button_color=S.BLUE_D, progress_color=S.BLUE_L)
        self.speed.set(1.0)
        self.speed.pack(side="left")
        self.speed_lbl = ctk.CTkLabel(r2, text="1×", font=S.font(13, "bold"), text_color=S.MUTED, width=40)
        self.speed_lbl.pack(side="left", padx=(6, 12))
        self.manual_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(r2, text="Manual", variable=self.manual_var, command=self._on_manual,
                        font=S.font(13), fg_color=S.BLUE_D, width=80).pack(side="left")
        self.next_btn = soft_button(r2, "Next ▶", self.next_step, width=90)
        self.next_btn.pack(side="left", padx=8)

        # ---- three panels
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x")
        for c in range(3):
            row.grid_columnconfigure(c, weight=1, uniform="p")
        self.panels = {}
        for c, name in enumerate(ALGORITHMS):
            p = AlgoPanel(row, name, compact=True)
            p.grid(row=0, column=c, padx=6, pady=4, sticky="n")
            self.panels[name] = p

        # ---- results
        self.result_card = card(scroll, fg_color=S.CARD, border_color=S.BLUE_D, border_width=2)
        self.res_head = ctk.CTkLabel(self.result_card, text="", font=S.font(20, "bold"), text_color=S.TEXT)
        self.res_head.pack(anchor="w", padx=18, pady=(14, 6))
        self.table = ctk.CTkFrame(self.result_card, fg_color="transparent")
        self.table.pack(fill="x", padx=18)
        self.res_text = ctk.CTkLabel(self.result_card, text="", font=S.font(14), text_color=S.TEXT,
                                     wraplength=1100, justify="left")
        self.res_text.pack(anchor="w", padx=18, pady=(10, 14))

        self.controller = PlaybackController(
            self, phases_for=self._phases_for, on_phase=self._on_phase,
            on_finish=self._on_finish, on_reset=self._on_reset, on_state=self._on_state)
        self._fill_example()
        self._on_state("idle")

    # ---------------------------------------------------------- helpers
    def _fill_example(self):
        self.refs_entry.delete(0, "end")
        self.refs_entry.insert(0, EXAMPLE_REFS)
        self.frames_entry.delete(0, "end")
        self.frames_entry.insert(0, EXAMPLE_FRAMES)
        self.error.configure(text="")

    def _phases_for(self, i):
        # one shared timeline: use the long phase list if ANY algorithm replaces a page
        if any(p.steps[i].replaced for p in self.panels.values()):
            return FULL_PHASES
        return SHORT_PHASES

    def _on_phase(self, i, phase):
        for p in self.panels.values():
            p.render(i, phase)

    def on_leave(self):
        self.controller.stop()
        for p in self.panels.values():
            p.stop_animation()

    # ---------------------------------------------------------- actions
    def start(self):
        try:
            refs = parse_reference_string(self.refs_entry.get())
            n = parse_frame_count(self.frames_entry.get())
        except ValidationError as e:
            self.error.configure(text="⚠  " + str(e))
            return
        self.error.configure(text="")
        self.controller.stop()
        self.refs, self.n = refs, n
        self.results = compare_all(refs, n)
        for name, p in self.panels.items():
            p.load(refs, n, self.results[name].steps)
        self.controller.load(len(refs))
        self.controller.set_speed(float(self.speed.get()))
        self.result_card.pack_forget()
        self.controller.start(auto=not self.manual_var.get())

    def controller_pause(self):
        self.controller.pause()

    def controller_resume(self):
        self.controller.resume()

    def restart(self):
        if not self.results:
            self.error.configure(text="Press START BATTLE first.")
            return
        self.result_card.pack_forget()
        self.controller.restart(auto=not self.manual_var.get())

    def next_step(self):
        if self.results:
            self.controller.step_once()

    def _on_speed(self, value):
        self.speed_lbl.configure(text=f"{float(value):.2g}×")
        self.controller.set_speed(float(value))

    def _on_manual(self):
        if self.manual_var.get():
            self.controller.pause()
        self._on_state(self.controller.state)

    def _on_reset(self):
        for p in self.panels.values():
            p.render_idle()

    def _on_state(self, state):
        playing, paused = state == "playing", state == "paused"
        self.pause_btn.configure(state="normal" if playing else "disabled")
        self.resume_btn.configure(state="normal" if paused and not self.manual_var.get() else "disabled")
        self.restart_btn.configure(state="normal" if self.results else "disabled")
        self.next_btn.configure(state="normal" if (self.manual_var.get() and self.results
                                                   and state != "finished") else "disabled")

    def _on_finish(self):
        best = best_algorithms(self.results)
        self.res_head.configure(text="\U0001F3C1  Battle results")
        for w in self.table.winfo_children():
            w.destroy()
        heads = ["Algorithm", "Page Faults", "Page Hits", "Fault Rate"]
        for c, h in enumerate(heads):
            ctk.CTkLabel(self.table, text=h, font=S.font(14, "bold"), text_color=S.MUTED,
                         anchor="w").grid(row=0, column=c, sticky="ew", padx=10, pady=4)
            self.table.grid_columnconfigure(c, weight=1)
        for r, (name, res) in enumerate(self.results.items(), start=1):
            win = name in best
            fill = S.GREEN_L if win else S.EMPTY_FILL
            vals = [name + ("   ★ fewest faults" if win else ""), str(res.faults), str(res.hits),
                    f"{res.fault_rate * 100:.1f}%"]
            for c, v in enumerate(vals):
                ctk.CTkLabel(self.table, text=v, font=S.font(15, "bold" if win else "normal"),
                             text_color=S.TEXT, fg_color=fill, corner_radius=8, anchor="w",
                             height=36).grid(row=r, column=c, sticky="ew", padx=3, pady=3, ipadx=8)
        self.res_text.configure(text=explain_comparison(self.results))
        self.result_card.pack(fill="x", padx=8, pady=12)
