import unittest

from tests.helpers import REFS, FRAMES, states
from algorithms import ALGORITHMS, ValidationError
from algorithms.fifo import simulate


class TestFIFO(unittest.TestCase):
    def test_reference_example_step_by_step(self):
        s = simulate(REFS, FRAMES)
        self.assertEqual(states(s), [
            [1, None, None], [1, 2, None], [1, 2, 3], [1, 2, 3],
            [4, 2, 3], [4, 2, 3], [4, 5, 3]])
        self.assertEqual([x.kind for x in s],
                         ["load", "load", "load", "hit", "replace", "hit", "replace"])
        self.assertEqual([x.victim for x in s], [None, None, None, None, 1, None, 2])
        self.assertEqual([x.hits for x in s], [0, 0, 0, 1, 1, 2, 2])
        self.assertEqual([x.faults for x in s], [1, 2, 3, 3, 4, 4, 5])

    def test_totals(self):
        # NOTE: the brief said 6, but working it by hand gives 5: page 2 is still
        # resident at reference 6 (FIFO evicted page 1, not page 2) -> a hit.
        s = simulate(REFS, FRAMES)
        self.assertEqual(s[-1].faults, 5)
        self.assertEqual(s[-1].hits, 2)

    def test_hit_does_not_change_arrival_order(self):
        s = simulate([1, 2, 1, 3, 4], 3)  # hit on 1 must NOT save it from eviction
        self.assertEqual(s[3].frames_after, [1, 2, 3])
        self.assertEqual(s[4].victim, 1)

    def test_one_frame(self):
        s = simulate([1, 1, 2, 2, 3], 1)
        self.assertEqual(s[-1].faults, 3)
        self.assertEqual(s[-1].hits, 2)
        self.assertEqual([x.victim for x in s], [None, None, 1, None, 2])

    def test_more_frames_than_pages(self):
        s = simulate([1, 2, 1, 2], 6)
        self.assertEqual(s[-1].faults, 2)
        self.assertTrue(all(x.victim is None for x in s))
        self.assertEqual(s[-1].frames_after, [1, 2, None, None, None, None])

    def test_empty_frames_filled_left_to_right(self):
        s = simulate([5, 6], 3)
        self.assertEqual(s[0].frames_after, [5, None, None])
        self.assertEqual(s[1].frames_after, [5, 6, None])

    def test_repeated_pages_all_hits_after_first(self):
        s = simulate([7, 7, 7, 7], 2)
        self.assertEqual((s[-1].faults, s[-1].hits), (1, 3))

    def test_beladys_anomaly(self):
        b = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        self.assertEqual(simulate(b, 3)[-1].faults, 9)
        self.assertEqual(simulate(b, 4)[-1].faults, 10)

    def test_explanation_is_generated_from_state(self):
        s = simulate(REFS, FRAMES)
        self.assertIn("Page 1 arrived earliest", s[4].reason)
        self.assertIn("Page 2 arrived earliest", s[6].reason)

    def test_empty_input_rejected(self):
        with self.assertRaises(ValidationError):
            simulate([], 3)
        with self.assertRaises(ValidationError):
            simulate([1], 0)

    def test_registry(self):
        self.assertIn("FIFO", ALGORITHMS)


if __name__ == "__main__":
    unittest.main()
