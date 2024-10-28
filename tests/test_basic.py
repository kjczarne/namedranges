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


if __name__ == "__main__":
    unittest.main()
