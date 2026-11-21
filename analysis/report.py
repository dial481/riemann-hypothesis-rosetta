"""Render the structural report, including the full reading spine."""
import json
from collections import Counter

from common import PROJECT, RESULTS, archive_data


def main():
    s = json.loads((RESULTS / "structure.json").read_text())
    t = json.loads((RESULTS / "trace-summary.json").read_text())
    mixed = json.loads((RESULTS / "combined-communities.json").read_text())
    groups = json.loads((RESULTS / "communities.json").read_text())
    adj, inv = archive_data()
    p = s["source_counts"]
    proof_count = p["Novel"][0]
    paths = json.loads((RESULTS / "longest-paths.json").read_text())
    novel = [m for m, r in inv.items() if r["category"] == "Novel"]
    areas = Counter(d.split(".")[1] for m in novel for d in adj[m] if d.startswith("Mathlib."))
    source = f"https://github.com/leanprover-community/riemann-hypothesis/blob/{PROJECT}/"
    def top(pairs, n=3):
        return ", ".join(f"{a} ({b:,})" for a, b in pairs[:n]) or "No area-specific import"
    def link(m):
        return f"[{m}]({source}{inv[m]['path']})"
    report = ["# Structural map of the original Alpöge RH source", "",
              f"The original archive contains **{proof_count:,} project modules and {p['Novel'][1]:,} lines**. "
              f"Every module is reachable from the two imports in [Main.lean]({source}src/Main.lean#L1). "
              f"To start reading the theorem, follow [riemannHypothesis at line 4]({source}src/Main.lean#L4) "
              f"to [rhOfAll at line 9]({source}src/Supplements/Kernels/MainTheorems.lean#L9). "
              "It applies Formalism.VW.rh_of_every to allChi. This call explains why nonvanishing for every "
              "Dirichlet character is a good entry into the much larger argument.", "",
              "[Jump to the ranked 200](#a-reading-spine-of-200-modules) · [Cross-validation](comparison.md) · [Methods and reproduction](../README.md)", "",
              "## Source boundary and reachability", "",
              "| Pinned source tree | Modules | Physical lines | Outside Main | Unreachable lines |",
              "|---|---:|---:|---:|---:|"]
    for cat, (n, lines, nr, lr) in p.items():
        report.append(f"| {cat} | {n:,} | {lines:,} | {n-nr:,} ({(n-nr)/n:.2%}) | {lines-lr:,} ({(lines-lr)/lines:.2%}) |")
    n, lines, nr, lr = (sum(x) for x in zip(*p.values()))
    report += [f"| Both trees | {n:,} | {lines:,} | {n-nr:,} ({(n-nr)/n:.2%}) | {lines-lr:,} ({(lines-lr)/lines:.2%}) |", "",
               "Mathlib includes its entire pinned repository, including tests, tooling and archived examples. "
               "Reachability measures explicit imports. [All unreachable files](unreachable.tsv.gz).", "",
               f"The adjacency list has {s['nodes_including_external']:,} vertices and {s['edges']:,} distinct directed imports. "
               f"The closure of Main contains {s['closure']:,} vertices, including {s['external_in_closure']} external imports "
               "whose internals lie outside these two source trees. [External boundary](external.tsv).", "",
               "## Depth, hubs and single points of failure", "",
               "A layer is the maximum import distance from Main, with Main at layer zero. "
               "External endpoint names are terminals in the export.", "",
               "| Graph followed from Main | Edges in longest chain | Layers including Main | Last vertex on one longest chain |",
               "|---|---:|---:|---|"]
    for key, label in [("novel_only","Project only"),("source_only","Both pinned source trees"),("through_external_boundary","Including external terminals")]:
        walk = paths[key]
        report.append(f"| {label} | {len(walk)-1} | {len(walk)} | {walk[-1]} |")
    report += ["", "All three paths begin with Main → Supplements.Kernels.MainTheoremsAll → Supplements.Kernels.MainTheoremsCritical "
               "→ Supplements.Kernels.MainTheorems → Development.AutomorphicArithmetic.CharacterBoxes.MainConclusion. "
               "The source-only path ends in Mathlib’s linter infrastructure. A long import chain can measure tool dependencies "
               "as well as mathematical prerequisites. [All path vertices](longest-paths.json).", "",
               "Dependents count distinct direct importers. Imports count distinct direct dependencies. "
               "A cut counts other novel modules that become unreachable when the indicated vertex is deleted.", "",
               "| Metric | Module | Count |", "|---|---|---:|"]
    for key, label in [("top_novel_dependents","Fan-out · novel dependents"),("top_novel_imports","Fan-in · novel imports"),
                       ("top_novel_cuts","Removal cut · novel losses")]:
        for m, v in s[key][:4]:
            report.append(f"| {label} | {link(m)} | {v:,} |")
    report += ["", f"In the full closure, Mathlib leads both degree tables with {s['top_dependents_closure'][0][1]:,} direct "
               f"dependents and {s['top_imports_closure'][0][1]:,} direct imports. The largest project cut is an import-only file, "
               "MainTheoremsAll. Its architectural importance and its lack of a declaration illustrate why the reading spine "
               "requires separate declaration evidence. [Full metrics](metrics.tsv.gz).", "",
               "![Directed imports between top-level source families](import-map.svg)", "",
               "## Where the project code concentrates", "",
               "| Original directory or file | Modules | Lines | Share of original lines |", "|---|---:|---:|---:|"]
    by_dir = {}
    for m in novel:
        folder = inv[m]["path"].split("/")[1]
        n, lines = by_dir.get(folder,(0,0))
        by_dir[folder] = (n+1, lines+int(inv[m]["lines"]))
    for folder, (n, lines) in sorted(by_dir.items(), key=lambda kv: -kv[1][1]):
        report.append(f"| src/{folder} | {n:,} | {lines:,} | {lines/p['Novel'][1]:.1%} |")
    report += ["", f"Of {proof_count:,} novel files, **{s['umbrella_direct']:,}** import Mathlib directly "
               f"({s['umbrella_direct']/proof_count:.1%}). Only **{s['distinct_explicit_area_modules']:,}** name a specific Mathlib submodule. "
               f"The {sum(areas.values()):,} distinct project-to-specific-Mathlib edges break down as follows. Counts measure "
               "explicit import choices.", "", top(areas.most_common(), 30) + ".", "",
               "## Communities", "",
               f"The project-only graph divides into {len(groups)} import communities (Louvain modularity {s['modularity']:.3f}). "
               "The largest groups below combine their dominant directory with the strongest explicit Mathlib area evidence. "
               "One or two imports give weak evidence for an area label.", "",
               "| Community | Dominant directory | Novel modules | Novel lines | Specific Mathlib edges by area |", "|---:|---|---:|---:|---|"]
    for g in groups[:12]:
        report.append(f"| {g['id']} | {g['prefixes'][0][0]} | {g['novel_modules']:,} | {g['novel_lines']:,} | {top(g['explicit_area_edges'])} |")
    report += ["", f"The two source trees together give {len(mixed['groups'])} communities "
               f"(modularity {mixed['modularity']:.3f}). The Mathlib umbrella concentrates most of its source tree in one group. "
               "The five groups with the most project source lines are below. IDs refer to this second partition.", "",
               "| Combined group | Novel modules | Mathlib-tree modules | Novel lines | Largest project directory |", "|---:|---:|---:|---:|---|"]
    for g in sorted(mixed["groups"], key=lambda g: -g["novel_lines"])[:5]:
        report.append(f"| {g['id']} | {g['novel_modules']:,} | {g['mathlib_modules']:,} | {g['novel_lines']:,} | {g['novel_prefixes'][0][0]} |")
    report += ["", "## What the RH traces establish", "",
               f"Starting at the single riemannHypothesis declaration, the lexical resolver finds {t['reached_sites']:,} "
               f"named source sites across {t['reached_modules']:,} project files. Each retained reference has an identifier spelling, a caller "
               "line and a visible candidate definition. The scan covers types and bodies. Tactic alternatives, implicit arguments, "
               "notation and local shadowing can cause divergences in either direction from elaborated proof terms. "
               "[Method details](../README.md) · [All traced sites](rh-trace.tsv.gz).", "",
               (RESULTS / "SPINE.md").read_text().replace("# A reading spine", "## A reading spine", 1)]
    (RESULTS / "REPORT.md").write_text("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
