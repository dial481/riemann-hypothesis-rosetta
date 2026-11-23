# Private audit of Andrew O’Desky’s *Statements of the Lean RH project*

**2026-11-23.** Andrew O’Desky rebuilt the site. The links below use the November 22 addresses. The citations and historical single-graph figures describe those pages. For links retained on November 23, the owner table reports “no recorded path between the tested declarations” when both compiled declaration graphs agree under exact naming. [Two-source results and original-source checks](2026-11-23/dependencies.md) · [Owner table](2026-11-23/owner-no-path.tsv)

## Author’s dependency-list corrections on 23 November 2026

Between 21:49:13 and 21:51:31 UTC on 23 November, Andrew O’Desky’s *Statements of the Lean RH project* listed 2,161 distinct directed “Depends on” links. Of the 133 pairs in the historical two-graph table, 123 had been removed from the site and 10 were still listed. This recount compares displayed links by stable card ID and direction. The historical graph results continue to describe the declarations tested at the earlier snapshot. [Author’s site](https://andrewodesky.com/rh/) · [Pair-by-pair status](2026-11-23/corrections/historical-link-status.tsv) · [Complete corrected list](2026-11-23/corrections/depends.tsv) · [Source hashes and capture times](2026-11-23/corrections/source-files.json)

Replay the comparison offline from the committed card-ID pairs with `LC_ALL=C .venv/bin/python analysis/catalogue_corrections.py results/phase-2/2026-11-23/corrections inputs/corrections-replay --pairs`. Compare both TSVs with the committed copies. For a new live capture, run the same script with an empty input cache, a separate output directory and `--capture`. Each request follows robots.txt and is spaced at least one second from the previous response.

**1,869 of 1,886 entries cite a line where at least one of their named declarations starts.** Another 14 name a declaration in a cited file without an exact line match. Of these, 13 point to a different line and [one entry](https://andrewodesky.com/rh/s/main.html) supplies file paths without line numbers. The remaining 3 name no declaration we could locate in a cited file. Most off-by-line rows are additional names in the same entry: 135 of 167 accompany a name whose starting line matches. [Citation evidence](odesky-audit-citations.tsv.gz)

Across 1,886 entries, 1,878 of 2,317 entry–name citations land at a declaration’s starting line in a listed file. Of 2,481 explicit entry dependencies, 1,827 have a positive-length path in James Shore’s compiled declaration graph. A path records a connection between the tested project declaration owners. The remaining 654 explicit links are unconfirmed. These counts check citations and dependencies, and the informalizations remain open for mathematical review. [Citation evidence](odesky-audit-citations.tsv.gz) · [Dependency evidence](odesky-audit-dependencies.tsv.gz)

## Historical November 22 comparison with Shore’s graph

| Measure | Previously shared | Updated |
| --- | ---: | ---: |
| Entries citing a named start line, of 1,886 | 1,869 | 1,869 |
| Explicit links with a positive path, of 2,481 | 1,802 | 1,827 |
| Complete endpoints, disjoint graph owners, no forward path | 140 | 149 |
| Of the preceding row, reverse path with exact graph endpoint names | 14 | 17 |
| Unsettled under the earlier grouping | 539 | 505 |
| ↳ Common graph owner and no positive path | 2 | 4 |
| ↳ Incomplete endpoint coverage and no positive path | 537 | 501 |
| Citation misses with no project owner (entry–name rows) | 34 | 23 |

The reverse count is a subset of the no-forward-path row. The unsettled subtotal preserves the earlier reporting convention. The two rows beneath it give distinct reasons. Of the original 537 incomplete links, 36 now have complete coverage or a forward witness.

## Where the citations land

| Result for one named declaration in one entry | Count |
|---|---:|
| Start line matches a file and line in the entry | 1,878 |
| Declaration found in a cited file at another line | 167 |
| Declaration found in a cited file without a line number | 3 |
| No declaration located under the cited spelling in a listed file | 269 |

The index gives each entry a list of names and a list of references. We look for each name in every file in that entry and count the best match once. A line inside a theorem body differs from its start line. We matched 2,042 citations by exact identity and 6 by a unique namespace-relative spelling in the cited files. The table records that distinction, the qualified name, original locations and the exact project owner when available. 246 misses have a known compiled owner in another file. 147 entries have at least one miss.

The source check verifies each consulted file against the frozen inventory, including Mathlib. It recognizes named declaration headers and explicit fields of structures and classes, skips comments, and retains one-based line numbers. Mentions in proof bodies are excluded. We mapped 23 field citations to their enclosing structures. Shore’s constants table supplied 22 mappings. For the remaining field, the original source identifies `Formalism.IndefR.IndefiniteRealisation.seeLev` at line 72. Its structure header is at line 30. Shore’s command span begins at line 28 with two local options. Across all 2,317 citation rows, 64 lack an exact printed-name mapping to a graph owner. [Field in IndefRRealT.lean](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/IndefRRealT.lean#L72) For example, `Formalism.L2.Pj.LawsCore.latZ`, `.cuNe` and `.expo` belong to `Formalism.L2.Pj.LawsCore` in `CuspidalL2Subspace.lean`. The table distinguishes the field name, the graph owner and the start of its command span. Source-line matches still use the field’s own line. An unlocated name can be a reference to an imported definition, an abbreviation used in prose, or a spelling outside the scanner’s coverage. [Levent Alpöge’s original source](https://github.com/leanprover-community/riemann-hypothesis/tree/40e56bab026552e089d7afcfeff08d2defb9c005) · [Pinned Mathlib](https://github.com/leanprover-community/mathlib4/tree/0df444a360eaa60ab8c11dca51a86af692955474)

For a printed name absent from the consulted project declarations, source matches and Shore’s constants table, the citation table records a different declaration with the same final name component if it starts on the cited line. These alternatives are reported separately from citation matches and graph endpoints.

| Printed name | Declaration starting on the cited line | Original source |
| --- | --- | --- |
| `GlobalTheory.CompHS.Deep` | `GlobalTheory.CovTop.Deep` | [NormNegCmConstantEqAtAllEmbeddings.lean, line 162](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Definitions/Divisors/NormNegCmConstantEqAtAllEmbeddings.lean#L162) |

## Which entry links have a recorded path in Shore’s compiled declaration graph?

| Evidence for A depending on B | Direct | Transitive | Common declaration, no positive path | No recorded path with complete endpoint coverage | Incomplete endpoint coverage, no path confirmed | Total |
|---|---:|---:|---:|---:|---:|---:|
| Explicit “Depends on” | 628 | 1,199 | 4 | 149 | 501 | 2,481 |
| Additional reverse “Used by” links | 2 | 820 | 0 | 4 | 12 | 838 |

Of the 149 explicit links with complete endpoints and no forward path or shared graph owner, 17 have a reverse witness with graph endpoint names present as printed on both entries. All resolved graph owners yield 18 reverse paths. The printed-owner count measures literal witness spelling. Exact-name resolution also maps exact structure-field names to their owners. [Two-source results for retained links](2026-11-23/dependencies.md) Each row records its direction and witness. [Directional evidence](odesky-audit-dependencies.tsv.gz)

| Entry | Listed dependency | Shared graph owner |
| --- | --- | --- |
| [family-arithmetic-data](https://andrewodesky.com/rh/s/family-arithmetic-data.html) | [family-integral-adjusted-sources](https://andrewodesky.com/rh/s/family-integral-adjusted-sources.html) | `Formalism.MainNotions.FamP` |
| [family-point-moduli-integral-evaluation](https://andrewodesky.com/rh/s/family-point-moduli-integral-evaluation.html) | [family-point-moduli-canonical](https://andrewodesky.com/rh/s/family-point-moduli-canonical.html) | `Formalism.L2.Pj.LawsM` |
| [q2-prime-norm-galois-patching](https://andrewodesky.com/rh/s/q2-prime-norm-galois-patching.html) | [r1-frobenius-semisimple-isomorphism](https://andrewodesky.com/rh/s/r1-frobenius-semisimple-isomorphism.html) | `UpperTheory.Gal.Int.Core.isoOne_holds` |
| [slope-inequality](https://andrewodesky.com/rh/s/slope-inequality.html) | [frame-codimension](https://andrewodesky.com/rh/s/frame-codimension.html) | `Formalism.HN.FrameLA1` |

A positive-length path takes precedence. For pairs without a forward path, a shared graph owner takes precedence over the opposite-direction test. Two fields of the same structure count as a common declaration. In particular, a reverse path between declarations owned by one page is not evidence that the dependency runs in the opposite direction between the pages. A folded-field witness records a path at the level of the owning declaration. Identifying a reference to a particular projection requires separate evidence.

The graph includes type and value edges and standalone project auxiliary constants. It excludes external libraries, self-loops, literal edges and block membership. The table prefers a direct witness and retains unresolved endpoints. [James Shore’s v0.2.1 schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md#decl_edges-the-project-declaration-graph-over-the-whole-environment-20372294-rows)

We read every explicit “Depends on” field from the pinned index and checked the fields on two individual pages. The graph provides both endpoint IDs for 1,199 within-field pairs. They match the within-field “Used by” links exactly. Cross-field paths run through field portals, so we resolved them from the entry lists and checked the graph’s count for every directed pair of fields. 838 reverse links have no corresponding explicit “Depends on” field link. We report their results separately. The November 23 comparison tests retained links against both compiled declaration graphs and the original source imports. Links added after the name snapshot are listed separately. [Retained-link evidence](2026-11-23/dependencies.md) [Andrew O’Desky’s graph](https://andrewodesky.com/rh/graph.html) · [Frozen link index](odesky-audit-relations.tsv.gz)

## RowSrc and the statement entry · unreviewed

Both informalizations start from `UpperTheory.Gal.Int.galoisLocalGlobalStrong_recParameter`. They put the choice of a global representation and its integral weights before the choice of a finite place. Both require a regular algebraic polarized cuspidal input over a CM field. The entry spells out the twist in the polarization and the sign condition at real places. The Rosetta autoinformalization points to the Lean predicates for those hypotheses and separates the existence of a local correspondence from the requirement that a chosen correspondence obey its laws. [Rosetta autoinformalization](01-row0b.md) · [Andrew O’Desky’s entry](https://andrewodesky.com/rh/s/galois-representations.html)

The conclusions agree on the quantifiers that matter for comparison. A single representation supplies the local tests. Spherical places over the coefficient prime give crystallinity and the specified jumps. Away from that prime, full parameter equality and agreement on inertia have different hypotheses. The entry develops the commutator and inertia tests and the local parameter conventions explicitly. The Rosetta autoinformalization traces the predicates through `Row0b` and follows the construction of the global witness into the downstream nonvanishing argument. We found no conflicting hypothesis or conclusion in these clauses. Equivalence of the expanded local conventions still needs expert review. [Original quantifiers and local clauses](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/TypeConditions/WeightsConjBis.lean#L54-L73)

## Inputs and replay

Andrew O’Desky’s identifier index has HTML SHA-256 `2c57f0ee0c8d291a1595ab46e1a6a4c732c10b14ca15b46cd4f0431b20e8879e` (2026-11-22 17:15:18 UTC). The graph snapshot from 18:49 UTC has SHA-256 `354e43be13ce0eb0075fdc2c0ea11fb6843f9407c41e5be00918c9ed2b25865e`. The global representation page (18:49 UTC) and the cohomological page (18:51 UTC) have SHA-256 `4a707d2ea0a23e255e246d35f482f1de93b28b4347957e1a09505079923bc9b8` and `9c0b7a34a97093673c55c5df8d89a07749ff3c3c9703c6d9f3dca4315f78cde4`, respectively. The site returned HTTP 404 for robots.txt at capture. Page requests were spaced by at least one second. The extract contains identifiers and links. [Statements of the Lean RH project](https://andrewodesky.com/rh/index.html) · [Global representation entry](https://andrewodesky.com/rh/s/galois-representations.html) · [Second dependency-list check](https://andrewodesky.com/rh/s/cohomological-bound.html)

Run from the checkout root after preparing the original source directories and Python environment as in the [README](../../README.md#reproduce). Set `PROOF` to the directory containing the original `src/` and `MATHLIB` to the root of the pinned Mathlib tree. The script checks both normalized indexes and the release SHA-256 values for `decl_edges.parquet` (`62a184a781184bc1f3953ed90f5b967a27a2a3517d7b1f7e169ca6cc7d1bbec3`), `constants.csv.gz` (`2964f5236046325ac7884906cb9517b0aa582330dd48a07eef291cb579444820`) and `decls.csv.gz` (`bdfeae289f2db8b279816439049f26ba69ec993af2bab3b30d53340fe02493b9`). The default replay runs without accessing the statement site. [James Shore’s v0.2.1 release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)

```bash
export LC_ALL=C
mkdir -p inputs/audit
release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1
curl -fL --retry 3 "$release/decl_edges.parquet" -o inputs/audit/decl_edges.parquet
curl -fL --retry 3 "$release/constants.csv.gz" -o inputs/audit/constants.csv.gz
curl -fL --retry 3 "$release/decls.csv.gz" -o inputs/audit/decls.csv.gz
.venv/bin/python analysis/odesky_audit.py "$PROOF" "$MATHLIB" inputs/audit --out inputs/audit-replay
cmp results/phase-2/odesky-audit-content-sha256.json inputs/audit-replay/odesky-audit-content-sha256.json
```

To reproduce the identifier extraction from the raw snapshots as well, run the following while the site still serves the recorded bytes. All raw HTML stays under the ignored `inputs/` directory. The content manifest hashes decompressed TSV payloads and the Markdown report.

```bash
.venv/bin/python analysis/fetch_catalogue_audit.py inputs/audit/html
.venv/bin/python analysis/odesky_audit.py "$PROOF" "$MATHLIB" inputs/audit --html inputs/audit/html --out inputs/audit-html
cmp results/phase-2/odesky-audit-content-sha256.json inputs/audit-html/odesky-audit-content-sha256.json
```
