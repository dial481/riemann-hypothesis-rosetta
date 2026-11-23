"""Read back the owner table and verify printed names, directions and direct edges."""
import json
from functools import cache

from scipy.sparse.csgraph import breadth_first_order

from common import read_rows

NO_RECORDED = "no recorded path between the tested declarations"
REVERSE_COLUMNS = ("B_caller", "A_dependency", "kind", "edge_direct")


def path_witness(graph, ids):
    targets = set(ids.values())
    # SciPy traverses double-precision CSR matrices. Convert once per graph.
    traversal = graph.astype("float64", copy=False)

    @cache
    def reachable(node):
        direct = targets.intersection(graph.indices[graph.indptr[node]:graph.indptr[node + 1]])
        walk = breadth_first_order(traversal, node, directed=True, return_predecessors=False)
        return direct, targets.intersection(walk)

    def check(callers, dependencies):
        hits = []
        for caller in callers:
            if caller not in ids:
                continue
            direct, reached = reachable(ids[caller])
            for dependency in dependencies:
                if dependency in ids and ids[dependency] in reached:
                    hits.append((ids[dependency] not in direct, caller, dependency))
        if not hits:
            return "", "", "", "n/a"
        indirect, caller, dependency = min(hits)
        if indirect:
            return caller, dependency, "transitive", "no"
        return caller, dependency, "direct", "yes"

    return check


def verify_owner_table(path, expected_pairs, entries, owners, cards, graphs):
    checks = {label: path_witness(*data) for label, data in graphs.items()}
    seen = set()
    for row in read_rows(path):
        pair = (row["A_card_id"], row["B_card_id"])
        if pair in seen or pair not in expected_pairs:
            raise ValueError(f"Unexpected or repeated owner pair {pair}")
        seen.add(pair)
        for side, key in zip(("A_", "B_"), pair):
            names = entries[key][0]
            if row[side + "printed_lean_names"] != " | ".join(names):
                raise ValueError(f"Printed November 22 names differ for {key}")
            if set(names) != set(owners[key]) or json.loads(row[side + "exact_name_to_tested_owner"]) != owners[key]:
                raise ValueError(f"Exact owner mapping differs for {key}")
            card = cards[key]
            citation = tuple(row[side + k] for k in ("number", "title", "url"))
            if citation != (card["number"] or "unnumbered", card["title"], card["url"]):
                raise ValueError(f"Display citation differs for {key}")
        a, b = (set(owners[k].values()) for k in pair)
        if a & b:
            raise ValueError(f"Shared owner in negative table for {pair}")
        if (a | b) - graphs["pr"][1].keys():
            raise ValueError(f"Missing owner in Proofs & Reasons for {pair}")
        for label, check in checks.items():
            if check(a, b)[0]:
                raise ValueError(f"Forward path in {label} for {pair}")
            expected = check(b, a)
            recorded = tuple(row[f"{label}_opposite_{k}"] for k in REVERSE_COLUMNS)
            if recorded != expected:
                raise ValueError(f"Opposite witness or direct flag differs in {label} for {pair}: {recorded} vs {expected}")
    if seen != expected_pairs:
        raise ValueError("Missing owner-table pairs")
