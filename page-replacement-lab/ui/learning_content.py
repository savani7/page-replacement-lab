"""Text for the Learn module.  Worked examples are produced by the real algorithms,
so every number printed here is guaranteed to match the simulator.

Block types: ("h", title) ("p", text) ("bullets", [..]) ("code", text) ("table", header, rows)
"""
from algorithms import ALGORITHMS, trace_text

EX = [1, 2, 3, 1, 4, 2, 5]          # short example you can follow by hand
EX_N = 3
CLASSIC = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def _t(algo, refs=EX, n=EX_N):
    return trace_text(ALGORITHMS[algo](refs, n))


def _f(algo, refs, n):
    return ALGORITHMS[algo](refs, n)[-1].faults


def basics():
    return [
        ("h", "1. Virtual memory"),
        ("p", "Virtual memory is a trick the operating system plays so that every program believes it has a large, "
              "private block of memory - even when the real RAM is small. Only the parts of a program that are "
              "needed right now are kept in RAM. The rest waits on disk and is brought in on demand."),
        ("h", "2. Pages and frames"),
        ("bullets", [
            "A PAGE is a fixed-size piece of a program's virtual memory (for example 4 KB).",
            "A FRAME is a fixed-size slot of physical RAM that can hold exactly one page.",
            "Because pages and frames have the same size, any page can be placed in any free frame.",
        ]),
        ("h", "3. What RAM does here"),
        ("p", "RAM is the fast working memory. In this lab RAM is a small row of frames (1 to 8). "
              "Each frame is either EMPTY or holds one page. The CPU can only use a page that is inside a frame."),
        ("h", "4. Page hit and page fault"),
        ("bullets", [
            "PAGE HIT: the requested page is already in a frame. The access is fast and nothing else happens.",
            "PAGE FAULT: the requested page is not in any frame. The OS must fetch it from disk, which is "
            "thousands of times slower than RAM.",
            "Page fault rate = page faults / total references.  Hits + faults = total references.",
        ]),
        ("h", "5. Why page replacement is necessary"),
        ("p", "RAM is smaller than the total memory programs want. Once every frame is occupied and a new page "
              "causes a fault, the OS has no free frame. It must pick one resident page (the VICTIM), remove it, "
              "and load the new page into that frame. Choosing a bad victim - one that will be needed again "
              "very soon - causes another fault almost immediately."),
        ("h", "6. What happens when RAM has no free frames"),
        ("code", "1. Page fault occurs for page P.\n"
                 "2. Look for an empty frame  -> none left.\n"
                 "3. Page replacement algorithm chooses a victim page V.\n"
                 "4. (Real OS) write V to disk if it was modified.\n"
                 "5. Load P into V's frame and update the tables.\n"
                 "6. Restart the instruction that faulted."),
        ("p", "The three algorithms in this lab differ only in step 3: how they choose the victim."),
        ("h", "7. Reading the reference string"),
        ("p", "A reference string is simply the order in which pages are requested, e.g. 1, 2, 3, 1, 4, 2, 5. "
              "The simulator walks through it one reference at a time; the number of frames is the size of RAM."),
    ]


def fifo():
    return [
        ("h", "Definition"),
        ("p", "FIFO (First In, First Out) replaces the page that has been in RAM the longest - the one that "
              "ARRIVED earliest among the pages currently in memory. Think of a queue: the page at the front "
              "leaves first."),
        ("h", "How it works"),
        ("bullets", [
            "Keep the arrival order of resident pages.",
            "Hit: do nothing. A hit NEVER changes the arrival order.",
            "Fault with a free frame: load the page; it joins the back of the queue.",
            "Fault with no free frame: remove the page at the front of the queue, load the new page at the back.",
        ]),
        ("h", f"Worked example: {', '.join(map(str, EX))} with {EX_N} frames"),
        ("code", _t("FIFO")),
        ("p", "Follow reference 5 (page 4): RAM is full with 1, 2, 3 and page 1 arrived first, so page 1 leaves. "
              "Reference 6 (page 2) is a HIT because page 2 is still resident. Reference 7 (page 5): the oldest "
              "resident page is now 2 (arrived second), so 2 leaves - even though it was just used."),
        ("h", "Advantages"),
        ("bullets", ["Very simple to understand and implement.", "Almost no overhead - just a queue.",
                     "Needs no information about how often or recently pages are used."]),
        ("h", "Limitations"),
        ("bullets", [
            "It ignores usage: a heavily used page can be evicted just because it is old.",
            f"Belady's anomaly: with FIFO, MORE frames can cause MORE faults. On 1,2,3,4,1,2,5,1,2,3,4,5 "
            f"FIFO gives {_f('FIFO', BELADY, 3)} faults with 3 frames but {_f('FIFO', BELADY, 4)} faults with 4 frames.",
        ]),
        ("h", "Common mistakes"),
        ("bullets", [
            "Moving a page to the back of the queue on a hit (that is closer to LRU, not FIFO).",
            "Removing the page with the smallest number instead of the one that arrived first.",
            "Counting a hit as a fault, or forgetting that filling empty frames also counts as faults.",
        ]),
    ]


def lru():
    return [
        ("h", "Definition"),
        ("p", "LRU (Least Recently Used) replaces the page that has not been used for the longest time. "
              "It assumes the past predicts the future: a page used recently is likely to be used again soon."),
        ("h", "How it works"),
        ("bullets", [
            "Remember the time (reference number) of the last use of every resident page.",
            "Hit: update that page's last-used time - it becomes the most recently used.",
            "Fault with no free frame: remove the page with the OLDEST last-used time.",
        ]),
        ("h", f"Worked example: {', '.join(map(str, EX))} with {EX_N} frames"),
        ("code", _t("LRU")),
        ("p", "At reference 5 (page 4) the last-used times are page 1 = ref 4, page 2 = ref 2, page 3 = ref 3. "
              "Page 2 is the least recently used, so it leaves. But page 2 is requested again at reference 6, "
              "which causes another fault - LRU guesses well most of the time, not always."),
        ("h", "Advantages"),
        ("bullets", ["Usually close to Optimal on real programs because of locality of reference.",
                     "Never suffers from Belady's anomaly (it is a 'stack algorithm').",
                     "Does not need to know the future."]),
        ("h", "Limitations"),
        ("bullets", ["Needs extra hardware or software to track recency on every access (counters or a stack).",
                     "Can perform badly on patterns like a loop slightly bigger than RAM.",
                     f"It is not always better than FIFO: on {', '.join(map(str, EX))} with 3 frames LRU has "
                     f"{_f('LRU', EX, 3)} faults and FIFO has {_f('FIFO', EX, 3)}."]),
        ("h", "Common mistakes"),
        ("bullets", ["Confusing LRU with FIFO: LRU looks at last USE, FIFO looks at ARRIVAL.",
                     "Forgetting to update the last-used time on a hit.",
                     "Choosing the page used least OFTEN (that is LFU, a different algorithm)."]),
    ]


def optimal():
    return [
        ("h", "Definition"),
        ("p", "Optimal (also called Belady's MIN or OPT) replaces the resident page whose next use is farthest "
              "in the future - or that is never used again. It produces the fewest possible page faults."),
        ("h", "How it works"),
        ("bullets", [
            "For each resident page, look ahead in the remaining reference string for its next use.",
            "A page that never appears again is the best victim.",
            "If several pages are never used again this lab breaks the tie by choosing the lowest-numbered frame.",
            "Otherwise remove the page whose next use is latest.",
        ]),
        ("h", f"Worked example: {', '.join(map(str, EX))} with {EX_N} frames"),
        ("code", _t("Optimal")),
        ("p", "At reference 5 (page 4) the remaining references are 2, 5. Page 1 and page 3 are never used "
              "again (a tie); page 2 is needed next. Optimal keeps page 2 and removes page 1 (lowest frame)."),
        ("h", "Advantages"),
        ("bullets", ["Lowest possible number of page faults for any reference string and frame count.",
                     "Perfect yardstick for judging other algorithms.", "No Belady's anomaly."]),
        ("h", "Limitations"),
        ("bullets", ["It needs to know the FUTURE references, which a real operating system cannot know.",
                     "Therefore it cannot be used as a real page replacement policy."]),
        ("h", "Why it is a theoretical benchmark"),
        ("p", "Because it uses future knowledge, Optimal is only used offline - in simulators like this one - "
              "to measure how close practical algorithms such as LRU come to the best possible result. "
              "If an algorithm's faults are near Optimal's, it is doing very well."),
    ]


def comparison():
    rows = [
        ["Victim chosen by", "Earliest ARRIVAL", "Oldest LAST USE", "Farthest NEXT USE"],
        ["Looks at", "Past (arrival time)", "Past (recent use)", "Future"],
        ["Hit changes state?", "No", "Yes (recency updated)", "No (look-ahead only)"],
        ["Implementable in a real OS?", "Yes, very easy", "Yes, with extra cost", "No - needs the future"],
        ["Belady's anomaly?", "Can occur", "Never", "Never"],
        ["Typical quality", "Fair", "Good", "Best possible"],
    ]
    c = CLASSIC
    return [
        ("h", "Side-by-side comparison"),
        ("table", ["", "FIFO", "LRU", "Optimal"], rows),
        ("h", "Same input, three results"),
        ("table", ["Reference string / frames", "FIFO", "LRU", "Optimal"], [
            [f"{', '.join(map(str, EX))}  /  3", str(_f("FIFO", EX, 3)), str(_f("LRU", EX, 3)), str(_f("Optimal", EX, 3))],
            [f"{', '.join(map(str, c))}  /  3", str(_f("FIFO", c, 3)), str(_f("LRU", c, 3)), str(_f("Optimal", c, 3))],
            [f"{', '.join(map(str, BELADY))}  /  3", str(_f("FIFO", BELADY, 3)), str(_f("LRU", BELADY, 3)), str(_f("Optimal", BELADY, 3))],
            [f"{', '.join(map(str, BELADY))}  /  4", str(_f("FIFO", BELADY, 4)), str(_f("LRU", BELADY, 4)), str(_f("Optimal", BELADY, 4))],
        ]),
        ("p", "Numbers in the table are page faults (lower is better). Notice that neither FIFO nor LRU wins "
              "everywhere: on the first row FIFO is better than LRU, on others LRU is better. Optimal is never "
              "beaten. The winner depends on the reference string and on the number of frames."),
        ("h", "Try it by hand (viva practice)"),
        ("p", f"Take {', '.join(map(str, c))} with 3 frames and work out each algorithm on paper. Then check "
              f"yourself in the Interactive Simulator. Full FIFO trace for reference:"),
        ("code", _t("FIFO", c, 3)),
        ("p", "Exam tips: always draw one column per reference; mark hits and faults; count faults only at the "
              "end; and remember that filling an empty frame is still a page fault."),
    ]


TABS = [("Basics", basics), ("FIFO", fifo), ("LRU", lru), ("Optimal", optimal), ("Comparison", comparison)]
