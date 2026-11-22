"""Audit declaration citations and positive-length entry dependencies at the original pin."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path

from catalogue_citations import locate
from catalogue_closure import check_links
from catalogue_links import GRAPH_SHA, PAGE_HASHES, catalogue_links
from common import PROJECT, content_digest, put_json, read_rows, table
from odesky_coverage import HTML_SHA, INDEX, OUT, from_html, from_index

RELATIONS = "odesky-audit-relations.tsv.gz"
RELATION_SHA = "bf1c74bfcf995ca04ed3fa79fe3a5d46631a8403540257b75dba2d50701671ed"
CITATIONS = "odesky-audit-citations.tsv.gz"
LINKS = "odesky-audit-dependencies.tsv.gz"
REPORT = "odesky-audit.md"
MANIFEST = "odesky-audit-content-sha256.json"
REL_FIELDS = ("entry_url", "dependency_url", "explicit_depends_on", "two_svg_endpoints")


def report(cites, links, entries):
    c = Counter(r[3] for r in cites)
    src = Counter(r[7] for r in cites if r[3] != "miss")
    entry_hits = defaultdict(set)
    for r in cites:
        entry_hits[r[0]].add(r[3])
    other = sum(r[3] == "miss" and bool(r[8]) for r in cites)
    counts = Counter((r[2],r[9]) for r in links)
    confirmed = counts[1,"direct"] + counts[1,"transitive"]
    explicit = sum(r[2] for r in links)
    positive = sum(r[8] and r[9] in ("no path","incomplete endpoint coverage") and r[2] for r in links)
    theorem = "UpperTheory.Gal.Int.galoisLocalGlobalStrong_recParameter"
    weights = "Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/TypeConditions/WeightsConjBis.lean"
    return f"""# Private catalogue audit

Across {len(entries):,} catalogue entries, {c['exact line']:,} of {len(cites):,} entry–name citations land at a declaration’s starting line in a listed file. Of {explicit:,} explicit entry dependencies, {confirmed:,} have a positive-length path in the original project declaration graph. A path establishes a formal dependency between at least one pair of named endpoints. The remaining {explicit-confirmed:,} explicit links are unconfirmed. These counts check citations and dependencies, and the readings remain open for mathematical review. [Citation evidence]({CITATIONS}) · [Dependency evidence]({LINKS})

## Where the citations land

| Result for one named declaration in one entry | Count |
|---|---:|
| Start line matches a file and line in the entry | {c['exact line']:,} |
| Declaration found in a cited file at another line | {c['off by line']:,} |
| Declaration found in a cited file without a line number | {c['file without line']:,} |
| No declaration located under the cited spelling in a listed file | {c['miss']:,} |

The index gives each entry a list of names and a list of references. We look for each name in every file in that entry and count the best match once. A line inside a theorem body differs from its start line. We matched {src['exact name']:,} citations by exact identity and {src['unique source suffix']:,} by a unique namespace-relative spelling in the cited files. The table records that distinction, the qualified name, original locations and the exact project owner when available. {other:,} misses have a known compiled owner in another file. {sum('miss' in states for states in entry_hits.values()):,} entries have at least one miss.

The source check verifies each consulted file against the frozen inventory, including Mathlib. It recognizes named declaration headers and explicit fields of structures and classes, skips comments, and retains one-based line numbers. Mentions in proof bodies are excluded. An unlocated name can be a reference to an imported definition, an abbreviation used in prose, or a spelling outside the scanner’s coverage. [Levent Alpöge’s original source]({SOURCE}/tree/{PROJECT}) · [Pinned Mathlib](https://github.com/leanprover-community/mathlib4/tree/0df444a360eaa60ab8c11dca51a86af692955474)

## Which entry links have a kernel path?

| Catalogue evidence for A depending on B | Direct | Transitive | No path with complete endpoint coverage | Incomplete endpoint coverage, no path confirmed | Total |
|---|---:|---:|---:|---:|---:|
{dependency_line("Explicit “Depends on”",1,counts)}
{dependency_line("Additional reverse “Used by” links",0,counts)}

For each ordered pair we ask whether a named project declaration of A reaches one of B’s named project declarations. We use exact compiled owners and accept a namespace-relative endpoint when the citation resolves uniquely in its source files and has a compiled declaration row. A generated field without its own declaration row remains unresolved in this graph. We retain both type and value edges and traverse standalone auxiliary constants as intermediate vertices. The two positive columns are disjoint. The table supplies a witness pair for each confirmation and prefers a direct witness when one exists. A declaration shared by two entries is recorded separately. Among explicit links lacking a positive path, {positive:,} share an owned declaration. The projected graph drops self-loops and omits external libraries, literal edges and block membership. An unresolved or external endpoint leaves an unconfirmed result open. A formal path can run through intermediate declarations beyond those singled out in the catalogue. [James Shore’s v0.2.1 schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md#decl_edges-the-project-declaration-graph-over-the-whole-environment-20372294-rows)

We read every explicit “Depends on” field from the pinned index and checked the fields on two individual pages. The graph provides both endpoint IDs for {sum(r[3] for r in links):,} within-field pairs. They match the within-field “Used by” links exactly. Cross-field paths run through field portals, so we resolved them from the entry lists and checked the graph’s count for every directed pair of fields. {len(links)-explicit:,} reverse links have no corresponding explicit “Depends on” field link. We report their results separately. [Andrew O’Desky’s graph](https://andrewodesky.com/rh/graph.html) · [Frozen link index]({RELATIONS})

## RowSrc and the catalogue entry · unreviewed

Both readings start from `{theorem}`. They put the choice of a global representation and its integral weights before the choice of a finite place. Both require a regular algebraic polarized cuspidal input over a CM field. The catalogue spells out the twist in the polarization and the sign condition at real places. The Rosetta reading points to the Lean predicates for those hypotheses and separates the existence of a local correspondence from the requirement that a chosen correspondence obey its laws. [Rosetta reading](01-row0b.md) · [Andrew O’Desky’s entry](https://andrewodesky.com/rh/s/galois-representations.html)

The conclusions agree on the quantifiers that matter for comparison. A single representation supplies the local tests. Spherical places over the coefficient prime give crystallinity and the specified jumps. Away from that prime, full parameter equality and agreement on inertia have different hypotheses. The catalogue develops the commutator and inertia tests and the local parameter conventions explicitly. The Rosetta reading traces the predicates through `Row0b` and follows the construction of the global witness into the downstream nonvanishing argument. We found no conflicting hypothesis or conclusion in these clauses. Equivalence of the expanded local conventions still needs expert review. [Original quantifiers and local clauses]({SOURCE}/blob/{PROJECT}/src/{weights}#L54-L73)

## Inputs and replay

Andrew O’Desky’s identifier index has HTML SHA-256 `{HTML_SHA}` (2026-11-22 17:15:18 UTC). The graph snapshot from 18:49 UTC has SHA-256 `{GRAPH_SHA}`. The global representation page (18:49 UTC) and the cohomological page (18:51 UTC) have SHA-256 `{PAGE_HASHES['galois-representations']}` and `{PAGE_HASHES['cohomological-bound']}`, respectively. The site returned HTTP 404 for robots.txt at capture. Page requests were spaced by at least one second. The extract contains identifiers and links. [Catalogue index](https://andrewodesky.com/rh/index.html) · [Global representation entry](https://andrewodesky.com/rh/s/galois-representations.html) · [Second dependency-list check](https://andrewodesky.com/rh/s/cohomological-bound.html)

Run from the checkout root after preparing the original source directories and Python environment as in the [README](../../README.md#reproduce). Set `PROOF` to the directory containing the original `src/` and `MATHLIB` to the root of the pinned Mathlib tree. The script checks both normalized indexes and the release SHA-256 values for `decl_edges.parquet` (`62a184a781184bc1f3953ed90f5b967a27a2a3517d7b1f7e169ca6cc7d1bbec3`) and `decls.csv.gz` (`bdfeae289f2db8b279816439049f26ba69ec993af2bab3b30d53340fe02493b9`). The default replay runs without accessing the catalogue site. [James Shore’s v0.2.1 release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)

```bash
export LC_ALL=C
mkdir -p inputs/audit
release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1
curl -fL --retry 3 "$release/decl_edges.parquet" -o inputs/audit/decl_edges.parquet
curl -fL --retry 3 "$release/decls.csv.gz" -o inputs/audit/decls.csv.gz
.venv/bin/python analysis/odesky_audit.py "$PROOF" "$MATHLIB" inputs/audit --out inputs/audit-replay
cmp results/phase-2/{MANIFEST} inputs/audit-replay/{MANIFEST}
```

To reproduce the identifier extraction from the raw snapshots as well, run the following while the site still serves the recorded bytes. All raw HTML stays under the ignored `inputs/` directory. The content manifest hashes decompressed TSV payloads and the Markdown report.

```bash
.venv/bin/python analysis/fetch_catalogue_audit.py inputs/audit/html
.venv/bin/python analysis/odesky_audit.py "$PROOF" "$MATHLIB" inputs/audit --html inputs/audit/html --out inputs/audit-html
cmp results/phase-2/{MANIFEST} inputs/audit-html/{MANIFEST}
```
"""


SOURCE = "https://github.com/leanprover-community/riemann-hypothesis"


def dependency_line(label, explicit, counts):
    vals = [counts[explicit,s] for s in ("direct","transitive","no path","incomplete endpoint coverage")]
    return "| " + label + " | " + " | ".join(f"{n:,}" for n in [*vals,sum(vals)]) + " |"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("proof",type=Path)
    cli.add_argument("mathlib",type=Path)
    cli.add_argument("release",type=Path)
    cli.add_argument("--html",type=Path)
    cli.add_argument("--out",type=Path,default=OUT)
    a = cli.parse_args()
    dest = a.out
    dest.mkdir(parents=True, exist_ok=True)
    entries,sections = from_index(OUT/INDEX)
    if a.html:
        if from_html(a.html/"index.html") != (entries,sections):
            raise ValueError("HTML and frozen citation indexes disagree")
        relations = catalogue_links(a.html/"index.html",a.html/"graph.html",a.html/"s", entries)
    else:
        if content_digest(OUT/RELATIONS) != RELATION_SHA:
            raise ValueError("Frozen relation index checksum mismatch")
        relations = {(r["entry_url"],r["dependency_url"]): (int(r["explicit_depends_on"]),int(r["two_svg_endpoints"]))
                     for r in read_rows(OUT/RELATIONS)}
    table(dest/RELATIONS,REL_FIELDS,((a,b,*v) for (a,b),v in sorted(relations.items())))
    if content_digest(dest/RELATIONS) != RELATION_SHA:
        raise ValueError("Re-extracted link index differs from the capture")
    cites, endpoints = locate(entries,a.proof,a.mathlib,a.release/"decls.csv.gz")
    links = check_links(a.release/"decl_edges.parquet", entries, relations, endpoints)
    table(dest/CITATIONS,("entry_url","cited_name","file_citations","result","matching_source_sites",
                          "best_file_citations","qualified_name","spelling","compiled_owner","owner_start_line"),cites)
    table(dest/LINKS,(*REL_FIELDS,"caller_names","caller_names_resolved","dependency_names","dependency_names_resolved",
                      "shared_owned_declaration","result","witness_caller","witness_dependency"),links)
    (dest/REPORT).write_text(report(cites,links,entries))
    put_json(dest/MANIFEST,{f:content_digest(dest/f) for f in sorted([RELATIONS,CITATIONS,LINKS,REPORT])})


if __name__ == "__main__":
    main()
