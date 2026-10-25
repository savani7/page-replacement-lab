"""Reusable widgets: canvases for page sequence and RAM, stat cards, badges, buttons."""
import math
import tkinter as tk

import customtkinter as ctk

from . import styles as S


# ------------------------------------------------------------------ small helpers
def rounded_rect(canvas, x1, y1, x2, y2, r=12, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
        x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def ui_scale(widget) -> float:
    """Pixel scale factor (1.0 at 96 dpi) so fixed-size drawings stay proportional."""
    try:
        return max(1.0, float(widget.winfo_fpixels("1i")) / 96.0)
    except Exception:
        return 1.0


def make_button(master, text, command, kind="primary", width=140, height=38):
    fg, hover, tc = (
        (S.FOREST, S.FOREST_HOVER, S.WHITE) if kind == "primary"
        else (S.MINT, S.MINT_HOVER, S.TEXT)
    )
    btn = ctk.CTkButton(
        master, text=text, command=command, fg_color=fg, hover_color=hover,
        text_color=tc, text_color_disabled=S.DISABLED_TEXT, corner_radius=12,
        height=height, width=width, font=S.font(14, "bold"),
    )
    btn._kind = kind
    return btn


def set_enabled(btn, enabled: bool) -> None:
    kind = getattr(btn, "_kind", "primary")
    fg = (S.FOREST if kind == "primary" else S.MINT) if enabled else S.DISABLED_BG
    btn.configure(state="normal" if enabled else "disabled", fg_color=fg)


def make_entry(master, width=240, placeholder=""):
    return ctk.CTkEntry(
        master, width=width, height=38, corner_radius=10, fg_color=S.FRAME_FILL,
        border_color=S.BORDER, border_width=2, text_color=S.TEXT,
        placeholder_text=placeholder, font=S.font(14),
    )


def make_card(master, **kw):
    opts = dict(fg_color=S.CREAM, corner_radius=18, border_width=1, border_color=S.BORDER)
    opts.update(kw)
    return ctk.CTkFrame(master, **opts)


# --------------------------------------------------------------- page sequence strip
class SequenceStrip(tk.Frame):
    """AREA A - PROCESS PAGES. A scrollable row of page boxes that follows the current one."""

    def __init__(self, master, compact=False):
        super().__init__(master, bg=S.CREAM)
        self.compact = compact
        self.refs = []
        self.current = None
        self.past_upto = 0
        self.outcomes = []          # True = hit, False = fault, for indices known so far
        self.canvas = tk.Canvas(self, bg=S.CREAM, highlightthickness=0, height=96)
        self.scroll = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self.canvas.xview, height=12,
            fg_color=S.CREAM, button_color=S.BORDER, button_hover_color=S.FOREST,
        )
        self.canvas.configure(xscrollcommand=self.scroll.set)
        self.canvas.pack(fill="x", expand=True)
        self.scroll.pack(fill="x", pady=(2, 0))
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def set_refs(self, refs):
        self.refs = list(refs)
        self.set_state(None, 0, [])

    def set_state(self, current, past_upto, outcomes):
        self.current = current
        self.past_upto = past_upto
        self.outcomes = list(outcomes)
        self.redraw()

    def redraw(self):
        c = self.canvas
        c.delete("all")
        sc = ui_scale(self)
        bw = int(62 * sc)
        bh = int((48 if self.compact else 56) * sc)
        gap = int(8 * sc)
        pad = int(10 * sc)
        top = int(22 * sc)
        height = top + bh + int(26 * sc)
        c.configure(height=height)
        if not self.refs:
            c.create_text(pad, height / 2, anchor="w", fill=S.TEXT_MUTED,
                          font=S.canvas_font(14 * sc),
                          text="Page references will appear here once you press Start.")
            c.configure(scrollregion=(0, 0, 1, height))
            return
        for i, page in enumerate(self.refs):
            x1 = pad + i * (bw + gap)
            x2, y1, y2 = x1 + bw, top, top + bh
            cx = (x1 + x2) / 2
            is_cur = i == self.current
            is_past = i < self.past_upto
            if is_cur:
                fill, outline, width, fg, sub = S.FOREST, S.FOREST_DARK, 3, S.WHITE, "#CFE6DA"
            elif is_past:
                fill, outline, width, fg, sub = S.PAST, S.BORDER, 1, S.TEXT_MUTED, S.TEXT_MUTED
            else:
                fill, outline, width, fg, sub = S.FRAME_FILL, S.BORDER, 2, S.TEXT, S.TEXT_MUTED
            rounded_rect(c, x1, y1, x2, y2, r=10 * sc, fill=fill, outline=outline, width=width)
            c.create_text(cx, y1 + bh * 0.26, text="PAGE", fill=sub,
                          font=S.canvas_font(10 * sc, "bold"))
            c.create_text(cx, y1 + bh * 0.66, text=str(page), fill=fg,
                          font=S.canvas_font(20 * sc, "bold"))
            label = "NOW" if is_cur else f"#{i + 1}"
            c.create_text(cx, y1 - 10 * sc, text=label,
                          fill=S.FOREST if is_cur else S.TEXT_MUTED,
                          font=S.canvas_font(11 * sc, "bold"))
            if i < len(self.outcomes):
                hit = self.outcomes[i]
                c.create_text(cx, y2 + 12 * sc, text="HIT" if hit else "FAULT",
                              fill=S.HIT if hit else S.FAULT,
                              font=S.canvas_font(11 * sc, "bold"))
        total = pad * 2 + len(self.refs) * (bw + gap)
        c.configure(scrollregion=(0, 0, total, height))
        self._keep_current_visible(pad, bw, gap, total)

    def _keep_current_visible(self, pad, bw, gap, total):
        view_w = self.canvas.winfo_width()
        if view_w <= 1 or total <= view_w:
            self.canvas.xview_moveto(0)
            return
        if self.current is None:
            return
        center = pad + self.current * (bw + gap) + bw / 2
        frac = (center - view_w / 2) / total
        self.canvas.xview_moveto(max(0.0, min(1.0, frac)))


# --------------------------------------------------------------- main memory canvas
class MemoryView(tk.Canvas):
    """AREA B - MAIN MEMORY. Incoming-page box, arrow, and large RAM frame boxes."""

    SLOT_STYLES = {
        # kind: (fill, outline, outline width, text color, tag)
        "hit": (S.HIT, S.FOREST_DARK, 4, S.WHITE, "HIT"),
        "victim": (S.VICTIM, S.FAULT, 5, S.TEXT, "VICTIM"),
        "evicted": (S.FAULT, "#A8503F", 4, S.WHITE, "EVICTED"),
        "loaded": (S.INCOMING, S.HIT, 4, S.TEXT, "LOADED"),
    }

    def __init__(self, master, compact=False):
        super().__init__(master, bg=S.CREAM, highlightthickness=0,
                         height=200 if compact else 260)
        self.compact = compact
        self._st = dict(frames=[], incoming=None, incoming_kind="idle", slot=None,
                        slot_kind=None, slot_page=None, arrow=None)
        self.bind("<Configure>", lambda e: self.draw())

    def render(self, frames, incoming=None, incoming_kind="idle", slot=None,
               slot_kind=None, slot_page=None, arrow=None):
        self._st = dict(frames=list(frames), incoming=incoming, incoming_kind=incoming_kind,
                        slot=slot, slot_kind=slot_kind, slot_page=slot_page, arrow=arrow)
        self.draw()

    # ---- drawing
    def draw(self):
        self.delete("all")
        st = self._st
        frames = st["frames"]
        n = len(frames)
        if n == 0:
            return
        sc = ui_scale(self)
        W = max(self.winfo_width(), 240)
        H = max(self.winfo_height(), 160)
        title_h = int(28 * sc)
        self.create_text(8, title_h / 2 + 2, anchor="w", text="MAIN MEMORY - RAM",
                         fill=S.TEXT, font=S.canvas_font((14 if self.compact else 17) * sc, "bold"))
        y0, y1 = title_h + 6, H - 6
        body_h = y1 - y0

        # ---- incoming page box (left)
        m = 8
        iw = max(86 * sc, min(180 * sc, W * 0.22))
        ih = min(110 * sc, body_h * 0.52)
        cy = (y0 + y1) / 2 - 8 * sc
        ix1, ix2, iy1, iy2 = m, m + iw, cy - ih / 2, cy + ih / 2
        self.create_text((ix1 + ix2) / 2, iy1 - 12 * sc, text="PAGE REQUEST", fill=S.TEXT_MUTED,
                         font=S.canvas_font(11 * sc, "bold"))
        kind = st["incoming_kind"]
        look = {
            "idle": (S.FRAME_EMPTY, S.BORDER, 2, S.TEXT_MUTED, "WAITING"),
            "request": (S.INCOMING, S.FOREST, 3, S.TEXT, "INCOMING"),
            "hit": (S.HIT, S.FOREST_DARK, 3, S.WHITE, "HIT"),
            "fault": (S.FAULT, "#A8503F", 3, S.WHITE, "PAGE FAULT"),
            "loading": (S.INCOMING, S.HIT, 3, S.TEXT, "LOADING"),
            "loaded": (S.INCOMING, S.HIT, 3, S.TEXT, "LOADED"),
        }[kind]
        fill, outline, width, fg, label = look
        rounded_rect(self, ix1, iy1, ix2, iy2, r=14 * sc, fill=fill, outline=outline, width=width,
                     dash=(5, 4) if kind == "idle" else None)
        if st["incoming"] is None:
            self.create_text((ix1 + ix2) / 2, (iy1 + iy2) / 2, text="-", fill=fg,
                             font=S.canvas_font(ih * 0.4, "bold"))
        else:
            self.create_text((ix1 + ix2) / 2, iy1 + ih * 0.24, text="PAGE", fill=fg,
                             font=S.canvas_font(max(10, ih * 0.14), "bold"))
            self.create_text((ix1 + ix2) / 2, iy1 + ih * 0.62, text=str(st["incoming"]), fill=fg,
                             font=S.canvas_font(max(16, ih * 0.42), "bold"))
        label_color = {"hit": S.HIT, "fault": S.FAULT}.get(kind, S.TEXT)
        self.create_text((ix1 + ix2) / 2, iy2 + 14 * sc, text=label, fill=label_color,
                         font=S.canvas_font(13 * sc, "bold"))

        # ---- RAM block (right)
        gap = max(44 * sc, W * 0.07)
        rx0, rx1 = ix2 + gap, W - m
        rounded_rect(self, rx0, y0, rx1, y1, r=16 * sc, fill=S.RAM_BG, outline=S.FOREST, width=2)
        ax0, ax1, ay0, ay1 = rx0 + 10, rx1 - 10, y0 + 10, y1 - 10
        cols = 1 if n <= 4 else 2
        rows = math.ceil(n / cols)
        gx = gy = 8
        fw = (ax1 - ax0 - (cols - 1) * gx) / cols
        fh = min((ay1 - ay0 - (rows - 1) * gy) / rows, 96 * sc)
        block_h = rows * fh + (rows - 1) * gy
        ay0 = ay0 + max(0, ((ay1 - ay0) - block_h) / 2)

        slot_rect = None
        for k in range(n):
            col, row = divmod(k, rows)
            fx1 = ax0 + col * (fw + gx)
            fy1 = ay0 + row * (fh + gy)
            fx2, fy2 = fx1 + fw, fy1 + fh
            page = frames[k]
            style = None
            if k == st["slot"] and st["slot_kind"]:
                style = self.SLOT_STYLES[st["slot_kind"]]
                if st["slot_page"] is not None:
                    page = st["slot_page"]
            if style:
                fill, outline, width, fg, tag = style
            elif page is None:
                fill, outline, width, fg, tag = S.FRAME_EMPTY, S.BORDER, 2, S.TEXT_MUTED, "EMPTY"
            else:
                fill, outline, width, fg, tag = S.FRAME_FILL, S.BORDER, 2, S.TEXT, "OCCUPIED"
            rounded_rect(self, fx1, fy1, fx2, fy2, r=12 * sc, fill=fill, outline=outline,
                         width=width, dash=(5, 4) if (page is None and not style) else None)
            small = max(10, min(14 * sc, fh * 0.2))
            self.create_text(fx1 + 12, fy1 + fh * 0.2, anchor="w", text=f"FRAME {k + 1}",
                             fill=fg, font=S.canvas_font(small, "bold"))
            self.create_text(fx2 - 12, fy1 + fh * 0.2, anchor="e", text=tag, fill=fg,
                             font=S.canvas_font(small, "bold"))
            big = max(13, min(30 * sc, fh * 0.36))
            if page is None:
                self.create_text((fx1 + fx2) / 2, fy1 + fh * 0.64, text="- empty -", fill=fg,
                                 font=S.canvas_font(big * 0.7, "bold"))
            else:
                weight = "bold overstrike" if st["slot_kind"] == "evicted" and k == st["slot"] else "bold"
                self.create_text((fx1 + fx2) / 2, fy1 + fh * 0.64, text=f"PAGE {page}", fill=fg,
                                 font=S.canvas_font(big, weight))
            if k == st["slot"]:
                slot_rect = (fx1, (fy1 + fy2) / 2)

        # ---- arrow from the request box to the frame being used
        if st["arrow"] and slot_rect:
            color = S.HIT if st["arrow"] == "ok" else S.FAULT
            self.create_line(ix2 + 6, (iy1 + iy2) / 2, slot_rect[0] - 3, slot_rect[1],
                             fill=color, width=max(3, int(4 * sc)), arrow=tk.LAST,
                             arrowshape=(16, 20, 7))


# ------------------------------------------------------------------- small widgets
class StatCard(ctk.CTkFrame):
    def __init__(self, master, title, value="-", compact=False):
        super().__init__(master, fg_color=S.CARD_INNER, corner_radius=12,
                         border_width=1, border_color=S.BORDER)
        self.value = ctk.CTkLabel(self, text=value, font=S.font(18 if compact else 24, "bold"),
                                  text_color=S.TEXT)
        self.value.pack(padx=8, pady=(6, 0))
        ctk.CTkLabel(self, text=title, font=S.font(11 if compact else 12),
                     text_color=S.TEXT_MUTED).pack(padx=8, pady=(0, 6))

    def set(self, value, color=None):
        self.value.configure(text=str(value), text_color=color or S.TEXT)


class StatusBadge(ctk.CTkLabel):
    COLORS = {
        "READY": (S.BORDER, S.TEXT),
        "CHECKING": (S.INCOMING, S.TEXT),
        "HIT": (S.HIT, S.WHITE),
        "PAGE FAULT": (S.FAULT, S.WHITE),
        "LOADING": (S.MINT, S.TEXT),
        "EVICTING": (S.VICTIM, S.TEXT),
        "COMPLETE": (S.FOREST, S.WHITE),
    }

    def __init__(self, master, compact=False):
        super().__init__(master, text="READY", width=130 if compact else 160,
                         height=30 if compact else 34, corner_radius=16,
                         font=S.font(13 if compact else 15, "bold"))
        self.set("READY")

    def set(self, status):
        bg, fg = self.COLORS.get(status, (S.BORDER, S.TEXT))
        self.configure(text=status, fg_color=bg, text_color=fg)


class FlowBar(ctk.CTkFrame):
    """PROCESS PAGES -> PAGE REQUEST -> OS DECISION -> MAIN MEMORY."""

    STAGES = ("PROCESS PAGES", "PAGE REQUEST", "OS DECISION", "MAIN MEMORY")

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.chips = []
        for i, name in enumerate(self.STAGES):
            chip = ctk.CTkLabel(self, text=name, corner_radius=12, height=30,
                                font=S.font(12, "bold"), fg_color=S.CARD_INNER,
                                text_color=S.TEXT_MUTED)
            chip.grid(row=0, column=2 * i, sticky="ew", padx=2)
            self.chips.append(chip)
            self.grid_columnconfigure(2 * i, weight=1)
            if i < len(self.STAGES) - 1:
                ctk.CTkLabel(self, text="->", width=26, font=S.font(14, "bold"),
                             text_color=S.FOREST).grid(row=0, column=2 * i + 1)
        self.highlight(0)

    def highlight(self, index):
        for i, chip in enumerate(self.chips):
            if i == index:
                chip.configure(fg_color=S.FOREST, text_color=S.WHITE)
            else:
                chip.configure(fg_color=S.CARD_INNER, text_color=S.TEXT_MUTED)


class DiagramBanner(tk.Canvas):
    """Static illustration for the dashboard: process pages -> OS -> RAM frames."""

    def __init__(self, master):
        super().__init__(master, bg=S.SAGE, highlightthickness=0, height=130)
        self.bind("<Configure>", lambda e: self.draw())

    def draw(self):
        self.delete("all")
        W = max(self.winfo_width(), 600)
        cy = 62
        # process pages
        x = W / 2 - 330
        self.create_text(x + 70, 8, text="PROCESS PAGES", fill=S.TEXT, font=S.canvas_font(13, "bold"))
        for i in range(4):
            rounded_rect(self, x + i * 36, cy - 28, x + i * 36 + 30, cy + 28, r=8,
                         fill=S.CREAM, outline=S.BORDER, width=2)
            self.create_text(x + i * 36 + 15, cy, text=f"P{i + 1}", fill=S.TEXT,
                             font=S.canvas_font(13, "bold"))
        self.create_line(x + 156, cy, x + 215, cy, arrow=tk.LAST, fill=S.FOREST, width=3,
                         arrowshape=(12, 15, 5))
        # operating system
        ox = x + 220
        rounded_rect(self, ox, cy - 34, ox + 160, cy + 34, r=14, fill=S.FOREST, outline=S.FOREST_DARK, width=2)
        self.create_text(ox + 80, cy - 8, text="OPERATING", fill=S.WHITE, font=S.canvas_font(13, "bold"))
        self.create_text(ox + 80, cy + 12, text="SYSTEM", fill=S.WHITE, font=S.canvas_font(13, "bold"))
        self.create_line(ox + 166, cy, ox + 225, cy, arrow=tk.LAST, fill=S.FOREST, width=3,
                         arrowshape=(12, 15, 5))
        # RAM frames
        rx = ox + 232
        self.create_text(rx + 85, 8, text="MAIN MEMORY (FRAMES)", fill=S.TEXT, font=S.canvas_font(13, "bold"))
        rounded_rect(self, rx, cy - 40, rx + 170, cy + 44, r=12, fill=S.RAM_BG, outline=S.FOREST, width=2)
        labels = [("F1", S.FRAME_FILL), ("F2", S.INCOMING), ("F3", S.VICTIM)]
        for i, (name, color) in enumerate(labels):
            rounded_rect(self, rx + 10, cy - 34 + i * 26, rx + 160, cy - 12 + i * 26, r=6,
                         fill=color, outline=S.BORDER, width=1)
            self.create_text(rx + 22, cy - 23 + i * 26, anchor="w", text=name, fill=S.TEXT,
                             font=S.canvas_font(11, "bold"))
        self.create_text(rx + 150, cy - 23 + 26, anchor="e", text="LOADED", fill=S.HIT,
                         font=S.canvas_font(10, "bold"))
        self.create_text(rx + 150, cy - 23 + 52, anchor="e", text="EVICTED", fill=S.FAULT,
                         font=S.canvas_font(10, "bold"))


class ExplanationBox(ctk.CTkFrame):
    """Card with a bold headline and a read-only multi-line body."""

    def __init__(self, master, height=130):
        super().__init__(master, fg_color=S.CARD_INNER, corner_radius=14,
                         border_width=1, border_color=S.BORDER)
        self.headline = ctk.CTkLabel(self, text="", anchor="w", font=S.font(14, "bold"),
                                     text_color=S.FOREST)
        self.headline.pack(fill="x", padx=14, pady=(8, 0))
        self.body = ctk.CTkTextbox(self, height=height, fg_color=S.CARD_INNER, text_color=S.TEXT,
                                   font=S.font(13), wrap="word", border_width=0,
                                   activate_scrollbars=True)
        self.body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.body.configure(state="disabled")

    def set(self, headline, body):
        self.headline.configure(text=headline)
        self.body.configure(state="normal")
        self.body.delete("1.0", "end")
        self.body.insert("1.0", body)
        self.body.configure(state="disabled")
