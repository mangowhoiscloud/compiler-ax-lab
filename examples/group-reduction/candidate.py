"""Seeded demonstration bug: group sums incorrectly retain the previous sum."""

import json
import sys


def reduce_groups(groups: list[list[int]]) -> list[int]:
    total = 0
    result = []
    for group in groups:
        total += sum(group)  # Seeded bug, not a defect found in a vendor's code.
        result.append(total)
    return result


if __name__ == "__main__":
    print(json.dumps(reduce_groups(json.load(sys.stdin))))
