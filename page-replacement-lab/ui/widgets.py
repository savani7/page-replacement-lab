"""Small drawing / widget helpers."""
import customtkinter as ctk

from . import styles as S


def round_rect(canvas, x1, y1, x2, y2, r=12, **kw):
    """Rounded rectangle on a tk.Canvas (smoothed polygon trick)."""
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def big_button(master, text, command, color=S.BLUE_D, hover=None, width=200, height=46, **kw):
    return ctk.CTkButton(master, text=text, command=command, width=width, height=height,
                         corner_radius=14, fg_color=color, hover_color=hover or color,
                         text_color="white", font=S.font(15, "bold"), **kw)


def soft_button(master, text, command, width=120, height=40, **kw):
    return ctk.CTkButton(master, text=text, command=command, width=width, height=height,
                         corner_radius=12, fg_color=S.BLUE_L, hover_color="#BFD9FA",
                         text_color=S.TEXT, text_color_disabled="#9AA5B1",
                         font=S.font(13, "bold"), **kw)


def card(master, **kw):
    kw.setdefault("fg_color", S.CARD)
    kw.setdefault("corner_radius", 20)
    kw.setdefault("border_width", 1)
    kw.setdefault("border_color", S.BORDER)
    return ctk.CTkFrame(master, **kw)


def home_bar(master, app, title):
    bar = ctk.CTkFrame(master, fg_color="transparent")
    soft_button(bar, "←  Home", lambda: app.show("dashboard"), width=110).pack(side="left")
    ctk.CTkLabel(bar, text=title, font=S.font(24, "bold"), text_color=S.TEXT).pack(side="left", padx=18)
    return bar
