"""Light-theme colours and fonts shared by every screen."""

BG = "#FAF8F4"          # warm off-white window background
CARD = "#FFFFFF"
BORDER = "#E2E8F0"
TEXT = "#1F2A37"
MUTED = "#5B6675"

BLUE_D, BLUE_L = "#2F80ED", "#D6E8FF"
TEAL_D, TEAL_L = "#0F9488", "#D3F1EC"
LAV_D, LAV_L = "#7C5CD6", "#E8E2FA"
GREEN_D, GREEN_L = "#2E9E5B", "#DDF3E4"
CORAL_D, CORAL_L = "#E5533D", "#FFDDD6"
AMBER_D, AMBER_L = "#B7791F", "#FFF1CC"

RESIDENT_FILL, RESIDENT_LINE = "#F1F6FD", "#B8CCE6"
EMPTY_FILL = "#F5F7FA"

ALGO_COLORS = {            # accent, light tint
    "FIFO": (TEAL_D, TEAL_L),
    "LRU": (LAV_D, LAV_L),
    "Optimal": (BLUE_D, BLUE_L),
}
ALGO_TAGLINE = {
    "FIFO": "First In, First Out",
    "LRU": "Least Recently Used",
    "Optimal": "Farthest Future Use",
}

FONT = "Segoe UI"
MONO = "Consolas"


def font(size=13, weight="normal"):
    return (FONT, size, weight)
