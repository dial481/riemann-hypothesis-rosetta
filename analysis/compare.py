"""Post-freeze comparisons. These inputs are never read by the independent analysis."""
import argparse
import csv
import gzip
import json
import re
import sys
from array import array
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

from check import verify_frozen
from common import PROJECT, RESULTS, digest, put_json, read_rows, table

URLS = {
    "shore/constants.csv.gz": ("2964f5236046325ac7884906cb9517b0aa582330dd48a07eef291cb579444820",
                               "https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1/constants.csv.gz"),
    "shore/per-theorem.tsv": ("dc74e65916b6b945be788657001859eb7f1666c863e10d92c5c8ef0be1651606",
                              "https://raw.githubusercontent.com/james-shore/rh-proof-dependencies/70fbb2fc21fed8de3c02d9f6df0b6067bf22e879/data/per-theorem.tsv"),
    "pr-graph.json.gz": ("82c88d25d909a1399c754b87ce298e1939ab0908aeb4766fdac8a57387c71dc5",
                         "https://photos.proofsandreasons.io/alp-graph/rh/alp-declaration-graph-used-by-rh.json.gz"),
    "atlas/data/model.json": ("8c85bd83b65afa31e330392acd81124397815d6d072a51dca19633936c4af544",
                              "https://raw.githubusercontent.com/nasqret/riemann-rev/d53b3804bd013df4cf9af3b4087728148c90c9bd/data/model.json")
}


def site(module, name):
    # Use explicit file and source-level name. Preserve symbol spelling and
    # remove only Lean's module-specific private prefix.
    name = re.sub(r"^_private\..*?\.\d+\.", "", name)
    return sys.intern(module), sys.intern(name)


def compare_sets(a, b):
    return {"ours": len(a), "theirs": len(b), "shared": len(a & b), "ours_only": len(a - b),
            "theirs_only": len(b - a)}


def check_input(file, sha, url, fetch):
    if file.is_file() and digest(file) == sha:
        return
    if not fetch:
        raise ValueError(f"Missing or incorrect comparison input: {file}")
    file.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=file.parent) as temp:
        downloaded = Path(temp) / "download"
        urlretrieve(url, downloaded)
        if digest(downloaded) != sha:
            raise ValueError(f"Unexpected digest for downloaded input: {file.name}")
        downloaded.replace(file)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("evidence_dir", type=Path)
    cli.add_argument("--fetch", action="store_true")
    a = cli.parse_args()
    verify_frozen()
    for name, (sha, url) in URLS.items():
        check_input(a.evidence_dir / name, sha, url, a.fetch)
    ours = {site(r["module"], r["name"]): int(r["line"]) for r in read_rows(RESULTS / "rh-trace.tsv.gz")}
    ours_set = set(ours)
    spine = list(read_rows(RESULTS / "spine.tsv"))
    spine_modules = {r["module"] for r in spine}
    paths = json.load(gzip.open(RESULTS / "spine-witnesses.json.gz", "rt"))
    chain_sites = {site(w["module"], w["name"]) for chain in paths.values() for w in chain}
    atlas = json.loads((a.evidence_dir / "atlas/data/model.json").read_text())
    assert atlas["pins"]["mirror_commit"] == PROJECT
    atlas_modules = {r["module"] for r in atlas["nodes"] if r.get("module")}
    atlas_positions = defaultdict(set)
    for key, number in ours.items():
        if key[0] in atlas_modules:
            atlas_positions[key[0], number].add(key)
    masks, shore_lines = {}, {}
    shore_mathlib = set()
    with gzip.open(a.evidence_dir / "shore/constants.csv.gz", "rt") as stream:
        for r in csv.DictReader(stream):
            mask = int(r["thm_mask"] or 0)
            if r["origin"] == "mathlib" and mask & 1:
                shore_mathlib.add(r["module"])
            if r["origin"] != "project" or not r["decl"] or not r["file"] or r["shared_aux"] == "true" or not mask:
                continue
            owner = r["file"].removeprefix("src/").removesuffix(".lean").replace("/", ".")
            key = site(owner, r["decl"])
            masks[key] = masks.get(key, 0) | mask
            if key in chain_sites and r["start_line"]:
                shore_lines[key] = (int(r["start_line"]), int(r["end_line"]))
    shore = {k for k, v in masks.items() if v & 1}
    roots = list(read_rows(a.evidence_dir / "shore/per-theorem.tsv"))
    per_target = []
    for i, r in enumerate(roots):
        ks = {k for k, v in masks.items() if v & (1 << i)}
        per_target.append({"theorem": r["theorem"], "published": int(r["project_decls"]),
                           "from_mask": len(ks), "overlap_with_our_RH": len(ours_set & ks)})

    pr, ids, outgoing, pr_lines = set(), {}, {}, {}
    node_count = 0
    with gzip.open(a.evidence_dir / "pr-graph.json.gz", "rt") as stream:
        metadata = json.loads(stream.readline().rstrip().removesuffix(",") + "}")["meta"]
        depths = array("i", [-1]) * metadata["declarations"]
        for line in stream:
            if not line.startswith('{"id":'):
                continue
            r = json.loads(line.rstrip().removesuffix(","))
            k = site(r["file"].removesuffix(".lean").replace("/", "."), r["name"])
            pr.add(k)
            node_count += 1
            depths[r["id"]] = r["steps_below_riemannHypothesis"]
            if k[0] in atlas_modules:
                atlas_positions[k[0], r["line"]].add(k)
            if k in chain_sites or k[0] in atlas_modules:
                ids[k] = r["id"]
                pr_lines[k] = r["line"]
                outgoing[k] = set(r["uses_in_body"]) | set(r["uses_in_signature"])
    assert node_count == metadata["declarations"]
    all_edges, matched_edges, absent_edges, missing_sites = set(), set(), set(), set()
    spine_comparison = []
    for r in spine:
        m = r["module"]
        k = site(m, r["anchor"])
        sequence = [site(w["module"], w["name"]) for w in paths[m]]
        matched = absent = missing = 0
        for edge in zip(sequence, sequence[1:]):
            x, y = edge
            all_edges.add(edge)
            if x not in ids or y not in ids:
                missing_sites.add(edge)
                missing += 1
            elif ids[y] in outgoing[x]:
                matched_edges.add(edge)
                matched += 1
            else:
                absent_edges.add(edge)
                absent += 1
        sl = shore_lines.get(k, (0, 0))
        spine_comparison.append((r["rank"], m, r["anchor"], r["line"], int(k in shore), int(k in pr),
                                 int(sl[0] <= int(r["line"]) <= sl[1]), pr_lines.get(k, ""), matched, absent, missing))
    table(RESULTS / "comparison-spine.tsv", ["rank","module","anchor","line","shore_RH_site","pr_RH_site",
          "in_shore_source_range","pr_line","pr_chain_edges_confirmed","pr_chain_edges_absent","pr_chain_edges_unmatched_endpoint"],spine_comparison)
    table(RESULTS / "comparison-witness-edges.tsv", ["caller_module","caller","dependency_module","dependency","pr_status"],
          ((*x,*y, "confirmed" if (x,y) in matched_edges else "unmatched endpoint" if (x,y) in missing_sites else "edge absent")
           for x,y in sorted(all_edges)))
    table(RESULTS / "comparison-disagreements.tsv.gz", ["module","name","source_trace","shore_RH","pr_RH"],
          ((*k, int(k in ours), int(k in shore), int(k in pr)) for k in sorted((ours_set | shore | pr) - (ours_set & shore & pr))))
    # External-only alternative shortest paths for selected anchors whose independent
    # source trail has a direct edge absent from the compiled graph.
    bad = [row for row in spine_comparison if row[-2] or row[-1]]
    prev = array("i", [-1]) * node_count
    with gzip.open(a.evidence_dir / "pr-graph.json.gz", "rt") as stream:
        for line in stream:
            if line.startswith('{"id":'):
                data = json.loads(line.rstrip().removesuffix(","))
                i = data["id"]
                for j in data["uses_in_body"] + data["uses_in_signature"]:
                    if prev[j] == -1 and depths[j] == depths[i] + 1:
                        prev[j] = i
    wanted, chains = set(), {}
    for row in bad:
        k = site(row[1], row[2])
        if k not in ids:
            continue
        walk = [ids[k]]
        while depths[walk[-1]] > 0:
            ancestor = prev[walk[-1]]
            assert ancestor != -1
            walk.append(ancestor)
        wanted.update(walk)
        chains[row[1]] = list(reversed(walk))
    alt = {}
    with gzip.open(a.evidence_dir / "pr-graph.json.gz", "rt") as stream:
        for line in stream:
            if line.startswith('{"id":'):
                data = json.loads(line.rstrip().removesuffix(","))
                if data["id"] in wanted:
                    alt[data["id"]] = {k:data[k] for k in ("id","name","file","line")}
    put_json(RESULTS / "comparison-alternative-paths.json", {m:[alt[i] for i in walk] for m,walk in chains.items()})
    atlas_rows = []
    atlas_keys = {}
    for r in atlas["nodes"]:
        if not r.get("module") or not r.get("declaration"):
            continue
        k = site(r["module"], r["declaration"])
        qualified = {x for x in atlas_positions[k[0],r["lines"][0]] if x[1].endswith("." + k[1])}
        if len(qualified) == 1 and k not in ours and k not in pr and k not in shore:
            k = qualified.pop()
        atlas_keys[r["id"]] = k
        atlas_rows.append((r["id"],r["component"],*k,r["lines"][0],ours.get(k,""),int(k in shore),int(k in pr),
                           int(k[0] in spine_modules)))
    table(RESULTS / "comparison-atlas.tsv", ["atlas_id","component","module","declaration","atlas_line","our_trace_line",
          "shore_RH","pr_RH","spine_module"], atlas_rows)
    edge_rows = []
    for edge in atlas["edges"]:
        x, y = (atlas_keys.get(edge[n]) for n in ("from", "to"))
        status = "concept endpoint" if x is None or y is None else (
            "outside RH graph" if x not in ids or y not in ids else (
                "direct" if ids[y] in outgoing[x] else "no direct edge"))
        edge_rows.append((edge["from"], edge["to"], edge["relation"], status))
    table(RESULTS / "comparison-atlas-edges.tsv", ["from", "to", "atlas_relation", "pr_RH_status"], edge_rows)
    inventory = list(read_rows(RESULTS / "inventory.tsv.gz"))
    unreachable = {r["module"] for r in read_rows(RESULTS / "unreachable.tsv.gz")}
    lib = {r["module"] for r in inventory if r["category"] == "Mathlib" and r["module"] not in unreachable}
    archive_modules = {r["module"] for r in inventory if r["category"] == "Novel" and r["module"] not in unreachable}
    pr_mods, shore_mods, own_mods = ({k[0] for k in ks} for ks in (pr,shore,ours))
    summary = {"input_sha256": {k:v[0] for k,v in URLS.items()}, "own_source_sites": len(ours_set),
               "shore_sites": compare_sets(ours_set, shore), "pr_sites": compare_sets(ours_set, pr),
               "shore_vs_pr_sites": compare_sets(shore,pr),
               "shore_modules":compare_sets(own_mods,shore_mods), "pr_modules":compare_sets(own_mods,pr_mods),
               "shore_modules_outside_imports":sorted(shore_mods-archive_modules),
               "pr_modules_outside_imports":sorted(pr_mods-archive_modules),
               "shore_mathlib_modules":len(shore_mathlib), "reachable_mathlib_modules": len(lib),
               "shore_mathlib_outside_imports":sorted(shore_mathlib-lib), "shore_per_theorem":per_target,
               "pr_reported_nodes":node_count, "pr_reported_edges":metadata["links"],
               "spine_shore_anchors":sum(x[4] for x in spine_comparison),
               "spine_pr_anchors":sum(x[5] for x in spine_comparison),
               "both_spine_anchors":sum(x[4]*x[5] for x in spine_comparison),
               "pr_complete_chains":sum(not(x[-1] or x[-2]) for x in spine_comparison),
               "pr_unique_edges":[len(all_edges),len(matched_edges),len(absent_edges),len(missing_sites)],
               "atlas_pins":len(atlas_rows), "atlas_modules":len({x[2] for x in atlas_rows}),
               "atlas_modules_inside_imports":sum(m in archive_modules for m in {x[2] for x in atlas_rows}),
               "atlas_spine_modules":len({x[2] for x in atlas_rows if x[-1]}),
               "atlas_named_matches":sum(x[5]!="" for x in atlas_rows),
               "atlas_exact_lines":sum(x[4]==x[5] for x in atlas_rows),
               "atlas_components_with_trace":len({x[1] for x in atlas_rows if x[5]!=""}),
               "atlas_components_with_spine":len({x[1] for x in atlas_rows if x[-1]}),
               "atlas_component_count":len(atlas["components"])}
    put_json(RESULTS / "comparison.json", summary)
    verify_frozen()


if __name__ == "__main__":
    main()
