import unittest
from namedranges import namedrange


class TestBasic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ranges = {
            "1": (1, 5),
            "2": (6, 22),
            "3": (23, 26),
            "4": (27, 38)
        }
        cls.gaps_1 = [(10, 10)]
        cls.expected_1 = {'1': (1, 5), '2': (6, 9), '2-1': (11, 22), '3': (23, 26), '4': (27, 38)}
        cls.gaps_2 = [(10, 10), (25, 30), (33, 35)]
        cls.expected_2 = {'1': (1, 5), '2': (6, 9), '2-1': (11, 22), '3': (23, 24), '4': (31, 32), '4-1': (36, 38)}
        cls.ranges_3 = {
            "1": (10, 15),
            "2": (21, 30)
        }
        cls.expected_3_with_gaps_maintained = {
            "1": (1, 6),
            "2": (12, 21)
        }
        cls.expected_3_with_gaps_left_out = {
            "1": (1, 6),
            "2": (7, 16)
        }

    def test_gap_insertion(self):
        nr = namedrange.from_dict(self.ranges)
        nr.add_gaps(self.gaps_1, lambda x, _, __, i: x + f"-{i}")
        self.assertDictEqual(nr.to_dict(), self.expected_1)
        nr = namedrange.from_dict(self.ranges)
        nr.add_gaps(self.gaps_2, lambda x, _, __, i: x + f"-{i}")
        self.assertDictEqual(nr.to_dict(), self.expected_2)

    def test_complement(self):
        nr = namedrange.from_dict(self.ranges, indexing=1)
        complement = nr.complement()
        self.assertListEqual(complement, [])
        nr = namedrange.from_dict(self.ranges, indexing=1)
        nr.add_gaps(self.gaps_2, lambda x, _, __, i: x + f"-{i}")
        complement = nr.complement()
        self.assertEqual(self.gaps_2, complement)

    def test_reindex(self):
        nr = namedrange.from_dict(self.ranges_3, indexing=1)
        reindexed_nr = nr.reindex(keep_gaps=False)
        reindexed_nr_with_gaps = nr.reindex(keep_gaps=True)
        self.assertDictEqual(reindexed_nr_with_gaps.to_dict(), self.expected_3_with_gaps_maintained)
        # print(reindexed_nr_with_gaps)
        # print(self.expected_3_with_gaps_maintained)
        self.assertDictEqual(reindexed_nr.to_dict(), self.expected_3_with_gaps_left_out)
        # print(reindexed_nr)
        # print(self.expected_3_with_gaps_left_out)


if __name__ == "__main__":
    unittest.main()
