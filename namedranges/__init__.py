import math
from typing import *
from copy import deepcopy

IndexingVariants = Literal[0, 1]
RangeExpr = Tuple[int, int]
RangeName = str

DEFAULT_INDEXING = 0
DEFAULT_RIGHT_SIDE_CLOSED = False


def calculate_complementary_ranges(input_ranges, start, end) -> List[RangeExpr]:
    complementary_ranges = []
    previous_end = start - 1
    # Calculate complementary ranges
    for range_start, range_end in input_ranges:
        # if range_start == range_end:
            # complementary_ranges.append((previous_end, range_start))
            # complementary_ranges.append((previous_end + 2, range_start - 1))
        # FIXME: multiple single-element ranges seem to not be resilient against this
        if range_start > previous_end + 1 :
            complementary_ranges.append((previous_end + 1, range_start - 1))
        previous_end = range_end
    
    # Handle the range after the last existing range
    if previous_end < end:
        complementary_ranges.append((previous_end + 1, end))

    return complementary_ranges


class namedrange:

    def __init__(self,
                 names: Iterable[RangeName],
                 ranges: Iterable[RangeExpr],
                 indexing: IndexingVariants = DEFAULT_INDEXING,
                 right_side_closed: bool = DEFAULT_RIGHT_SIDE_CLOSED):
        if not (hasattr(names, "__len__") or hasattr(ranges, "__len__")):
            raise TypeError("Names and ranges arguments should be iterables"\
                            "that support length evaluation via `__len__()`")
        if len(names) != len(ranges):
            raise ValueError(f"Lengths of names and ranges are not the same. "\
                             f"`names`: {len(names)} vs. `ranges`: {len(ranges)}")
        self._ranges = dict(zip(names, ranges))
        self.indexing = indexing
        if self.indexing not in [1, 0]:
            raise ValueError(f"Only 0-based or 1-based indexing supported, got: {indexing}")
        self.right_side_closed = right_side_closed

    @classmethod
    def from_dict(cls,
                  range_dict: Dict[RangeName, RangeExpr],
                  indexing: IndexingVariants = DEFAULT_INDEXING,
                  right_side_closed: bool = DEFAULT_RIGHT_SIDE_CLOSED):
        self = cls(list(range_dict.keys()),
                   list(range_dict.values()),
                   indexing,
                   right_side_closed)
        return self

    @property
    def first(self):
        min_val = math.inf
        min_val_tup = (math.inf, math.inf)
        min_key = None
        for k, v in self._ranges.items():
            if v[0] < min_val:
                min_val = v[0]
                min_val_tup = v
                min_key = k
        return {min_key: min_val_tup}

    @property
    def last(self):
        max_val = -math.inf
        max_val_tup = (-math.inf, -math.inf)
        max_key = None
        for k, v in self._ranges.items():
            if v[1] > max_val:
                max_val = v[1]
                max_val_tup = v
                max_key = k
        return {max_key: max_val_tup}

    def complement(self, start: int | None = None, end: int | None = None, return_list: bool = True) -> List[RangeExpr]:
        if start is None:
            start = 1 if self.indexing == 1 else 0
        if end is None:
            end = list(self.last.values())[0][1] if self.right_side_closed else list(self.last.values())[0][1] - 1
        input_ranges = sorted(self._ranges.values())
        complement_ = calculate_complementary_ranges(input_ranges, start, end)
        if return_list:
            return complement_
        return namedrange.from_dict({idx: v for idx, v in enumerate(complement_)}, self.indexing, self.right_side_closed)

    def to_dict(self):
        return self._ranges

    def to_list(self):
        return list(self.values())

    def keys(self):
        return self._ranges.keys()

    def values(self):
        return self._ranges.values()

    def items(self):
        return self._ranges.items()

    def __str__(self):
        return str(self._ranges)
        # return ",".join([f"({i[0]}, {i[1]})" for i in self._ranges])

    def __repr__(self):
        return f"namedrange(complement={self.complement()})"

    def add_gaps(self,
                 gap_positions: List[RangeExpr],
                 name_generator: Callable[[str, int, int, int], str] = lambda x, _, __, i: x + f"-{i}"):
        """
        Introduce gaps into the ranges by removing or splitting portions of existing ranges.
        
        Parameters:
        - gap_positions: List of tuples (start, end) specifying the positions of gaps to introduce.
        - name_generator: A callable that generates a unique name for each new range created by a split.
        """
        updated_ranges = {}

        for name, (range_start, range_end) in self._ranges.items():
            current_ranges = [(range_start, range_end)]
            
            for gap_start, gap_end in gap_positions:
                new_ranges = []
                for (start, end) in current_ranges:
                    # Check for overlap with the gap and split the range if needed
                    if gap_start <= end and gap_end >= start:
                        # Create range before the gap if applicable
                        if gap_start > start:
                            new_ranges.append((start, gap_start - 1))
                        # Create range after the gap if applicable
                        if gap_end < end:
                            new_ranges.append((gap_end + 1, end))
                    else:
                        # No overlap, keep the range as is
                        new_ranges.append((start, end))

                current_ranges = new_ranges

            # Assign names to the resulting ranges after applying gaps
            for i, new_range in enumerate(current_ranges):
                # If it's the original range and has not been split, retain the original name
                if i == 0:
                    updated_ranges[name] = new_range
                else:
                    # Use name generator for any additional ranges created by splitting
                    updated_ranges[name_generator(name, new_range[0], new_range[1], i)] = new_range

        # Update the ranges dictionary with new entries
        self._ranges = updated_ranges

    def reindex(self, keep_gaps: bool = True, inplace: bool = False):
        repl = {}
        new_r_start = 0 if self.indexing == 0 else 1

        sorted_ranges = sorted(self._ranges.items(), key=lambda x: x[1])
        complement_ranges = self.complement()

        for idx, (name, r) in enumerate(sorted_ranges):
            range_length = r[1] - r[0] + 1
            new_r_end = new_r_start + range_length
            if not self.right_side_closed:
                new_r_end -= 1
            reindexed_range = (new_r_start, new_r_end)
            repl[name] = reindexed_range
            if not keep_gaps:
                new_r_start = new_r_end + 1
            else:
                if len(complement_ranges) > idx + 1:
                    if r[0] == self.indexing:
                        gap_start, gap_end = complement_ranges[idx]
                    else:
                        gap_start, gap_end = complement_ranges[idx + 1]
                    gap_len = gap_end - gap_start + 1
                    new_r_start = new_r_end + gap_len + 1
                    new_r_end += gap_len + range_length + 1
                else:
                    new_r_start = new_r_end + 1
                    new_r_end += range_length + 1
                if not self.right_side_closed:
                    new_r_end -= 1

        if inplace:
            self._ranges = repl
        else:
            cp = deepcopy(self)
            cp._ranges = repl
            return cp


def namedrange_closure(indexing: IndexingVariants = DEFAULT_INDEXING,
                       right_side_closed: bool = DEFAULT_RIGHT_SIDE_CLOSED):
    """A closure for creating `namedrange` objects. This lets you define
    consistent behavior for all `namedrange` objects you're using, e.g.
    defined indexing or whether the interval should be closed or open.
    """

    return lambda names, ranges: namedrange(names, ranges, indexing, right_side_closed)
