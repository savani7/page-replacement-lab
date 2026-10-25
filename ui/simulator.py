"""Interactive Simulator screen: one algorithm, full-size live view."""
import customtkinter as ctk

from algorithms.simulator_engine import (ALGORITHM_ORDER, EXAMPLES, InputError, MAX_FRAMES,
                                         MAX_PAGE, MAX_REFS, MIN_FRAMES, format_frames,
                                         result_summary, simulate, validate_inputs)

from . import styles as S
from .panel import SimulationPanel
from .playback import (FINISHED, IDLE, PAUSED, RUNNING, PlaybackController, delay_for_speed)
from .widgets import make_button, make_card, make_entry, set_enabled

DEFAULT_SPEED = 7


class SimulatorScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.SAGE)
        self.app = app
        self._example_index = 0
        self.run = None
        self.controller = PlaybackController(
            self,
            on_phase=self._on_phase,
            on_complete=self._on_complete,
            on_reset=self._on_reset,
            on_state=lambda state: self._refresh_buttons(),
            delay_ms=delay_for_speed(DEFAULT_SPEED),
        )
        self._build()
        self._refresh_buttons()

    # ------------------------------------------------------------------ layout
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(14, 6))
        make_button(header, "<  Dashboard", lambda: self.app.show_screen("dashboard"),
                    kind="secondary", width=130, height=34).pack(side="left")
        ctk.CTkLabel(header, text="Interactive Simulator", font=S.font(26, "bold"),
                     text_color=S.TEXT).pack(side="left", padx=16)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        side = ctk.CTkScrollableFrame(body, width=300, fg_color=S.CREAM, corner_radius=18,
                                      border_width=1, border_color=S.BORDER,
                                      scrollbar_button_color=S.BORDER,
                                      scrollbar_button_hover_color=S.FOREST)
        side.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        self.side = side

        def label(text, size=13, weight="bold", color=S.TEXT, pady=(10, 2)):
            ctk.CTkLabel(side, text=text, anchor="w", font=S.font(size, weight),
                         text_color=color).pack(fill="x", padx=6, pady=pady)

        label("Simulation Settings", 18, pady=(2, 0))
        label("Page reference string")
        self.refs_entry = make_entry(side, width=270, placeholder="1, 2, 3, 1, 4, 2, 5")
        self.refs_entry.pack(padx=6)
        label(f"Whole numbers 0-{MAX_PAGE}, separated by commas or spaces (max {MAX_REFS}).",
              11, "normal", S.TEXT_MUTED, pady=(2, 0))
        label(f"Number of frames ({MIN_FRAMES}-{MAX_FRAMES})")
        self.frames_entry = make_entry(side, width=90, placeholder="3")
        self.frames_entry.pack(anchor="w", padx=6)
        label("Algorithm")
        self.algo_var = ctk.StringVar(value=ALGORITHM_ORDER[0])
        self.algo_buttons = ctk.CTkSegmentedButton(
            side, values=list(ALGORITHM_ORDER), variable=self.algo_var,
            command=self._on_algorithm_change, selected_color=S.FOREST,
            selected_hover_color=S.FOREST_HOVER, unselected_color=S.MINT,
            unselected_hover_color=S.MINT_HOVER, text_color=S.TEXT, font=S.font(13, "bold"),
            height=34,
        )
        self.algo_buttons.pack(fill="x", padx=6)

        make_button(side, "Fill Example", self._fill_example, kind="secondary",
                    height=34).pack(fill="x", padx=6, pady=(12, 0))
        self.error_label = ctk.CTkLabel(side, text="", anchor="w", justify="left", wraplength=270,
                                        font=S.font(12, "bold"), text_color="#B5503C")
        self.error_label.pack(fill="x", padx=6, pady=(6, 0))

        label("Playback", 18, pady=(14, 2))
        self.start_btn = make_button(side, "Start Simulation", self._start)
        self.start_btn.pack(fill="x", padx=6, pady=3)
        row = ctk.CTkFrame(side, fg_color="transparent")
        row.pack(fill="x", padx=6)
        row.grid_columnconfigure((0, 1), weight=1)
        self.pause_btn = make_button(row, "Pause", self._pause, kind="secondary", width=120)
        self.pause_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=3)
        self.resume_btn = make_button(row, "Resume", self._resume, kind="secondary", width=120)
        self.resume_btn.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=3)
        self.restart_btn = make_button(side, "Restart", self._restart, kind="secondary")
        self.restart_btn.pack(fill="x", padx=6, pady=3)

        self.manual_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(side, text="Manual step mode", variable=self.manual_var,
                        command=self._on_manual_toggle, text_color=S.TEXT, font=S.font(13),
                        fg_color=S.FOREST, hover_color=S.FOREST_HOVER,
                        border_color=S.BORDER).pack(anchor="w", padx=8, pady=(10, 2))
        self.next_btn = make_button(side, "Next Step", self._next, kind="secondary")
        self.next_btn.pack(fill="x", padx=6, pady=3)

        self.speed_label = ctk.CTkLabel(side, text=f"Speed: {DEFAULT_SPEED}/10", anchor="w",
                                        font=S.font(13, "bold"), text_color=S.TEXT)
        self.speed_label.pack(fill="x", padx=6, pady=(10, 0))
        self.speed = ctk.CTkSlider(side, from_=1, to=10, number_of_steps=9,
                                   command=self._on_speed, button_color=S.FOREST,
                                   button_hover_color=S.FOREST_HOVER, progress_color=S.FOREST,
                                   fg_color=S.MINT)
        self.speed.set(DEFAULT_SPEED)
        self.speed.pack(fill="x", padx=6, pady=(2, 6))

        # final results card (shown when playback finishes)
        self.results = make_card(side, fg_color=S.CARD_INNER, corner_radius=14)
        self.results_title = ctk.CTkLabel(self.results, text="Final Results", anchor="w",
                                          font=S.font(16, "bold"), text_color=S.FOREST)
        self.results_title.pack(fill="x", padx=12, pady=(10, 2))
        self.results_body = ctk.CTkLabel(self.results, text="", anchor="w", justify="left",
                                         wraplength=250, font=S.font(12), text_color=S.TEXT)
        self.results_body.pack(fill="x", padx=12, pady=(0, 10))

        self.panel = SimulationPanel(body, ALGORITHM_ORDER[0], compact=False, show_flow=True)
        self.panel.grid(row=0, column=1, sticky="nsew")

    # ---------------------------------------------------------------- handlers
    def _fill_example(self):
        text, frames = EXAMPLES[self._example_index % len(EXAMPLES)]
        self._example_index += 1
        self.refs_entry.delete(0, "end")
        self.refs_entry.insert(0, text)
        self.frames_entry.delete(0, "end")
        self.frames_entry.insert(0, str(frames))
        self._show_error("")

    def _show_error(self, message):
        self.error_label.configure(text=message)
        color = S.FAULT if message else S.BORDER
        self.refs_entry.configure(border_color=color)
        self.frames_entry.configure(border_color=color)

    def _start(self):
        try:
            refs, frames = validate_inputs(self.refs_entry.get(), self.frames_entry.get())
        except InputError as err:
            self._show_error(str(err))
            return
        self._show_error("")
        self.run = simulate(self.algo_var.get(), refs, frames)
        self.results.pack_forget()
        self.panel.set_algorithm(self.algo_var.get())
        self.panel.set_run(self.run)
        self.controller.load([self.run])
        self.controller.manual = self.manual_var.get()
        self.controller.start()

    def _pause(self):
        self.controller.pause()

    def _resume(self):
        self.controller.resume()

    def _restart(self):
        self.controller.manual = self.manual_var.get()
        self.controller.restart()

    def _next(self):
        self.controller.step()

    def _on_manual_toggle(self):
        self.controller.manual = self.manual_var.get()
        if self.manual_var.get() and self.controller.state == RUNNING:
            self.controller.pause()
        self._refresh_buttons()

    def _on_speed(self, value):
        speed = int(round(float(value)))
        self.speed_label.configure(text=f"Speed: {speed}/10")
        self.controller.set_delay(delay_for_speed(speed))

    def _on_algorithm_change(self, value):
        self.controller.clear()
        self.run = None
        self.results.pack_forget()
        self.panel.set_algorithm(value)
        self._refresh_buttons()

    # ----------------------------------------------------- controller callbacks
    def _on_phase(self, ref, phase):
        self.panel.show_phase(ref, phase)

    def _on_reset(self):
        self.results.pack_forget()
        self.panel.reset()

    def _on_complete(self):
        self.panel.show_complete()
        run = self.run
        frames = format_frames(run.final_frames)
        self.results_body.configure(text=(
            f"Total page references: {run.total}\n"
            f"Page hits: {run.hits}\n"
            f"Page faults: {run.faults}\n"
            f"Page fault rate: {run.fault_rate:.1f}%\n\n"
            f"Final RAM:\n{frames.replace(' | ', chr(10))}\n\n"
            f"{result_summary(run).split(chr(10) + chr(10), 1)[1]}"
        ))
        self.results.pack(fill="x", padx=6, pady=(8, 4))

    def _refresh_buttons(self):
        state = self.controller.state
        set_enabled(self.start_btn, state in (IDLE, FINISHED))
        set_enabled(self.pause_btn, state == RUNNING)
        set_enabled(self.resume_btn, state == PAUSED)
        set_enabled(self.restart_btn, self.controller.has_runs)
        set_enabled(self.next_btn, state == PAUSED)

    # ------------------------------------------------------------ screen events
    def on_show(self):
        self._refresh_buttons()

    def on_hide(self):
        """Cancel pending after() callbacks so nothing keeps animating off-screen."""
        self.controller.clear()
        self.run = None
        self.results.pack_forget()
        self.panel.clear()
        self._refresh_buttons()
