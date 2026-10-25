"""AlgoPanel: one complete visual simulation (sequence, incoming page, RAM boxes,
replacement animation, explanation, statistics).  Used full-size by the
Interactive Simulator and compact (x3) by the Battle Arena.

The panel is a pure *renderer*: ``render(step_index, phase)`` draws the state
described by the pre-computed algorithm steps.  Phases of one reference:

  incoming -> decide -> remove -> enter -> done      (replacement)
  incoming -> enter -> done                          (hit / free frame)
"""
import tkinter as tk

import customtkinter as ctk

from . import styles as S
from .widgets import round_rect


class AlgoPanel(ctk.CTkFrame):
    def __init__(self, master, algo_name, compact=False):
        super().__init__(master, fg_color=S.CARD, corner_radius=20, border_width=3,
                         border_color=S.ALGO_COLORS[algo_name][0])
        self.compact = compact
        self.algo = algo_name
        self.refs, self.steps, self.n = [], [], 3
        self._anim_id = None
        self._slide_i = 0

        # geometry
        if compact:
            self.box, self.gap, self.seq_h = 32, 6, 96
            self.W, self.fw, self.fx, self.ix, self.iw = 380, 104, 96, 8, 60
            self.info_x, self.info_w = 208, 165
            self.fh_big, self.fh_small, self.fgap, self.y0 = 44, 34, 8, 30
            self.wrap = 360
        else:
            self.box, self.gap, self.seq_h = 44, 8, 118
            self.W, self.fw, self.fx, self.ix, self.iw = 720, 250, 200, 20, 110
            self.info_x, self.info_w = 480, 230
            self.fh_big, self.fh_small, self.fgap, self.y0 = 64, 48, 12, 44
            self.wrap = 780

        # header
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(10, 0))
        self.title_lbl = ctk.CTkLabel(head, text="", font=S.font(18 if compact else 24, "bold"))
        self.title_lbl.pack(side="left")
        self.badge = ctk.CTkLabel(head, text="READY", corner_radius=12, height=28, width=120,
                                  font=S.font(12, "bold"), fg_color=S.BLUE_L, text_color=S.TEXT)
        self.badge.pack(side="right")

        # reference sequence
        ctk.CTkLabel(self, text="PAGE REFERENCE SEQUENCE", font=S.font(11, "bold"),
                     text_color=S.MUTED).pack(anchor="w", padx=16, pady=(6, 0))
        self.seq = tk.Canvas(self, height=self.seq_h, bg=S.CARD, highlightthickness=0)
        self.seq.pack(fill="x", padx=12)
        self.seq_bar = ctk.CTkScrollbar(self, orientation="horizontal", height=10,
                                        command=self.seq.xview)
        self.seq_bar.pack(fill="x", padx=14)
        self.seq.configure(xscrollcommand=self.seq_bar.set)

        # RAM drawing
        self.ram = tk.Canvas(self, width=self.W, height=300, bg=S.CARD, highlightthickness=0)
        self.ram.pack(pady=(6, 0))

        # bookkeeping line (arrival order / recency order / remaining references)
        self.note = ctk.CTkLabel(self, text="", font=S.font(12 if compact else 14, "bold"),
                                 text_color=S.MUTED, wraplength=self.wrap, justify="left")
        self.note.pack(anchor="w", padx=16, pady=(2, 4))

        # explanation card
        self.exp_card = ctk.CTkFrame(self, fg_color=S.BLUE_L, corner_radius=16)
        self.exp_card.pack(fill="x", padx=12, pady=4)
        self.exp_head = ctk.CTkLabel(self.exp_card, text="", font=S.font(14 if compact else 18, "bold"),
                                     text_color=S.TEXT, anchor="w")
        self.exp_head.pack(fill="x", padx=14, pady=(8, 0))
        self.exp_text = ctk.CTkLabel(self.exp_card, text="", font=S.font(12 if compact else 15),
                                     text_color=S.TEXT, wraplength=self.wrap - 30,
                                     justify="left", anchor="w")
        self.exp_text.pack(fill="x", padx=14, pady=(2, 10))

        # statistics
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(4, 12))
        keys = ([("ref", "Reference"), ("hits", "Hits"), ("faults", "Faults"), ("rate", "Fault rate")]
                if compact else
                [("ref", "Reference"), ("page", "Page"), ("hits", "Page hits"), ("faults", "Page faults"),
                 ("rate", "Fault rate"), ("frames", "Frames used"), ("total", "Total refs")])
        self.stats = {}
        for k, title in keys:
            c = ctk.CTkFrame(row, fg_color=S.EMPTY_FILL, corner_radius=12)
            c.pack(side="left", expand=True, fill="x", padx=3)
            v = ctk.CTkLabel(c, text="-", font=S.font(15 if compact else 20, "bold"), text_color=S.TEXT)
            v.pack(pady=(5, 0))
            ctk.CTkLabel(c, text=title, font=S.font(10 if compact else 11), text_color=S.MUTED).pack(pady=(0, 5))
            self.stats[k] = v

        self.set_algorithm(algo_name)
        self.load([], 3, [])

    # ------------------------------------------------------------------ setup
    def set_algorithm(self, name):
        self.algo = name
        dark, light = S.ALGO_COLORS[name]
        self.configure(border_color=dark)
        self.title_lbl.configure(text=f"{name}  •  {S.ALGO_TAGLINE[name]}" if not self.compact
                                 else name.upper(), text_color=dark)

    def load(self, refs, n_frames, steps):
        """Give the panel a finished simulation and show the idle state."""
        self.stop_animation()
        self.refs, self.n, self.steps = list(refs), n_frames, list(steps)
        fh = self.fh_big if self.n <= 5 else self.fh_small
        if self.compact:
            h = self.y0 + self.n * (fh + self.fgap) + 56
        else:
            h = self.y0 + self.n * (fh + self.fgap) + 30 + 150
        self.ram.configure(height=h)
        self.render_idle()

    def phases(self, i):
        from .playback import FULL_PHASES, SHORT_PHASES
        return FULL_PHASES if self.steps[i].replaced else SHORT_PHASES

    def stop_animation(self):
        if self._anim_id is not None:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

    # ---------------------------------------------------------------- render
    def render_idle(self):
        self.stop_animation()
        self.badge.configure(text="READY", fg_color=S.BLUE_L)
        self._draw_sequence(-1, "idle")
        self._draw_ram(None, "idle")
        self.note.configure(text="")
        self.exp_card.configure(fg_color=S.BLUE_L)
        self.exp_head.configure(text="Ready")
        self.exp_text.configure(text="Press START to watch the page replacement animation."
                                if self.steps else "Enter a reference string and press START.")
        total = len(self.refs)
        vals = {"ref": f"0 / {total}", "page": "-", "hits": "0", "faults": "0", "rate": "0%",
                "frames": f"0 / {self.n}", "total": str(total)}
        for k, lbl in self.stats.items():
            lbl.configure(text=vals[k])

    def render(self, i, phase):
        if i < 0 or i >= len(self.steps):
            self.render_idle()
            return
        st = self.steps[i]
        self.stop_animation()
        self._draw_sequence(i, phase)
        self._draw_ram(st, phase)
        self.note.configure(text=st.order_note)

        # explanation + badge
        if phase == "incoming":
            head, text, tint = (f"Reference {i + 1}: Page {st.page} arrives",
                                f"The operating system needs Page {st.page}. Is it already in RAM?", S.BLUE_L)
            badge, bcol = "CHECKING...", S.BLUE_L
        else:
            tint = {"hit": S.GREEN_L, "load": S.AMBER_L, "replace": S.CORAL_L}[st.kind]
            bcol = {"hit": S.GREEN_L, "load": S.AMBER_L, "replace": S.CORAL_L}[st.kind]
            badge = {"hit": "PAGE HIT", "load": "PAGE FAULT", "replace": "FAULT + REPLACE"}[st.kind]
            head = st.headline
            text = st.reason if phase in ("decide", "remove") else st.explanation
        self.exp_card.configure(fg_color=tint)
        self.exp_head.configure(text=head)
        self.exp_text.configure(text=text)
        self.badge.configure(text=badge, fg_color=bcol)

        # statistics (totals change only once the step is finished)
        counted = phase == "done"
        prev = self.steps[i - 1] if i > 0 else None
        hits = st.hits if counted else (prev.hits if prev else 0)
        faults = st.faults if counted else (prev.faults if prev else 0)
        processed = i + 1 if counted else i
        frames = st.frames_after if phase in ("enter", "done") else st.frames_before
        vals = {"ref": f"{i + 1} / {len(self.refs)}", "page": str(st.page), "hits": str(hits),
                "faults": str(faults),
                "rate": f"{(faults / processed * 100) if processed else 0:.0f}%",
                "frames": f"{sum(p is not None for p in frames)} / {self.n}",
                "total": str(len(self.refs))}
        for k, lbl in self.stats.items():
            lbl.configure(text=vals[k])

    # -------------------------------------------------------- sequence strip
    def _draw_sequence(self, cur, phase):
        c = self.seq
        c.delete("all")
        b, g = self.box, self.gap
        for j, page in enumerate(self.refs):
            x = 8 + j * (b + g)
            y = 6
            if j < cur or (j == cur and phase == "done"):
                hit = self.steps[j].hit
                fill, line, tc = (S.GREEN_L, S.GREEN_D, S.TEXT) if hit else (S.CORAL_L, S.CORAL_D, S.TEXT)
                w = 3 if j == cur else 1
                if j == cur:
                    line = S.BLUE_D
            elif j == cur:
                fill, line, tc, w = S.BLUE_D, S.BLUE_D, "white", 2
            else:
                fill, line, tc, w = S.CARD, S.RESIDENT_LINE, S.TEXT, 1
            round_rect(c, x, y, x + b, y + b, r=8, fill=fill, outline=line, width=w)
            c.create_text(x + b / 2, y + b / 2, text=str(page), fill=tc,
                          font=S.font(14 if self.compact else 17, "bold"))
            c.create_text(x + b / 2, y + b + 10, text=str(j + 1), fill=S.MUTED, font=S.font(9))
            if j == cur:
                ax = x + b / 2
                ay = y + b + 20
                c.create_polygon(ax, ay, ax - 7, ay + 10, ax + 7, ay + 10, fill=S.BLUE_D, outline="")
                c.create_text(ax, ay + 20, text="CURRENT PAGE", fill=S.BLUE_D, font=S.font(9, "bold"))
        total_w = 16 + len(self.refs) * (b + g)
        c.configure(scrollregion=(0, 0, max(total_w, 10), self.seq_h))
        if cur >= 0 and total_w > c.winfo_width() > 1:
            c.xview_moveto(max(0.0, ((8 + cur * (b + g)) - c.winfo_width() / 2) / total_w))
        elif total_w <= max(c.winfo_width(), 1):
            c.xview_moveto(0)

    # ----------------------------------------------------------- RAM drawing
    def _frame_geometry(self):
        fh = self.fh_big if self.n <= 5 else self.fh_small
        return fh, [self.y0 + s * (fh + self.fgap) for s in range(self.n)]

    def _draw_ram(self, st, phase):
        c = self.ram
        c.delete("all")
        fh, ys = self._frame_geometry()
        fx, fw = self.fx, self.fw
        compact = self.compact

        showing_after = st is not None and phase in ("enter", "done")
        frames = ([None] * self.n if st is None else (st.frames_after if showing_after else st.frames_before))
        infos = ([""] * self.n if st is None else (st.info_after if showing_after else st.info_before))

        # RAM title
        c.create_text(fx + fw / 2, 14 if compact else 22, text="RAM", fill=S.TEXT,
                      font=S.font(13 if compact else 17, "bold"))

        # frame boxes
        for s in range(self.n):
            style = self._frame_style(s, frames[s], st, phase)
            fill, line, width, dash, tag, tag_col, text, text_col = style
            y = ys[s]
            round_rect(c, fx, y, fx + fw, y + fh, r=12, fill=fill, outline=line, width=width, dash=dash)
            c.create_text(fx + 10, y + fh * 0.27, text=f"FRAME {s + 1}", anchor="w", fill=S.MUTED,
                          font=S.font(8 if compact else 10, "bold"))
            if tag:
                c.create_text(fx + fw - 8, y + fh * 0.27, text=tag, anchor="e", fill=tag_col,
                              font=S.font(7 if compact else 9, "bold"))
            c.create_text(fx + fw / 2, y + fh * 0.66, text=text, fill=text_col,
                          font=S.font(11 if compact else 17, "bold"))
            info = infos[s] if frames[s] is not None else ""
            if info:
                strong = "<-" in info
                c.create_text(self.info_x, y + fh / 2, text=info.replace("<-", "←"), anchor="w",
                              width=self.info_w, fill=S.CORAL_D if strong else S.MUTED,
                              font=S.font(9 if compact else 11, "bold" if strong else "normal"))

        # incoming page box + arrow to the target frame
        iy = ys[0] + (self.n * (fh + self.fgap) - self.fgap) / 2 - (28 if compact else 40)
        ih = 56 if compact else 80
        c.create_text(self.ix + self.iw / 2, iy - 12, text="INCOMING" if compact else "INCOMING PAGE",
                      fill=S.BLUE_D, font=S.font(8 if compact else 10, "bold"))
        round_rect(c, self.ix, iy, self.ix + self.iw, iy + ih, r=12, fill=S.BLUE_L, outline=S.BLUE_D, width=3)
        c.create_text(self.ix + self.iw / 2, iy + ih / 2, text="-" if st is None else str(st.page),
                      fill=S.TEXT, font=S.font(20 if compact else 30, "bold"))
        if st is not None:
            target = self._target_slot(st, phase)
            ty = ys[target] + fh / 2 if target is not None else iy + ih / 2
            col = S.GREEN_D if st.kind == "hit" and phase != "incoming" else S.BLUE_D
            c.create_line(self.ix + self.iw + 2, iy + ih / 2, fx - 4, ty, arrow="last", width=3,
                          fill=col, dash=(4, 3) if phase == "incoming" else None, arrowshape=(10, 12, 5))

        if st is None:
            return

        # message pill
        msg, mcol, mfill = self._banner(st, phase)
        if compact:
            by = self.y0 + self.n * (fh + self.fgap) + 4
            round_rect(c, 8, by, self.W - 8, by + 34, r=10, fill=mfill, outline=mcol, width=2)
            c.create_text(self.W / 2, by + 17, text=msg, fill=mcol, font=S.font(10, "bold"), width=self.W - 30)
        else:
            self._draw_transformation(c, st, phase, msg, mcol, mfill, self.y0 + self.n * (fh + self.fgap) + 6)

        # sliding token = visible page movement
        if phase == "enter" and st.kind in ("load", "replace"):
            ty = ys[st.slot] + fh / 2
            self._slide(self.ix + self.iw / 2, iy + ih / 2, fx + fw / 2, ty, str(st.page))

    def _target_slot(self, st, phase):
        if phase == "incoming":
            return None
        if st.kind == "replace":
            return st.victim_slot
        return st.slot

    def _banner(self, st, phase):
        p, v = st.page, st.victim
        if phase == "incoming":
            return f"PAGE {p} IS REQUESTED - IS IT IN RAM?", S.BLUE_D, S.BLUE_L
        if st.kind == "hit":
            return f"PAGE {p} FOUND IN FRAME {st.slot + 1} - HIT", S.GREEN_D, S.GREEN_L
        if st.kind == "load":
            t = f"PAGE {p} NOT IN RAM - LOADED INTO FREE FRAME {st.slot + 1}"
            return t, S.AMBER_D, S.AMBER_L
        if phase == "decide":
            return f"PAGE {v} SELECTED FOR REMOVAL", S.CORAL_D, S.CORAL_L
        if phase == "remove":
            return f"PAGE {v} REMOVED FROM FRAME {st.slot + 1}", S.CORAL_D, S.CORAL_L
        if phase == "enter":
            return f"PAGE {p} ENTERS RAM (FRAME {st.slot + 1})", S.BLUE_D, S.BLUE_L
        return f"PAGE {v} REPLACED BY PAGE {p}", S.GREEN_D, S.GREEN_L

    def _frame_style(self, s, page, st, phase):
        """(fill, outline, width, dash, tag, tag colour, text, text colour)"""
        if page is None:
            fill, line, width, dash, text, tcol = S.EMPTY_FILL, S.BORDER, 2, (4, 3), "EMPTY", S.MUTED
        else:
            fill, line, width, dash, text, tcol = S.RESIDENT_FILL, S.RESIDENT_LINE, 2, None, f"PAGE {page}", S.TEXT
        tag, tagc = "", S.MUTED
        if st is None or phase == "incoming":
            return fill, line, width, dash, tag, tagc, text, tcol
        if st.kind == "hit" and s == st.slot:
            return S.GREEN_L, S.GREEN_D, 4, None, "HIT", S.GREEN_D, text, tcol
        if st.kind == "load" and s == st.slot:
            if phase in ("decide", "remove"):
                return S.BLUE_L, S.BLUE_D, 3, (5, 3), "FREE FRAME", S.BLUE_D, "EMPTY", S.MUTED
            if phase == "enter":
                return S.BLUE_L, S.BLUE_D, 4, None, "NEW PAGE", S.BLUE_D, text, tcol
            return S.GREEN_L, S.GREEN_D, 3, None, "LOADED", S.GREEN_D, text, tcol
        if st.kind == "replace" and s == st.victim_slot:
            if phase == "decide":
                return S.CORAL_L, S.CORAL_D, 4, None, "VICTIM", S.CORAL_D, text, tcol
            if phase == "remove":
                return "#FFF3F0", S.CORAL_D, 3, (6, 4), "REMOVED", S.CORAL_D, text, S.CORAL_D
            if phase == "enter":
                return S.BLUE_L, S.BLUE_D, 4, None, "NEW PAGE", S.BLUE_D, text, tcol
            return S.GREEN_L, S.GREEN_D, 3, None, "REPLACED", S.GREEN_D, text, tcol
        return fill, line, width, dash, tag, tagc, text, tcol

    def _draw_transformation(self, c, st, phase, msg, mcol, mfill, y):
        """RAM BEFORE -> selected -> removed -> enters -> RAM AFTER (full mode)."""
        bw, bh, g = (64, 38, 10) if self.n <= 4 else (44, 38, 8)
        c.create_text(20, y + 8, text="RAM BEFORE", anchor="w", fill=S.MUTED, font=S.font(10, "bold"))
        for s, p in enumerate(st.frames_before):
            x = 20 + s * (bw + g)
            hot = st.kind == "replace" and s == st.victim_slot and phase != "incoming"
            fill, line = (S.CORAL_L, S.CORAL_D) if hot else (S.RESIDENT_FILL, S.RESIDENT_LINE)
            if p is None:
                fill, line = S.EMPTY_FILL, S.BORDER
            round_rect(c, x, y + 20, x + bw, y + 20 + bh, r=8, fill=fill, outline=line, width=3 if hot else 1)
            c.create_text(x + bw / 2, y + 20 + bh / 2, text="-" if p is None else f"P{p}",
                          fill=S.CORAL_D if hot and phase in ("remove", "enter", "done") else S.TEXT,
                          font=S.font(13, "bold"))
            if hot and phase in ("remove", "enter", "done"):
                c.create_line(x + 6, y + 20 + bh - 6, x + bw - 6, y + 26, fill=S.CORAL_D, width=2)
        y2 = y + 20 + bh + 28
        c.create_text(20, y2 - 8, text="RAM AFTER", anchor="w", fill=S.MUTED, font=S.font(10, "bold"))
        reveal = phase in ("enter", "done")
        for s in range(len(st.frames_after)):
            x = 20 + s * (bw + g)
            p = st.frames_after[s] if reveal else None
            new = reveal and st.kind in ("load", "replace") and s == st.slot
            if not reveal:
                fill, line, w, txt = S.EMPTY_FILL, S.BORDER, 1, "?"
            elif new:
                fill, line, w, txt = S.BLUE_L, S.BLUE_D, 3, f"P{p}"
            elif p is None:
                fill, line, w, txt = S.EMPTY_FILL, S.BORDER, 1, "-"
            else:
                fill, line, w, txt = S.RESIDENT_FILL, S.RESIDENT_LINE, 1, f"P{p}"
            round_rect(c, x, y2 + 4, x + bw, y2 + 4 + bh, r=8, fill=fill, outline=line, width=w)
            c.create_text(x + bw / 2, y2 + 4 + bh / 2, text=txt, fill=S.MUTED if txt == "?" else S.TEXT,
                          font=S.font(13, "bold"))
        mx = 20 + max(len(st.frames_before), 3) * (bw + g) + 20
        mx = max(mx, 300)
        round_rect(c, mx, y + 14, self.W - 10, y2 + 4 + bh, r=14, fill=mfill, outline=mcol, width=2)
        c.create_text((mx + self.W - 10) / 2, (y + 14 + y2 + 4 + bh) / 2, text=msg, fill=mcol,
                      font=S.font(14, "bold"), width=self.W - 10 - mx - 24)

    # ------------------------------------------------------------- animation
    def _slide(self, x0, y0, x1, y1, text, steps=10, interval=25):
        self.stop_animation()
        self._slide_i = 0
        r = 16 if self.compact else 24

        def tick():
            self._anim_id = None
            self.ram.delete("token")
            t = (self._slide_i + 1) / steps
            t = t * t * (3 - 2 * t)                       # ease in-out
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if self._slide_i < steps - 1:
                round_rect(self.ram, x - r, y - r, x + r, y + r, r=8, fill=S.BLUE_D, outline="white",
                           width=2, tags="token")
                self.ram.create_text(x, y, text=text, fill="white", font=S.font(11 if self.compact else 14, "bold"),
                                     tags="token")
                self._slide_i += 1
                self._anim_id = self.after(interval, tick)

        tick()
