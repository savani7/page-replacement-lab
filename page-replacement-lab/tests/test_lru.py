import unittest

from tests.helpers import REFS, FRAMES, states
from algorithms.lru import simulate


class TestLRU(unittest.TestCase):
    def test_reference_example_step_by_step(self):
        s = simulate(REFS, FRAMES)
        self.assertEqual(states(s), [
            [1, None, None], [1, 2, None], [1, 2, 3], [1, 2, 3],
            [1, 4, 3], [1, 4, 2], [5, 4, 2]])
        self.assertEqual([x.victim for x in s], [None, None, None, None, 2, 3, 1])
        self.assertEqual([x.kind for x in s],
                         ["load", "load", "load", "hit", "replace", "replace", "replace"])
        self.assertEqual([x.hits for x in s], [0, 0, 0, 1, 1, 1, 1])
        self.assertEqual([x.faults for x in s], [1, 2, 3, 3, 4, 5, 6])

    def test_totals(self):
        s = simulate(REFS, FRAMES)
        self.assertEqual((s[-1].faults, s[-1].hits), (6, 1))

    def test_hit_refreshes_recency(self):
        s = simulate([1, 2, 1, 3, 4], 3)  # 1 was refreshed, so 2 is evicted
        self.assertEqual(s[4].victim, 2)

    def test_last_used_info(self):
        s = simulate(REFS, FRAMES)
        self.assertEqual(s[3].info_after[0], "Last used: ref 4")
        self.assertIn("LEAST RECENTLY USED", s[3].info_after[1])  # page 2, last used ref 2

    def test_one_frame(self):
        s = simulate([1, 2, 1, 2], 1)
        self.assertEqual(s[-1].faults, 4)

    def test_more_frames_than_pages(self):
        s = simulate([1, 2, 3, 1, 2, 3], 10)
        self.assertEqual((s[-1].faults, s[-1].hits), (3, 3))

    def test_repeated_pages(self):
        s = simulate([4, 4, 4], 1)
        self.assertEqual((s[-1].faults, s[-1].hits), (1, 2))

    def test_explanation_mentions_real_values(self):
        s = simulate(REFS, FRAMES)
        self.assertIn("Page 2 was last used at reference 2", s[4].reason)

    def test_lru_can_lose_to_fifo(self):
        from algorithms.fifo import simulate as fifo
        self.assertGreater(simulate(REFS, FRAMES)[-1].faults, fifo(REFS, FRAMES)[-1].faults)


if __name__ == "__main__":
    unittest.main()
