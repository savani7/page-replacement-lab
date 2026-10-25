from . import fifo, lru, optimal
from .base import (ValidationError, Step, parse_reference_string, parse_frame_count,
                   run_simulation, summarize, trace_text, MAX_FRAMES, MAX_REFERENCES)

ALGORITHMS = {
    "FIFO": fifo.simulate,
    "LRU": lru.simulate,
    "Optimal": optimal.simulate,
}
