"""Learn Page Replacement: tabbed, scrollable lessons."""
import customtkinter as ctk

from . import styles as S
from .learning_content import TABS
from .widgets import card, home_bar

TAB_COLORS = {"Basics": S.TEAL_D, "FIFO": S.TEAL_D, "LRU": S.LAV_D, "Optimal": S.BLUE_D, "Comparison": S.GREEN_D}


class LearningScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.BG)
        home_bar(self, app, "Learn Page Replacement").pack(fill="x", padx=24, pady=(16, 8))
        self.tabs = ctk.CTkTabview(self, fg_color=S.CARD, corner_radius=20, border_width=1,
                                   border_color=S.BORDER, segmented_button_selected_color=S.BLUE_D,
                                   segmented_button_selected_hover_color=S.BLUE_D,
                                   segmented_button_unselected_color=S.BLUE_L,
                                   segmented_button_unselected_hover_color="#BFD9FA", text_color=S.TEXT)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        for name, builder in TABS:
            tab = self.tabs.add(name)
            body = ctk.CTkScrollableFrame(tab, fg_color="transparent")
            body.pack(fill="both", expand=True)
            self._render(body, builder(), TAB_COLORS.get(name, S.BLUE_D))

    def on_leave(self):
        pass

    def _render(self, parent, blocks, accent):
        for block in blocks:
            kind = block[0]
            if kind == "h":
                ctk.CTkLabel(parent, text=block[1], font=S.font(20, "bold"), text_color=accent,
                             anchor="w").pack(fill="x", padx=14, pady=(18, 4))
            elif kind == "p":
                ctk.CTkLabel(parent, text=block[1], font=S.font(15), text_color=S.TEXT, wraplength=980,
                             justify="left", anchor="w").pack(fill="x", padx=14, pady=4)
            elif kind == "bullets":
                for item in block[1]:
                    ctk.CTkLabel(parent, text="•  " + item, font=S.font(15), text_color=S.TEXT,
                                 wraplength=960, justify="left", anchor="w").pack(fill="x", padx=26, pady=2)
            elif kind == "code":
                f = ctk.CTkFrame(parent, fg_color=S.EMPTY_FILL, corner_radius=14, border_width=1,
                                 border_color=S.BORDER)
                f.pack(anchor="w", padx=14, pady=6)
                ctk.CTkLabel(f, text=block[1], font=(S.MONO, 14), text_color=S.TEXT, justify="left",
                             anchor="w").pack(padx=16, pady=12)
            elif kind == "table":
                self._table(parent, block[1], block[2])

    def _table(self, parent, header, rows):
        t = ctk.CTkFrame(parent, fg_color=S.BORDER, corner_radius=14)
        t.pack(fill="x", padx=14, pady=8)
        for c, h in enumerate(header):
            ctk.CTkLabel(t, text=h, font=S.font(14, "bold"), text_color=S.TEXT, fg_color=S.BLUE_L,
                         corner_radius=6, anchor="w", wraplength=300, justify="left").grid(
                row=0, column=c, sticky="nsew", padx=1, pady=1, ipadx=8, ipady=6)
            t.grid_columnconfigure(c, weight=1, uniform="col")
        for r, row in enumerate(rows, start=1):
            for c, v in enumerate(row):
                ctk.CTkLabel(t, text=v, font=S.font(14, "bold" if c == 0 else "normal"), text_color=S.TEXT,
                             fg_color=S.CARD, corner_radius=6, anchor="w", wraplength=300,
                             justify="left").grid(row=r, column=c, sticky="nsew", padx=1, pady=1, ipadx=8, ipady=6)
