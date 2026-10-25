import unittest

from tests.helpers import REFS, FRAMES
from algorithms import ValidationError, parse_reference_string, parse_frame_count
from algorithms.compare import compare_all, best_algorithms, explain_comparison


class TestValidation(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_reference_string("1, 2, 3, 1,4 2;5"), [1, 2, 3, 1, 4, 2, 5])
        self.assertEqual(parse_frame_count(" 3 "), 3)

    def test_empty(self):
        for bad in ["", "   ", None]:
            with self.assertRaises(ValidationError):
                parse_reference_string(bad)
        with self.assertRaises(ValidationError):
            parse_frame_count("")

    def test_invalid(self):
        for bad in ["1, a, 3", "1, -2", "1.5", "abc", "1, 100"]:
            with self.assertRaises(ValidationError, msg=bad):
                parse_reference_string(bad)
        for bad in ["0", "-1", "x", "2.5", "99"]:
            with self.assertRaises(ValidationError, msg=bad):
                parse_frame_count(bad)

    def test_too_long(self):
        with self.assertRaises(ValidationError):
            parse_reference_string(",".join(["1"] * 100))

    def test_friendly_message(self):
        try:
            parse_reference_string("1, x")
        except ValidationError as e:
            self.assertIn("'x'", str(e))


class TestCompare(unittest.TestCase):
    def test_results(self):
        r = compare_all(REFS, FRAMES)
        self.assertEqual((r["FIFO"].faults, r["LRU"].faults, r["Optimal"].faults), (5, 6, 5))
        self.assertEqual(r["FIFO"].hits + r["FIFO"].faults, len(REFS))
        self.assertAlmostEqual(r["LRU"].fault_rate, 6 / 7)

    def test_best_includes_ties(self):
        r = compare_all(REFS, FRAMES)
        self.assertEqual(sorted(best_algorithms(r)), ["FIFO", "Optimal"])

    def test_explanation_does_not_claim_fifo_always_worse(self):
        text = explain_comparison(compare_all(REFS, FRAMES))
        self.assertIn("FIFO (5) beat LRU (6)", text)
        self.assertNotIn("always worse", text)

    def test_explanation_when_lru_wins(self):
        text = explain_comparison(compare_all([1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5], 3))
        self.assertIn("LRU", text)


if __name__ == "__main__":
    unittest.main()
