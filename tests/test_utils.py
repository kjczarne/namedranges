import unittest
from namedranges import list_to_ranges, ranges_to_list


class TestUtils(unittest.TestCase):

    def test_range_conversion_to_list(self):
        i = [2, 3, 8, 15, 16, 17, 18, 20, 23, 24, 25]
        e = ['2-3', '8-8', '15-18', '20-20', '23-25']
        o = list_to_ranges(i)
        self.assertListEqual(e, o)

    def test_list_conversion_to_ranges(self):
        i = ['2-3', '8-8', '15-18', '20-20', '23-25']
        e_f = [2, 3, 8, 15, 16, 17, 18, 20, 23, 24, 25]
        e = [[2, 3], [8], [15, 16, 17, 18], [20], [23, 24, 25]]
        o_f = ranges_to_list(i, flatten=True)
        o = ranges_to_list(i)
        self.assertListEqual(e, o)
        self.assertListEqual(e_f, o_f)



if __name__ == "__main__":
    unittest.main()
