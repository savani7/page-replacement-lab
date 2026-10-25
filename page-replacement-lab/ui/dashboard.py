"""Home screen with the three main options (+ quiz)."""
import customtkinter as ctk

from . import styles as S
from .widgets import big_button, soft_button


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.BG)
        self.app = app
        ctk.CTkLabel(self, text="PAGE REPLACEMENT LAB", font=S.font(42, "bold"),
                     text_color=S.TEXT).pack(pady=(46, 4))
        ctk.CTkLabel(self, text="Understand FIFO, LRU, and Optimal through interactive visual simulations.",
                     font=(S.FONT, 17, "italic"), text_color=S.MUTED).pack(pady=(0, 36))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(expand=True)
        options = [
            ("\U0001F4D8", "Learn Page Replacement",
             "Virtual memory, pages, frames and page faults - then FIFO, LRU and Optimal with worked examples.",
             S.TEAL_L, S.TEAL_D, "learning", "Start learning"),
            ("\U0001F3AC", "Interactive Simulator",
             "Pick an algorithm and press one button. Watch pages enter RAM and victims get replaced, automatically.",
             S.BLUE_L, S.BLUE_D, "simulator", "Open simulator"),
            ("⚔️", "Algorithm Battle Arena",
             "FIFO, LRU and Optimal run side by side on the same input so you can compare every decision.",
             S.LAV_L, S.LAV_D, "arena", "Enter the arena"),
        ]
        for c, (icon, title, desc, light, dark, target, btn) in enumerate(options):
            box = ctk.CTkFrame(row, fg_color=light, corner_radius=26, width=340, height=360)
            box.grid(row=0, column=c, padx=14)
            box.pack_propagate(False)
            ctk.CTkLabel(box, text=icon, font=(S.FONT, 52)).pack(pady=(30, 6))
            ctk.CTkLabel(box, text=title, font=S.font(21, "bold"), text_color=S.TEXT).pack(padx=16)
            ctk.CTkLabel(box, text=desc, font=S.font(14), text_color=S.TEXT, wraplength=290,
                         justify="center").pack(padx=20, pady=12)
            big_button(box, btn, lambda t=target: app.show(t), color=dark, width=230, height=48).pack(
                side="bottom", pady=26)

        extra = ctk.CTkFrame(self, fg_color="transparent")
        extra.pack(pady=(10, 40))
        soft_button(extra, "\U0001F4DD  Quiz & Viva practice", lambda: app.show("quiz"), width=260,
                    height=46).pack()

    def on_leave(self):
        pass
