import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REFS = [1, 2, 3, 1, 4, 2, 5]
FRAMES = 3


def states(steps):
    return [s.frames_after for s in steps]
