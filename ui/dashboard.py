"""Home screen: PAGE REPLACEMENT LAB."""
import customtkinter as ctk

from . import styles as S
from .widgets import DiagramBanner, make_button, make_card


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.SAGE)
        self.app = app

        ctk.CTkLabel(self, text="PAGE REPLACEMENT LAB", font=S.font(44, "bold"),
                     text_color=S.FOREST).pack(pady=(34, 0))
        ctk.CTkLabel(self, text="Visualize how operating systems manage pages in main memory.",
                     font=S.font(18), text_color=S.TEXT).pack(pady=(4, 8))

        DiagramBanner(self).pack(fill="x", padx=40, pady=(4, 10))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="both", expand=True, padx=60, pady=(0, 10))
        cards.grid_columnconfigure((0, 1), weight=1, uniform="card")
        cards.grid_rowconfigure(0, weight=1)

        self._option(
            cards, 0, ">", "Interactive Simulator",
            "Run FIFO, LRU, or Optimal and watch the page reference sequence move through "
            "memory, one decision at a time.",
            "Open Simulator", lambda: app.show_screen("simulator"),
        )
        self._option(
            cards, 1, "=", "Algorithm Comparison Arena",
            "Compare two algorithms or all three side by side on the same reference string "
            "and number of frames.",
            "Open Arena", lambda: app.show_screen("comparison"),
        )

        ctk.CTkLabel(self, text="FIFO   -   LRU   -   Optimal", font=S.font(14, "bold"),
                     text_color=S.TEXT_MUTED).pack(pady=(0, 18))

    def _option(self, parent, column, icon, title, text, button_text, command):
        card = make_card(parent, corner_radius=22)
        card.grid(row=0, column=column, sticky="nsew", padx=14, pady=6)
        badge = ctk.CTkLabel(card, text=icon, width=64, height=64, corner_radius=32,
                             fg_color=S.FOREST, text_color=S.WHITE, font=S.font(28, "bold"))
        badge.pack(pady=(28, 10))
        ctk.CTkLabel(card, text=title, font=S.font(26, "bold"), text_color=S.TEXT).pack()
        ctk.CTkLabel(card, text=text, font=S.font(15), text_color=S.TEXT_MUTED, wraplength=400,
                     justify="center").pack(padx=28, pady=(10, 18))
        make_button(card, button_text, command, width=220, height=44).pack(pady=(0, 28))

    def on_show(self):
        pass

    def on_hide(self):
        pass
