"""Cross-check the exported graph metrics and cuts with a DAG-specific algorithm."""
import json
import math
from collections import Counter, defaultdict
from graphlib import TopologicalSorter

from common import PAGERANK_PLACES, RESULTS, SCORE_PLACES, archive_data, read_rows


def main():
    adjacency, inventory = archive_data()
    project = {m for m, row in inventory.items() if row["category"] == "Novel"}
    predecessors = defaultdict(list)
    for m, imports in adjacency.items():
        for d in imports:
            predecessors[d].append(m)

    root = "Main"
    distance = {root: 0}
    queue = [root]
    for m in queue:
        for d in adjacency[m]:
            if d not in distance:
                distance[d] = distance[m] + 1
                queue.append(d)

    parents = {m: [p for p in predecessors[m] if p in distance] for m in queue}
    order = list(TopologicalSorter(parents).static_order())
    position = {m: i for i, m in enumerate(order)}
    idom, longest, height = {root: root}, {root: 0}, {}
    for m in order[1:]:
        # On a DAG every path into m ends at one of these predecessors.
        # Their lowest common dominator is the immediate dominator of m.
        ancestor = parents[m][0]
        for p in parents[m][1:]:
            while p != ancestor:
                if position[p] > position[ancestor]:
                    p = idom[p]
                else:
                    ancestor = idom[ancestor]
        idom[m] = ancestor
        longest[m] = 1 + max(longest[p] for p in parents[m])

    lost, lost_project = Counter(), Counter()
    for m in reversed(order):
        height[m] = max((1 + height[d] for d in adjacency[m]), default=0)
        if m != root:
            lost[idom[m]] += 1 + lost[m]
            lost_project[idom[m]] += (m in project) + lost_project[m]

    project_degree = {m: sum(d in project for d in adjacency[m]) for m in project}
    pagerank, scores, ranks, communities = {}, {}, {}, Counter()
    seen = set()
    for row in read_rows(RESULTS / "metrics.tsv.gz"):
        m = row["module"]
        assert m not in seen
        seen.add(m)
        assert int(row["reachable"]) == (m in distance), m
        assert int(row["imports"]) == len(adjacency[m]), m
        assert int(row["dependents"]) == len(predecessors[m]), m
        if m in distance:
            assert row["immediate_dominator"] == ("" if m == root else idom[m]), m
            assert int(row["closure_dependents"]) == len(parents[m]), m
            assert int(row["shortest_from_Main"]) == distance[m], m
            assert int(row["longest_from_Main"]) == longest[m], m
            assert int(row["height_to_leaf"]) == height[m], m
            assert int(row["disconnected_others"]) == lost[m], m
            assert int(row["disconnected_novel"]) == lost_project[m], m
        if m in project:
            assert int(row["novel_dependents"]) == sum(p in project for p in predecessors[m]), m
            pagerank[m] = float(row["novel_pagerank"])
            assert round(pagerank[m], PAGERANK_PLACES) == pagerank[m], m
            scores[m] = float(row["score"])
            ranks[m] = int(row["import_rank"])
            communities[int(row["community"])] += 1
    assert seen == adjacency.keys()
    raw = {m: (math.log1p(len(project) * pagerank[m]),
               math.log1p(sum(p in project for p in predecessors[m])),
               math.log1p(lost_project[m] if m != root else 0)) for m in project}
    maxima = tuple(map(max, zip(*raw.values())))
    def score(m):
        return round(sum(w * v / mx for w, v, mx in zip((0.40, 0.25, 0.35), raw[m], maxima)), SCORE_PLACES)
    for i, m in enumerate(sorted(project, key=lambda m: (-score(m), m)), start=1):
        assert ranks[m] == i, m
        assert scores[m] == score(m), m
    assert communities == {g["id"]: g["novel_modules"] for g in json.loads((RESULTS / "communities.json").read_text())}

    n = len(project)
    dangling_mass = math.fsum(pagerank[m] for m in project if not project_degree[m])
    base = (0.15 + 0.85 * dangling_mass) / n
    def error(m):
        incoming = math.fsum(pagerank[p] / project_degree[p] for p in predecessors[m] if p in project)
        return abs(pagerank[m] - (base + 0.85 * incoming))
    residual = math.fsum(error(m) for m in project)
    assert math.isclose(math.fsum(pagerank.values()), 1.0, abs_tol=1e-12)
    assert residual < n * 1e-12
    print(f"{len(seen):,} degree records, {len(order):,} full dominator and distance records, "
          f"{len(ranks):,} project rank entries. PageRank L1 residual {residual:.3g}.")


if __name__ == "__main__":
    main()
