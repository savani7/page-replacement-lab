"""Algorithm Comparison Arena: 2 or 3 algorithms side by side on the same input."""
import tkinter as tk

import customtkinter as ctk

from algorithms.simulator_engine import (ALGORITHM_FULL_NAMES, ALGORITHM_ORDER, EXAMPLES,
                                         InputError, MAX_FRAMES, MAX_PAGE, MIN_FRAMES,
                                         compare_summary, simulate,
                                         validate_comparison_selection, validate_inputs)

from . import styles as S
from .panel import SimulationPanel
from .playback import (FINISHED, IDLE, PAUSED, RUNNING, PlaybackController, delay_for_speed)
from .widgets import (make_button, make_card, make_entry, rounded_rect, set_enabled)

DEFAULT_SPEED = 7
LIVE, SUMMARY = "Live Comparison", "Summary"
BEST_FILL = "#CFE8DB"


class ComparisonScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.SAGE)
        self.app = app
        self.panels = {}
        self.results = {}
        self._example_index = 0
        self._summary_job = None
        self.controller = PlaybackController(
            self,
            on_phase=self._on_phase,
            on_complete=self._on_complete,
            on_reset=self._on_reset,
            on_state=lambda state: self._refresh_buttons(),
            delay_ms=delay_for_speed(DEFAULT_SPEED),
        )
        self._build()
        self._rebuild_panels(self._selected())
        self._refresh_buttons()

    # ------------------------------------------------------------------ layout
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(12, 4))
        make_button(header, "<  Dashboard", lambda: self.app.show_screen("dashboard"),
                    kind="secondary", width=130, height=34).pack(side="left")
        ctk.CTkLabel(header, text="Algorithm Comparison Arena", font=S.font(26, "bold"),
                     text_color=S.TEXT).pack(side="left", padx=16)

        controls = make_card(self)
        controls.pack(fill="x", padx=18, pady=(0, 4))

        row1 = ctk.CTkFrame(controls, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(row1, text="Page reference string", font=S.font(13, "bold"),
                     text_color=S.TEXT).pack(side="left")
        self.refs_entry = make_entry(row1, width=330, placeholder="1, 2, 3, 1, 4, 2, 5")
        self.refs_entry.pack(side="left", padx=(8, 14))
        ctk.CTkLabel(row1, text=f"Frames ({MIN_FRAMES}-{MAX_FRAMES})", font=S.font(13, "bold"),
                     text_color=S.TEXT).pack(side="left")
        self.frames_entry = make_entry(row1, width=60, placeholder="3")
        self.frames_entry.pack(side="left", padx=(8, 14))
        make_button(row1, "Fill Example", self._fill_example, kind="secondary", width=120,
                    height=34).pack(side="left")

        picker = ctk.CTkFrame(row1, fg_color="transparent")
        picker.pack(side="right")
        ctk.CTkLabel(picker, text="Compare:", font=S.font(13, "bold"),
                     text_color=S.TEXT).pack(side="left", padx=(0, 6))
        self.sel_vars = {}
        for name in ALGORITHM_ORDER:
            var = ctk.BooleanVar(value=True)
            self.sel_vars[name] = var
            card = ctk.CTkFrame(picker, fg_color=S.FRAME_FILL, corner_radius=12,
                                border_width=1, border_color=S.BORDER)
            card.pack(side="left", padx=3)
            ctk.CTkCheckBox(card, text=name, variable=var, command=self._on_selection_change,
                            font=S.font(13, "bold"), text_color=S.TEXT, fg_color=S.FOREST,
                            hover_color=S.FOREST_HOVER, border_color=S.BORDER,
                            width=90).pack(padx=10, pady=6)

        row2 = ctk.CTkFrame(controls, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(2, 4))
        self.start_btn = make_button(row2, "Start Comparison", self._start, width=170, height=36)
        self.start_btn.pack(side="left", padx=(0, 6))
        self.pause_btn = make_button(row2, "Pause", self.controller.pause, kind="secondary",
                                     width=90, height=36)
        self.pause_btn.pack(side="left", padx=3)
        self.resume_btn = make_button(row2, "Resume", self.controller.resume, kind="secondary",
                                      width=90, height=36)
        self.resume_btn.pack(side="left", padx=3)
        self.restart_btn = make_button(row2, "Restart", self._restart, kind="secondary",
                                       width=90, height=36)
        self.restart_btn.pack(side="left", padx=3)
        self.manual_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row2, text="Manual step", variable=self.manual_var,
                        command=self._on_manual_toggle, text_color=S.TEXT, font=S.font(13),
                        fg_color=S.FOREST, hover_color=S.FOREST_HOVER, border_color=S.BORDER,
                        width=110).pack(side="left", padx=(14, 4))
        self.next_btn = make_button(row2, "Next Step", self.controller.step, kind="secondary",
                                    width=100, height=36)
        self.next_btn.pack(side="left", padx=3)
        self.speed_label = ctk.CTkLabel(row2, text=f"Speed: {DEFAULT_SPEED}/10",
                                        font=S.font(13, "bold"), text_color=S.TEXT)
        self.speed_label.pack(side="left", padx=(16, 6))
        self.speed = ctk.CTkSlider(row2, from_=1, to=10, number_of_steps=9, width=150,
                                   command=self._on_speed, button_color=S.FOREST,
                                   button_hover_color=S.FOREST_HOVER, progress_color=S.FOREST,
                                   fg_color=S.MINT)
        self.speed.set(DEFAULT_SPEED)
        self.speed.pack(side="left")

        self.error_label = ctk.CTkLabel(controls, text="", anchor="w", justify="left",
                                        font=S.font(12, "bold"), text_color="#B5503C", height=4)
        self.error_label.pack(fill="x", padx=14, pady=(0, 6))

        # view switch + stacked views
        self.view_var = ctk.StringVar(value=LIVE)
        self.view_switch = ctk.CTkSegmentedButton(
            self, values=[LIVE, SUMMARY], variable=self.view_var, command=self._show_view,
            selected_color=S.FOREST, selected_hover_color=S.FOREST_HOVER,
            unselected_color="#7FA593", unselected_hover_color="#6C9582", text_color=S.WHITE,
            font=S.font(13, "bold"), height=32,
        )
        self.view_switch.pack(anchor="w", padx=18, pady=(2, 4))

        stack = ctk.CTkFrame(self, fg_color="transparent")
        stack.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        stack.grid_rowconfigure(0, weight=1)
        stack.grid_columnconfigure(0, weight=1)
        self.live_frame = ctk.CTkFrame(stack, fg_color="transparent")
        self.live_frame.grid(row=0, column=0, sticky="nsew")
        self.live_frame.grid_rowconfigure(0, weight=1)
        self.live_frame.grid_columnconfigure(0, weight=1)
        self.panels_holder = ctk.CTkFrame(self.live_frame, fg_color="transparent")
        self.panels_holder.grid(row=0, column=0, sticky="nsew")
        self.summary_frame = ctk.CTkFrame(stack, fg_color="transparent")
        self.summary_frame.grid(row=0, column=0, sticky="nsew")
        self.summary_frame.grid_remove()
        self._reset_summary()

    # ------------------------------------------------------------- selection
    def _selected(self):
        return [n for n in ALGORITHM_ORDER if self.sel_vars[n].get()]

    def _rebuild_panels(self, names):
        for child in self.panels_holder.winfo_children():
            child.destroy()
        self.panels = {}
        self.panels_holder.grid_rowconfigure(0, weight=1)
        for col in range(len(ALGORITHM_ORDER)):
            active = col < len(names)
            self.panels_holder.grid_columnconfigure(
                col, weight=1 if active else 0, uniform="panel" if active else "")
        for col, name in enumerate(names):
            panel = SimulationPanel(self.panels_holder, name, compact=True)
            panel.grid(row=0, column=col, sticky="nsew", padx=5)
            self.panels[name] = panel

    def _on_selection_change(self):
        self.controller.clear()
        self._cancel_summary_job()
        self.results = {}
        self._reset_summary()
        self._show_view(LIVE)
        names = self._selected()
        self._rebuild_panels(names)
        if len(names) < 2:
            self._show_error("Please select at least two algorithms to compare.")
        else:
            self._show_error("")
        self._refresh_buttons()

    # ---------------------------------------------------------------- helpers
    def _fill_example(self):
        text, frames = EXAMPLES[self._example_index % len(EXAMPLES)]
        self._example_index += 1
        self.refs_entry.delete(0, "end")
        self.refs_entry.insert(0, text)
        self.frames_entry.delete(0, "end")
        self.frames_entry.insert(0, str(frames))
        if len(self._selected()) >= 2:
            self._show_error("")

    def _show_error(self, message):
        self.error_label.configure(text=message, height=22 if message else 4)
        color = S.FAULT if message else S.BORDER
        self.refs_entry.configure(border_color=color)
        self.frames_entry.configure(border_color=color)

    def _show_view(self, value):
        self.view_var.set(value)
        if value == SUMMARY:
            self.live_frame.grid_remove()
            self.summary_frame.grid()
        else:
            self.summary_frame.grid_remove()
            self.live_frame.grid()

    def _cancel_summary_job(self):
        if self._summary_job is not None:
            try:
                self.after_cancel(self._summary_job)
            except Exception:
                pass
            self._summary_job = None

    # --------------------------------------------------------------- handlers
    def _start(self):
        try:
            names = validate_comparison_selection(self._selected())
            refs, frames = validate_inputs(self.refs_entry.get(), self.frames_entry.get())
        except InputError as err:
            self._show_error(str(err))
            return
        self._show_error("")
        self._cancel_summary_job()
        self.results = {n: simulate(n, refs, frames) for n in names}
        for name in names:
            self.panels[name].set_run(self.results[name])
        self._reset_summary()
        self._show_view(LIVE)
        self.controller.load([self.results[n] for n in names])
        self.controller.manual = self.manual_var.get()
        self.controller.start()

    def _restart(self):
        self.controller.manual = self.manual_var.get()
        self.controller.restart()

    def _on_manual_toggle(self):
        self.controller.manual = self.manual_var.get()
        if self.manual_var.get() and self.controller.state == RUNNING:
            self.controller.pause()
        self._refresh_buttons()

    def _on_speed(self, value):
        speed = int(round(float(value)))
        self.speed_label.configure(text=f"Speed: {speed}/10")
        self.controller.set_delay(delay_for_speed(speed))

    def _refresh_buttons(self):
        state = self.controller.state
        can_start = len(self._selected()) >= 2
        set_enabled(self.start_btn, can_start and state in (IDLE, FINISHED))
        set_enabled(self.pause_btn, state == RUNNING)
        set_enabled(self.resume_btn, state == PAUSED)
        set_enabled(self.restart_btn, self.controller.has_runs)
        set_enabled(self.next_btn, state == PAUSED)

    # ----------------------------------------------------- controller callbacks
    def _on_phase(self, ref, phase):
        # every selected algorithm shows the same reference at the same tick
        for panel in self.panels.values():
            panel.show_phase(ref, phase)

    def _on_reset(self):
        self._cancel_summary_job()
        for panel in self.panels.values():
            panel.reset()
        self._reset_summary()
        self._show_view(LIVE)

    def _on_complete(self):
        for panel in self.panels.values():
            panel.show_complete()
        self._build_summary()
        self._cancel_summary_job()
        # let the user see the final RAM states for a moment, then open the summary
        self._summary_job = self.after(1600, self._open_summary)

    def _open_summary(self):
        self._summary_job = None
        if self.results and self.controller.state == FINISHED:
            self._show_view(SUMMARY)

    # ----------------------------------------------------------------- summary
    def _reset_summary(self):
        for child in self.summary_frame.winfo_children():
            child.destroy()
        card = make_card(self.summary_frame)
        card.pack(fill="both", expand=True, padx=4)
        ctk.CTkLabel(card, text="Run a comparison to see the summary here.",
                     font=S.font(16), text_color=S.TEXT_MUTED).pack(expand=True)

    def _build_summary(self):
        for child in self.summary_frame.winfo_children():
            child.destroy()
        names = [n for n in ALGORITHM_ORDER if n in self.results]
        best, explanation = compare_summary(self.results)
        first = self.results[names[0]]

        wrap = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        wrap.pack(fill="both", expand=True)
        wrap.grid_columnconfigure(0, weight=3, uniform="sum")
        wrap.grid_columnconfigure(1, weight=2, uniform="sum")
        wrap.grid_rowconfigure(0, weight=1)

        # left: table + explanation
        left = make_card(wrap)
        left.grid(row=0, column=0, sticky="nsew", padx=(4, 6))
        ctk.CTkLabel(left, text="Comparison Summary", anchor="w", font=S.font(22, "bold"),
                     text_color=S.FOREST).pack(fill="x", padx=18, pady=(14, 0))
        refs_text = ", ".join(str(p) for p in first.refs)
        if len(refs_text) > 90:
            refs_text = refs_text[:87] + "..."
        ctk.CTkLabel(left, text=f"Same input for every algorithm - {first.total} references, "
                                f"{first.num_frames} frame(s)\nReferences: {refs_text}",
                     anchor="w", justify="left", font=S.font(12), text_color=S.TEXT_MUTED,
                     wraplength=560).pack(fill="x", padx=18, pady=(0, 8))

        table = ctk.CTkFrame(left, fg_color="transparent")
        table.pack(fill="x", padx=14, pady=4)
        heads = ["Algorithm", "Page Faults", "Page Hits", "Fault Rate", "Result"]
        for c, text in enumerate(heads):
            ctk.CTkLabel(table, text=text, font=S.font(13, "bold"), text_color=S.TEXT_MUTED,
                         anchor="w").grid(row=0, column=c, sticky="ew", padx=6, pady=(0, 4))
            table.grid_columnconfigure(c, weight=1)
        for r, name in enumerate(names, start=1):
            res = self.results[name]
            is_best = name in best
            fill = BEST_FILL if is_best else S.CARD_INNER
            verdict = ("Fewest faults" if len(best) < len(names) else "Same as others") if is_best else "-"
            cells = [name, res.faults, res.hits, f"{res.fault_rate:.1f}%", verdict]
            for c, value in enumerate(cells):
                ctk.CTkLabel(table, text=str(value), anchor="w", corner_radius=8, fg_color=fill,
                             text_color=S.HIT if (is_best and c == 4) else S.TEXT,
                             font=S.font(15, "bold" if (c == 0 or is_best) else "normal"),
                             height=40).grid(row=r, column=c, sticky="ew", padx=3, pady=3, ipadx=6)

        ctk.CTkLabel(left, text=explanation, anchor="w", justify="left", wraplength=560,
                     font=S.font(14), text_color=S.TEXT).pack(fill="x", padx=18, pady=(12, 6))
        for name in names:
            ctk.CTkLabel(left, text=f"{name}: {ALGORITHM_FULL_NAMES[name]}", anchor="w",
                         font=S.font(12), text_color=S.TEXT_MUTED).pack(fill="x", padx=18)
        ctk.CTkLabel(left, text="", height=8).pack()

        # right: bar chart of page faults
        right = make_card(wrap)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 4))
        ctk.CTkLabel(right, text="Page faults (lower is better)", anchor="w",
                     font=S.font(18, "bold"), text_color=S.FOREST).pack(fill="x", padx=18, pady=(14, 4))
        chart = tk.Canvas(right, bg=S.CREAM, highlightthickness=0)
        chart.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        chart.bind("<Configure>", lambda e: self._draw_chart(chart, names, best))

    def _draw_chart(self, canvas, names, best):
        canvas.delete("all")
        W = max(canvas.winfo_width(), 260)
        H = max(canvas.winfo_height(), 160)
        top_faults = max((self.results[n].faults for n in names), default=0)
        scale_max = max(1, top_faults)
        left, right_pad = 84, 90
        row_h = min(70, (H - 10) / max(1, len(names)))
        bar_h = row_h * 0.55
        for i, name in enumerate(names):
            res = self.results[name]
            y = 8 + i * row_h + (row_h - bar_h) / 2
            is_best = name in best
            canvas.create_text(8, y + bar_h / 2, anchor="w", text=name, fill=S.TEXT,
                               font=S.canvas_font(15, "bold"))
            length = max(6, (W - left - right_pad) * res.faults / scale_max) if res.faults else 4
            rounded_rect(canvas, left, y, left + length, y + bar_h, r=8,
                         fill=S.HIT if is_best else S.MINT,
                         outline=S.FOREST_DARK if is_best else S.BORDER, width=2)
            label = f"{res.faults} faults" + ("  BEST" if is_best and len(best) < len(names) else "")
            canvas.create_text(left + length + 8, y + bar_h / 2, anchor="w", text=label,
                               fill=S.HIT if is_best else S.TEXT,
                               font=S.canvas_font(13, "bold"))

    # ------------------------------------------------------------ screen events
    def on_show(self):
        self._refresh_buttons()

    def on_hide(self):
        """Cancel every pending callback so nothing animates after leaving the screen."""
        self.controller.clear()
        self._cancel_summary_job()
        self.results = {}
        for panel in self.panels.values():
            panel.clear()
        self._reset_summary()
        self._show_view(LIVE)
        self._refresh_buttons()
