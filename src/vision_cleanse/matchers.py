"""Matchers for VisionCleanse MVP: exact and near-duplicate grouping.

Near-duplicate grouping is pairwise (O(n^2)) in the MVP. That is
fine for small-to-medium datasets and for the test suite; a vector
index (FAISS) replaces it in a later ring.

A pair is grouped when *either* perceptual hash is within
threshold. The two hashes are complementary, not redundant:
dHash reads horizontal gradient signs and proved extremely stable
under JPEG noise (distance 0 even at quality 30, including on
smooth images where pHash drifts to 16); pHash reads global
low-frequency structure and catches changes dHash is blind to
(dHash only compares left-right neighbours). Requiring both
(AND) would systematically miss heavily compressed smooth images,
so the MVP uses OR and relies on quarantine + reporting --
never silent deletion -- to absorb the looser rule. A geometric
verification ring (SIFT + RANSAC) tightens this later.
"""

from __future__ import annotations


def hamming(a: int, b: int) -> int:
    """Hamming distance between two integer hashes."""
    return (a ^ b).bit_count()  # Python 3.10+; falls back below on old versions


try:
    (0).bit_count()
except AttributeError:  # pragma: no cover - Python < 3.10 fallback
    def hamming(a: int, b: int) -> int:  # type: ignore[no-redef]
        return bin(a ^ b).count("1")


class UnionFind:
    """Minimal union-find used to merge exact and near-duplicate edges."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self) -> list[list[int]]:
        buckets: dict[int, list[int]] = {}
        for i in range(len(self.parent)):
            buckets.setdefault(self.find(i), []).append(i)
        return [g for g in buckets.values() if len(g) > 1]


def group_duplicates(
    records: list[dict],
    phash_threshold: int = 10,
    dhash_threshold: int = 10,
) -> list[dict]:
    """Group records that are exact or near duplicates.

    Each record must carry ``md5``, ``phash`` and ``dhash`` keys
    (see :mod:`vision_cleanse.extractors`). Returns a list of
    ``{"members": [...], "method": "exact" | "near"}`` dicts, where
    ``members`` are the record indices. ``method`` is ``"exact"``
    only when every member shares one MD5; otherwise ``"near"``.
    """
    n = len(records)
    uf = UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if records[i]["md5"] == records[j]["md5"]:
                uf.union(i, j)
            elif (
                hamming(records[i]["phash"], records[j]["phash"]) <= phash_threshold
                or hamming(records[i]["dhash"], records[j]["dhash"]) <= dhash_threshold
            ):
                uf.union(i, j)
    out = []
    for members in uf.groups():
        md5s = {records[i]["md5"] for i in members}
        out.append({"members": members, "method": "exact" if len(md5s) == 1 else "near"})
    return out
