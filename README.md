# Riemann Hypothesis Rosetta

A source-level map of the original Lean formalization released by Levent Alpöge on 20 November 2026. It is a starting point for mathematicians reading the proof. The analysis follows imports across both pinned source trees, then follows explicit declaration references from the single theorem `riemannHypothesis`. All extraction and ranking use Python and raw source. No Lean code was run.

**Start with RowSrc.lean, line 6.** Removing this file makes **13,054 other project modules** unreachable from Main, although only two project files import it directly. Its single theorem supplies the Galois representation existence and compatibility result used to prove nonvanishing for every Dirichlet character. The reading note follows both the construction and its use on the way to RH. [Pinned source at line 6](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/RowSrc.lean#L6) · [First reading note](results/phase-2/01-row0b.md) · [All 200 spine entries](results/SPINE.md)

AI drafted the mathematical reading notes from the pinned source. They are starting points for expert review. [Reader notice](results/NOTICE.md)

| Question | Where to look |
|---|---|
| How is the archive organized? | [Structural report and complete ranked list](results/REPORT.md) · [Import map](results/import-map.svg) |
| Why read a particular file, and at what line? | [200 annotated modules](results/SPINE.md) · [Machine-readable ranks and evidence](results/spine.tsv) · [Complete RH witness chains](results/spine-witnesses.json.gz) |
| What did the follow-up review find? | [Graph audit and resolver correction](results/review/2026-11-21.md) · [New community work and reading leads](results/surveys/2026-11-21.md) |
| How well do the reading trails agree with compiled evidence? | [Cross-validation and investigation list](results/comparison.md) · [Checks for each of the 200](results/comparison-spine.tsv) |
| What imports what? | [JSON adjacency list](results/imports.json.gz) · [Module inventory with paths, line counts and hashes](results/inventory.tsv.gz) |
| Which files are hubs, bottlenecks or unreachable? | [Per-module graph metrics](results/metrics.tsv.gz) · [Longest paths](results/longest-paths.json) · [Unreachable files](results/unreachable.tsv.gz) |
| Which mathematical areas occur together? | [Project communities](results/communities.json) · [Combined communities](results/combined-communities.json) · [Combined membership](results/combined-membership.tsv.gz) · [Directory totals](results/directories.tsv.gz) |

## Results at a glance

- All **175,187** original project files and **17,374,215** original lines are in the import closure of Main. The classification also covers **8,852** Lean files and **2,377,849** lines from the entire pinned Mathlib repository. Main reaches **8,312** of those Mathlib files.
- The longest project-only path spans **202 imports**, or **203 layers** including Main. Following pinned Mathlib source extends the path to **370 imports**. Following the last explicit import to an external terminal extends it to **371**.
- **Development** accounts for **12,232,663 project lines**. The most widely imported project module, **CTSmallCone**, has **3,088** distinct direct project dependents. The import-only file **MainTheoremsAll** is the largest project bottleneck.
- The independent textual RH trace reaches **641,100 named sites**. Both external compiled datasets contain all **200** selected anchors. Proofs & Reasons contains **460 of the 462** distinct direct edges in the selected trails. Ranks **14 and 128** each have a source mention whose direct edge is absent there. [Exact discrepancies and alternative compiled trails](results/comparison.md)

## What the measurements mean

**Source and provenance.** The 14 original archive parts were concatenated in numeric order. The resulting 239,275,554 bytes have SHA-256 `9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc`. The inventory stage rebuilt the entire Git tree from disk for both inputs and matched the tree IDs recorded in the two commits. The proof pins Lean `v4.33.1`. [Archive-equivalent commit 40e56bab](https://github.com/leanprover-community/riemann-hypothesis/tree/40e56bab026552e089d7afcfeff08d2defb9c005) · [Pinned Mathlib](https://github.com/leanprover-community/mathlib4/tree/0df444a360eaa60ab8c11dca51a86af692955474) · [Verified tree identities](results/provenance.json)

**Classification and boundaries.** Novel means the file belongs to the submitted source tree. The label describes provenance and makes no claim of mathematical originality. Mathlib means a file belongs to the entire pinned Mathlib repository, including its tests, scripts and archived examples. Every source file has exactly one category. Imports from Lean, Std, Batteries and other dependencies whose sources are outside the pins appear as named terminal vertices. Their unknown imports are outside the measurement. Library/test files outside Main are included in the inventory and dead-code denominator. The report gives separate denominators for each tree. [External imports](results/external.tsv)

**Import parsing.** Module names come from paths relative to the proof’s `src/` directory or the Mathlib repository root. The parser reads the header, skips nested and line comments, and handles `module`, `prelude`, visibility, `meta import`, `import all` and quoted identifiers. The JSON maps each module to its sorted distinct explicit imports. Implicit prelude dependencies are outside scope. Repeated imports contribute to the inventory’s command count and become one graph edge. An independent line scan matched all **909,822** import commands in the original proof, file by file. A second line-oriented header scan independently matched all **36,329** explicit imports across the **8,852** Mathlib-tree files. Physical line totals include blanks and count a final unterminated line.

**Critical paths and cuts.** Edges point from importer to dependency. In the user-requested terminology, fan-out counts distinct direct dependents (NetworkX in-degree), and fan-in counts direct imports (NetworkX out-degree). The longest paths use dynamic programming on Main’s acyclic closure. Immediate dominators give exact removal cuts: a strictly dominated vertex loses every path from Main when the dominator disappears. Counts exclude the removed vertex itself. The five largest cuts were cross-checked by deleting the vertex and repeating reachability. The metrics distinguish full-tree degrees, closure degrees and novel-only degrees. [Counts and top lists](results/structure.json)

**Communities.** Seeded Louvain partitions the undirected projection of the actual import edges. The first partition uses reachable project modules. The second includes all source files in both trees and retains the umbrella import. In both runs the seed is 42, resolution is 1, and each distinct module pair has unit weight. Directory tables include nested parent totals, so sums across directory depths double-count. A community’s area profile counts explicit named Mathlib imports by their first area component. The umbrella supplies no area-specific evidence. Community IDs belong to their own partition, and the partitions describe import density. [Project memberships in the metrics](results/metrics.tsv.gz) · [Directory-to-directory edge counts](results/family-edges.tsv)

**RH-specific evidence.** The declaration index recognizes common named top-level commands in the original project. A breadth-first search begins at `src/Main.lean:4`. It scans type and body for literal identifiers, honors explicit global names and handles ordinary namespace and open scopes, checks import visibility, and requires a single eligible project declaration. Same-file references must point backwards. It suppresses detected local binders, string literals, and unqualified identifiers shorter than four characters. Each retained site records a shortest witnessed source trail, its caller and the line containing the token. The scanner does not elaborate terms. Field notation, generated declarations, tactics, implicit arguments, short names and unhandled scope syntax can hide references. Tactic alternatives, local shadowing and names in simplifier lists can introduce extra candidates. A missing trace is inconclusive. [All sites and parent links](results/rh-trace.tsv.gz) · [Validation of these limitations](results/comparison.md)

**Reading priority.** The import rank orders every reachable novel module by a weighted combination of PageRank, direct novel dependents and dominated novel descendants. For each measure we use `log(1+x)` divided by its graph-wide maximum on the same transformed scale. For PageRank, `x` is the novel vertex count times its PageRank (damping 0.85, uniform teleportation). The weights are 0.40, 0.25 and 0.35. Main’s trivial all-graph cut gets zero weight. Separately, the cut rank orders non-root novel modules with positive cut size by the number of novel descendants lost. Ties break by module name.

For modules with an RH source witness, reading priority is `1/(50 + import_rank) + 1/(50 + cut_rank)`, with the second term omitted for a zero cut or Main. This gives both widely reused foundations and narrow gateways a place in the first 200. The starting declaration has shortest source-trace distance within its module, with theorem/lemma preferred at equal distance and source order breaking remaining ties. The one-line notes were written after inspecting those source locations. Ranks are a reading choice. An import-only wrapper can top the cuts table and have no declaration to annotate. [Reader annotations](analysis/reader-notes.tsv) · [Scoring implementation](analysis/spine.py)

## A guide to the largest project communities

These labels come from the frozen import communities and their dominant source folders. They give more detail than the top-level directory names. The right column lists the strongest area evidence from specifically named Mathlib imports. A small count warrants caution.

| Project community | Reading label from directory membership | Leading Mathlib area evidence |
|---:|---|---|
| 1 | Divisors and degeneration of abelian varieties | Ring theory (15), algebraic geometry (13) |
| 2 | Heights, theta and automorphic metric geometry | Analysis (4), ring theory (3) |
| 3 | Divisors and Iwasawa decomposition | Analysis (2), algebraic geometry (1) |
| 4 | Decorated lattices and twisted operators | No specific Mathlib import |
| 5 | Hermitian curvature and flag measures | Analysis (27), measure theory (7) |
| 6 | Block decomposition of the automorphic spectrum | Analysis (12), representation theory (1) |
| 7 | Divisor proofs and existence of unitary data | Algebra (1), ring theory (1) |
| 8 | Divisor proofs and twisted operators | No specific Mathlib import |
| 9 | Modularity arguments and Shimura theory | Ring theory (68), number theory (26) |
| 10 | Twisted operators and divisor proofs | Analysis (2), ring theory (2) |
| 11 | Inertia eigenvalues and cocycles | Ring theory (17), analysis (3) |
| 12 | Theta-pair lifts and inertia eigenvalues | No specific Mathlib import |

## Reproduce

From this repository root, use Python 3.14, Git, curl and tar. The analysis reads source as data. Raw archives, the Python environment and third-party comparison downloads can live outside the repository.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p inputs/parts inputs/mathlib
for n in $(seq -w 1 14); do
  curl --fail --location --retry 3 "https://alpo.ge/lean.tar.gz.part$n" -o "inputs/parts/lean.tar.gz.part$n"
done
cat inputs/parts/lean.tar.gz.part* > inputs/lean.tar.gz
echo '9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc  inputs/lean.tar.gz' | sha256sum -c -
tar -xzf inputs/lean.tar.gz -C inputs
curl --fail --location --retry 3 https://codeload.github.com/leanprover-community/mathlib4/tar.gz/0df444a360eaa60ab8c11dca51a86af692955474 -o inputs/mathlib.tar.gz
tar -xzf inputs/mathlib.tar.gz --strip-components=1 -C inputs/mathlib
.venv/bin/python analysis/run.py inputs/lean inputs/mathlib --out inputs/reproduced
cmp results/independent-sha256.json inputs/reproduced/independent-sha256.json
```

If the split archive is unavailable, unpack the [exact mirror snapshot](https://codeload.github.com/leanprover-community/riemann-hypothesis/tar.gz/40e56bab026552e089d7afcfeff08d2defb9c005) into `inputs/lean` with `--strip-components=1`. Both routes pass through the same Git-tree check. The default output directory is `results/`. The example uses a separate directory to compare with the committed files.

The independent run finishes by verifying the 200 citation chains and recording SHA-256 for its 20 artifacts. The following optional command verifies that manifest, downloads only digest-pinned comparison inputs, joins the datasets and checks the independent manifest again. It writes separate `comparison*` outputs. Commit `aca7e18` preserves the original independent run made before the first comparison. A later source audit corrected explicit global-name resolution. The revised trace has its own frozen manifest. [Frozen snapshot](results/independent-sha256.json)

```bash
ROSETTA_RESULTS=inputs/reproduced .venv/bin/python analysis/compare.py inputs/comparisons --fetch
```

## Community work and credit

Alpöge and Claude produced the submitted formalization. The Lean and Mathlib communities verified it, with endorsement by the Lean FRO and Mathlib Initiative. The certification is theirs. [Author’s announcement](https://alpo.ge/remark.pdf) · [Community verification statement](https://leanprover-community.github.io/blog/posts/riemann-hypothesis/) · [Independent verification resources at MIT](https://math.mit.edu/~drew/grh/)

- James Shore publishes dependency data from proof terms, per-theorem masks and dominator analyses. Proofs & Reasons at Carnegie Mellon publishes a separate RH-only declaration graph with signature and body edges. This project compares against both once the independent results are frozen. [Shore v0.2.1](https://github.com/james-shore/rh-proof-dependencies/tree/v0.2.1) · [Proofs & Reasons graph](https://proofsandreasons.io/rh-graph.html)
- Naskręcki’s atlas supplies a human-facing blueprint with source pins and mathematical interfaces. Michael Rubinstein at Waterloo collects an exposition and verification material. Additional community reading projects include Tam Nguyen Duc’s exposition and Riemann Hypothesis Solved. [Naskręcki’s atlas](https://nasqret.github.io/riemann-rev/) · [Rubinstein’s Waterloo project](https://www.math.uwaterloo.ca/~mrubinst/alpoge_claude_grh/) · [riemann.tamnd.com](https://riemann.tamnd.com/) · [riemannhypothesissolved.com](https://riemannhypothesissolved.com/)
- Earlier work also includes a project-wide module ledger, a source-file map, static import scripts, and additional declaration visualizations. [Replay ledger](https://github.com/rohanarun/alpoge-rh-replay) · [riemann.world](https://github.com/linusheck/riemann.world) · [F# import scripts](https://github.com/kant2002/riemann-hypothesis-supplimentary) · [YiweiIvy’s atlas](https://github.com/YiweiIvy/riemann-hypothesis-atlas) · [DeepTheory proof maps](https://deeptheory-labs.github.io/GRH/)

For comparison, [Alessandro Masullo’s human-drafted approach](https://math216.wordpress.com/wp-content/uploads/2026/11/the-music-of-the-primes.pdf) (940 pages, [known issues under review](https://math216.wordpress.com/2026/11/20/hurried-announcement-alessandro-masullo-grh/)).

**Parked for Phase 3.** Use the Masullo formalization’s errata to ask whether a reported trace-formula issue has a counterpart in Alpöge’s deformalized spine and, if so, how that step is justified. [Masullo formalization](https://github.com/mccorvie/riemann-masullo) · [ERRATA.md](https://github.com/mccorvie/riemann-masullo/blob/main/ERRATA.md)

The repository contains analysis code, metadata, measurements and reading notes. Pinned links take readers to the original mathematical source.
