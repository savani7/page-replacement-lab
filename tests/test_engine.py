import pytest

from algorithms.simulator_engine import (
    ALGORITHM_ORDER, EXAMPLES, InputError, build_phases, compare_summary,
    fault_rate, parse_reference_string, result_summary, simulate,
    validate_comparison_selection, validate_frames, validate_inputs,
)

SPEC = [1, 2, 3, 1, 4, 2, 5]


# ------------------------------------------------------------------ input validation
def test_parse_valid_formats():
    assert parse_reference_string("1, 2, 3, 1, 4, 2, 5") == SPEC
    assert parse_reference_string("1 2 3") == [1, 2, 3]
    assert parse_reference_string(" 0,10 ,  99 ") == [0, 10, 99]


@pytest.mark.parametrize("bad", ["", "   ", None, ",,,", "a, b", "1, x, 3", "1.5", "1;2",
                                 "-1, 2", "100", "1, 2, 3!", "²"])
def test_parse_rejects_bad_input(bad):
    with pytest.raises(InputError):
        parse_reference_string(bad)


def test_parse_rejects_too_many_and_too_long():
    with pytest.raises(InputError):
        parse_reference_string(",".join(["1"] * 101))
    with pytest.raises(InputError):
        parse_reference_string("1," * 400)
    assert len(parse_reference_string(",".join(["1"] * 100))) == 100


def test_error_messages_are_friendly():
    with pytest.raises(InputError, match="negative"):
        parse_reference_string("1, -4")
    with pytest.raises(InputError, match="not a valid page number"):
        parse_reference_string("1, two")
    with pytest.raises(InputError, match="empty"):
        parse_reference_string("")


@pytest.mark.parametrize("bad", ["", "0", "9", "-1", "abc", "2.5", None, True])
def test_validate_frames_rejects(bad):
    with pytest.raises(InputError):
        validate_frames(bad)


@pytest.mark.parametrize("good,expected", [("1", 1), (" 8 ", 8), (3, 3)])
def test_validate_frames_accepts(good, expected):
    assert validate_frames(good) == expected


def test_examples_are_valid():
    for text, frames in EXAMPLES:
        refs, n = validate_inputs(text, frames)
        assert refs and 1 <= n <= 8


# ------------------------------------------------------------------------ simulation
def test_spec_example_all_three():
    assert simulate("FIFO", SPEC, 3).faults == 5
    assert simulate("LRU", SPEC, 3).faults == 6
    assert simulate("Optimal", SPEC, 3).faults == 5


def test_victims_differ_between_algorithms():
    victims = {a: simulate(a, SPEC, 3).steps[4].victim for a in ALGORITHM_ORDER}
    assert victims["FIFO"] == 1 and victims["LRU"] == 2 and victims["Optimal"] == 1


def test_stats_and_division_by_zero():
    assert fault_rate(0, 0) == 0.0
    r = simulate("FIFO", SPEC, 3)
    assert r.steps[0].fault_rate == 100.0
    assert r.steps[-1].hits + r.steps[-1].faults == len(SPEC)


def test_unknown_algorithm_and_bad_frames():
    with pytest.raises(InputError):
        simulate("MRU", SPEC, 3)
    with pytest.raises(InputError):
        simulate("FIFO", SPEC, 0)


def test_every_algorithm_finishes_every_frame_count():
    for algo in ALGORITHM_ORDER:
        for frames in range(1, 9):
            r = simulate(algo, SPEC * 3, frames)
            assert len(r.steps) == 21 and r.hits + r.faults == 21


def test_phase_counts_and_kinds():
    r = simulate("LRU", SPEC, 3)
    assert [p.kind for p in r.phases[3]] == ["request", "hit"]
    assert [p.kind for p in r.phases[0]] == ["request", "fault", "load", "done"]
    assert [p.kind for p in r.phases[4]] == [
        "request", "fault", "select", "evict", "load", "done"]
    assert "EVICTED" in r.phases[4][3].text and "LOADED" in r.phases[4][4].text
    assert r.phases[4][2].text.startswith("LRU removes Page 2")


# ---------------------------------------------------------------- comparison logic
@pytest.mark.parametrize("pair", [("FIFO", "LRU"), ("FIFO", "Optimal"), ("LRU", "Optimal")])
def test_two_algorithm_selection(pair):
    assert validate_comparison_selection(pair) == list(pair)
    assert validate_comparison_selection(reversed(pair)) == list(pair)  # canonical order


def test_three_algorithm_selection():
    assert validate_comparison_selection(["Optimal", "LRU", "FIFO"]) == ["FIFO", "LRU", "Optimal"]


def test_selection_needs_two():
    for bad in ([], ["FIFO"], ["FIFO", "FIFO"]):
        with pytest.raises(InputError, match="at least two"):
            validate_comparison_selection(bad)
    with pytest.raises(InputError):
        validate_comparison_selection(["FIFO", "MRU"])


def test_switching_selections_in_sequence():
    seq = [["FIFO", "LRU"], ["FIFO", "LRU", "Optimal"], ["LRU", "Optimal"], ["FIFO", "Optimal"]]
    for names in seq:
        assert validate_comparison_selection(names) == names


def test_compare_summary_only_selected_algorithms():
    res = {a: simulate(a, SPEC, 3) for a in ("FIFO", "LRU")}
    best, text = compare_summary(res)
    assert best == ["FIFO"]
    assert "FIFO had the fewest page faults (5)" in text
    assert "Optimal" not in text
    assert "no practical algorithm is best for every" in text


def test_compare_summary_tie_and_all_equal():
    res = {a: simulate(a, SPEC, 3) for a in ALGORITHM_ORDER}
    best, text = compare_summary(res)
    assert best == ["FIFO", "Optimal"] and "tied" in text
    res = {a: simulate(a, [1, 1, 1], 2) for a in ALGORITHM_ORDER}
    best, text = compare_summary(res)
    assert best == list(ALGORITHM_ORDER) and "same number" in text


def test_result_summary_uses_real_numbers():
    r = simulate("LRU", SPEC, 3)
    s = result_summary(r)
    assert "6 page faults" in s and "1 hits" in s and "85.7%" in s
