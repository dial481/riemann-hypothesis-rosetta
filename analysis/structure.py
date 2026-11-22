"""Module graph, dominator cuts, import communities and topology-only ranking."""
import math
from collections import Counter, defaultdict

import networkx as nx

from common import PAGERANK_PLACES, RESULTS, SCORE_PLACES, archive_data, put_json, table


def cuts(graph, root, novel):
    # Every strict dominator ancestor is unavoidable on all paths from Main.
    parent = nx.immediate_dominators(graph, root)
    children = defaultdict(list)
    for m, p in parent.items():
        if p != m:
            children[p].append(m)
    order = [root]
    for m in order:
        order.extend(children[m])
    below, own = Counter(), Counter()
    for m in reversed(order[1:]):
        below[parent[m]] += 1 + below[m]
        own[parent[m]] += (m in novel) + own[m]
    return parent, below, own


def main():
    adj, meta = archive_data()
    graph = nx.DiGraph(adj)
    root = "Main"
    reachable = nx.descendants(graph, root) | {root}
    cone = graph.subgraph(sorted(reachable)).copy()
    novel = {m for m, r in meta.items() if r["category"] == "Novel"}
    proof = graph.subgraph(sorted(novel & reachable)).copy()
    topo = list(nx.topological_sort(cone))
    height, next_node, source_height, source_next = {}, {}, {}, {}
    # Deterministic lexicographic tie breaking between longest paths.
    for m in reversed(topo):
        for h, nxt, neighbors in [(height, next_node, adj[m]),
                                   (source_height, source_next, [d for d in adj[m] if d in meta])]:
            n = min(neighbors, key=lambda t: (-h[t], t), default=None)
            h[m] = 1 + h[n] if n is not None else 0
            nxt[m] = n

    dist = nx.single_source_shortest_path_length(cone, root)
    longest_from_root = {root: 0}
    for m in topo:
        for d in adj[m]:
            longest_from_root[d] = max(longest_from_root.get(d, 0), longest_from_root[m] + 1)
    parent, dominated, dom_novel = cuts(cone, root, novel)
    pr = {m: round(value, PAGERANK_PLACES) for m, value in
          nx.pagerank(proof, alpha=0.85, tol=1e-12, max_iter=500).items()}
    # Only project-to-project dependents enter the reading-priority score.
    metrics = {m: (math.log1p(len(proof) * pr[m]), math.log1p(proof.in_degree(m)),
                   math.log1p(dom_novel[m] if m != root else 0)) for m in proof}
    maxima = [max(x[i] for x in metrics.values()) for i in range(3)]
    scores = {m: round(sum(w * v / largest for w, v, largest in zip((.40, .25, .35), vs, maxima)), SCORE_PLACES)
              for m, vs in metrics.items()}
    order = sorted(scores, key=lambda m: (-scores[m], m))
    rank = {m: i for i, m in enumerate(order, 1)}
    print("centrality complete", flush=True)

    undirected = proof.to_undirected()
    groups = nx.community.louvain_communities(undirected, seed=42, resolution=1.0)
    groups.sort(key=lambda g: (-len(g), min(g)))
    modularity = nx.community.modularity(undirected, groups)
    del undirected
    membership = {m: i for i, group in enumerate(groups, 1) for m in group}
    communities = []
    for i, group in enumerate(groups, 1):
        areas, dirs, prefixes = Counter(), Counter(), Counter()
        umbrella, specific = 0, 0
        for m in group:
            dirs[m.split(".")[0]] += 1
            prefixes[".".join(m.split(".")[:2])] += 1
            for d in adj[m]:
                if d == "Mathlib":
                    umbrella += 1
                elif d.startswith("Mathlib."):
                    specific += 1
                    areas[d.split(".")[1]] += 1
        communities.append({"id": i, "novel_modules": len(group),
                            "novel_lines": sum(int(meta[m]["lines"]) for m in group),
                            "directories": dirs.most_common(4), "prefixes": prefixes.most_common(5),
                            "explicit_area_edges": areas.most_common(), "specific_edges": specific,
                            "umbrella_edges": umbrella,
                            "hub": min(group, key=rank.get)})
    put_json(RESULTS / "communities.json", communities)

    def path(nxt):
        out, m = [], root
        while m is not None:
            out.append(m)
            m = nxt[m]
        return out

    project_next, ph = {}, {}
    for m in reversed(topo):
        if m in proof:
            n = min(proof[m], key=lambda t: (-ph[t], t), default=None)
            project_next[m] = n
            ph[m] = 1 + ph[n] if n else 0
    paths = {"through_external_boundary": path(next_node), "source_only": path(source_next),
             "novel_only": path(project_next)}
    put_json(RESULTS / "longest-paths.json", paths)
    fields = ["module", "reachable", "imports", "dependents", "closure_dependents", "shortest_from_Main",
              "longest_from_Main", "height_to_leaf", "immediate_dominator", "disconnected_others",
              "disconnected_novel", "novel_dependents", "novel_pagerank", "score", "import_rank", "community"]
    table(RESULTS / "metrics.tsv.gz", fields,
          ((m, int(m in reachable), graph.out_degree(m), graph.in_degree(m),
            cone.in_degree(m) if m in cone else "", dist.get(m, ""), longest_from_root.get(m, ""),
            height.get(m, ""), parent.get(m, ""), dominated[m] if m in cone else "",
            dom_novel[m] if m in cone else "", proof.in_degree(m) if m in proof else "",
            pr.get(m, ""), scores.get(m, ""), rank.get(m, ""), membership.get(m, "")) for m in sorted(graph)))
    table(RESULTS / "unreachable.tsv.gz", ["module", "category", "path", "lines"],
          ((m, meta[m]["category"], meta[m]["path"], meta[m]["lines"]) for m in sorted(meta.keys() - reachable)))
    table(RESULTS / "external.tsv", ["module", "direct_importers", "reachable"],
          ((m, graph.in_degree(m), int(m in reachable)) for m in sorted(graph.nodes - meta.keys())))
    directories = defaultdict(lambda: [0, 0, 0, 0])
    totals = defaultdict(lambda: [0, 0, 0, 0])
    for m, r in meta.items():
        v = [1, int(r["lines"]), int(m in reachable), int(r["lines"]) if m in reachable else 0]
        cat = r["category"]
        totals[cat] = [a + b for a, b in zip(totals[cat], v)]
        dirs = r["path"].split("/")[:-1]
        for j in range(len(dirs) + 1):
            k = (cat, "/".join(dirs[:j]) or ".")
            directories[k] = [a + b for a, b in zip(directories[k], v)]
    table(RESULTS / "directories.tsv.gz", ["category", "directory", "modules", "lines", "reachable_modules",
                                          "reachable_lines"], ((*k, *v) for k, v in sorted(directories.items())))
    def leaders(count, pool):
        return [(m, count(m)) for m in sorted(pool, key=lambda m: (-count(m), m))[:30]]
    summary = {"source_counts": dict(totals), "nodes_including_external": len(graph),
               "edges": graph.number_of_edges(), "closure": len(cone), "closure_edges": cone.number_of_edges(),
               "novel_edges": proof.number_of_edges(), "external_in_closure": len(reachable - meta.keys()),
               "heights": {k: len(v) - 1 for k, v in paths.items()},
               "level_counts": sorted(Counter(longest_from_root.values()).items()),
               "top_imports_closure": leaders(cone.out_degree, cone),
               "top_dependents_closure": leaders(cone.in_degree, cone),
               "top_novel_imports": leaders(proof.out_degree, proof),
               "top_novel_dependents": leaders(proof.in_degree, proof),
               "top_cuts": leaders(dominated.__getitem__, reachable - {root}),
               "top_novel_cuts": leaders(dom_novel.__getitem__, (novel & reachable) - {root}),
               "communities": len(groups), "modularity": modularity,
               "umbrella_direct": sum("Mathlib" in adj[m] for m in novel),
               "distinct_explicit_area_modules": sum(any(d.startswith("Mathlib.") for d in adj[m]) for m in novel),
               "unreachable_external": len(graph.nodes - reachable - meta.keys())}
    put_json(RESULTS / "structure.json", summary)
    print("communities and structure complete", flush=True)


if __name__ == "__main__":
    main()
