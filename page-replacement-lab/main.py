"""PAGE REPLACEMENT LAB - run with:  python main.py"""
import customtkinter as ctk

from ui import styles as S


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")          # light theme only
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=S.BG)
        self.title("Page Replacement Lab")
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{min(1420, sw - 30)}x{min(900, sh - 90)}+10+10")
        self.minsize(1100, 680)
        self.container = ctk.CTkFrame(self, fg_color=S.BG)
        self.container.pack(fill="both", expand=True)
        self.screens, self.current = {}, None
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.show("dashboard")

    def _make(self, name):
        # imported lazily so start-up is fast and light on memory
        if name == "dashboard":
            from ui.dashboard import DashboardScreen as cls
        elif name == "simulator":
            from ui.simulator import SimulatorScreen as cls
        elif name == "arena":
            from ui.battle_arena import BattleArenaScreen as cls
        elif name == "learning":
            from ui.learning_module import LearningScreen as cls
        elif name == "quiz":
            from ui.quiz import QuizScreen as cls
        else:
            raise KeyError(name)
        return cls(self.container, self)

    def show(self, name):
        if self.current:
            old = self.screens[self.current]
            old.on_leave()                  # cancels pending after() callbacks
            old.pack_forget()
        if name not in self.screens:
            self.screens[name] = self._make(name)
        self.current = name
        self.screens[name].pack(fill="both", expand=True)

    def close(self):
        for s in self.screens.values():
            try:
                s.on_leave()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
