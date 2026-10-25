from algorithms.simulator_engine import simulate

SPEC = [1, 2, 3, 1, 4, 2, 5]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def run(refs, frames):
    return simulate("LRU", refs, frames)


def test_spec_example_fault_count():
    r = run(SPEC, 3)
    assert r.faults == 6
    assert r.hits == 1


def test_victims_are_least_recently_used():
    r = run(SPEC, 3)
    assert r.steps[4].victim == 2   # Page 1 was refreshed by the hit
    assert r.steps[5].victim == 3
    assert r.steps[6].victim == 1


def test_hit_refreshes_last_used():
    r = run([1, 2, 3, 1, 4], 3)
    assert r.steps[4].victim == 2   # FIFO would pick 1 here


def test_lru_differs_from_fifo():
    fifo = simulate("FIFO", SPEC, 3)
    lru = run(SPEC, 3)
    assert fifo.steps[4].victim != lru.steps[4].victim


def test_details_show_last_used_references():
    step = run(SPEC, 3).steps[4]
    assert "Page 2 - last used at reference 2" in step.details[0]
    assert "Page 3 - last used at reference 3" in step.details[1]
    assert "Page 1 - last used at reference 4" in step.details[2]
    assert step.reason == "LRU removes Page 2 because it was used least recently."


def test_repeated_references():
    r = run([4, 4, 4], 2)
    assert (r.faults, r.hits) == (1, 2)


def test_single_frame():
    assert run([1, 2, 1], 1).faults == 3


def test_more_frames_than_pages():
    r = run([1, 2, 1, 2], 6)
    assert r.faults == 2


def test_different_frame_counts():
    assert run(BELADY, 3).faults == 10
    assert run(BELADY, 4).faults == 8


def test_classic_string():
    refs = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    assert run(refs, 3).faults == 12
