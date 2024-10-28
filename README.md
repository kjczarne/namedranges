# `namedranges`

This lib provides a simple way to work with intervals/ranges in Python using a tuple representation for each interval and a string annotation.

## Installation

```bash
pip install namedranges
```

## Usage

```python
ranges = {
    "1": (1, 5),
    "2": (6, 22),
    "3": (23, 26),
    "4": (27, 38)
}

nr = namedrange.from_dict(ranges)
nr.add_gaps([(10, 10)])
complement = nr.complement()
print(complement)
```
