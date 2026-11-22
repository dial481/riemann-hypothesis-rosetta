# Upstream module comparison

Of 25,792 original proof files removed upstream as unused, the frozen RH trace reached 30 and missed 25,762 (99.9%). Upstream retained 15,249 other files the trace missed. Trace absence alone does not establish mathematical irrelevance.

The baseline is [the original proof](https://github.com/leanprover-community/riemann-hypothesis/tree/40e56bab026552e089d7afcfeff08d2defb9c005) and the comparison uses [one upstream commit](https://github.com/leanprover-community/riemann-hypothesis/tree/e5ae821a00834f8043e987947f8151cc769bafe2). Each graph uses the Mathlib revision in its own dependency manifest, `0df444a360eaa60ab8c11dca51a86af692955474` and `fc4f59e577feb1a4956671bc04ac18aaaf8cd842` respectively. The project-file boundary is `src/**/*.lean`, including files directly under `src/`. A path is trace-reached when at least one frozen trace site belongs to it. All upstream measurements use module imports.

| Original paths | Trace reached | Trace unreached | Total |
|---|---:|---:|---:|
| Removed upstream as unused | 30 | 25,762 | 25,792 |
| Retained upstream | 134,146 | 15,249 | 149,395 |
| All original paths | 134,176 | 41,011 | 175,187 |

## Kernel cross-check on the original files

Of 28,900 files with no owned declaration in the union of the five kernel target cones, 25,756 were removed upstream as unused and 3,144 were retained. Of 36 removed files with a kernel-used declaration, the frozen trace reached 30. The 15,249 retained trace misses include 12,235 RH-used files, 3 used by another target but outside RH, and 3,011 unused by all five.

At file level, RH recall is 134,043/146,284 = 91.6%. Precision is 134,043/134,176 = 99.90%. The join uses each declaration owner's original file. The union from the declaration table agrees with the union of nonshared project constants' theorem masks. Bit 1 selects RH. [Per-file masks and trace membership](upstream/e5ae821a/kernel-file-usage.tsv.gz) · [v0.2.1 schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md)

**Unverified at the upstream pin. No Lean build was run.** For all 3,144 retained kernel-unused files, we enumerated their direct upstream importers and joined each importer and target to the original whole-environment compiled declaration edges (type or value). On these retained import pairs, 2,354 targets are labelled **referenced by an unused declaration** and 790 **conduit only**. The latter means no original compiled declaration edge was found from these importers. Neither label establishes what upstream's kernel would use. The importer table also identifies former direct imports.

The upstream source check found corroborating command or token evidence from an originally unused caller for 1,982 targets with a compiled reference. For 39 provisionally labelled conduits it found a candidate upstream source reference. Those disagreements are retained for review. The evidence table separates byte-identical caller commands, scoped identifier mentions, and historical edges whose upstream use remains unconfirmed. Identifier mentions can occur in tactic alternatives. Implicit arguments and elaborator-generated references can lack a literal token. [All file labels](upstream/e5ae821a/retained-unused.tsv.gz) · [Every retained importer](upstream/e5ae821a/retained-importers.tsv.gz) · [Declaration witnesses and upstream lines](upstream/e5ae821a/importer-references.tsv.gz)

The 36 removed kernel-used files owned 109 declarations in total. Across the upstream source tree, 14 have the same public qualified name or a byte-identical command under another identity. All declarations were found elsewhere for 7 files, some for 2, and none under the search criteria for 27. A missing name leaves open renaming, inlining, and equivalent mathematics. A matching public name establishes identity by name, not equivalence of proofs. Module-private names encode the original path. Unconfirmed same-spelling candidates appear separately. [All 36 file outcomes](upstream/e5ae821a/removed-used-files.tsv) · [Every declaration and upstream location](upstream/e5ae821a/removed-used-declarations.tsv)

Upstream adds 1 path outside the original denominator (`src/Challenge.lean`). [Full path classification](upstream/e5ae821a/path-status.tsv.gz)

## Main and the frozen spine

| Module-graph measure | Original | Upstream |
|---|---:|---:|
| Project files | 175,187 | 149,396 |
| Project files reachable from Main | 175,187 | 149,395 |
| Distinct imports within the reachable project graph | 753,261 | 725,379 |
| Longest project path (imports) | 202 | 198 |
| Longest path including pinned Mathlib (imports) | 370 | 377 |
| Longest path including external terminals (imports) | 371 | 378 |
| Other project modules disconnected by removing RowSrc | 13,054 | 12,424 |

199 of the 200 frozen spine paths survive. 199 remain reachable by imports from Main. Original rank 45, [VolumeTheoremOfInputsStatement](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicSpectrum/Proofs/DivisibilityProofs/VolumeTheoremOfInputsStatement.lean), was removed upstream as unused. [All spine paths, ranks and cuts](upstream/e5ae821a/spine-survival.tsv) · [Longest paths](upstream/e5ae821a/longest-paths.json)

## Five largest project cuts

Removing a module disconnects the other project modules whose every import path from Main passes through it. The cut excludes the removed module itself. The ranking excludes Main. Each reported cut was also checked by deleting the module and walking the graph again.

| Rank | Original module | Original cut | Upstream module | Upstream cut |
|---:|---|---:|---|---:|
| 1 | [MainTheoremsAll](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Supplements/Kernels/MainTheoremsAll.lean) | 175,184 | [MainConclusion](https://github.com/leanprover-community/riemann-hypothesis/blob/e5ae821a00834f8043e987947f8151cc769bafe2/src/Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean) | 149,389 |
| 2 | [RowSrc](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/RowSrc.lean) | 13,054 | [RowSrc](https://github.com/leanprover-community/riemann-hypothesis/blob/e5ae821a00834f8043e987947f8151cc769bafe2/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/RowSrc.lean) | 12,424 |
| 3 | [GaloisRepresentationsOfThetaLift](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/GaloisRepresentationsOfThetaLift.lean) | 12,271 | [GaloisRepresentationsOfThetaLift](https://github.com/leanprover-community/riemann-hypothesis/blob/e5ae821a00834f8043e987947f8151cc769bafe2/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/GaloisRepresentationsOfThetaLift.lean) | 11,694 |
| 4 | [WeightOneGeometricRealization](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/GeometricFlagBases/WeightOneGeometricRealization.lean) | 10,801 | [WeightOneGeometricRealization](https://github.com/leanprover-community/riemann-hypothesis/blob/e5ae821a00834f8043e987947f8151cc769bafe2/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/GeometricFlagBases/WeightOneGeometricRealization.lean) | 10,277 |
| 5 | [GeometricRealizationOfWeightOne](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/GeometricFlagBases/GeometricRealizationOfWeightOne.lean) | 10,429 | [GeometricRealizationOfWeightOne](https://github.com/leanprover-community/riemann-hypothesis/blob/e5ae821a00834f8043e987947f8151cc769bafe2/src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/GeometricFlagBases/GeometricRealizationOfWeightOne.lean) | 9,911 |

## Community membership

The reachable project graph partitions into 94 original and 103 upstream communities. Among 149,395 paths in both reachable graphs, 98,533 (66.0%) fall into aligned pairs and 50,862 (34.0%) fall outside those pairs. The alignment maximizes total shared membership across a one-to-one assignment. Community numbers are local to each partition. A split can place a retained module outside the alignment even if many of its neighbors stay together.

| Original community | Shared paths | Largest upstream overlap | Paths in overlap |
|---:|---:|---:|---:|
| 1 | 16,523 | 1 | 11,466 |
| 2 | 9,900 | 6 | 7,398 |
| 3 | 5,744 | 2 | 4,846 |
| 4 | 8,016 | 3 | 5,546 |
| 5 | 7,912 | 13 | 3,833 |
| 6 | 6,839 | 4 | 5,833 |
| 7 | 6,617 | 10 | 3,528 |
| 8 | 2,856 | 5 | 2,391 |
| 9 | 6,136 | 8 | 5,817 |
| 10 | 5,577 | 5 | 4,451 |

The table follows the ten largest original communities. [All overlaps and aligned pairs](upstream/e5ae821a/community-overlap.tsv) · [Upstream per-module memberships and cuts](upstream/e5ae821a/metrics.tsv.gz)

## Reproduce

Run from the repository root with the README environment, original source inputs and byte-reproduced baseline in place. The runner checks both Git trees, performs the removal gate, repeats the module inventory, graph and community stages, then verifies the headers, distances, ranks and cuts. The SHA-256 manifest covers the module outputs, comparison tables and this report.

```bash
set -eu
export LC_ALL=C
cmp results/independent-sha256.json inputs/reproduced/independent-sha256.json
mkdir -p inputs/upstream inputs/upstream-mathlib
curl -fsSL --retry 3 https://codeload.github.com/leanprover-community/riemann-hypothesis/tar.gz/e5ae821a00834f8043e987947f8151cc769bafe2 -o inputs/upstream-proof.tgz
tar xzf inputs/upstream-proof.tgz --strip-components=1 -C inputs/upstream
curl -fsSL --retry 3 https://codeload.github.com/leanprover-community/mathlib4/tar.gz/fc4f59e577feb1a4956671bc04ac18aaaf8cd842 -o inputs/upstream-mathlib.tgz
tar xzf inputs/upstream-mathlib.tgz --strip-components=1 -C inputs/upstream-mathlib
mkdir -p inputs/kernel
for file in constants.csv.gz decls.csv.gz decl_edges.csv.gz; do
  curl -fsSL --retry 3 "https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1/$file" -o "inputs/kernel/$file"
done
.venv/bin/python analysis/upstream.py inputs/upstream inputs/upstream-mathlib --original-proof inputs/lean --kernel inputs/kernel --dest inputs/replayed
cmp results/upstream/e5ae821a/sha256.json inputs/replayed/upstream/e5ae821a/sha256.json
cmp results/independent-sha256.json inputs/reproduced/independent-sha256.json
```
