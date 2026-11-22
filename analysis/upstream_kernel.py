"""File-level checks against the v0.2.1 kernel tables; static evidence at the upstream pin."""
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from common import NAME, NAME_RE, digest, put_json, read_rows, table
from trace import BOUND, ancestors, index_file, scope

DIGESTS = {
    "constants.csv.gz": "2964f5236046325ac7884906cb9517b0aa582330dd48a07eef291cb579444820",
    "decls.csv.gz": "bdfeae289f2db8b279816439049f26ba69ec993af2bab3b30d53340fe02493b9",
    "decl_edges.csv.gz": "0e450a0120add04c917c574150a2898db6c07c87e1da9623d2eafe506ddc2025",
}
FROZEN = Path("results")
PRIVATE = re.compile(r"^_private\..*?\.\d+\.")
HEADER = re.compile(r"\b(?:theorem|lemma|def|abbrev|structure|inductive|class|opaque|axiom)\s+(" + NAME + r")")
ALIAS_HEADER = re.compile(r"^\s*(?:public\s+|private\s+)?alias\s+(" + NAME + r")\s*:=", re.M)
OUTPUTS = ("kernel-counts.json", "kernel-file-usage.tsv.gz", "retained-unused.tsv.gz", "retained-importers.tsv.gz",
           "importer-references.tsv.gz", "removed-used-files.tsv", "removed-used-declarations.tsv")


def module(path):
    return path[4:-5].replace("/", ".")


def csv_rows(path):
    with gzip.open(path, "rt", newline="") as stream:
        yield from csv.DictReader(stream)


def gate(data, paths):
    for name, expected in DIGESTS.items():
        if digest(data / name) != expected:
            raise ValueError(f"Checksum mismatch for {name}")
    original, upstream, trace = paths
    used = {r["file"] for r in csv_rows(data / "decls.csv.gz") if r["origin"] == "project" and r["in_cone"] == "true"}
    masks = defaultdict(int)
    for r in csv_rows(data / "constants.csv.gz"):
        if r["origin"] == "project" and r["file"] and r["decl"] and r["shared_aux"] == "false":
            masks[r["file"]] |= int(r["thm_mask"] or 0)
    assert used <= original and used == {p for p, mask in masks.items() if mask}
    rh = {p for p, mask in masks.items() if mask & 1}
    removed, unused = original - upstream, original - used
    retained_miss = (original & upstream) - trace
    shared = len(trace & rh)
    counts = dict(unused=len(unused), unused_removed=len(removed & unused), unused_retained=len(unused & upstream),
                  used_removed=len(removed & used), used_removed_traced=len(removed & used & trace),
                  retained_miss_rh=len(retained_miss & rh), retained_miss_other=len((retained_miss & used) - rh),
                  retained_miss_unused=len(retained_miss & unused), rh_files=len(rh), trace_files=len(trace), shared=shared)
    expected = (28900, 25756, 3144, 36, 30, 12235, 3, 3011, 146284, 134176, 134043)
    if tuple(counts.values()) != expected:
        raise ValueError(f"Kernel comparison gate failed: {counts}")
    return counts, unused & upstream, removed & used, dict(masks)


def import_pairs(directory, retained, targets):
    paths = {module(p): p for p in retained}
    providers = {module(p): p for p in targets}
    with gzip.open(directory / "imports.json.gz", "rt") as stream:
        graph = json.load(stream)
    return {(paths[m], providers[d]) for m in paths if m in graph for d in graph[m] if d in providers}


def owners(data, importers, targets, removed):
    selected = importers | targets | removed
    callers, providers, missing = {}, {}, defaultdict(list)
    for r in csv_rows(data / "decls.csv.gz"):
        p, name = r["file"], r["decl"]
        if p not in selected:
            continue
        if p in importers:
            callers[name] = (p, r["in_cone"] == "true", int(r["start_line"]), int(r["end_line"]))
        if p in targets:
            providers[name] = p
        if p in removed:
            missing[p].append(r)
    return callers, providers, missing


def kernel_edges(data, pairs, callers, providers):
    edges = defaultdict(set)
    with gzip.open(data / "decl_edges.csv.gz", "rt", newline="") as stream:
        reader = csv.reader(stream)
        assert next(reader) == ["src", "src_kind", "dst", "dst_kind", "via"]
        for src, sk, dst, dk, via in reader:
            if dk != "decl" or dst not in providers or sk != "decl" or src not in callers:
                continue
            caller, used, _, _ = callers[src]
            pair = (caller, providers[dst])
            if pair in pairs:
                assert not used, (src, dst)
                edges[pair].add((src, dst, via))
    return edges


def written(name):
    return PRIVATE.sub("", name)


def source_sites(proof, paths):
    return {p: index_file((proof / p).read_text().splitlines(), p) for p in sorted(paths)}


COMMENT_TOKEN = re.compile(r'/-|-/')
CODE_TOKEN = re.compile(r'/-|--|"(?:\\.|[^"\\])*"')


def mask_noncode(lines):
    output, depth = [], 0
    for line in lines:
        chars = list(line)
        pos = 0
        while pos < len(line):
            token = (COMMENT_TOKEN if depth else CODE_TOKEN).search(line, pos)
            if depth:
                end = token.end() if token else len(line)
                chars[pos:end] = " " * (end-pos)
            if token is None:
                break
            start, end = token.span()
            if token[0] == "--":
                chars[start:] = " " * (len(line)-start)
                break
            chars[start:end] = " " * (end-start)
            if token[0] == "/-":
                depth += 1
            elif token[0] == "-/":
                depth -= 1
            pos = end
        output.append("".join(chars))
    return output


def literal_refs(lines, decl, candidates):
    """Exact qualified or namespace-resolved tokens in a named caller's type or body."""
    tails = {n.rsplit(".", 1)[-1] for n in candidates}
    local, hits = set(), set()
    for i in range(decl.line, decl.stop):
        line = lines[i][decl.head:] if i == decl.line else lines[i]
        for binder in BOUND.finditer(line):
            local.update((binder[1] or binder[2]).split())
        for token in NAME_RE.findall(line):
            if token.rsplit(".", 1)[-1] not in tails or token.partition(".")[0] in local:
                continue
            if token.startswith("_root_."):
                options = {token[7:]}
            else:
                options = {scope(ns, token) for ns in ancestors(decl.ns)}
                options.update(scope(scope(ns, op), token) for ns in ancestors(decl.ns) for op in decl.opens)
            matches = options & candidates.keys()
            if len(matches) == 1:
                name = matches.pop()
                if len(candidates[name]) == 1:
                    hits.add((next(iter(candidates[name])), name, i+1))
    return hits


def retained_evidence(proof, original_proof, data, out, original, upstream, targets, removed):
    baseline = import_pairs(FROZEN, original & upstream, targets)
    current = import_pairs(out, upstream, targets)
    pairs = baseline | current
    importers = {p for p, _ in pairs}
    callers, providers, missing = owners(data, importers, targets, removed)
    edges = kernel_edges(data, pairs, callers, providers)
    sites = source_sites(proof, importers | targets)
    target_names = {p: {d.name for d in sites[p] if not d.private} for p in targets}
    by_caller = defaultdict(set)
    for p, target in current:
        by_caller[p].add(target)
    old_names = {(p, written(n)): (n, used) for n,(p,used,_,_) in callers.items()}
    # Validate each original source file used to compare command spans with the upstream text.
    old_hashes = {r["path"]: r["sha256"] for r in read_rows(FROZEN / "inventory.tsv.gz") if r["category"]=="Novel"}
    for p in removed:
        assert digest(original_proof / p) == old_hashes[p]
    evidence, historical, unmatched = defaultdict(set), Counter(), set()
    for p in sorted(importers):
        lines = (proof / p).read_text().splitlines()
        if p in original:
            assert digest(original_proof / p) == old_hashes[p]
            old_lines = (original_proof / p).read_text().splitlines()
        else:
            old_lines = []
        candidates = defaultdict(set)
        for target in by_caller[p]:
            for name in target_names[target]:
                candidates[name].add(target)
            for src, dst, via in edges[p, target]:
                historical[p, target] += 1
                old_path, used, lo, hi = callers[src]
                assert old_path == p and not used
                callee = written(dst)
                segment = old_lines[lo-1:hi]
                # Locate the entire original command, including anonymous/generated callers.
                if segment and callee in target_names[target]:
                    starts = [i for i,line in enumerate(lines) if line==segment[0] and lines[i:i+len(segment)]==segment]
                    if len(starts)==1:
                        evidence[p,target].add((src, dst, "original unused", "unchanged caller; compiled "+via, starts[0]+1))
                        continue
                unmatched.add((p,target,src,dst,via))
        if candidates:
            masked = mask_noncode(lines)
            for d in sites[p]:
                source, used = old_names.get((p,d.name),(d.name,None))
                status = "new or unmapped" if used is None else ("original used" if used else "original unused")
                for target, name, line in literal_refs(masked, d, candidates):
                    evidence[p,target].add((source, name, status, "upstream source token", line))
    # Preserve historical edges even when the changed upstream caller could not be confirmed.
    witness_rows = [(p,t,src,dst,status,method,line) for (p,t),rs in evidence.items()
                    for src,dst,status,method,line in rs]
    witness_rows.extend((p,t,s,d,"original unused","original edge; upstream unconfirmed "+via,"")
                        for p,t,s,d,via in unmatched)
    table(out/"importer-references.tsv.gz", ["importer","target","caller","declaration","caller_usage","evidence","upstream_line"],
          sorted(witness_rows))
    labels, tally = [], Counter()
    by_target = defaultdict(list)
    pair_rows = []
    for p,t in sorted(pairs, key=lambda pair:(pair[1],pair[0])):
        rs = evidence[p,t]
        positive = {(s,d) for s,d,status,_,_ in rs if status=="original unused"}
        other = {(s,d) for s,d,status,_,_ in rs if status!="original unused"}
        pair_rows.append((t,p,int((p,t) in baseline),int((p,t) in current),len(edges[p,t]),len(positive),len(other)))
        if (p,t) in current:
            by_target[t].append((p,len(positive),len(other),historical[p,t]))
    table(out/"retained-importers.tsv.gz", ["target","importer","original_direct","upstream_direct","original_kernel_edge_kinds",
          "upstream_supported_unused_caller_pairs","other_source_pairs"],pair_rows)
    for t in sorted(targets):
        current_rows = by_target[t]
        pos = sum(n>0 for _,n,_,_ in current_rows)
        other = sum(n>0 for _,_,n,_ in current_rows)
        hist = sum(n>0 for _,_,_,n in current_rows)
        label = "referenced by an unused declaration" if hist else "conduit only"
        labels.append((t,label,len(current_rows),pos,other,hist,"unverified"))
        tally[label] += 1
        tally["conduits_with_upstream_source_candidate"] += bool((other or pos) and not hist)
        tally["referenced_with_upstream_unused_caller_evidence"] += bool(hist and pos)
    table(out/"retained-unused.tsv.gz",["path","label","upstream_direct_importers","importers_with_unused_witness",
          "importers_with_other_source_reference","importers_with_original_kernel_reference","status"],labels)
    assert sum(tally[k] for k in ("conduit only", "referenced by an unused declaration")) == len(targets)
    return missing, dict(tally)


def removed_files(proof, original_proof, missing, trace, out):
    names = {written(r["decl"]) for rs in missing.values() for r in rs}
    tails = {n.rsplit(".",1)[-1] for n in names}
    hits = defaultdict(list)
    for path in sorted((proof/"src").rglob("*.lean")):
        source = path.read_text()
        for alias in ALIAS_HEADER.finditer(source):
            if alias[1].rsplit(".",1)[-1] in tails:
                raise ValueError(f"Alias requires a namespace check: {alias[1]} in {path}")
        headers = [m for m in HEADER.finditer(source) if m[1].rsplit(".",1)[-1] in tails]
        if not headers:
            continue
        ds = index_file(source.splitlines(),0)
        # Independently look for command keywords and suffixes anywhere on the line.
        # Reject a "gone" result if the scoped index missed a candidate header.
        seen = {(d.line+1, d.name.rsplit(".",1)[-1]) for d in ds}
        for m in headers:
            candidate = (source.count("\n", 0, m.start(1))+1, m[1].rsplit(".",1)[-1])
            if candidate not in seen:
                raise ValueError(f"Unindexed candidate {candidate} in {path}")
        for d in ds:
            tail = d.name.rsplit(".",1)[-1]
            if tail in tails:
                hits[tail].append((path.relative_to(proof).as_posix(),d.line+1,d.private,d.name))
    rows, summary = [], []
    for p, rs in sorted(missing.items()):
        present, used_present = 0, 0
        old_lines = (original_proof / p).read_text().splitlines()
        for r in sorted(rs,key=lambda r:(int(r["start_line"]),r["decl"])):
            name = r["decl"]
            sites = hits[written(name).rsplit(".",1)[-1]]
            # A module-private kernel identity includes its owner path.
            exact = [(q,line) for q,line,priv,qualified in sites if qualified==written(name) and not priv and not name.startswith("_private.")]
            old_command = old_lines[int(r["start_line"])-1:int(r["end_line"])]
            copied = []
            for q, line, private, qualified in sites:
                if (q,line) in exact:
                    continue
                new_lines = (proof / q).read_text().splitlines()
                if new_lines[line-1:line-1+len(old_command)] == old_command:
                    copied.append((q,line))
            locations = exact + copied
            present += bool(locations)
            used_present += bool(locations) and r["in_cone"]=="true"
            status = "same public name" if exact else ("same command, different identity" if copied else "gone under original name")
            rows.append((p,name,r["start_line"],r["in_cone"],status,
                         "|".join(f"{q}#L{n}" for q,n in locations),
                         "|".join(f"{q}#L{n}" for q,n,_,qualified in sites if qualified==written(name) and (q,n) not in locations)))
        label = "elsewhere" if present==len(rs) else ("mixed" if present else "gone under original names")
        summary.append((p,int(p in trace),len(rs),sum(r["in_cone"]=="true" for r in rs),present,used_present,label))
    table(out/"removed-used-files.tsv",["original_path","trace_reached","declarations","kernel_used_declarations",
          "found_elsewhere","kernel_used_found_elsewhere","status"],summary)
    table(out/"removed-used-declarations.tsv",["original_path","original_kernel_name","original_line","kernel_used",
          "source_name_status","upstream_declaration_locations","same_written_name_different_identity"],rows)
    return dict(Counter(row[-1] for row in summary)),len(rows),sum(row[4] for row in summary)


def analyze(proof, original_proof, data, out, paths, gated):
    counts, targets, removed, masks = gated
    original, upstream, traced = paths
    table(out / "kernel-file-usage.tsv.gz", ["original_path", "upstream_retained", "trace_reached", "target_mask"],
          ((p, int(p in upstream), int(p in traced), masks.get(p, 0)) for p in sorted(original)))
    missing, labels = retained_evidence(proof, original_proof, data, out, paths[0],paths[1],targets,removed)
    statuses, n, survivors = removed_files(proof, original_proof, missing, paths[2],out)
    result = dict(counts=counts, source_classification=labels, removed_status=statuses,
                  removed_declarations=n, removed_declarations_elsewhere=survivors, input_sha256=DIGESTS)
    put_json(out/"kernel-counts.json",result)
    return result
