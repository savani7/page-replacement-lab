"""Quiz + viva questions.  Calculation questions are computed with the real algorithms."""
from algorithms import ALGORITHMS

STATIC = [
    ("What is a page fault?",
     "The requested page is not currently in a RAM frame",
     ["The CPU overheats while running a program", "A page in RAM is corrupted", "The program finishes executing"],
     "A page fault happens when the CPU needs a page that is not in any frame, so the OS must load it from disk."),
    ("When does a page HIT occur?",
     "The requested page is already in RAM",
     ["The page must be loaded from disk", "A victim page is removed", "All frames are empty"],
     "A hit means the page is resident - no loading and no replacement are needed."),
    ("What is a frame?",
     "A fixed-size slot of physical RAM that holds one page",
     ["A fixed-size piece of a program's virtual memory", "A block of disk space", "A list of page numbers"],
     "Pages live in virtual memory; frames are the RAM slots that hold them."),
    ("FIFO replaces which page?",
     "The page that has been in RAM the longest",
     ["The page used least recently", "The page used least often", "The page needed farthest in the future"],
     "FIFO looks only at arrival order among the resident pages."),
    ("LRU replaces which page?",
     "The page that was used longest ago",
     ["The page that arrived first", "The page with the smallest number", "The page needed farthest in the future"],
     "LRU compares last-use times - a hit updates a page's last-use time."),
    ("Optimal replaces which page?",
     "The page whose next use is farthest in the future (or never)",
     ["The page used longest ago", "The page that arrived first", "A random resident page"],
     "Optimal looks ahead in the remaining references."),
    ("Why is Optimal not used in real operating systems?",
     "It needs to know future page references",
     ["It produces too many page faults", "It needs too much disk space", "It only works with one frame"],
     "Real systems cannot see the future, so Optimal is only a benchmark."),
    ("Which algorithm can show Belady's anomaly (more frames -> more faults)?",
     "FIFO",
     ["LRU", "Optimal", "All three equally"],
     "FIFO can; LRU and Optimal are stack algorithms and cannot."),
    ("In FIFO, what happens to a page's position in the arrival order when it is HIT?",
     "Nothing - the order does not change",
     ["It moves to the back of the queue", "It moves to the front of the queue", "It is removed"],
     "Moving a hit page to the back would be LRU-like behaviour."),
    ("How is the page fault rate calculated?",
     "Page faults divided by total references",
     ["Page hits divided by page faults", "Frames divided by pages", "Page faults divided by frames"],
     "Fault rate = faults / total references; hits + faults = total references."),
    ("Which algorithm always gives the fewest page faults for a given string and frame count?",
     "Optimal",
     ["FIFO", "LRU", "They are always equal"],
     "Optimal is the lower bound, which is why it is the benchmark."),
    ("If the number of frames is at least the number of DISTINCT pages, how many faults occur?",
     "Exactly one per distinct page",
     ["Zero", "One per reference", "It depends on the algorithm"],
     "Every distinct page faults once on its first use, then stays in RAM forever."),
    ("Is LRU always better than FIFO?",
     "No - it depends on the reference string",
     ["Yes, always", "Yes, but only with 3 frames", "No - FIFO is always better"],
     "On 1,2,3,1,4,2,5 with 3 frames FIFO has fewer faults than LRU."),
]

# (reference string, frames, algorithm)
CALC = [
    ([1, 2, 3, 1, 4, 2, 5], 3, "FIFO"),
    ([1, 2, 3, 1, 4, 2, 5], 3, "LRU"),
    ([1, 2, 3, 1, 4, 2, 5], 3, "Optimal"),
    ([1, 1, 2, 2, 3], 1, "FIFO"),
    ([7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2], 3, "LRU"),
]


def _numeric_options(correct, total):
    cands = [v for v in range(max(0, correct - 3), min(total, correct + 3) + 1) if v != correct]
    cands.sort(key=lambda v: (abs(v - correct), v))
    return [str(v) for v in cands[:3]]


def build_questions():
    """List of dicts: question, correct, wrong[list], explanation."""
    qs = [dict(question=q, correct=c, wrong=w, explanation=e) for q, c, w, e in STATIC]
    for refs, n, algo in CALC:
        steps = ALGORITHMS[algo](refs, n)
        faults = steps[-1].faults
        fault_refs = ", ".join(str(s.index + 1) for s in steps if not s.hit)
        qs.append(dict(
            question=f"Reference string {', '.join(map(str, refs))} with {n} frame(s). "
                     f"How many page faults does {algo} produce?",
            correct=str(faults), wrong=_numeric_options(faults, len(refs)),
            explanation=f"{algo} faults at references {fault_refs} - that is {faults} faults and "
                        f"{steps[-1].hits} hits out of {len(refs)} references."))
    return qs


VIVA = [
    ("What is virtual memory?",
     "A technique that lets programs use more memory than physically exists by keeping only the needed pages in RAM and the rest on disk."),
    ("Difference between a page and a frame?",
     "A page is a fixed-size block of virtual memory; a frame is a fixed-size block of physical RAM that holds one page."),
    ("What is a page fault and why is it expensive?",
     "It occurs when the needed page is not in RAM. The OS must read it from disk, which is thousands of times slower than RAM."),
    ("Why do we need page replacement?",
     "Because RAM is limited. When all frames are full and a new page is needed, one resident page must be removed."),
    ("Explain FIFO in one sentence.",
     "It removes the resident page that entered RAM earliest, ignoring how recently or often it was used."),
    ("Explain LRU in one sentence.",
     "It removes the resident page whose last use was the longest time ago, assuming recently used pages will be used again."),
    ("Explain Optimal in one sentence.",
     "It removes the resident page that will not be used for the longest time in the future, giving the minimum possible faults."),
    ("What is Belady's anomaly?",
     "A situation where giving a process MORE frames produces MORE page faults. It can happen with FIFO but never with LRU or Optimal."),
    ("Why is Optimal only a benchmark?",
     "It needs future knowledge of the reference string, which a real OS does not have."),
    ("Does a hit change anything in FIFO? In LRU?",
     "FIFO: no, the arrival order is untouched. LRU: yes, the page's last-used time is updated."),
    ("Is LRU always better than FIFO?",
     "No. It usually is on real programs because of locality, but for some reference strings FIFO has fewer faults."),
    ("How do you compute the page fault rate?",
     "Page faults divided by the total number of references (hits + faults)."),
]
