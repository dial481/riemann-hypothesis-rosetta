"""Compare two pinned module graphs and intersect source paths with the frozen trace."""
import argparse
import gzip
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from check import line_header, verify_frozen
from common import digest, put_json, read_rows, table
from inventory import ORIGINAL_PINS, UPSTREAM_PINS
import upstream_kernel as kernel

FROZEN = Path("results")
PIN, LIB = (p[0] for p in UPSTREAM_PINS)
SHORT = PIN[:8]
OUTPUTS = (
    "combined-communities.json", "combined-membership.tsv.gz", "communities.json",
    "community-overlap.tsv", "directories.tsv.gz", "external.tsv", "family-edges.tsv",
    "import-map.svg", "imports.json.gz", "inventory.tsv.gz", "longest-paths.json",
    "metrics.tsv.gz", "path-status.tsv.gz", "provenance.json", "spine-survival.tsv",
    "structure.json", "unreachable.tsv.gz",
) + kernel.OUTPUTS


def proof_paths(source):
    root = source / "src"
    return {p.relative_to(source).as_posix() for p in root.rglob("*.lean")}


def cross_tab(source):
    original = {r["module"]: r["path"] for r in read_rows(FROZEN / "inventory.tsv.gz") if r["category"] == "Novel"}
    reached = {original[r["module"]] for r in read_rows(FROZEN / "rh-trace.tsv.gz")}
    paths = set(original.values())
    upstream = proof_paths(source)
    assert len(paths) == len(original) == 175187
    removed, retained = paths - upstream, paths & upstream
    counts = (len(removed), len(removed - reached), len(removed & reached), len(retained - reached))
    if counts != (25792, 25762, 30, 15249):
        raise ValueError(f"Stopping before upstream graph analysis: removal gate returned {counts}")
    return paths, upstream, reached


def metrics(directory):
    return {r["module"]: r for r in read_rows(directory / "metrics.tsv.gz") if r["community"]}


def communities(old, new, out):
    shared = sorted(old.keys() & new.keys())
    counts = Counter((int(old[m]["community"]), int(new[m]["community"])) for m in shared)
    rows = sorted({int(r["community"]) for r in old.values()})
    cols = sorted({int(r["community"]) for r in new.values()})
    matrix = np.array([[counts[i, j] for j in cols] for i in rows], dtype=np.int64)
    ri, ci = linear_sum_assignment(matrix, maximize=True)
    matched = {(rows[i], cols[j]) for i, j in zip(ri, ci) if matrix[i, j]}
    table(out / "community-overlap.tsv", ["original_community", "upstream_community", "shared_modules", "aligned"],
          ((i, j, n, int((i, j) in matched)) for (i, j), n in sorted(counts.items())))
    return len(shared), sum(counts[pair] for pair in matched), counts


def verify_imports(out, proof, mathlib):
    with gzip.open(out / "imports.json.gz", "rt") as f:
        edges = json.load(f)
    for row in read_rows(out / "inventory.tsv.gz"):
        root = proof if row["category"] == "Novel" else mathlib
        names = [n.replace("«", "").replace("»", "") for n in line_header((root / row["path"]).read_text())]
        if sorted(set(names)) != edges[row["module"]] or len(names) != int(row["import_commands"]):
            raise ValueError(f'Header scans disagree at {row["path"]}')


def verify_cuts(directory, metric, names):
    with gzip.open(directory / "imports.json.gz", "rt") as f:
        adj = json.load(f)
    def reached(skip):
        visited = {"Main"}
        todo = ["Main"]
        while todo:
            for module in adj[todo.pop()]:
                if module != skip and module not in visited:
                    visited.add(module)
                    todo.append(module)
        return visited
    base = reached(None)
    for m in names:
        if m in metric:
            lost = (base - reached(m) - {m}) & metric.keys()
            assert len(lost) == int(metric[m]["disconnected_novel"]), m


def render(dest, out, old_paths, new_paths, reached, kernel_result):
    old, new = metrics(FROZEN), metrics(out)
    sp = list(read_rows(FROZEN / "spine.tsv"))
    assert len(sp) == len({s["path"] for s in sp}) == 200
    table(out / "path-status.tsv.gz", ["path", "original", "upstream", "original_trace_reached"],
          ((p, int(p in old_paths), int(p in new_paths), int(p in reached) if p in old_paths else "")
           for p in sorted(old_paths | new_paths)))
    fields = ("import_rank", "disconnected_novel", "community")
    def spine_rows():
        for s in sp:
            m = s["module"]
            yield (s["rank"], s["path"], int(s["path"] in new_paths), int(m in new),
                   *(old[m][k] for k in fields), *(new.get(m, {}).get(k, "") for k in fields))
    table(out / "spine-survival.tsv", ["original_spine_rank", "path", "upstream_present", "upstream_reachable",
          *["original_" + k for k in fields], *["upstream_" + k for k in fields]], spine_rows())
    original, upstream = [json.loads((d / "structure.json").read_bytes()) for d in (FROZEN, out)]
    shared, aligned, counts = communities(old, new, out)
    row_src, = [r["module"] for r in sp if r["path"].endswith("/IntegralStructures/RowSrc.lean")]
    leads = set(m for summary in (original, upstream) for m, _ in summary["top_novel_cuts"][:5])
    for directory, metric in [(FROZEN, old), (out, new)]:
        verify_cuts(directory, metric, leads | {row_src})
    removed, retained = old_paths - new_paths, old_paths & new_paths
    absent = [s for s in sp if s["path"] not in new_paths]
    def path(m):
        return "src/" + m.replace(".", "/") + ".lean"
    def link(m, pin):
        return f'[{m.split(".")[-1]}](https://github.com/leanprover-community/riemann-hypothesis/blob/{pin}/{path(m)})'
    prefix = f"upstream/{SHORT}/"
    report = [
        "# Upstream module comparison", "",
        f"Of {len(removed):,} original proof files removed upstream as unused, the frozen RH trace reached "
        f"{len(removed & reached):,} and missed {len(removed - reached):,} ({len(removed - reached)/len(removed):.1%}). "
        f"Upstream retained {len(retained - reached):,} other files the trace missed. Trace absence alone does not establish mathematical irrelevance.", "",
        f"The baseline is [the original proof](https://github.com/leanprover-community/riemann-hypothesis/tree/{ORIGINAL_PINS[0][0]}) "
        f"and the comparison uses [one upstream commit](https://github.com/leanprover-community/riemann-hypothesis/tree/{PIN}). "
        f"Each graph uses the Mathlib revision in its own dependency manifest, `{ORIGINAL_PINS[1][0]}` and `{LIB}` respectively. "
        "The project-file boundary is `src/**/*.lean`, including files directly under `src/`. "
        "A path is trace-reached when at least one frozen trace site belongs to it. All upstream measurements use module imports.", "",
        "| Original paths | Trace reached | Trace unreached | Total |", "|---|---:|---:|---:|",
    ]
    for label, paths in [("Removed upstream as unused", removed), ("Retained upstream", retained), ("All original paths", old_paths)]:
        report.append(f"| {label} | {len(paths & reached):,} | {len(paths - reached):,} | {len(paths):,} |")
    added = sorted(new_paths - old_paths)
    k = kernel_result["counts"]
    labels = kernel_result["source_classification"]
    states = kernel_result["removed_status"]
    report += ["", "## Kernel cross-check on the original files", "",
               f"Of {k['unused']:,} files with no owned declaration in the union of the five kernel target cones, "
               f"{k['unused_removed']:,} were removed upstream as unused and {k['unused_retained']:,} were retained. "
               f"Of {k['used_removed']} removed files with a kernel-used declaration, the frozen trace reached {k['used_removed_traced']}. "
               f"The {len(retained-reached):,} retained trace misses include {k['retained_miss_rh']:,} RH-used files, "
               f"{k['retained_miss_other']} used by another target but outside RH, and {k['retained_miss_unused']:,} unused by all five.", "",
               f"At file level, RH recall is {k['shared']:,}/{k['rh_files']:,} = {k['shared']/k['rh_files']:.1%}. "
               f"Precision is {k['shared']:,}/{k['trace_files']:,} = {k['shared']/k['trace_files']:.2%}. "
               "The join uses each declaration owner's original file. The union from the declaration table agrees with the union of nonshared "
               "project constants' theorem masks. Bit 1 selects RH. "
               f"[Per-file masks and trace membership]({prefix}kernel-file-usage.tsv.gz) · "
               "[v0.2.1 schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md)", "",
               f"**Unverified at the upstream pin. No Lean build was run.** For all {k['unused_retained']:,} retained kernel-unused files, "
               "we enumerated their direct upstream importers and joined each importer and target to the original whole-environment compiled "
               "declaration edges (type or value). On these retained import pairs, "
               f"{labels['referenced by an unused declaration']:,} targets are labelled **referenced by an unused declaration** "
               f"and {labels['conduit only']:,} **conduit only**. The latter means no original compiled declaration edge was found from these importers. "
               "Neither label establishes what upstream's kernel would use. The importer table also identifies former direct imports.", "",
               f"The upstream source check found corroborating command or token evidence from an originally unused caller for "
               f"{labels['referenced_with_upstream_unused_caller_evidence']:,} targets with a compiled reference. "
               f"For {labels['conduits_with_upstream_source_candidate']} provisionally labelled conduits it found a candidate upstream source reference. "
               "Those disagreements are retained for review. The evidence table separates byte-identical caller commands, scoped identifier mentions, "
               "and historical edges whose upstream use remains unconfirmed. Identifier mentions can occur in tactic alternatives. "
               "Implicit arguments and elaborator-generated references can lack a literal token. "
               f"[All file labels]({prefix}retained-unused.tsv.gz) · [Every retained importer]({prefix}retained-importers.tsv.gz) · "
               f"[Declaration witnesses and upstream lines]({prefix}importer-references.tsv.gz)", "",
               f"The {k['used_removed']} removed kernel-used files owned {kernel_result['removed_declarations']} declarations in total. "
               f"Across the upstream source tree, {kernel_result['removed_declarations_elsewhere']} have the same public qualified name "
               "or a byte-identical command under another identity. "
               f"All declarations were found elsewhere for {states.get('elsewhere',0)} files, some for {states.get('mixed',0)}, "
               f"and none under the search criteria for {states.get('gone under original names',0)}. "
               "A missing name leaves open renaming, inlining, and equivalent mathematics. A matching public name establishes identity by name, "
               "not equivalence of proofs. Module-private names encode the original path. Unconfirmed same-spelling candidates appear separately. "
               f"[All 36 file outcomes]({prefix}removed-used-files.tsv) · [Every declaration and upstream location]({prefix}removed-used-declarations.tsv)"]
    report += ["", f"Upstream adds {len(added):,} path outside the original denominator ({', '.join(f'`{p}`' for p in added)}). "
               f"[Full path classification]({prefix}path-status.tsv.gz)", "", "## Main and the frozen spine", "",
               "| Module-graph measure | Original | Upstream |", "|---|---:|---:|"]
    for label, a, b in [("Project files", len(old_paths), len(new_paths)), ("Project files reachable from Main", len(old), len(new)),
                        ("Distinct imports within the reachable project graph", original["novel_edges"], upstream["novel_edges"])]:
        report.append(f"| {label} | {a:,} | {b:,} |")
    for key, label in [("novel_only", "project path"), ("source_only", "path including pinned Mathlib"),
                       ("through_external_boundary", "path including external terminals")]:
        report.append(f'| Longest {label} (imports) | {original["heights"][key]} | {upstream["heights"][key]} |')
    old_cut, new_cut = [int(x[row_src]["disconnected_novel"]) for x in (old, new)]
    report += [f"| Other project modules disconnected by removing RowSrc | {old_cut:,} | {new_cut:,} |", "",
               f"{len(sp)-len(absent)} of the {len(sp)} frozen spine paths survive. "
               f"{sum(s['module'] in new for s in sp)} remain reachable by imports from Main. "
               + " ".join(f'Original rank {s["rank"]}, {link(s["module"], ORIGINAL_PINS[0][0])}, was removed upstream as unused.' for s in absent)
               + f" [All spine paths, ranks and cuts]({prefix}spine-survival.tsv) · [Longest paths]({prefix}longest-paths.json)", "",
               "## Five largest project cuts", "",
               "Removing a module disconnects the other project modules whose every import path from Main passes through it. "
               "The cut excludes the removed module itself. The ranking excludes Main. Each reported cut was also checked by deleting the module and walking the graph again.", "",
               "| Rank | Original module | Original cut | Upstream module | Upstream cut |", "|---:|---|---:|---|---:|"]
    for n, ((a, ac), (b, bc)) in enumerate(zip(original["top_novel_cuts"][:5], upstream["top_novel_cuts"][:5]), 1):
        report.append(f"| {n} | {link(a, ORIGINAL_PINS[0][0])} | {ac:,} | {link(b, PIN)} | {bc:,} |")
    report += ["", "## Community membership", "",
               f"The reachable project graph partitions into {original['communities']} original and {upstream['communities']} upstream communities. "
               f"Among {shared:,} paths in both reachable graphs, {aligned:,} ({aligned/shared:.1%}) fall into aligned pairs and "
               f"{shared-aligned:,} ({(shared-aligned)/shared:.1%}) fall outside those pairs. "
               "The alignment maximizes total shared membership across a one-to-one assignment. Community numbers are local to each partition. "
               "A split can place a retained module outside the alignment even if many of its neighbors stay together.", "",
               "| Original community | Shared paths | Largest upstream overlap | Paths in overlap |", "|---:|---:|---:|---:|"]
    for i in range(1, min(original["communities"], 10)+1):
        overlaps = [(n, j) for (k,j), n in counts.items() if k==i]
        n,j = min(overlaps, key=lambda item:(-item[0],item[1]), default=(0,0))
        report.append(f"| {i} | {sum(v for v,_ in overlaps):,} | {j or '—'} | {n:,} |")
    report += ["", f"The table follows the ten largest original communities. [All overlaps and aligned pairs]({prefix}community-overlap.tsv) · "
               f"[Upstream per-module memberships and cuts]({prefix}metrics.tsv.gz)", "", "## Reproduce", "",
               "Run from the repository root with the README environment, original source inputs and byte-reproduced baseline in place. "
               "The runner checks both Git trees, performs the removal gate, repeats the module inventory, graph and community stages, "
               "then verifies the headers, distances, ranks and cuts. The SHA-256 manifest covers the module outputs, comparison tables and this report.", "",
               "```bash", "set -eu", "export LC_ALL=C", "cmp results/independent-sha256.json inputs/reproduced/independent-sha256.json",
               "mkdir -p inputs/upstream inputs/upstream-mathlib",
               f"curl -fsSL --retry 3 https://codeload.github.com/leanprover-community/riemann-hypothesis/tar.gz/{PIN} -o inputs/upstream-proof.tgz",
               "tar xzf inputs/upstream-proof.tgz --strip-components=1 -C inputs/upstream",
               f"curl -fsSL --retry 3 https://codeload.github.com/leanprover-community/mathlib4/tar.gz/{LIB} -o inputs/upstream-mathlib.tgz",
               "tar xzf inputs/upstream-mathlib.tgz --strip-components=1 -C inputs/upstream-mathlib",
               "mkdir -p inputs/kernel",
               "for file in constants.csv.gz decls.csv.gz decl_edges.csv.gz; do",
               '  curl -fsSL --retry 3 "https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1/$file" -o "inputs/kernel/$file"',
               "done",
               ".venv/bin/python analysis/upstream.py inputs/upstream inputs/upstream-mathlib --original-proof inputs/lean --kernel inputs/kernel --dest inputs/replayed",
               f"cmp results/{prefix}sha256.json inputs/replayed/{prefix}sha256.json",
               "cmp results/independent-sha256.json inputs/reproduced/independent-sha256.json", "```", ""]
    (dest / "upstream-comparison.md").write_text("\n".join(report))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("proof", type=Path)
    cli.add_argument("mathlib", type=Path)
    cli.add_argument("--original-proof", required=True, type=Path)
    cli.add_argument("--kernel", required=True, type=Path)
    cli.add_argument("--dest", type=Path, default=FROZEN)
    args = cli.parse_args()
    out = args.dest / "upstream" / SHORT
    verify_frozen(FROZEN)
    paths = cross_tab(args.proof)
    gated = kernel.gate(args.kernel, paths)
    print("Removal and kernel gates passed", flush=True)
    out.mkdir(exist_ok=True, parents=True)
    env = dict(os.environ, LC_ALL="C", PYTHONHASHSEED="0", OPENBLAS_NUM_THREADS="1", ROSETTA_RESULTS=str(out.resolve()))
    stages = [("inventory", [args.proof, args.mathlib, "--upstream"]), ("structure", []), ("overview", []), ("audit_graph", [])]
    for stage, params in stages:
        print(f"Running {stage}", flush=True)
        subprocess.run([sys.executable, f"analysis/{stage}.py", *params], env=env, check=True)
    verify_imports(out, args.proof, args.mathlib)
    kernel_result = kernel.analyze(args.proof, args.original_proof, args.kernel, out, paths, gated)
    render(args.dest, out, *paths, kernel_result)
    verify_frozen(FROZEN)
    if {p.name for p in out.iterdir()} - {"sha256.json"} != set(OUTPUTS):
        raise ValueError("Unexpected files in the upstream output directory")
    artifacts = [args.dest / "upstream-comparison.md", *(out / name for name in OUTPUTS)]
    put_json(out / "sha256.json", {p.relative_to(args.dest).as_posix(): digest(p) for p in sorted(artifacts)})


if __name__ == "__main__":
    main()
