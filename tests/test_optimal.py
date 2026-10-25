from algorithms.simulator_engine import simulate

SPEC = [1, 2, 3, 1, 4, 2, 5]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def run(refs, frames):
    return simulate("Optimal", refs, frames)


def test_spec_example_fault_count():
    r = run(SPEC, 3)
    assert r.faults == 5
    assert r.hits == 2


def test_never_used_again_is_chosen_and_ties_are_deterministic():
    step = run(SPEC, 3).steps[4]
    # Pages 1 and 3 are never used again; the lowest-numbered frame (Page 1) wins.
    assert step.victim == 1
    assert "never used again" in step.reason
    assert any(d.startswith("Remaining references: 2, 5") for d in step.details)


def test_farthest_next_use_is_chosen():
    step = run([1, 2, 3, 4, 1, 2, 3], 3).steps[3]
    assert step.victim == 3
    assert "next use (reference 7)" in step.reason
    assert "farther in the future" in step.reason


def test_note_explains_theoretical_benchmark():
    step = run(SPEC, 3).steps[4]
    assert "theoretical benchmark" in step.note


def test_repeated_references():
    assert run([2, 2, 2, 2], 3).faults == 1


def test_single_frame():
    assert run([1, 2, 3, 1], 1).faults == 4


def test_more_frames_than_pages():
    assert run([1, 2, 3, 1, 2, 3], 4).faults == 3


def test_different_frame_counts():
    assert run(BELADY, 3).faults == 7
    assert run(BELADY, 4).faults == 6


def test_classic_string():
    refs = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    assert run(refs, 3).faults == 9


def test_optimal_never_worse_than_others():
    import random
    rnd = random.Random(7)
    for _ in range(50):
        refs = [rnd.randint(0, 6) for _ in range(rnd.randint(1, 30))]
        frames = rnd.randint(1, 5)
        opt = run(refs, frames).faults
        assert opt <= simulate("FIFO", refs, frames).faults
        assert opt <= simulate("LRU", refs, frames).faults
