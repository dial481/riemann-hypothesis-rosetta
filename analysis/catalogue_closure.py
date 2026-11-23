"""Test catalogue links against positive-length paths in the project declaration graph."""
from collections import deque

import duckdb
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

from common import digest

EDGE_SHA = "62a184a781184bc1f3953ed90f5b967a27a2a3517d7b1f7e169ca6cc7d1bbec3"


def project_graph(edge_file, declarations):
    if digest(edge_file) != EDGE_SHA:
        raise ValueError("Declaration edge digest mismatch")
    with duckdb.connect(config={"threads": 4, "memory_limit": "4GB"}) as db:
        db.read_parquet(str(edge_file)).create_view("edges")
        db.execute("""
            CREATE TEMP TABLE nodes AS
            SELECT name, kind, (row_number() OVER (ORDER BY name, kind) - 1)::INTEGER AS id
            FROM (SELECT src AS name, src_kind AS kind FROM edges UNION
                  SELECT dst AS name, dst_kind AS kind FROM edges)
        """)
        size = db.execute("SELECT count(*) FROM nodes").fetchone()[0]
        lookup = dict(db.execute("SELECT name,id FROM nodes WHERE kind='decl' AND name IN "
                                 "(SELECT unnest(?))", [sorted(declarations)]).fetchall())
        ids = db.execute("""
            SELECT a.id AS src, b.id AS dst FROM edges e
            JOIN nodes a ON (e.src,e.src_kind)=(a.name,a.kind)
            JOIN nodes b ON (e.dst,e.dst_kind)=(b.name,b.kind)
        """).fetchnumpy()
    src, dst = ids["src"], ids["dst"]
    graph = csr_matrix((np.ones(len(src), dtype=bool), (src, dst)), shape=(size,size))
    return graph, lookup


def reachable_targets(graph, target_ids):
    # Contract cycles before propagation. A bit denotes reachability to one of
    # the named targets, so unrelated declarations add no bits to the result.
    count, component = connected_components(graph, directed=True, connection="strong")
    edges = graph.tocoo()
    src, dst = component[edges.row], component[edges.col]
    outside = src != dst
    parents = csr_matrix((np.ones(np.count_nonzero(outside), dtype=bool),
                          (dst[outside], src[outside])), shape=(count,count))
    pending = np.bincount(parents.indices, minlength=count).tolist()
    bits = {node: 1 << i for i,node in enumerate(sorted(target_ids))}
    masks = [0] * count
    for node, bit in bits.items():
        masks[component[node]] |= bit
    queue = deque(i for i,n in enumerate(pending) if n == 0)
    processed = 0
    offsets, indices = parents.indptr, parents.indices
    while queue:
        child = queue.popleft()
        processed += 1
        for parent in indices[offsets[child]:offsets[child+1]]:
            masks[parent] |= masks[child]
            pending[parent] -= 1
            if pending[parent] == 0:
                queue.append(parent)
    if processed != count:
        raise ValueError("Cycle in the condensed graph")
    sizes = np.bincount(component)
    return component, sizes, masks, bits


def check_links(edges_path, entries, links, endpoints, cited_identities):
    owners = {n for mapping in endpoints.values() for n in mapping.values()}
    graph, ids = project_graph(edges_path, owners)
    targets = set(ids.values())  # Either endpoint can be the target in the direction check.
    component, sizes, masks, bits = reachable_targets(graph, targets)
    direct = {node: set(graph.indices[graph.indptr[node]:graph.indptr[node+1]]) & targets
              for node in ids.values()}
    def witnesses(src_owned, dst_owned):
        hits = []
        for caller in src_owned:
            if caller not in ids:
                continue
            node = ids[caller]
            for callee in dst_owned:
                if callee not in ids:
                    continue
                dep = ids[callee]
                if dep in direct[node]:
                    hits.append((0, caller, callee))
                elif masks[component[node]] & bits[dep] and (node != dep or sizes[component[node]] > 1):
                    hits.append((1, caller, callee))
        return sorted(hits)

    rows = []
    for (a,b),(explicit,svg_pair) in sorted(links.items()):
        source, target = entries[a][0], entries[b][0]
        src_owned = sorted(set(endpoints[a].values()))
        dst_owned = sorted(set(endpoints[b].values()))
        shared = sorted(cited_identities[a] & cited_identities[b])
        hits = witnesses(src_owned, dst_owned)
        if hits:
            distance, caller, callee = min(hits)
            result = "direct" if distance == 0 else "transitive"
        else:
            caller = callee = ""
            complete = len(endpoints[a]) == len(source) and len(endpoints[b]) == len(target)
            result = "common declaration" if shared else "no path" if complete else "incomplete endpoint coverage"
        opposite = witnesses(dst_owned, src_owned) if explicit and result == "no path" else []
        exact_reverse = any(rev_src in target and rev_dst in source for _, rev_src, rev_dst in opposite)
        reverse_result = ("direct" if opposite[0][0] == 0 else "transitive") if opposite else ""
        reverse_caller, reverse_callee = opposite[0][1:] if opposite else ("", "")
        rows.append((a, b, explicit, svg_pair, len(source), len(endpoints[a]), len(target), len(endpoints[b]),
                     int(bool(set(src_owned) & set(dst_owned))), result, caller, callee, reverse_result, reverse_caller, reverse_callee, int(exact_reverse) if opposite else "", "|".join(shared)))
    return rows
