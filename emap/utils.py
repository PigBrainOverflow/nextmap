from typing import Iterable


class XorHash:
    def hash(self, xs: Iterable[int]) -> int:
        h = 0
        for x in xs:
            h ^= hash(x)
        return h

    def update(self, old_h: int, old_x: int, new_x: int) -> int:
        """
        Update the hash value by replacing old_x with new_x.
        """
        return old_h ^ hash(old_x) ^ hash(new_x)


class DisjointSetUnion:
    def __init__(self):
        self._parents: dict[int, int] = {}

    @property
    def parents(self) -> dict[int, int]:
        return self._parents

    def find(self, x: int) -> int:
        if x not in self._parents:
            self._parents[x] = x  # initialize parent to itself
            return x
        if self._parents[x] != x:
            self._parents[x] = self.find(self._parents[x])  # path compression
        return self._parents[x]

    def union(self, x: int, y: int) -> bool:
        xr, yr = self.find(x), self.find(y)
        if xr == yr:
            return False  # already in same set

        # union
        if xr < yr:
            self._parents[yr] = xr  # choose the smaller as parent
        else:
            self._parents[xr] = yr

        return True