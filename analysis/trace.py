"""Trace lexically explicit project names starting from Main.riemannHypothesis.

This deliberately incomplete name resolver reads the original source only.
"""
import argparse
import re
import sys
from collections import Counter, deque, namedtuple
from functools import lru_cache
from pathlib import Path

import networkx as nx
from pyroaring import BitMap

from common import NAME, NAME_RE, RESULTS, archive_data, put_json, table

DECL = re.compile(r"^(?:@\[[^\n]*?\]\s*)*(?:(?:private|protected|noncomputable|public|unsafe|partial|"
                  r"nonrec|local|scoped|mutual|meta|opaque_reducible)\s+)*"
                  rf"(theorem|lemma|def|abbrev|structure|class|inductive|instance|opaque|axiom)\s+({NAME})")
FRAME = re.compile(r"^(?:(?:noncomputable|public|private|protected)\s+)*(namespace|section|end)\b(?:\s+(" + NAME + r"))?")
COMMAND = re.compile(r"^(?:@\[|#|(?:import|open|namespace|section|end|variable|universe|include|omit|"
                     r"set_option|attribute|export|notation|infix[lr]?|macro(?:_rules)?|syntax|elab(?:_rules)?|"
                     r"example|instance|deriving|noncomputable|private|protected|local|scoped|initialize|"
                     r"run_cmd|mutual|class|inductive|structure|abbrev|def|theorem|lemma|alias)\b)")
STRING = re.compile(r'"(?:\\.|[^"\\])*"')
BOUND = re.compile(r"[(\[{⦃]\s*([\w' ]+?)\s*:|\b(?:have|let|intro|rename_i|fun|∀|obtain)\s+([\w' ]+)")
D = namedtuple("Decl", "name module line stop head ns opens kind private")


def scope(prefix, name):
    if name.startswith("_root_."):
        return name[7:]
    return prefix + "." + name if prefix else name


def ancestors(ns):
    while ns:
        yield ns
        ns = ns.rpartition(".")[0]
    yield ""


def index_file(lines, mid):
    frames, ns, opened, found = [], "", (), []
    current = None
    for line_no, line in enumerate(lines):
        if not line or line[0].isspace():
            continue
        match = DECL.match(line)
        if current is not None and (match or COMMAND.match(line)):
            found.append(current._replace(stop=line_no))
            current = None
        frame = FRAME.match(line)
        if frame:
            kind, arg = frame.groups()
            if kind == "end":
                if frames:
                    ns, opened = frames.pop()
            else:
                frames.append((ns, opened))
                if kind == "namespace" and arg:
                    ns = sys.intern(scope(ns, arg))
        elif line.startswith("open ") and not line.startswith("open scoped "):
            words = line.strip().split()[1:]
            if words and all(NAME_RE.fullmatch(w) for w in words) and "in" not in words:
                opened = tuple(dict.fromkeys((*opened, *(sys.intern(w) for w in words))))
        elif match:
            kind, name = match.groups()
            if kind == "instance" and name in {"where", "of", "in", "nonempty"}:
                continue
            current = D(scope(ns, name), mid, line_no, len(lines), match.end(), ns, opened, kind,
                        "private " in line[:match.start(1)])
    if current is not None:
        found.append(current)
    return found


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("proof", type=Path)
    proof = cli.parse_args().proof
    adj, meta = archive_data()
    names = sorted(m for m in meta if meta[m]["category"] == "Novel")
    ids = {m: i for i, m in enumerate(names)}
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(ids)))
    graph.add_edges_from((ids[m], ids[d]) for m in names for d in adj[m] if d in ids)
    visibility = {}
    for m in reversed(list(nx.topological_sort(graph))):
        v = BitMap([m])
        for d in graph[m]:
            v |= visibility[d]
        v.run_optimize()
        visibility[m] = v
    paths = [proof / meta[m]["path"] for m in names]
    del meta, adj, graph
    decls, by_name, tails = [], {}, set()
    @lru_cache(maxsize=1024)
    def lines(mid):
        return paths[mid].read_text().splitlines()
    for mid in range(len(names)):
        for decl in index_file(lines(mid), mid):
            idx = len(decls)
            decls.append(decl)
            key = decl.name
            tails.add(key.rsplit(".", 1)[-1])
            if key in by_name:
                old = by_name[key]
                if isinstance(old, int):
                    by_name[key] = [old, idx]
                else:
                    old.append(idx)
            else:
                by_name[key] = idx
    print(f"indexed {len(decls):,} named declaration sites", flush=True)
    def resolve(token, cur):
        token = token.removeprefix("_root_.")
        tail = token.rsplit(".", 1)[-1]
        if tail not in tails or ("." not in token and len(token) < 4):
            return None
        # Dotted literals can also be relative inside a namespace. Any competing
        # visible matches are grounds to omit the edge.
        options = set()
        for space in ancestors(cur.ns):
            options.add(scope(space, token))
        for opened in cur.opens:
            for space in ancestors(cur.ns):
                options.add(scope(scope(space, opened), token))
        hits = []
        for k in options:
            match = by_name.get(k)
            if match is None:
                continue
            for idx in ([match] if isinstance(match, int) else match):
                dest = decls[idx]
                if dest.module == cur.module:
                    if dest.line < cur.line:
                        hits.append(idx)
                elif not dest.private and dest.module in visibility[cur.module]:
                    hits.append(idx)
        if len(hits) == 1:
            return hits[0]
        return None

    root = by_name["riemannHypothesis"]
    assert isinstance(root, int) and names[decls[root].module] == "Main"
    parent, use, spelling, depths = {root: root}, {root: decls[root].line + 1}, {root: ""}, {root: 0}
    queue = deque([root])
    while queue:
        src = queue.popleft()
        cur = decls[src]
        body = lines(cur.module)[cur.line:cur.stop]
        body[0] = body[0][cur.head:]
        local, seen = set(), set()
        for offset, line in enumerate(body):
            line = STRING.sub("", line)
            if "--" in line:
                line = line.split("--", 1)[0]
            for binder in BOUND.finditer(line):
                local.update((binder[1] or binder[2]).split())
            for word in NAME_RE.finditer(line):
                token = word[0]
                if token in seen or token.partition(".")[0] in local:
                    continue
                seen.add(token)
                dest = resolve(token, cur)
                if dest is None or dest in parent:
                    continue
                parent[dest], use[dest], spelling[dest] = src, cur.line + offset + 1, token
                depths[dest] = depths[src] + 1
                queue.append(dest)
    def evidence():
        for i, p in parent.items():
            d, caller = decls[i], decls[p]
            yield (names[d.module], d.name, d.line + 1, d.kind, depths[i], names[caller.module],
                   caller.name, caller.line + 1, use[i], spelling[i])
    table(RESULTS / "rh-trace.tsv.gz", ["module", "name", "line", "kind", "depth", "caller_module",
          "caller", "caller_decl_line", "use_line", "token"], evidence())
    put_json(RESULTS / "trace-summary.json", {"indexed_named_sites": len(decls), "reached_sites": len(parent),
             "reached_modules": len({decls[i].module for i in parent}), "max_witness_length": max(depths.values())})
    print("source trace complete", flush=True)


if __name__ == "__main__":
    main()
