"""Post-freeze benchmark of two published source tracers against the compiled RH sets."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

from check import verify_frozen
from common import RESULTS, put_json, read_rows
from compare import URLS, check_input, site


def overlap(predicted, reference):
    matched = len(predicted & reference)
    return {"predicted": len(predicted), "reference": len(reference), "matched": matched,
            "precision": matched / len(predicted), "recall": matched / len(reference)}


def names_digest(names):
    checksum = hashlib.sha256()
    for name in sorted(names):
        checksum.update((name + "\n").encode("utf-8"))
    return checksum.hexdigest()


def pr_references(file, root_module, root_name, depth):
    # The pinned JSON stores one complete node per line. Node IDs index the edges.
    nodes = {}
    root_ids = []
    with gzip.open(file, "rt") as stream:
        for line in stream:
            if line.startswith('{"id":'):
                node = json.loads(line.rstrip().removesuffix(","))
                module = node["file"].removesuffix(".lean").replace("/", ".")
                _, name = site(module, node["name"])
                nodes[node["id"]] = name, node["uses_in_body"] + node["uses_in_signature"]
                if (module, name) == (root_module, root_name):
                    root_ids.append(node["id"])
    if len(root_ids) != 1:
        raise ValueError(f"Expected one compiled root for {root_name}, found {len(root_ids)}")
    frontier = set(root_ids)
    reached = frontier.copy()
    for _ in range(depth):
        frontier = {d for n in frontier for d in nodes[n][1]} - reached
        reached.update(frontier)
    return {name for name, _ in nodes.values()}, {nodes[n][0] for n in reached}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("reference_dir", type=Path)
    cli.add_argument("cadamcat_cone", type=Path)
    cli.add_argument("jae_depth12", type=Path)
    args = cli.parse_args()
    verify_frozen()
    for key in ("shore/constants.csv.gz", "pr-graph.json.gz"):
        sha, url = URLS[key]
        check_input(args.reference_dir / key, sha, url, False)
    ours = {r["name"] for r in read_rows(RESULTS / "rh-trace.tsv.gz")}
    with args.cadamcat_cone.open() as f:
        records = csv.reader(f, delimiter="\t")
        first = next(records, None)
        if first != ["0", "riemannHypothesis"]:
            raise ValueError("Expected cadamcat's riemannHypothesis cone")
        cadamcat = {name for _, name in records}
        cadamcat.add(first[1])
    root = "UpperTheory.FinalTheorems.everyCharacter"
    with args.jae_depth12.open() as f:
        jae_nodes = json.load(f)["nodes"]
    if {n for n, r in jae_nodes.items() if r["d"] == 0} != {root} or max(r["d"] for r in jae_nodes.values()) != 12:
        raise ValueError("Expected jae-63's published root and depth")
    jae = set(jae_nodes)
    root_module = jae_nodes[root]["mod"]
    del jae_nodes
    shore = set()
    with gzip.open(args.reference_dir / "shore/constants.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            if (r["origin"] == "project" and r["decl"] and r["file"] and
                    r["shared_aux"] != "true" and int(r["thm_mask"] or 0) & 1):
                shore.add(site("", r["decl"])[1])
    pr, bounded = pr_references(args.reference_dir / "pr-graph.json.gz", root_module, root, 12)
    rows = {label: {"shore_RH": overlap(names, shore), "proofs_and_reasons_RH": overlap(names, pr)}
            for label, names in (("rosetta", ours), ("cadamcat", cadamcat), ("jae_63", jae))}
    put_json(RESULTS / "comparison-peer-traces.json",
             {"identity": "source-level declaration name without module, normalized for private prefixes in compiled data",
              "cadamcat_commit": "b3e1e2df268c5d81a54594ef405dd4f7d51ce917",
              "jae_63_commit": "0434143d80c94d491e2228e234507d38dfcb57d7",
              "sorted_names_sha256": {"cadamcat": names_digest(cadamcat), "jae_63": names_digest(jae)},
              "whole_RH": rows, "jae_63_depth12_from_everyCharacter": overlap(jae, bounded)})
    verify_frozen()


if __name__ == "__main__":
    main()
