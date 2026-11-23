# Private catalogue audit

**1,869 of 1,886 entries cite a line where at least one of their named declarations starts.** Another 14 name a declaration in a cited file without an exact line match. Of these, 13 point to a different line and [one entry](https://andrewodesky.com/rh/s/main.html) supplies file paths without line numbers. The remaining 3 name no declaration we could locate in a cited file. Most off-by-line rows are additional names in the same entry: 135 of 167 accompany a name whose starting line matches. [Citation evidence](odesky-audit-citations.tsv.gz)

Across 1,886 catalogue entries, 1,878 of 2,317 entry–name citations land at a declaration’s starting line in a listed file. Of 2,481 explicit entry dependencies, 1,802 have a positive-length path in the original project declaration graph. A path establishes a formal dependency between at least one pair of named endpoints. The remaining 679 explicit links are unconfirmed. These counts check citations and dependencies, and the readings remain open for mathematical review. [Citation evidence](odesky-audit-citations.tsv.gz) · [Dependency evidence](odesky-audit-dependencies.tsv.gz)

## Where the citations land

| Result for one named declaration in one entry | Count |
|---|---:|
| Start line matches a file and line in the entry | 1,878 |
| Declaration found in a cited file at another line | 167 |
| Declaration found in a cited file without a line number | 3 |
| No declaration located under the cited spelling in a listed file | 269 |

The index gives each entry a list of names and a list of references. We look for each name in every file in that entry and count the best match once. A line inside a theorem body differs from its start line. We matched 2,042 citations by exact identity and 6 by a unique namespace-relative spelling in the cited files. The table records that distinction, the qualified name, original locations and the exact project owner when available. 235 misses have a known compiled owner in another file. 147 entries have at least one miss.

The source check verifies each consulted file against the frozen inventory, including Mathlib. It recognizes named declaration headers and explicit fields of structures and classes, skips comments, and retains one-based line numbers. Mentions in proof bodies are excluded. An unlocated name can be a reference to an imported definition, an abbreviation used in prose, or a spelling outside the scanner’s coverage. [Levent Alpöge’s original source](https://github.com/leanprover-community/riemann-hypothesis/tree/40e56bab026552e089d7afcfeff08d2defb9c005) · [Pinned Mathlib](https://github.com/leanprover-community/mathlib4/tree/0df444a360eaa60ab8c11dca51a86af692955474)

## Which entry links have a kernel path?

| Catalogue evidence for A depending on B | Direct | Transitive | No path with complete endpoint coverage | Incomplete endpoint coverage, no path confirmed | Total |
|---|---:|---:|---:|---:|---:|
| Explicit “Depends on” | 606 | 1,196 | 142 | 537 | 2,481 |
| Additional reverse “Used by” links | 2 | 820 | 4 | 12 | 838 |

Of the 142 explicit links with fully resolved endpoints and no forward path, **14 have a positive-length path in the opposite direction using names exactly as printed**. The same namespace resolution used for the forward check adds one, for 15 reverse links in all. The [slope-inequality](https://andrewodesky.com/rh/s/slope-inequality.html) entry spells the target `FrameLA1`. Its source-qualified name `Formalism.HN.FrameLA1` is reached from `Formalism.HN.frame_linear_algebra_first` in the [other entry](https://andrewodesky.com/rh/s/frame-codimension.html). The table records each reverse witness and whether an exact-spelling reverse witness exists. This describes the orientation in the compiled graph. [Directional evidence](odesky-audit-dependencies.tsv.gz)

For each ordered pair we ask whether a named project declaration of A reaches one of B’s named project declarations. We use exact compiled owners and accept a namespace-relative endpoint when the citation resolves uniquely in its source files and has a compiled declaration row. A generated field without its own declaration row remains unresolved in this graph. We retain both type and value edges and traverse standalone auxiliary constants as intermediate vertices. The two positive columns are disjoint. The table supplies a witness pair for each confirmation and prefers a direct witness when one exists. A declaration shared by two entries is recorded separately. Among explicit links lacking a positive path, 2 share an owned declaration. The projected graph drops self-loops and omits external libraries, literal edges and block membership. An unresolved or external endpoint leaves an unconfirmed result open. A formal path can run through intermediate declarations beyond those singled out in the catalogue. [James Shore’s v0.2.1 schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md#decl_edges-the-project-declaration-graph-over-the-whole-environment-20372294-rows)

We read every explicit “Depends on” field from the pinned index and checked the fields on two individual pages. The graph provides both endpoint IDs for 1,199 within-field pairs. They match the within-field “Used by” links exactly. Cross-field paths run through field portals, so we resolved them from the entry lists and checked the graph’s count for every directed pair of fields. 838 reverse links have no corresponding explicit “Depends on” field link. We report their results separately. [Andrew O’Desky’s graph](https://andrewodesky.com/rh/graph.html) · [Frozen link index](odesky-audit-relations.tsv.gz)

## RowSrc and the catalogue entry · unreviewed

Both readings start from `UpperTheory.Gal.Int.galoisLocalGlobalStrong_recParameter`. They put the choice of a global representation and its integral weights before the choice of a finite place. Both require a regular algebraic polarized cuspidal input over a CM field. The catalogue spells out the twist in the polarization and the sign condition at real places. The Rosetta reading points to the Lean predicates for those hypotheses and separates the existence of a local correspondence from the requirement that a chosen correspondence obey its laws. [Rosetta reading](01-row0b.md) · [Andrew O’Desky’s entry](https://andrewodesky.com/rh/s/galois-representations.html)

The conclusions agree on the quantifiers that matter for comparison. A single representation supplies the local tests. Spherical places over the coefficient prime give crystallinity and the specified jumps. Away from that prime, full parameter equality and agreement on inertia have different hypotheses. The catalogue develops the commutator and inertia tests and the local parameter conventions explicitly. The Rosetta reading traces the predicates through `Row0b` and follows the construction of the global witness into the downstream nonvanishing argument. We found no conflicting hypothesis or conclusion in these clauses. Equivalence of the expanded local conventions still needs expert review. [Original quantifiers and local clauses](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/TypeConditions/WeightsConjBis.lean#L54-L73)

## Inputs and replay

Andrew O’Desky’s identifier index has HTML SHA-256 `2c57f0ee0c8d291a1595ab46e1a6a4c732c10b14ca15b46cd4f0431b20e8879e` (2026-11-22 17:15:18 UTC). The graph snapshot from 18:49 UTC has SHA-256 `354e43be13ce0eb0075fdc2c0ea11fb6843f9407c41e5be00918c9ed2b25865e`. The global representation page (18:49 UTC) and the cohomological page (18:51 UTC) have SHA-256 `4a707d2ea0a23e255e246d35f482f1de93b28b4347957e1a09505079923bc9b8` and `9c0b7a34a97093673c55c5df8d89a07749ff3c3c9703c6d9f3dca4315f78cde4`, respectively. The site returned HTTP 404 for robots.txt at capture. Page requests were spaced by at least one second. The extract contains identifiers and links. [Catalogue index](https://andrewodesky.com/rh/index.html) · [Global representation entry](https://andrewodesky.com/rh/s/galois-representations.html) · [Second dependency-list check](https://andrewodesky.com/rh/s/cohomological-bound.html)

Run from the checkout root after preparing the original source directories and Python environment as in the [README](../../README.md#reproduce). Set `PROOF` to the directory containing the original `src/` and `MATHLIB` to the root of the pinned Mathlib tree. The script checks both normalized indexes and the release SHA-256 values for `decl_edges.parquet` (`62a184a781184bc1f3953ed90f5b967a27a2a3517d7b1f7e169ca6cc7d1bbec3`) and `decls.csv.gz` (`bdfeae289f2db8b279816439049f26ba69ec993af2bab3b30d53340fe02493b9`). The default replay runs without accessing the catalogue site. [James Shore’s v0.2.1 release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)

```bash
export LC_ALL=C
mkdir -p inputs/audit
release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1
curl -fL --retry 3 "$release/decl_edges.parquet" -o inputs/audit/decl_edges.parquet
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
