"""Page Replacement Lab - entry point.  Run with:  python main.py"""
import customtkinter as ctk

from ui import styles as S
from ui.comparison_arena import ComparisonScreen
from ui.dashboard import DashboardScreen
from ui.simulator import SimulatorScreen


class App(ctk.CTk):
    SCREENS = {
        "dashboard": DashboardScreen,
        "simulator": SimulatorScreen,
        "comparison": ComparisonScreen,
    }

    def __init__(self):
        ctk.set_appearance_mode("light")      # light theme only (no dark mode)
        super().__init__()
        S.init_fonts(self)
        self.title("Page Replacement Lab")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=S.SAGE)
        self.container = ctk.CTkFrame(self, fg_color=S.SAGE)
        self.container.pack(fill="both", expand=True)
        self.screens = {}
        self.current = None
        self.show_screen("dashboard")
        self.protocol("WM_DELETE_WINDOW", self._close)
        try:
            self.after(50, lambda: self.state("zoomed"))   # maximize on Windows
        except Exception:
            pass

    def show_screen(self, name):
        if self.current is not None:
            self.current.on_hide()        # cancels pending after() callbacks
            self.current.pack_forget()
        if name not in self.screens:
            self.screens[name] = self.SCREENS[name](self.container, self)
        self.current = self.screens[name]
        self.current.pack(fill="both", expand=True)
        self.current.on_show()

    def _close(self):
        if self.current is not None:
            self.current.on_hide()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
