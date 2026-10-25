import unittest

from tests.helpers import REFS, FRAMES, states
from algorithms.optimal import simulate, next_use


class TestOptimal(unittest.TestCase):
    def test_reference_example_step_by_step(self):
        s = simulate(REFS, FRAMES)
        self.assertEqual(states(s), [
            [1, None, None], [1, 2, None], [1, 2, 3], [1, 2, 3],
            [4, 2, 3], [4, 2, 3], [5, 2, 3]])
        self.assertEqual([x.victim for x in s], [None, None, None, None, 1, None, 4])
        self.assertEqual([x.faults for x in s], [1, 2, 3, 3, 4, 4, 5])
        self.assertEqual([x.hits for x in s], [0, 0, 0, 1, 1, 2, 2])

    def test_totals(self):
        s = simulate(REFS, FRAMES)
        self.assertEqual((s[-1].faults, s[-1].hits), (5, 2))

    def test_tie_between_never_used_pages_is_explained(self):
        s = simulate(REFS, FRAMES)
        self.assertIn("tie", s[4].reason)
        self.assertEqual(s[4].victim_slot, 0)  # lowest frame wins the tie

    def test_farthest_next_use_chosen(self):
        s = simulate([1, 2, 3, 4, 2, 3, 1], 3)  # at ref 4: next uses 1->7, 2->5, 3->6
        self.assertEqual(s[3].victim, 1)
        self.assertIn("furthest", s[3].reason)

    def test_next_use_helper(self):
        self.assertEqual(next_use(2, REFS, 0), 1)
        self.assertEqual(next_use(2, REFS, 1), 5)
        self.assertIsNone(next_use(3, REFS, 2))

    def test_info_shows_remaining_and_next_use(self):
        s = simulate(REFS, FRAMES)
        self.assertEqual(s[4].order_note, "Remaining references: 2, 5")
        self.assertEqual(s[4].info_before[0].split("  ")[0], "Never used again")
        self.assertEqual(s[4].info_before[1], "Next use: ref 6")

    def test_one_frame_and_big_ram(self):
        self.assertEqual(simulate([1, 2, 1, 2], 1)[-1].faults, 4)
        self.assertEqual(simulate([1, 2, 1, 2], 9)[-1].faults, 2)

    def test_never_worse_than_fifo_or_lru(self):
        import random
        from algorithms.fifo import simulate as f
        from algorithms.lru import simulate as l
        rnd = random.Random(7)
        for _ in range(200):
            refs = [rnd.randint(0, 6) for _ in range(rnd.randint(1, 25))]
            n = rnd.randint(1, 5)
            o = simulate(refs, n)[-1].faults
            self.assertLessEqual(o, f(refs, n)[-1].faults)
            self.assertLessEqual(o, l(refs, n)[-1].faults)


if __name__ == "__main__":
    unittest.main()
