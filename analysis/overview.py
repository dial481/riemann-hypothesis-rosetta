"""Cluster the entire two-tree source graph and draw its directory-level import map."""
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import LogNorm

from common import RESULTS, archive_data, put_json, table


def main():
    adj, meta = archive_data()
    graph = nx.Graph()
    graph.add_nodes_from(sorted(meta))
    for m in sorted(meta):
        graph.add_edges_from((m, d) for d in adj[m] if d in meta and m != d)
    groups = sorted(nx.community.louvain_communities(graph, seed=42, resolution=1.0), key=lambda g: (-len(g), min(g)))
    modularity = nx.community.modularity(graph, groups)
    rows = []
    for i, group in enumerate(groups, 1):
        novel = [m for m in group if meta[m]["category"] == "Novel"]
        lib = sorted(group - set(novel))
        area = Counter(m.split(".")[1] for m in lib if m.startswith("Mathlib."))
        explicit = Counter(d.split(".")[1] for m in novel for d in adj[m] if d.startswith("Mathlib."))
        dirs = Counter(".".join(m.split(".")[:2]) for m in novel)
        rows.append({"id": i, "novel_modules": len(novel), "mathlib_modules": len(lib),
                     "novel_lines": sum(int(meta[m]["lines"]) for m in novel),
                     "mathlib_lines": sum(int(meta[m]["lines"]) for m in lib),
                     "mathlib_member_areas": sorted(area.items(), key=lambda v: (-v[1], v[0]))[:5],
                     "explicit_area_edges": sorted(explicit.items(), key=lambda v: (-v[1], v[0]))[:5],
                     "novel_prefixes": sorted(dirs.items(), key=lambda v: (-v[1], v[0]))[:3]})
    put_json(RESULTS / "combined-communities.json", {"modularity": modularity, "groups": rows})
    table(RESULTS / "combined-membership.tsv.gz", ["module", "community"],
          ((m, i) for i, g in enumerate(groups, 1) for m in sorted(g)))

    def family(m):
        if m not in meta:
            return "External"
        if meta[m]["category"] == "Mathlib":
            return "Mathlib"
        return m.split(".")[0]

    cats = ["Main", "Statements", "Supplements", "Development", "Formalism", "GroundTheory",
            "ReciprocityTheory", "CompanionTheory", "PositivityTheory", "Lemmata", "BuildAid", "Mathlib", "External"]
    ix = {k: i for i, k in enumerate(cats)}
    grid = np.zeros((len(ix), len(ix)), dtype=int)
    for m, deps in adj.items():
        for d in deps:
            grid[ix[family(m)], ix[family(d)]] += 1
    table(RESULTS / "family-edges.tsv", ["importer", "dependency", "edges"],
          ((a, b, grid[i, j]) for i, a in enumerate(cats) for j, b in enumerate(cats) if grid[i, j]))
    plt.rcParams.update({"svg.hashsalt": "rh-rosetta", "font.size": 10, "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(11.6, 8.4), layout="constrained")
    pic = ax.imshow(np.ma.masked_equal(grid, 0), norm=LogNorm(1, grid.max()), cmap="Blues")
    for i, j in zip(*np.nonzero(grid)):
        v = grid[i, j]
        label = f"{v / 1000:.1f}k" if v >= 10000 else str(v)
        ax.text(j, i, label, ha="center", va="center", color="white" if v >= 2500 else "#16263b", fontsize=8)
    ax.set_xticks(range(len(cats)), cats, rotation=48, ha="right")
    ax.set_yticks(range(len(cats)), cats)
    ax.set(xlabel="Imported family", ylabel="Importing family", title="Where the original source trees import their dependencies")
    fig.colorbar(pic, ax=ax, shrink=.72, label="Distinct module-to-module edges (log scale)")
    fig.savefig(RESULTS / "import-map.svg", metadata={"Date": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
