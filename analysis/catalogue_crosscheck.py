"""Check exact owners against the RH declaration graph and original Lean file order."""
import gzip
import hashlib
import json
import re
from array import array
from graphlib import TopologicalSorter

import duckdb
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order

from common import RESULTS, content_digest, imports, read_rows
from compare import URLS, check_input
from upstream_kernel import mask_noncode

THETA = "Formalism.MainNotions.GL3Theta."
CUBE = THETA + "cube2"
UNKILLED = THETA + "IsTwoTorsionPointUnkilled"
HELPER = CUBE + "._proof_2"
THETA_FILE = "src/Formalism/SharpRestriction/GlobalSchurBounds/GL3Theta.lean"
DISPUTE = ("family-point-kernel-bases", "family-point-kernel-ideals")


def rh_graph(filename, sites):
    check_input(filename, *URLS["pr-graph.json.gz"], False)
    offsets, edges, ids = array("i", [0]), array("i"), {}
    with gzip.open(filename, "rt") as stream:
        meta = json.loads(stream.readline().rstrip().removesuffix(",") + "}")["meta"]
        for line in stream:
            if not line.startswith('{"id":'):
                continue
            node = json.loads(line.rstrip().removesuffix(","))
            index = len(offsets) - 1
            if node["id"] != index:
                raise ValueError("Nonsequential declaration IDs in the pinned RH graph")
            name = node["name"]
            if name in sites and "src/" + node["file"] == sites[name][0]:
                if name in ids:
                    raise ValueError(f"Ambiguous RH graph site for {name}")
                ids[name] = index
            edges.extend(sorted(set(node["uses_in_signature"]) | set(node["uses_in_body"])))
            offsets.append(len(edges))
    size = meta["declarations"]
    if len(offsets) != size + 1 or len(edges) != meta["links"]:
        raise ValueError("RH graph size differs from its metadata")
    graph = csr_matrix((np.ones(len(edges), dtype=bool), edges, offsets), shape=(size, size))
    return graph, ids


def mutual_lines(source):
    """Identify the lines inside explicit mutual commands in the pinned original."""
    stack = []
    inside = set()
    for n, line in enumerate(mask_noncode(source.splitlines()), 1):
        command = re.match(r"^\s*(?:(?:public|private|protected|noncomputable|unsafe)\s+)*(mutual|namespace|section|end)\b", line)
        if command and command[1] == "mutual":
            stack.append("mutual")
        elif stack and command and command[1] in ("namespace", "section"):
            stack.append(command[1])
        if stack:
            inside.add(n)
            if command and command[1] == "end":
                stack.pop()
    if stack:
        raise ValueError("Unterminated mutual block")
    return inside


def same_file_order(caller, dependency, mutual):
    if caller in mutual or dependency in mutual:
        return "order inconclusive (mutual block)"
    return "later in same file" if dependency[1] > caller[1] else "file order permits"


def source_paths(proof, sites):
    manifest = json.loads((RESULTS / "independent-content-sha256.json").read_text())
    for filename in ("inventory.tsv.gz", "imports.json.gz"):
        if content_digest(RESULTS / filename) != manifest[filename]:
            raise ValueError(f"Frozen source input differs for {filename}")
    with gzip.open(RESULTS / "imports.json.gz", "rt") as stream:
        adjacency = json.load(stream)
    files = {r["path"]: r for r in read_rows(RESULTS / "inventory.tsv.gz") if r["category"] == "Novel"}
    if {p.relative_to(proof).as_posix() for p in (proof / "src").rglob("*.lean")} != files.keys():
        raise ValueError("Original Lean file set differs from the pinned inventory")
    mutual = set()
    for path, row in files.items():
        raw = (proof / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Original source digest mismatch for {path}")
        text = raw.decode("utf-8")
        if "mutual" in text:
            mutual.update((path, n) for n in mutual_lines(text))
        deps = sorted(set(imports(text)))
        module = row["module"]
        if deps != adjacency[module]:
            raise ValueError(f"Import header differs for {path}")
        adjacency[module] = deps
    modules = {name: files[path]["module"] for name, (path, _) in sites.items()}
    bits = {m: 1 << n for n, m in enumerate(sorted(set(modules.values())))}
    closure = {}
    for m in TopologicalSorter(adjacency).static_order():
        reachable = 0
        for dep in adjacency[m]:
            reachable |= bits.get(dep, 0) | closure[dep]
        closure[m] = reachable

    def test(caller, dependency):
        a, b = modules[caller], modules[dependency]
        if a == b:
            return same_file_order(sites[caller], sites[dependency], mutual)
        return "transitive imports permit" if closure[a] & bits[b] else "no transitive import"

    return test, len(files)


def verify_fold(edge_file, graph, ids, endpoints, shore_witnesses, proof):
    # The two source declarations independently refer to the same auxiliary constant.
    with duckdb.connect() as db:
        shared = db.execute("""
            SELECT DISTINCT src FROM read_parquet(?) WHERE src IN (?,?) AND dst=?
            AND src_kind='decl' AND dst_kind='constant' AND via='value'
        """, [str(edge_file), UNKILLED, CUBE, HELPER]).fetchall()
    if {r[0] for r in shared} != {CUBE, UNKILLED}:
        raise ValueError("Shared value-edge evidence differs")
    # Remove exactly the folded edge in a counterfactual copy and repeat BFS
    # from *every* A owner to *every* B owner, preserving all other edges.
    source, target = ids[UNKILLED], ids[CUBE]
    if not graph[source, target] or shore_witnesses([UNKILLED], [CUBE]):
        raise ValueError("RH graph folding or Shore reachability differs")
    altered = graph.copy()
    altered[source, target] = False
    altered.eliminate_zeros()
    callers, dependencies = ({ids[n] for n in endpoints[key].values()} for key in DISPUTE)

    def has_path(g):
        return any(dependencies.intersection(breadth_first_order(g, n, return_predecessors=False))
                   for n in callers)

    if not has_path(graph) or has_path(altered):
        raise ValueError("Removing the folded helper edge did not explain the disputed link")
    lines = (proof / THETA_FILE).read_text().splitlines()
    if not lines[123].startswith("def cube2 ") or not lines[197].startswith("def IsTwoTorsionPointUnkilled "):
        raise ValueError("Helper example moved in the original source")
    if "cube2" in " ".join(lines[197:200]):
        raise ValueError("Unexpected source reference to cube2")
