"""Colors and fonts for the Sage Green + Cream theme."""
import tkinter.font as tkfont

import customtkinter as ctk

# --- required palette -------------------------------------------------------
SAGE = "#DDE8DF"        # main background
CREAM = "#F5F0E5"       # cards and panels
FOREST = "#356859"      # primary buttons
MINT = "#A8D5BA"        # secondary accent
TEXT = "#263B32"        # main text
HIT = "#398568"         # page hit
FAULT = "#D87560"       # page fault (terracotta)
VICTIM = "#F3D6C9"      # selected victim (pale terracotta)
INCOMING = "#D6E9E1"    # incoming page (soft mint)
BORDER = "#A8BBAE"      # borders

# --- supporting shades (derived from the palette) ---------------------------
FOREST_HOVER = "#2A5448"
FOREST_DARK = "#1F4034"
MINT_HOVER = "#93C7A9"
TEXT_MUTED = "#5C7267"
CARD_INNER = "#EAF1E6"      # light sage used for small cards inside cream panels
FRAME_FILL = "#FBF8F0"      # occupied RAM frame
FRAME_EMPTY = "#EDE8D8"     # empty RAM frame
RAM_BG = "#E6EEE2"          # RAM block background
PAST = "#E1E9DF"            # references already processed
DISABLED_BG = "#CBD8CE"
DISABLED_TEXT = "#7F9187"
WHITE = "#FFFFFF"

_FAMILY = "Segoe UI"
_CACHE = {}


def init_fonts(root) -> str:
    """Pick Aptos or Inter if installed, otherwise a sensible fallback."""
    global _FAMILY
    try:
        available = set(tkfont.families(root))
    except Exception:
        available = set()
    for name in ("Aptos", "Inter", "Segoe UI", "Helvetica Neue", "Calibri", "Arial"):
        if name in available:
            _FAMILY = name
            break
    else:
        _FAMILY = "TkDefaultFont"
    _CACHE.clear()
    return _FAMILY


def family() -> str:
    return _FAMILY


def font(size: int, weight: str = "normal") -> "ctk.CTkFont":
    """Font for customtkinter widgets (size in points)."""
    key = (size, weight)
    if key not in _CACHE:
        _CACHE[key] = ctk.CTkFont(family=_FAMILY, size=size, weight=weight)
    return _CACHE[key]


def canvas_font(px: float, weight: str = "normal"):
    """Font tuple for raw canvases. Negative size = pixels, so it scales with my geometry."""
    return (_FAMILY, -max(6, int(px)), weight)
