"""Render the retained-link evidence and the comparison with the reviewer's counts."""
from collections import Counter

from catalogue_crosscheck import CUBE, DISPUTE, HELPER, THETA_FILE, UNKILLED
from common import PROJECT
from compare import URLS
from odesky_coverage import UTC


def write_note(dest, details, prior, current, entries, cards, captures, frame_cards, file_count):
    classes = Counter(r["classification"] for r in details.values())
    paths = [r for r in details.values() if r["exact_result"] in {"direct", "transitive"}]
    negatives = [r for r in details.values() if r["classification"] == "no dependency"]
    ruled = sum(r["source_result"] == "ruled out" for r in negatives)
    reversed_both = sum(bool(r["exact_opposite_path"] and r["pr_opposite_path"]) for r in negatives)
    unsettled = len(details) - classes["path"] - len(negatives)
    measures = [
        ("Retained directed links", len(details), 1965),
        ("Forward path in Shore", len(paths), 1746),
        ("↳ Path in Proofs & Reasons", sum(r["pr_result"] == "path" for r in paths), 1742),
        ("↳ Not testable in Proofs & Reasons", sum(r["pr_result"] == "not testable" for r in paths), 4),
        ("↳ Contradicted in Proofs & Reasons", sum(r["pr_result"] == "no path" for r in paths), 0),
        ("No dependency between tested owners in either graph", len(negatives), 133),
        ("↳ Ruled out by source imports or line order", ruled, 79),
        ("↳ Opposite path in both graphs", reversed_both, 14),
        ("Unsettled", unsettled, 86),
        ("↳ Unmatched printed name", classes["unmatched name"], 77),
        ("↳ Same declaration", classes["same declaration"], 3),
        ("↳ No Shore path and second graph not testable", classes["second graph not testable"], 5),
        ("↳ Graphs disagree", classes["graphs disagree"], 1),
        ("Links with a path in either graph forbidden by source", sum(
            r["source_result"] == "ruled out" and (r["exact_result"] in {"direct", "transitive"} or r["pr_result"] == "path")
            for r in details.values()), 0),
    ]
    added = current - prior.keys()
    mapped = sum(a in entries and b in entries for a, b in added)
    counts = [f"| {k} | {actual:,} | {expected:,} | {actual-expected:,} |"
              for k, actual, expected in measures]
    frame_pairs = [(a,b) for (a,b),r in details.items() if r["classification"] == "unmatched name"
                   and prior[a,b]["result"] == "no path" and frame_cards.intersection((a,b))]
    both = f"{len(negatives)} retained links have no dependency between their exact declaration owners in either compiled graph."
    section = [
        "# Dependency checks for the rebuilt statement site", "",
        f"**{both}** Original source imports or declaration order rule out {ruled} of those links. For {reversed_both}, both graphs have a path in the opposite direction. Of the {len(details):,} retained links in Andrew O’Desky’s *Statements of the Lean RH project*, {len(paths):,} have a forward path in James Shore’s graph and {unsettled} are unsettled. These results describe the listed Lean declarations. A statement can have a mathematical motivation outside those declarations. [Owner table](owner-no-path.tsv) · [Every directed link](checked.tsv.gz)", "",
        "| Measure | Reproduced | Expected | Difference |", "| --- | ---: | ---: | ---: |", *counts, "",
        "Indented rows describe subsets. Source exclusions and opposite paths can overlap. The expected figures are the reviewer’s counts. The per-link table identifies A and B and records each result separately.", "",
        "## How a link is tested", "",
        f"A → B means A lists B in its “Depends on” field. Of the {len(current):,} links in the November 23 snapshot, {len(details):,} also occur on November 22. The {len(added)} additions have empty evidence fields. Of these, {mapped} connect two older card IDs and {len(added)-mapped} have an unmapped endpoint. A surviving statement can inherit links from one it absorbed. The November 22 snapshot contained {len(prior):,} links, of which {len(prior.keys()-current)} disappeared. The theorem index was captured at {captures['index.html']['utc']} and the definitions page at {captures['definitions.html']['utc']}. The Lean name mapping is from {UTC}. [Andrew O’Desky’s statement index](https://andrewodesky.com/rh/index.html) · [Snapshot hashes](snapshots.json) · [Historical citation audit](../odesky-audit.md)", "",
        "1. Resolve each printed name exactly. Map an identified structure field to its owning declaration. Search all pairs of owners for a positive-length forward path, preferring a direct witness. A common owner is recorded separately from a path. For a negative conclusion every printed name must resolve, the two sets of owners must be disjoint and every owner must be present in the second graph. The historical audit preserves the earlier single-graph counts. [James Shore’s v0.2.1 declaration graph](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)",
        f"2. Search the signature and body edges in the RH graph from Proofs & Reasons, led by Simon DeDeo. Match both file and exact owner name. A found path supplies a witness even when another endpoint is absent. If there is no witness and an endpoint is missing, the result is *not testable*. This graph covers the RH cone. Its output can therefore confirm fewer paths than the whole-project graph. [Proofs & Reasons](https://proofsandreasons.io/rh-graph.html) · [Pinned declaration graph]({URLS['pr-graph.json.gz'][1]})",
        f"3. Read the import headers of all {file_count:,} original project source files. Check each file’s SHA-256 and imports against the frozen inventory and follow the transitive imports. In a shared file, compare the owners’ declaration-start lines. A source exclusion requires every A–B combination to fail. An available import or earlier line permits a dependency without establishing one. The evidence table records the number of owner pairs under each source test. Every positive owner pair in both directions was checked against its own files and lines. [Levent Alpöge’s original source](https://github.com/leanprover-community/riemann-hypothesis/tree/{PROJECT})", "",
        "## Cases where the second graph changes what can be reported", "",
        f"The table below identifies Shore paths that the second graph cannot test and the pairs removed from the earlier exact-name list of {sum(r['exact_result'] == 'no path' for r in details.values())}. Each row also appears in the full evidence table. The owner table contains the pairs with two negative results.", "",
        "| A | Listed B | Shore | Proofs & Reasons | Missing owner or forward witness in Proofs & Reasons |",
        "| --- | --- | --- | --- | --- |",
    ]
    for (a,b), r in details.items():
        if r["exact_result"] not in {"direct","transitive","no path"}:
            continue
        if r["pr_result"] != "not testable" and r["classification"] != "graphs disagree":
            continue
        reason = r["pr_missing_owners"] or r["unmatched_printed_names"] or f"{r['pr_witness_caller']} → {r['pr_witness_dependency']}"
        reason = reason.replace(" | ", ", ")
        section.append(f"| [{a}]({cards[a]['url']}) | [{b}]({cards[b]['url']}) | {r['exact_result']} | {r['pr_result']} | `{reason}` |")
    source = f"https://github.com/leanprover-community/riemann-hypothesis/blob/{PROJECT}/{THETA_FILE}"
    section += ["",
        f"For `{DISPUTE[0]}` → `{DISPUTE[1]}`, Proofs & Reasons folds the shared helper `{HELPER}` into `cube2`. That supplies an edge from `{UNKILLED}` to `{CUBE}`. Removing that single folded edge eliminates every forward path between the owners of the two pages in Proofs & Reasons. Shore records a value edge from each declaration to the shared helper and no path from the former declaration to the latter. The source at lines 198–200 defines a predicate about membership in a subgroup and makes no call to `cube2`, defined at line 124. The link remains unsettled. [Predicate source]({source}#L198-L200) · [cube2 source]({source}#L124-L127)", "",
        f"**Name-resolution footnote.** Allowing the bare `FrameLA1` to stand for `Formalism.HN.FrameLA1` moved {len(frame_pairs)} links into the earlier single-graph no-path list. Exact naming leaves them unsettled. " +
        " · ".join(f"[`{a}`]({cards[a]['url']}) → [`{b}`]({cards[b]['url']})" for a,b in frame_pairs), "",
        "## Replay", "",
        "Run from the checkout root with the original source directory in `PROOF` and the November 22 citation and dependency outputs in place. The script checks both compiled input digests. The content manifest hashes decompressed table bytes.", "",
        "```bash", "export LC_ALL=C", "r=results/phase-2/2026-11-23", "mkdir -p inputs/audit",
        "release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1",
        'curl -fL --retry 3 "$release/decl_edges.parquet" -o inputs/audit/decl_edges.parquet',
        f"curl -fL --retry 3 {URLS['pr-graph.json.gz'][1]} -o inputs/audit/pr-graph.json.gz",
        '.venv/bin/python analysis/catalogue_rebuild.py inputs/audit/decl_edges.parquet inputs/audit/pr-graph.json.gz "$PROOF" --out inputs/rebuilt-audit',
        'cmp "$r/content-sha256.json" inputs/rebuilt-audit/content-sha256.json',
        "```", "", "To re-extract the statement pairs, place the two HTML captures in `inputs/rebuilt-html/` as `index.html` and `definitions.html`. The extractor verifies their recorded hashes. Run in the same shell.", "", "```bash",
        '.venv/bin/python analysis/statement_index.py inputs/rebuilt-html "$r/snapshots.json" inputs/cards.tsv --depends inputs/depends.tsv',
        'cmp "$r/cards.tsv" inputs/cards.tsv', 'cmp "$r/depends.tsv" inputs/depends.tsv', "```", ""]
    (dest / "dependencies.md").write_text("\n".join(section))
