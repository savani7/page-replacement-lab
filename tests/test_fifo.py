from algorithms.simulator_engine import simulate

SPEC = [1, 2, 3, 1, 4, 2, 5]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def run(refs, frames):
    return simulate("FIFO", refs, frames)


def test_spec_example_fault_count():
    # Hand trace: 1F 2F 3F 1H 4F(evict 1) 2H 5F(evict 2) -> 5 faults, 2 hits.
    # (The project brief said 6, but Page 2 is still resident when it is requested.)
    r = run(SPEC, 3)
    assert r.faults == 5
    assert r.hits == 2
    assert r.fault_rate == 5 / 7 * 100


def test_victims_follow_arrival_order():
    r = run(SPEC, 3)
    assert r.steps[4].victim == 1
    assert r.steps[6].victim == 2
    assert r.final_frames == [4, 5, 3]


def test_hit_does_not_change_arrival_order():
    # Page 1 is hit at reference 4, but FIFO must still evict it first.
    r = run([1, 2, 3, 1, 4], 3)
    assert r.steps[3].hit
    assert r.steps[4].victim == 1


def test_reason_names_the_actual_victim():
    r = run(SPEC, 3)
    assert r.steps[4].reason == (
        "FIFO removes Page 1 because it entered RAM before the other resident pages."
    )


def test_repeated_references_are_hits():
    r = run([1, 1, 1, 1], 2)
    assert (r.faults, r.hits) == (1, 3)


def test_empty_frames_filled_before_any_eviction():
    r = run([1, 2, 3], 3)
    assert [s.victim for s in r.steps] == [None, None, None]
    assert r.steps[0].frames_before == [None, None, None]
    assert [s.slot for s in r.steps] == [0, 1, 2]


def test_full_memory_evicts():
    r = run([1, 2, 3, 4], 3)
    assert r.steps[3].victim == 1 and r.steps[3].slot == 0


def test_single_frame():
    r = run([1, 2, 1, 2], 1)
    assert r.faults == 4 and r.hits == 0


def test_more_frames_than_pages():
    r = run([1, 2, 3, 1, 2, 3], 5)
    assert r.faults == 3 and r.hits == 3
    assert r.final_frames == [1, 2, 3, None, None]


def test_different_frame_counts_belady():
    assert run(BELADY, 3).faults == 9
    assert run(BELADY, 4).faults == 10  # Belady's anomaly


def test_classic_string():
    refs = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    assert run(refs, 3).faults == 15
