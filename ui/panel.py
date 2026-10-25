"""SimulationPanel: one algorithm's complete live view (used by both screens)."""
import customtkinter as ctk

from algorithms.simulator_engine import (ALGORITHM_FULL_NAMES, ALGORITHMS, fault_rate,
                                         result_summary)

from . import styles as S
from .widgets import (ExplanationBox, FlowBar, MemoryView, SequenceStrip, StatCard,
                      StatusBadge)

INTRO = {
    "FIFO": "FIFO removes the page that entered RAM first. Press Start to watch it work.",
    "LRU": "LRU removes the page that was used least recently. Press Start to watch it work.",
    "Optimal": ("Optimal removes the page whose next use is farthest in the future. It is a "
                "theoretical benchmark. Press Start to watch it work."),
}

FLOW_STAGE = {"request": 1, "hit": 2, "fault": 2, "select": 2, "evict": 3, "load": 3, "done": 3}


class SimulationPanel(ctk.CTkFrame):
    def __init__(self, master, algorithm, compact=False, show_flow=False):
        super().__init__(master, fg_color=S.CREAM, corner_radius=18,
                         border_width=1, border_color=S.BORDER)
        self.algorithm = algorithm
        self.compact = compact
        self.run = None
        pad = 10 if compact else 16

        # header: algorithm name + status badge
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=pad, pady=(pad - 2, 2))
        head.grid_columnconfigure(0, weight=1)
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.grid(row=0, column=0, sticky="w")
        self.title_label = ctk.CTkLabel(titles, text=algorithm, anchor="w", text_color=S.FOREST,
                                        font=S.font(22 if compact else 28, "bold"))
        self.title_label.pack(anchor="w")
        self.subtitle = ctk.CTkLabel(titles, text=ALGORITHM_FULL_NAMES[algorithm], anchor="w",
                                     text_color=S.TEXT_MUTED, font=S.font(12 if compact else 14))
        self.subtitle.pack(anchor="w")
        self.badge = StatusBadge(head, compact=compact)
        self.badge.grid(row=0, column=1, sticky="e")

        self.flow = None
        if show_flow:
            self.flow = FlowBar(self)
            self.flow.pack(fill="x", padx=pad, pady=(4, 2))

        ctk.CTkLabel(self, text="PROCESS PAGE REFERENCES", anchor="w", text_color=S.TEXT,
                     font=S.font(12 if compact else 14, "bold")).pack(fill="x", padx=pad + 2, pady=(6, 0))
        self.strip = SequenceStrip(self, compact=compact)
        self.strip.pack(fill="x", padx=pad, pady=(2, 2))

        self.memory = MemoryView(self, compact=compact)
        self.memory.pack(fill="both", expand=True, padx=pad, pady=2)

        self.explain = ExplanationBox(self, height=84 if compact else 96)
        self.explain.pack(fill="x", padx=pad, pady=(4, 4))

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=pad, pady=(2, pad))
        names = (["Hits", "Faults", "Fault rate", "Frames used"] if compact else
                 ["Reference", "Current page", "Hits", "Faults", "Fault rate", "Frames used"])
        self.cards = {}
        for i, name in enumerate(names):
            card = StatCard(stats, name, compact=compact)
            card.grid(row=0, column=i, sticky="nsew", padx=3)
            stats.grid_columnconfigure(i, weight=1, uniform="stat")
            self.cards[name] = card
        self.clear()

    # ---------------------------------------------------------------- state
    def set_algorithm(self, algorithm):
        self.algorithm = algorithm
        self.title_label.configure(text=algorithm)
        self.subtitle.configure(text=ALGORITHM_FULL_NAMES[algorithm])
        self.clear()

    def clear(self):
        """Nothing loaded yet (before the first Start)."""
        self.run = None
        self.strip.set_refs([])
        self.memory.render([None] * 3)
        self.badge.set("READY")
        self.explain.set(f"{self.algorithm} - READY", INTRO[self.algorithm])
        self._set_stats(0, "-", 0, 0, 0.0, 0, 0)
        if self.flow:
            self.flow.highlight(0)

    def set_run(self, run):
        self.run = run
        self.reset()

    def reset(self):
        """Back to the start of the loaded run: empty frames, zero statistics, no highlights."""
        if self.run is None:
            return self.clear()
        self.strip.set_refs(self.run.refs)
        self.memory.render([None] * self.run.num_frames)
        self.badge.set("READY")
        self.explain.set(f"{self.algorithm} - READY", INTRO[self.algorithm])
        self._set_stats(0, "-", 0, 0, 0.0, 0, self.run.total)
        if self.flow:
            self.flow.highlight(0)

    def phase_count(self, ref_index):
        return len(self.run.phases[ref_index]) if self.run else 0

    # ---------------------------------------------------------------- rendering
    def show_phase(self, ref_index, phase_index):
        if self.run is None or ref_index >= len(self.run.steps):
            return
        step = self.run.steps[ref_index]
        phases = self.run.phases[ref_index]
        phase = phases[min(phase_index, len(phases) - 1)]
        kind = phase.kind

        # strip: current box + outcomes known so far
        known = ref_index + (0 if kind == "request" else 1)
        outcomes = [s.hit for s in self.run.steps[:known]]
        self.strip.set_state(ref_index, ref_index, outcomes)

        # memory view
        page = step.page
        before, after = step.frames_before, step.frames_after
        if kind == "request":
            self.memory.render(before, incoming=page, incoming_kind="request")
        elif kind == "hit":
            self.memory.render(before, incoming=page, incoming_kind="hit", slot=step.slot,
                               slot_kind="hit", arrow="ok")
        elif kind == "fault":
            self.memory.render(before, incoming=page, incoming_kind="fault")
        elif kind == "select":
            self.memory.render(before, incoming=page, incoming_kind="fault", slot=step.slot,
                               slot_kind="victim")
        elif kind == "evict":
            self.memory.render(before, incoming=page, incoming_kind="fault", slot=step.slot,
                               slot_kind="evicted")
        elif kind == "load":
            self.memory.render(before, incoming=page, incoming_kind="loading", slot=step.slot,
                               slot_kind="loaded", slot_page=page, arrow="ok")
        else:  # done: final stable view of RAM
            self.memory.render(after, incoming=page, incoming_kind="loaded")

        self.badge.set(phase.status)
        self.explain.set(phase.title, phase.text)
        if self.flow:
            self.flow.highlight(FLOW_STAGE.get(kind, 0))

        # statistics (the outcome counts as known once the request has been checked)
        if kind == "request":
            prev = self.run.steps[ref_index - 1] if ref_index > 0 else None
            hits = prev.hits if prev else 0
            faults = prev.faults if prev else 0
            processed = ref_index
            frames_shown = before
        else:
            hits, faults, processed = step.hits, step.faults, step.processed
            frames_shown = after if kind in ("done", "hit") else before
        used = sum(1 for f in frames_shown if f is not None)
        self._set_stats(ref_index + 1, page, hits, faults, fault_rate(faults, processed),
                        used, self.run.total, hit_color=kind == "hit",
                        fault_color=kind in ("fault", "select", "evict", "load", "done") and not step.hit)

    def show_complete(self):
        if self.run is None:
            return
        run = self.run
        self.strip.set_state(None, run.total, [s.hit for s in run.steps])
        self.memory.render(run.final_frames)
        self.badge.set("COMPLETE")
        self.explain.set(f"{self.algorithm} - COMPLETE", result_summary(run))
        used = sum(1 for f in run.final_frames if f is not None)
        self._set_stats(run.total, run.refs[-1], run.hits, run.faults, run.fault_rate,
                        used, run.total)
        if self.flow:
            self.flow.highlight(3)

    def _set_stats(self, position, page, hits, faults, rate, used, total,
                   hit_color=False, fault_color=False):
        c = self.cards
        if "Reference" in c:
            c["Reference"].set(f"{position}/{total}" if total else "0/0")
            c["Current page"].set(page)
        c["Hits"].set(hits, S.HIT if hit_color else None)
        c["Faults"].set(faults, S.FAULT if fault_color else None)
        c["Fault rate"].set(f"{rate:.1f}%")
        frames = self.run.num_frames if self.run else 0
        c["Frames used"].set(f"{used}/{frames}" if frames else "0")
