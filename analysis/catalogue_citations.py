"""Locate each exact catalogue identifier in the source files cited for its entry."""
import csv
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path

from check_witness_edges import CONSTANTS_SHA256
from common import SEG, content_digest, digest, read_rows
from odesky_coverage import OWNER_SHA
from trace import index_file
from upstream_kernel import mask_noncode

MATHLIB_PREFIX = "../.lake/packages/mathlib/"


def citation_site(ref):
    file, _, line = ref.partition(":")
    path = file.removeprefix(MATHLIB_PREFIX) if file.startswith(MATHLIB_PREFIX) else "src/" + file
    return path, int(line) if line else None


def locate(entries, proof, mathlib, decls, constants):
    inventory = Path("results/inventory.tsv.gz")
    expected = json.loads(Path("results/independent-content-sha256.json").read_text())[inventory.name]
    if content_digest(inventory) != expected or digest(decls) != OWNER_SHA:
        raise ValueError("Frozen inventory or compiled declaration digest mismatch")
    files = {citation_site(ref)[0] for _,refs in entries.values() for ref in refs}
    names = {n for ns,_ in entries.values() for n in ns}
    original = {r["path"]:r for r in read_rows(inventory) if r["path"] in files}
    # Key on qualified source identity. Retain unique dot-boundary suffixes
    # separately, for catalogue spellings relative to a namespace.
    tails = {n.rsplit(".",1)[-1] for n in names}
    candidates = defaultdict(lambda: defaultdict(set))
    field = re.compile(r"^( +)(" + SEG + r")\s*(?::|[(\[{])")
    for path,r in sorted(original.items()):
        file = (proof if r["category"] == "Novel" else mathlib) / path
        if digest(file) != r["sha256"]:
            raise ValueError(f"Source checksum mismatch for {path}")
        lines = mask_noncode(file.read_text().splitlines())
        for decl in index_file(lines, path):
            if decl.name.rsplit(".",1)[-1] in tails:
                candidates[path][decl.name].add(decl.line + 1)
            if decl.kind not in {"structure", "class"}:
                continue
            # Fields appear at the outermost indented field level after where.
            body = lines[decl.line:decl.stop]
            where = next((i for i,l in enumerate(body) if re.search(r"\bwhere\s*$", l)), None)
            if where is None:
                continue
            matches = [(i,m) for i,l in enumerate(body[where+1:], where+1) if (m := field.match(l))]
            indent = min((len(m[1]) for _,m in matches), default=0)
            for i,m in matches:
                if len(m[1]) == indent and m[2] in tails:
                    candidates[path][decl.name + "." + m[2]].add(decl.line + i + 1)

    wanted = names | {name for file in candidates.values() for name in file}
    owners = {}
    with gzip.open(decls, "rt", newline="") as stream:
        for r in csv.DictReader(stream):
            if r["origin"] == "project" and r["decl"] in wanted:
                if r["decl"] in owners:
                    raise ValueError(f"Ambiguous compiled owner {r['decl']}")
                owners[r["decl"]] = (r["file"], int(r["start_line"]))
    if digest(constants) != CONSTANTS_SHA256:
        raise ValueError("Compiled constants digest mismatch")
    known_constants = set()
    fields = {}
    with gzip.open(constants, "rt", newline="") as stream:
        for r in csv.DictReader(stream):
            name = r["name"]
            if name not in wanted:
                continue
            known_constants.add(name)
            if (r["origin"] == "project" and r["shared_aux"] == "false"
                    and r["aux_rule"] == "nested" and r["decl"] == name.rpartition(".")[0]):
                fields[name] = (r["decl"], r["file"], int(r["start_line"]))
    # Verify that the graph endpoint really is a structure/class in this release.
    parents = {key for key, _, _ in fields.values()}
    with gzip.open(decls, "rt", newline="") as stream:
        structures = {(r["decl"], r["file"], int(r["start_line"])) for r in csv.DictReader(stream)
                      if r["decl"] in parents and r["command_kind"] in {"structure", "class"} and r["origin"] == "project"}
    fields = {name: row for name, row in fields.items() if row in structures}
    rows = []
    endpoints = {}
    for url,(entry_names,refs) in sorted(entries.items()):
        endpoints[url] = {}
        cited = {citation_site(ref)[0] for ref in refs}
        for name in entry_names:
            identities = {key for path in cited for key in candidates[path]
                          if key == name or key.endswith("." + name)}
            if name in identities or name in owners or name in fields:
                identity, spelling = name, "exact name"
            elif len(identities) == 1:
                identity, spelling = identities.pop(), "unique source suffix"
            else:
                identity, spelling = "", "ambiguous suffix" if identities else "unresolved"
            matches = []
            for ref in refs:
                path, line = citation_site(ref)
                for actual in candidates[path].get(identity, ()):
                    quality = "exact line" if actual == line else "file without line" if line is None else "off by line"
                    matches.append((quality, path, actual, ref))
            owner, owner_line = owners.get(identity, ("",""))
            graph_name = identity if owner else ""
            if not owner and identity in fields:
                graph_name, owner, owner_line = fields[identity]
            if graph_name:
                endpoints[url][name] = graph_name
            alternatives = set()
            if not identity and name not in known_constants:
                for ref in refs:
                    path, line = citation_site(ref)
                    for actual, lines in candidates[path].items():
                        if line in lines and actual.rsplit(".",1)[-1] == name.rsplit(".",1)[-1]:
                            alternatives.add(f"{actual}@{path}:{line}")
            order = {"exact line": 0, "file without line": 1, "off by line": 2}
            status = min((q for q, *_ in matches), key=order.get, default="miss")
            rows.append((url,name,"|".join(refs),status,
                         "|".join(sorted({f"{p}:{n}" for _,p,n,_ in matches})),
                         "|".join(sorted({ref for q,_,_,ref in matches if q == status})),
                         identity,spelling,owner,owner_line,graph_name,
                         "structure field" if identity in fields else "declaration" if owner else "",
                         "|".join(sorted(alternatives))))
    return rows, endpoints
