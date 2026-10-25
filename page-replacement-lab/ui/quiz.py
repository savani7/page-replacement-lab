"""Quiz (answers are hidden until the student answers) and Viva Q&A."""
import random

import customtkinter as ctk

from . import styles as S
from .quiz_data import build_questions, VIVA
from .widgets import big_button, soft_button, card, home_bar

QUIZ_LENGTH = 10


class QuizScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=S.BG)
        home_bar(self, app, "Quiz & Viva").pack(fill="x", padx=24, pady=(16, 8))
        self.mode = ctk.StringVar(value="Quiz")
        ctk.CTkSegmentedButton(self, values=["Quiz", "Viva Q&A"], variable=self.mode, command=self._switch,
                               height=40, font=S.font(14, "bold"), selected_color=S.BLUE_D,
                               selected_hover_color=S.BLUE_D, unselected_color=S.BLUE_L,
                               unselected_hover_color="#BFD9FA", text_color=S.TEXT).pack(pady=(0, 10))
        self.area = ctk.CTkFrame(self, fg_color="transparent")
        self.area.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        self._switch("Quiz")

    def on_leave(self):
        pass

    def _clear(self):
        for w in self.area.winfo_children():
            w.destroy()

    def _switch(self, which):
        self._clear()
        if which == "Quiz":
            self._new_quiz()
        else:
            self._viva()

    # ------------------------------------------------------------ quiz
    def _new_quiz(self):
        pool = build_questions()
        random.shuffle(pool)
        self.questions = pool[:QUIZ_LENGTH]
        self.qi = 0
        self.score = 0
        self.answered = False
        self._show_question()

    def _show_question(self):
        self._clear()
        q = self.questions[self.qi]
        self.answered = False
        c = card(self.area)
        c.pack(fill="both", expand=True)
        ctk.CTkLabel(c, text=f"Question {self.qi + 1} of {len(self.questions)}      Score: {self.score}",
                     font=S.font(14, "bold"), text_color=S.MUTED).pack(anchor="w", padx=24, pady=(18, 4))
        ctk.CTkLabel(c, text=q["question"], font=S.font(20, "bold"), text_color=S.TEXT, wraplength=1000,
                     justify="left").pack(anchor="w", padx=24, pady=(4, 14))
        options = [q["correct"]] + list(q["wrong"])
        random.shuffle(options)
        self.opt_buttons = {}
        for text in options:
            b = ctk.CTkButton(c, text=text, height=48, corner_radius=14, anchor="w", font=S.font(15),
                              fg_color=S.BLUE_L, hover_color="#BFD9FA", text_color=S.TEXT,
                              text_color_disabled=S.TEXT, command=lambda t=text: self._answer(t))
            b.pack(fill="x", padx=24, pady=5)
            self.opt_buttons[text] = b
        self.feedback = ctk.CTkLabel(c, text="", font=S.font(15), text_color=S.TEXT, wraplength=1000,
                                     justify="left")
        self.feedback.pack(anchor="w", padx=24, pady=(14, 6))
        self.next_btn = big_button(c, "Next ▶", self._next, color=S.BLUE_D, width=160)
        # shown only after answering, so nothing is revealed early

    def _answer(self, chosen):
        if self.answered:
            return
        self.answered = True
        q = self.questions[self.qi]
        right = chosen == q["correct"]
        if right:
            self.score += 1
        for text, b in self.opt_buttons.items():
            b.configure(state="disabled")
            if text == q["correct"]:
                b.configure(fg_color=S.GREEN_L, border_width=3, border_color=S.GREEN_D)
            elif text == chosen:
                b.configure(fg_color=S.CORAL_L, border_width=3, border_color=S.CORAL_D)
        self.feedback.configure(
            text=("✅ Correct!  " if right else f"❌ Not quite. The correct answer is: {q['correct']}.  ")
            + q["explanation"],
            text_color=S.GREEN_D if right else S.CORAL_D)
        last = self.qi == len(self.questions) - 1
        self.next_btn.configure(text="See results" if last else "Next ▶")
        self.next_btn.pack(anchor="e", padx=24, pady=10)

    def _next(self):
        self.qi += 1
        if self.qi >= len(self.questions):
            self._results()
        else:
            self._show_question()

    def _results(self):
        self._clear()
        total = len(self.questions)
        pct = self.score / total * 100
        msg = ("Excellent - you are ready for the viva!" if pct >= 80 else
               "Good effort - review the Learn module and try again." if pct >= 50 else
               "Keep practising - read the Learn module, then retry.")
        c = card(self.area)
        c.pack(fill="both", expand=True)
        ctk.CTkLabel(c, text="Quiz complete", font=S.font(30, "bold"), text_color=S.TEXT).pack(pady=(50, 8))
        ctk.CTkLabel(c, text=f"{self.score} / {total}   ({pct:.0f}%)", font=S.font(40, "bold"),
                     text_color=S.GREEN_D if pct >= 50 else S.CORAL_D).pack(pady=8)
        ctk.CTkLabel(c, text=msg, font=S.font(17), text_color=S.MUTED).pack(pady=8)
        big_button(c, "↻  Retry with new questions", self._new_quiz, color=S.BLUE_D, width=300).pack(pady=24)

    # ------------------------------------------------------------ viva
    def _viva(self):
        self._clear()
        ctk.CTkLabel(self.area, text="Think of your own answer first, then click a question to reveal the model answer.",
                     font=S.font(14), text_color=S.MUTED).pack(anchor="w", padx=6, pady=(0, 6))
        scroll = ctk.CTkScrollableFrame(self.area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        for i, (q, a) in enumerate(VIVA, start=1):
            c = card(scroll)
            c.pack(fill="x", padx=6, pady=6)
            ans = ctk.CTkLabel(c, text=a, font=S.font(15), text_color=S.TEXT, wraplength=980, justify="left",
                               fg_color=S.GREEN_L, corner_radius=12)
            btn = ctk.CTkButton(c, text=f"Q{i}.  {q}", anchor="w", height=46, corner_radius=12,
                                fg_color=S.LAV_L, hover_color="#D7CCF5", text_color=S.TEXT,
                                font=S.font(15, "bold"))
            btn.configure(command=lambda a_=ans, b_=btn: self._toggle(a_, b_))
            btn.pack(fill="x", padx=12, pady=(12, 8))

    @staticmethod
    def _toggle(ans, btn):
        if ans.winfo_ismapped():
            ans.pack_forget()
        else:
            ans.pack(fill="x", padx=12, pady=(0, 12), ipadx=10, ipady=8)
