"""Audit declaration citations and positive-length entry dependencies at the original pin."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path

from catalogue_citations import locate
from catalogue_closure import check_links
from catalogue_links import GRAPH_SHA, PAGE_HASHES, catalogue_links
from common import MATHLIB, PROJECT, content_digest, put_json, read_rows, table
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
    exact_entries = sum("exact line" in states for states in entry_hits.values())
    off_entries = sum("exact line" not in states and "off by line" in states for states in entry_hits.values())
    no_line = [url for url,states in entry_hits.items() if "file without line" in states and not states & {"exact line","off by line"}]
    absent = sum(states == {"miss"} for states in entry_hits.values())
    secondary = sum(r[3] == "off by line" and "exact line" in entry_hits[r[0]] for r in cites)
    reversed_paths = sum(bool(r[12]) for r in links if r[2] and r[9] == "no path")
    literal_reverse = sum(r[15] == 1 for r in links)
    if (exact_entries, off_entries, len(no_line), absent) != (1869, 13, 1, 3):
        raise ValueError("Entry citation totals changed")
    other = sum(r[3] == "miss" and bool(r[8]) for r in cites)
    counts = Counter((r[2],r[9]) for r in links)
    confirmed = counts[1,"direct"] + counts[1,"transitive"]
    explicit = sum(r[2] for r in links)
    common = [r for r in links if r[2] and r[9] == "common declaration"]
    shared_rows = "\n".join(
        f"| [{r[0].split('/')[-1][:-5]}]({r[0]}) | [{r[1].split('/')[-1][:-5]}]({r[1]}) | `{r[16]}` |"
        for r in common)
    incomplete = counts[1, "incomplete endpoint coverage"]
    no_path = counts[1, "no path"]
    unsettled = incomplete + len(common)
    unresolved = sum(r[3] == "miss" and not r[8] for r in cites)
    field_rows = [r for r in cites if r[11].startswith("structure field")]
    source_fields = [r for r in field_rows if r[11] == "structure field (pinned source)"]
    unresolved_exact = sum(not r[10] or r[7] != "exact name" for r in cites)
    alternative_rows = []
    for r in cites:
        for alternative in filter(None, r[12].split("|")):
            candidate, site = alternative.rsplit("@", 1)
            file, line = site.rsplit(":", 1)
            link = f"{SOURCE}/blob/{PROJECT}/{file}#L{line}" if file.startswith("src/") else (
                f"https://github.com/leanprover-community/mathlib4/blob/{MATHLIB}/{file}#L{line}")
            alternative_rows.append(f"| `{r[1]}` | `{candidate}` | [{Path(file).name}, line {line}]({link}) |")
    if explicit != confirmed + no_path + unsettled or literal_reverse > reversed_paths:
        raise ValueError("Inconsistent link counts")
    theorem = "UpperTheory.Gal.Int.galoisLocalGlobalStrong_recParameter"
    weights = "Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/TypeConditions/WeightsConjBis.lean"
    return f"""# Private audit of Andrew O’Desky’s *Statements of the Lean RH project*

**2026-11-23.** Andrew O’Desky rebuilt the site. The links below use the November 22 addresses. The citations and historical single-graph figures describe those pages. For links retained on November 23, the owner table reports “no recorded path between the tested declarations” when both compiled declaration graphs agree under exact naming. [Two-source results and original-source checks](2026-11-23/dependencies.md) · [Owner table](2026-11-23/owner-no-path.tsv)

**{exact_entries:,} of {len(entries):,} entries cite a line where at least one of their named declarations starts.** Another {off_entries + len(no_line)} name a declaration in a cited file without an exact line match. Of these, {off_entries} point to a different line and [one entry]({no_line[0]}) supplies file paths without line numbers. The remaining {absent} name no declaration we could locate in a cited file. Most off-by-line rows are additional names in the same entry: {secondary} of {c['off by line']} accompany a name whose starting line matches. [Citation evidence]({CITATIONS})

Across {len(entries):,} entries, {c['exact line']:,} of {len(cites):,} entry–name citations land at a declaration’s starting line in a listed file. Of {explicit:,} explicit entry dependencies, {confirmed:,} have a positive-length path in James Shore’s compiled declaration graph. A path records a connection between the tested project declaration owners. The remaining {explicit-confirmed:,} explicit links are unconfirmed. These counts check citations and dependencies, and the informalizations remain open for mathematical review. [Citation evidence]({CITATIONS}) · [Dependency evidence]({LINKS})

## Historical November 22 comparison with Shore’s graph

| Measure | Previously shared | Updated |
| --- | ---: | ---: |
| Entries citing a named start line, of {len(entries):,} | 1,869 | {exact_entries:,} |
| Explicit links with a positive path, of {explicit:,} | 1,802 | {confirmed:,} |
| Complete endpoints, disjoint graph owners, no forward path | 140 | {no_path:,} |
| Of the preceding row, reverse path with exact graph endpoint names | 14 | {literal_reverse:,} |
| Unsettled under the earlier grouping | 539 | {unsettled:,} |
| ↳ Common graph owner and no positive path | 2 | {len(common):,} |
| ↳ Incomplete endpoint coverage and no positive path | 537 | {incomplete:,} |
| Citation misses with no project owner (entry–name rows) | 34 | {unresolved:,} |

The reverse count is a subset of the no-forward-path row. The unsettled subtotal preserves the earlier reporting convention. The two rows beneath it give distinct reasons. Of the original 537 incomplete links, {537-incomplete} now have complete coverage or a forward witness.

## Where the citations land

| Result for one named declaration in one entry | Count |
|---|---:|
| Start line matches a file and line in the entry | {c['exact line']:,} |
| Declaration found in a cited file at another line | {c['off by line']:,} |
| Declaration found in a cited file without a line number | {c['file without line']:,} |
| No declaration located under the cited spelling in a listed file | {c['miss']:,} |

The index gives each entry a list of names and a list of references. We look for each name in every file in that entry and count the best match once. A line inside a theorem body differs from its start line. We matched {src['exact name']:,} citations by exact identity and {src['unique source suffix']:,} by a unique namespace-relative spelling in the cited files. The table records that distinction, the qualified name, original locations and the exact project owner when available. {other:,} misses have a known compiled owner in another file. {sum('miss' in states for states in entry_hits.values()):,} entries have at least one miss.

The source check verifies each consulted file against the frozen inventory, including Mathlib. It recognizes named declaration headers and explicit fields of structures and classes, skips comments, and retains one-based line numbers. Mentions in proof bodies are excluded. We mapped {len(field_rows)} field citations to their enclosing structures. Shore’s constants table supplied {len(field_rows)-len(source_fields)} mappings. For the remaining field, the original source identifies `Formalism.IndefR.IndefiniteRealisation.seeLev` at line 72. Its structure header is at line 30. Shore’s command span begins at line 28 with two local options. Across all {len(cites):,} citation rows, {unresolved_exact} lack an exact printed-name mapping to a graph owner. [Field in IndefRRealT.lean]({SOURCE}/blob/{PROJECT}/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/IndefRRealT.lean#L72) For example, `Formalism.L2.Pj.LawsCore.latZ`, `.cuNe` and `.expo` belong to `Formalism.L2.Pj.LawsCore` in `CuspidalL2Subspace.lean`. The table distinguishes the field name, the graph owner and the start of its command span. Source-line matches still use the field’s own line. An unlocated name can be a reference to an imported definition, an abbreviation used in prose, or a spelling outside the scanner’s coverage. [Levent Alpöge’s original source]({SOURCE}/tree/{PROJECT}) · [Pinned Mathlib](https://github.com/leanprover-community/mathlib4/tree/0df444a360eaa60ab8c11dca51a86af692955474)

For a printed name absent from the consulted project declarations, source matches and Shore’s constants table, the citation table records a different declaration with the same final name component if it starts on the cited line. These alternatives are reported separately from citation matches and graph endpoints.

| Printed name | Declaration starting on the cited line | Original source |
| --- | --- | --- |
{chr(10).join(alternative_rows)}

## Which entry links have a recorded path in Shore’s compiled declaration graph?

| Evidence for A depending on B | Direct | Transitive | Common declaration, no positive path | No recorded path with complete endpoint coverage | Incomplete endpoint coverage, no path confirmed | Total |
|---|---:|---:|---:|---:|---:|---:|
{dependency_line("Explicit “Depends on”",1,counts)}
{dependency_line("Additional reverse “Used by” links",0,counts)}

Of the {no_path} explicit links with complete endpoints and no forward path or shared graph owner, {literal_reverse} have a reverse witness with graph endpoint names present as printed on both entries. All resolved graph owners yield {reversed_paths} reverse paths. The printed-owner count measures literal witness spelling. Exact-name resolution also maps exact structure-field names to their owners. [Two-source results for retained links](2026-11-23/dependencies.md) Each row records its direction and witness. [Directional evidence]({LINKS})

| Entry | Listed dependency | Shared graph owner |
| --- | --- | --- |
{shared_rows}

A positive-length path takes precedence. For pairs without a forward path, a shared graph owner takes precedence over the opposite-direction test. Two fields of the same structure count as a common declaration. In particular, a reverse path between declarations owned by one page is not evidence that the dependency runs in the opposite direction between the pages. A folded-field witness records a path at the level of the owning declaration. Identifying a reference to a particular projection requires separate evidence.

The graph includes type and value edges and standalone project auxiliary constants. It excludes external libraries, self-loops, literal edges and block membership. The table prefers a direct witness and retains unresolved endpoints. [James Shore’s v0.2.1 schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md#decl_edges-the-project-declaration-graph-over-the-whole-environment-20372294-rows)

We read every explicit “Depends on” field from the pinned index and checked the fields on two individual pages. The graph provides both endpoint IDs for {sum(r[3] for r in links):,} within-field pairs. They match the within-field “Used by” links exactly. Cross-field paths run through field portals, so we resolved them from the entry lists and checked the graph’s count for every directed pair of fields. {len(links)-explicit:,} reverse links have no corresponding explicit “Depends on” field link. We report their results separately. The November 23 comparison tests retained links against both compiled declaration graphs and the original source imports. Links added after the name snapshot are listed separately. [Retained-link evidence](2026-11-23/dependencies.md) [Andrew O’Desky’s graph](https://andrewodesky.com/rh/graph.html) · [Frozen link index]({RELATIONS})

## RowSrc and the statement entry · unreviewed

Both informalizations start from `{theorem}`. They put the choice of a global representation and its integral weights before the choice of a finite place. Both require a regular algebraic polarized cuspidal input over a CM field. The entry spells out the twist in the polarization and the sign condition at real places. The Rosetta autoinformalization points to the Lean predicates for those hypotheses and separates the existence of a local correspondence from the requirement that a chosen correspondence obey its laws. [Rosetta autoinformalization](01-row0b.md) · [Andrew O’Desky’s entry](https://andrewodesky.com/rh/s/galois-representations.html)

The conclusions agree on the quantifiers that matter for comparison. A single representation supplies the local tests. Spherical places over the coefficient prime give crystallinity and the specified jumps. Away from that prime, full parameter equality and agreement on inertia have different hypotheses. The entry develops the commutator and inertia tests and the local parameter conventions explicitly. The Rosetta autoinformalization traces the predicates through `Row0b` and follows the construction of the global witness into the downstream nonvanishing argument. We found no conflicting hypothesis or conclusion in these clauses. Equivalence of the expanded local conventions still needs expert review. [Original quantifiers and local clauses]({SOURCE}/blob/{PROJECT}/src/{weights}#L54-L73)

## Inputs and replay

Andrew O’Desky’s identifier index has HTML SHA-256 `{HTML_SHA}` (2026-11-22 17:15:18 UTC). The graph snapshot from 18:49 UTC has SHA-256 `{GRAPH_SHA}`. The global representation page (18:49 UTC) and the cohomological page (18:51 UTC) have SHA-256 `{PAGE_HASHES['galois-representations']}` and `{PAGE_HASHES['cohomological-bound']}`, respectively. The site returned HTTP 404 for robots.txt at capture. Page requests were spaced by at least one second. The extract contains identifiers and links. [Statements of the Lean RH project](https://andrewodesky.com/rh/index.html) · [Global representation entry](https://andrewodesky.com/rh/s/galois-representations.html) · [Second dependency-list check](https://andrewodesky.com/rh/s/cohomological-bound.html)

Run from the checkout root after preparing the original source directories and Python environment as in the [README](../../README.md#reproduce). Set `PROOF` to the directory containing the original `src/` and `MATHLIB` to the root of the pinned Mathlib tree. The script checks both normalized indexes and the release SHA-256 values for `decl_edges.parquet` (`62a184a781184bc1f3953ed90f5b967a27a2a3517d7b1f7e169ca6cc7d1bbec3`), `constants.csv.gz` (`2964f5236046325ac7884906cb9517b0aa582330dd48a07eef291cb579444820`) and `decls.csv.gz` (`bdfeae289f2db8b279816439049f26ba69ec993af2bab3b30d53340fe02493b9`). The default replay runs without accessing the statement site. [James Shore’s v0.2.1 release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)

```bash
export LC_ALL=C
mkdir -p inputs/audit
release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1
curl -fL --retry 3 "$release/decl_edges.parquet" -o inputs/audit/decl_edges.parquet
curl -fL --retry 3 "$release/constants.csv.gz" -o inputs/audit/constants.csv.gz
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
    vals = [counts[explicit,s] for s in ("direct","transitive","common declaration","no path","incomplete endpoint coverage")]
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
    cites, endpoints = locate(entries,a.proof,a.mathlib,a.release/"decls.csv.gz",a.release/"constants.csv.gz")
    links = check_links(a.release/"decl_edges.parquet", entries, relations, endpoints)
    table(dest/CITATIONS,("entry_url","cited_name","file_citations","result","matching_source_sites",
                          "best_file_citations","qualified_name","spelling","compiled_owner","owner_start_line","graph_owner","owner_kind","same_short_name_at_cited_line"),cites)
    table(dest/LINKS,(*REL_FIELDS,"caller_names","caller_names_resolved","dependency_names","dependency_names_resolved",
                      "shared_owned_declaration","result","witness_caller","witness_dependency","opposite_path","opposite_witness_caller","opposite_witness_dependency","opposite_with_exact_names","shared_graph_owners"),links)
    (dest/REPORT).write_text(report(cites,links,entries))
    put_json(dest/MANIFEST,{f:content_digest(dest/f) for f in sorted([RELATIONS,CITATIONS,LINKS,REPORT])})


if __name__ == "__main__":
    main()
