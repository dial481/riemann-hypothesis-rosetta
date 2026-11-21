"""Independent consistency checks on the exported results, including literal citations."""
import argparse
import gzip
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import networkx as nx

from common import RESULTS, archive_data, digest, imports, put_json, read_rows

FREEZE = "independent-sha256.json"


def verify_frozen():
    manifest = json.loads((RESULTS / FREEZE).read_text())
    for name, expected in manifest.items():
        if digest(RESULTS / name) != expected:
            raise ValueError(f"Independent output changed: {name}")
    return manifest


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("proof", type=Path)
    cli.add_argument("--freeze", action="store_true")
    args = cli.parse_args()
    adj, inv = archive_data()
    graph = nx.DiGraph(adj)
    cone = nx.descendants(graph, "Main") | {"Main"}
    summary = json.loads((RESULTS / "structure.json").read_text())
    assert not set(inv) - graph.nodes
    assert sum(map(len, adj.values())) == summary["edges"]
    assert len(cone) == summary["closure"]
    unreachable = {r["module"] for r in read_rows(RESULTS / "unreachable.tsv.gz")}
    assert unreachable == inv.keys() - cone
    assert {r["module"] for r in read_rows(RESULTS / "external.tsv")} == graph.nodes - inv.keys()
    assert set(r["module"] for r in read_rows(RESULTS / "combined-membership.tsv.gz")) == set(inv)
    node_paths = json.loads((RESULTS / "longest-paths.json").read_text())
    for scope, walk in node_paths.items():
        assert walk[0] == "Main"
        assert all(b in adj[a] for a, b in zip(walk, walk[1:]))
        assert scope != "novel_only" or all(inv[m]["category"] == "Novel" for m in walk)
        assert scope != "source_only" or all(m in inv for m in walk)
    bounds = {"through_external_boundary": cone, "source_only": cone & inv.keys(),
              "novel_only": {m for m in cone if m in inv and inv[m]["category"] == "Novel"}}
    for scope, nodes in bounds.items():
        assert nx.dag_longest_path_length(graph.subgraph(nodes)) == len(node_paths[scope]) - 1
    for cut, losses in summary["top_cuts"][:5]:
        present = nx.descendants(nx.restricted_view(graph, [cut], []), "Main") | {"Main"}
        assert len(cone - present) - 1 == losses
    # Independently read each original file's single-line imports. This corpus has
    # no comments or multiline import commands; the richer header parser handles Mathlib.
    count = 0
    for m, r in inv.items():
        if r["category"] == "Novel":
            data = (args.proof / r["path"]).read_bytes()
            names = [s.decode() for s in re.findall(rb"^import ([^\s]+)[ \t]*$", data, flags=re.M)]
            assert len(names) == int(r["import_commands"]) and sorted(set(names)) == adj[m], m
            count += len(names)
    assert imports("/- /- import False -/ -/\nmodule\npublic meta import all Mathlib.X\n"
                   "-- import Nope\nimport «A».B\n#check \"import Ghost\"") == ["Mathlib.X", "A.B"]
    spine = list(read_rows(RESULTS / "spine.tsv"))
    assert len(spine) == len(set(r["module"] for r in spine)) == 200
    chains = json.load(gzip.open(RESULTS / "spine-witnesses.json.gz", "rt"))
    @lru_cache(maxsize=4096)
    def lines(path):
        return (args.proof / path).read_text().splitlines()
    for priority, r in enumerate(spine, 1):
        m = r["module"]
        chain = chains[m]
        assert r["description"] and int(r["rank"]) == priority and m in cone and inv[m]["category"] == "Novel"
        assert (chain[0]["module"], chain[0]["name"]) == ("Main", "riemannHypothesis")
        assert chain[-1]["module"] == m and str(chain[-1]["line"]) == r["line"]
        assert len(chain) == int(r["rh_steps"]) + 1
        for step in chain:
            assert step["name"].split(".")[-1] in lines(step["path"])[step["line"] - 1]
        for a, b in zip(chain, chain[1:]):
            assert b["token_in_caller"] in lines(a["path"])[b["caller_use_line"] - 1]
    print(f"Verified archive imports ({count:,} occurrences), three path lengths, five cuts, and 200 source trails.")
    if args.freeze:
        files = sorted(p for p in RESULTS.iterdir() if p.is_file() and p.name != FREEZE)
        if any(p.name.startswith("comparison") for p in files):
            raise ValueError("Freeze the independent run in a clean results directory")
        put_json(RESULTS / FREEZE, {p.name: digest(p) for p in files})


if __name__ == "__main__":
    main()
