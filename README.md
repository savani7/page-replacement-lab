# Page Replacement Lab

An interactive desktop app that shows how an operating system maps **process pages** to
**main-memory frames** and how **FIFO**, **LRU** and **Optimal** decide which page to evict
when memory is full. Built with Python + CustomTkinter. Works offline, no paid services.

* **Interactive Simulator** - pick one algorithm, press *Start*, and watch every reference
  play automatically: request, hit/fault check, victim selection, eviction, loading.
* **Algorithm Comparison Arena** - choose FIFO vs LRU, FIFO vs Optimal, LRU vs Optimal, or
  all three. Selected algorithms run side by side on the same input, in sync, followed by a
  summary table, bar chart and plain-English explanation.

---

## 1. Setup on Windows (beginner friendly)

1. **Install Python 3.10 or newer** from <https://www.python.org/downloads/>.
   In the installer, tick **"Add python.exe to PATH"**, and keep **"tcl/tk and IDLE"**
   ticked (tkinter is needed for the GUI).
2. **Install VS Code** from <https://code.visualstudio.com/> and add the **Python**
   extension (Extensions icon on the left -> search "Python" -> Install).
3. **Open the project**: unzip `page-replacement-lab.zip`, then in VS Code choose
   *File -> Open Folder...* and select the `page-replacement-lab` folder.
4. **Open a terminal** in VS Code: *Terminal -> New Terminal*, then run:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The dashboard opens. If PowerShell refuses to run `activate`, either use the
*Command Prompt* terminal profile, or run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.

If VS Code asks which interpreter to use, pick the one inside `.venv`
(*Ctrl+Shift+P -> Python: Select Interpreter*). You can then also press the
**Run** button on `main.py`.

### Run the automated tests

```
python -m pytest
```

---

## 2. How to use it

1. On the dashboard choose **Interactive Simulator** or **Algorithm Comparison Arena**.
2. Type a **page reference string** (whole numbers 0-99, separated by commas or spaces,
   up to 100 references) and the **number of frames** (1-8). Press **Fill Example** to
   load a sample (press it again for a second sample).
3. Press **Start**. Playback is automatic. Use **Pause / Resume / Restart**, the **Speed**
   slider, or tick **Manual step mode** and press **Next Step**.
4. Invalid input (empty, letters, negatives, too large, too long, bad frame count) shows a
   plain-English message and never crashes the app.

### What you see on screen

| Area | Meaning |
|---|---|
| **Process page references** (top row) | Every reference as a box. Current = dark green "NOW", processed = muted with HIT/FAULT tag, upcoming = cream. The row scrolls to keep the current page visible. |
| **PAGE REQUEST box** (left of RAM) | The page being requested, with an arrow to the frame it uses. |
| **MAIN MEMORY - RAM** (large frame boxes) | One box per frame: frame number, resident page, and a text tag: EMPTY, OCCUPIED, HIT, VICTIM, EVICTED, LOADED. |
| **Flow bar** (simulator) | PROCESS PAGES -> PAGE REQUEST -> OS DECISION -> MAIN MEMORY, highlighting the current stage. |
| **Explanation card** | What is happening and *why*, using the algorithm's real victim and real numbers. |
| **Statistic cards** | Reference position, current page, hits, faults, fault rate, frames used. |

A page fault with a full RAM plays as: **PAGE FAULT -> SELECT VICTIM -> EVICTED -> LOADED -> result**.

Colors: green = hit / loaded, terracotta = fault / victim, mint = incoming page,
forest green = main buttons. Text labels (HIT, PAGE FAULT, EVICTED, LOADED) are always shown,
so meaning never depends on color alone.

---

## 3. The algorithms

* **FIFO** - evicts the page that entered RAM earliest. A hit does *not* change arrival order.
* **LRU** - evicts the page whose most recent use is oldest. Every hit refreshes the page.
* **Optimal** - evicts the page whose next use is farthest in the future; a page never used
  again is the best candidate. Ties are broken deterministically (lowest-numbered frame).
  It needs future knowledge, so it is a **theoretical benchmark**, not a real-world policy.

Formula used everywhere: `fault rate = faults / references processed x 100`
(0 before the first reference, so no division by zero).

### Worked example: `1, 2, 3, 1, 4, 2, 5` with 3 frames

| Algorithm | Page faults | Hits |
|---|---:|---:|
| FIFO | 5 | 2 |
| LRU | 6 | 1 |
| Optimal | 5 | 2 |

FIFO has 5 faults here, not 6: when Page 4 arrives FIFO evicts Page 1, leaving 4, 2, 3 in RAM,
so the next request for Page 2 is a hit. This is a good example that LRU is not always ahead of
FIFO - it depends on the reference string. A longer sample (`Fill Example`) with 3 frames gives
FIFO 15, LRU 12, Optimal 9 faults.

---

## 4. Project structure

```
page-replacement-lab/
├── main.py                      app window + screen switching
├── requirements.txt
├── pytest.ini
├── algorithms/                  no UI code in here
│   ├── base.py                  policy interface + Decision
│   ├── fifo.py  lru.py  optimal.py
│   └── simulator_engine.py      validation, simulate(), animation phases, summaries
├── ui/
│   ├── styles.py                sage + cream palette, fonts (Aptos/Inter/Segoe UI fallback)
│   ├── widgets.py               page strip, RAM canvas, stat cards, badges, buttons
│   ├── panel.py                 one algorithm's complete live view
│   ├── playback.py              after()-based play/pause/resume/restart controller
│   ├── dashboard.py  simulator.py  comparison_arena.py
└── tests/
    ├── test_fifo.py  test_lru.py  test_optimal.py
    ├── test_engine.py           validation, phases, comparison selection and summaries
    └── test_playback.py         pause, resume, restart, manual mode, synchronization
```

Animation uses `after()` only (never `time.sleep()`), and every pending callback is cancelled
on Restart, on changing the algorithm or comparison selection, and when leaving a screen.

## 5. Limits

Up to 100 references, pages 0-99, 1-8 frames, input under 600 characters.
