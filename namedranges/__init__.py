import math
from typing import *
from copy import deepcopy
from dataclasses import dataclass, asdict
from collections import OrderedDict

IndexingVariants = Literal[0, 1]
TupleRangeExpr = Tuple[int, int] 
RangeExpr = TupleRangeExpr | str
RangeName = str

DEFAULT_INDEXING = 0
DEFAULT_RIGHT_SIDE_CLOSED = False
DEFAULT_SEPARATOR = "-"
DEFAULT_COMPARE_START = True


@dataclass
class namedrange_args:
    indexing: IndexingVariants = DEFAULT_INDEXING
    right_side_closed: bool = DEFAULT_RIGHT_SIDE_CLOSED
    separator_for_str_range_expressions: bool = DEFAULT_SEPARATOR
    compare_start_when_sorting: bool = DEFAULT_COMPARE_START


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


def str_ranges_to_tuple_ranges(ranges: Iterable[RangeExpr], separator: str = DEFAULT_SEPARATOR) -> List[TupleRangeExpr]:
    if all(map(lambda x: isinstance(x, tuple), ranges)):
        # Ensure idempotency but with consistent return type:
        return list(ranges)
    tuple_ranges = []
    for range_ in ranges:
        start, end = range_.split(separator)
        tuple_ranges.append((int(start), int(end)))
    return tuple_ranges


class namedrange:

    def __init__(self,
                 names: Iterable[RangeName],
                 ranges: Iterable[RangeExpr],
                 args: namedrange_args | None = None):
        if args is None:
            args = namedrange_args()
        if not (hasattr(names, "__len__") or hasattr(ranges, "__len__")):
            raise TypeError("Names and ranges arguments should be iterables"\
                            "that support length evaluation via `__len__()`")
        if len(names) != len(ranges):
            raise ValueError(f"Lengths of names and ranges are not the same. "\
                             f"`names`: {len(names)} vs. `ranges`: {len(ranges)}")
        self._ranges = dict(zip(names, str_ranges_to_tuple_ranges(ranges, args.separator_for_str_range_expressions)))
        if args.indexing not in [1, 0]:
            raise ValueError(f"Only 0-based or 1-based indexing supported, got: {args.indexing}")
        self.args = args
        for k, v in asdict(args).items():
            setattr(self, k, v)
        self._iterator = iter(self._ranges.values())

    @classmethod
    def from_dict(cls,
                  range_dict: Dict[RangeName, RangeExpr],
                  args: namedrange_args | None = None):
        if not isinstance(range_dict, dict):
            raise TypeError(f"Input into the `from_dict` function should be a dictionary, got {type(range_dict)}")
        self = cls(list(range_dict.keys()),
                   list(range_dict.values()),
                   args)
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
            start = 1 if self.args.indexing == 1 else 0
        if end is None:
            end = list(self.last.values())[0][1] if self.args.right_side_closed else list(self.last.values())[0][1] - 1
        input_ranges = sorted(self._ranges.values())
        complement_ = calculate_complementary_ranges(input_ranges, start, end)
        if return_list:
            return complement_
        return namedrange.from_dict({idx: v for idx, v in enumerate(complement_)}, self.args)

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

    def sorted(self):
        if self.args.compare_start_when_sorting:
            # return sorted(self._ranges.values(), key=lambda x: x[0])
            return OrderedDict(sorted(self._ranges.items(), key=lambda item: item[1][0]))
        # return sorted(self._ranges, key=lambda x: x[1])
        return OrderedDict(sorted(self._ranges.items(), key=lambda item: item[1][1]))

    def __eq__(self, other):
        if isinstance(other, namedrange):
            return all(map(lambda x: x[0] == x[1], zip(self._ranges, other._ranges)))
        raise TypeError("Comparison only between `namedrange` objects is supported")

    def __lt__(self, other):
        if isinstance(other, namedrange):
            if self.args.compare_start_when_sorting:
                return all(map(lambda r1, r2: r1[0] < r2[0], zip(self._ranges, other._ranges)))
            return all(map(lambda r1, r2: r1[1] < r2[1], zip(self._ranges, other._ranges)))
        raise TypeError("Comparison only between `namedrange` objects is supported")

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iterator)

    def __str__(self):
        return str(self._ranges)
        # return ",".join([f"({i[0]}, {i[1]})" for i in self._ranges])

    def __repr__(self):
        return f"namedrange({self._ranges})"

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
        new_r_start = 0 if self.args.indexing == 0 else 1
        sorted_ranges = sorted(self._ranges.items(), key=lambda x: x[1])
        complement_ranges = self.complement() if keep_gaps else []

        # For reindexing if the first gap is [0, x] for 0-indexed inputs
        # or [1, x] for 1-indexed inputs, we need to drop the first gap from the complement:
        if len(complement_ranges) > 0:
            if complement_ranges[0][0] == self.args.indexing:
                complement_ranges = complement_ranges[1:]

        for idx, (name, r) in enumerate(sorted_ranges):
            range_length = r[1] - r[0] + 1
            new_r_end = new_r_start + range_length - 1 if self.args.right_side_closed else new_r_start + range_length

            reindexed_range = (new_r_start, new_r_end)
            repl[name] = reindexed_range

            # print(complement_ranges)
            if idx < len(complement_ranges):
                # Use the complement range to determine the gap length
                gap_start, gap_end = complement_ranges[idx]
                gap_len = gap_end - gap_start + 1
                new_r_start = new_r_end + gap_len + 1
            else:
                new_r_start = new_r_end + 1

        if inplace:
            self._ranges = repl
            return self
        return namedrange.from_dict(repl, self.args)


def rework_range_lists_into_dict(range_exprs: Dict[str, Iterable[RangeExpr]]) -> Dict[str, RangeExpr]:
    out = {}
    for key, range_list in range_exprs.items():
        for idx, range_ in enumerate(range_list):
            out[f"{key}-{idx}"] = range_

    return out


def range_expr_to_tuple(expr: RangeExpr) -> Tuple[int, int]:
    l, r = expr.split("-")
    return int(l), int(r)


def tuple_to_range_expr(tuple_range: Tuple[int, int]) -> RangeExpr:
    return f"{tuple_range[0]}-{tuple_range[1]}"


def tuple_ranges_to_list(ranges: List[Tuple[int, int]], flatten: bool = False):
    """Converts closed-interval ranges to a list of indices.
    For example: [(1, 3), (5, 6)] would yield [[1, 2, 3], [5, 6]].
    If `flatten` is set to `True`, then the list is flattened, e.g.
    [1, 2, 3, 5, 6].
    """
    out = []
    for r in ranges:
        s, e = r
        range_as_list = list(range(s, e + 1))
        out.append(range_as_list)
    if flatten:
        return [i for r in out for i in r]
    return out


def ranges_to_list(ranges: List[RangeExpr], flatten: bool = False):
    """Converts closed-interval range expressions to a list of indices.
    For example: ["1-3", "5-6"] would yield [[1, 2, 3], [5, 6]].
    If `flatten` is set to `True`, then the list is flattened, e.g.
    [1, 2, 3, 5, 6].
    """
    tuple_ranges = [range_expr_to_tuple(r) for r in ranges]
    return tuple_ranges_to_list(tuple_ranges, flatten)


def list_to_ranges(l: List[int]):
    """Converts a list of integers to string range expressions
    such as `1-10`, `2-30`
    """
    residue_list = sorted(set(l))  # Ensure the list is sorted and remove duplicates
    ranges = []

    if len(residue_list) == 0:
        return []

    start = end = residue_list[0]

    for i in range(1, len(residue_list)):
        if residue_list[i] == end + 1:
            end = residue_list[i]
        else:
            ranges.append((start, end))
            start = end = residue_list[i]
    
    ranges.append((start, end))  # Add the last range

    # Convert ranges to a more readable format
    ranges_str = []
    for r in ranges:
        ranges_str.append(tuple_to_range_expr(r))

    return ranges_str
