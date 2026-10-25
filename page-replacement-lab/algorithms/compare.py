"""Run all three algorithms on the same input and explain the comparison."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from . import ALGORITHMS
from .base import Step, summarize


@dataclass
class Result:
    name: str
    faults: int
    hits: int
    fault_rate: float
    steps: List[Step]


def compare_all(refs: List[int], n_frames: int) -> Dict[str, Result]:
    out = {}
    for name, fn in ALGORITHMS.items():
        steps = fn(refs, n_frames)
        t = summarize(steps)
        out[name] = Result(name, t["faults"], t["hits"], t["fault_rate"], steps)
    return out


def best_algorithms(results: Dict[str, Result]) -> List[str]:
    fewest = min(r.faults for r in results.values())
    return [n for n, r in results.items() if r.faults == fewest]


def explain_comparison(results: Dict[str, Result]) -> str:
    f, l, o = results["FIFO"].faults, results["LRU"].faults, results["Optimal"].faults
    best = best_algorithms(results)
    parts = []
    if len(best) == 3:
        parts.append(f"All three algorithms tie with {f} page faults on this input.")
    else:
        parts.append(f"Fewest page faults: {' and '.join(best)} with {results[best[0]].faults}.")
    if f == l:
        parts.append(f"FIFO and LRU tie ({f} faults each) on this input.")
    elif f < l:
        parts.append(f"Here FIFO ({f}) beat LRU ({l}). That is perfectly possible: neither "
                     f"algorithm is better on every reference string.")
    else:
        parts.append(f"Here LRU ({l}) beat FIFO ({f}), because recently used pages were reused. "
                     f"On a different string the result could be reversed.")
    if o < min(f, l):
        parts.append(f"Optimal ({o}) is lowest, as expected: it looks into the future, "
                     f"so no real algorithm can do better.")
    elif o == min(f, l):
        parts.append(f"Optimal ({o}) is never worse than the others; here it ties with the best "
                     f"real algorithm.")
    parts.append("Remember: results depend on the reference string and the number of frames.")
    return " ".join(parts)
