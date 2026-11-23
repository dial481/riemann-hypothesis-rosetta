# Where `anyGeometry` occurs in the checked RH proof

The constant-True predicate `GlobalTheory.Mem.Top.Bl.anyGeometry` is eight dependency edges from `riemannHypothesis` on a kernel-checked path. Beside it, `geoOf` requires a positive integer satisfying `IsGeoOf` and a `HasTrueSurf` witness. None of the five theorems uses this predicate. [Original definitions](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Definitions/AutomorphicMembership/OverIx.lean#L16) · [Checked path](anygeometry-path.tsv)

The final statement is Mathlib’s `RiemannHypothesis` and its proof uses the standard three axioms, so the predicate choice does not bear on whether this theorem is proved. The checked route does not use the geometric conditions suggested by these names. These tables do not locate the argument’s mathematical content. [Main theorem](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Main.lean#L4) · [Mathlib statement](https://github.com/leanprover-community/mathlib4/blob/0df444a360eaa60ab8c11dca51a86af692955474/Mathlib/NumberTheory/LSeries/RiemannZeta.lean#L185) · [Axioms](anygeometry-axioms.tsv)

## The eight edges

Each row gives the declaration’s starting line. Each arrow to the following row has a `value` edge between those exact constant names in Shore’s kernel edge table. Searching backwards from the predicate, one edge per layer, establishes that the path is shortest. The search retains the declaration graph’s distinct declaration and constant endpoint kinds. [Edge-by-edge data](anygeometry-path.tsv)

| Distance from RH | Declaration | Original source |
| ---: | --- | --- |
| 0 | `riemannHypothesis` | [Main.lean, line 4](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Main.lean#L4) |
| 1 | `rhOfAll` | [MainTheorems.lean, line 9](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Supplements/Kernels/MainTheorems.lean#L9) |
| 2 | `allChi` | [MainTheorems.lean, line 7](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Supplements/Kernels/MainTheorems.lean#L7) |
| 3 | `UpperTheory.FinalTheorems.everyCharacter` | [MainConclusion.lean, line 10](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean#L10) |
| 4 | `UpperTheory.FinalTheorems.everyCharacter_of_row` | [MainConclusion.lean, line 7](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean#L7) |
| 5 | `UpperTheory.LiteratureTheorems.every_character_of_literature_of_vWin` | [EveryCharacterOfLiteratureOfVWin.lean, line 810](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/EveryCharacterOfLiteratureOfVWin.lean#L810) |
| 6 | `UpperTheory.Lit.every_character_of_theta_integrals_local_matching` | [SiegelEisensteinSecondTermHypotheses.lean, line 69](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/SiegelEisensteinSecondTermHypotheses.lean#L69) |
| 7 | `GlobalTheory.Mem.Top.Bl.parametersOfDependence` | [Prm1.lean, line 20](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/Prm1.lean#L20) |
| 8 | `GlobalTheory.Mem.Top.Bl.anyGeometry` | [OverIx.lean, line 19](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Definitions/AutomorphicMembership/OverIx.lean#L19) |

Harry Tong independently found `anyGeometry` in all five compiled dependency closures. His RH witness gives a second shortest path of eight edges. It shares steps 0–6 above, then passes through `UpperTheory.Lit.nonempty_hyps_definite_side_of_closed_bound` and reaches `GlobalTheory.Mem.Top.Bl.anyGeometry`. Both alternate edges occur as value references in Shore’s kernel data. [Tong’s compiled dependency audit](https://github.com/harrytong/rh-verification/blob/f2f706c1e625702ea2f5f7be09604b264eca305b/RH_critics_dependency_findings.md#exact-witness-paths)

## Reach and source occurrences

In the original tree, `geoOf` starts at line 16 and `anyGeometry` at line 19 of `OverIx.lean`. Rosetta’s source trace reaches `anyGeometry` at depth 8. It misses `GlobalTheory.Mem.Top.Bl.geoOf`, `GlobalTheory.ShFam.IsGeoOf` and `GlobalTheory.ShFam.Pad.HasTrueSurf`. Shore records zero owned kernel constants and zero incident constant edges for each of these three declarations. [Trace lookup](anygeometry-trace.tsv) · [Masks and incident edges](anygeometry-masks.tsv)

The mask for `anyGeometry` is 31, the sum of the five target bits. The named constants `GlobalTheory.Mem.Top.Bl.GeoCl`, `GlobalTheory.Fc.HypsAlt`, `Formalism.L2.Geo.geoDegenerate`, `UpperTheory.Top.TopG`, `UpperTheory.Top.zeroFreeAll_of_topG` and `UpperTheory.LiteratureTheorems.every_character_of_literature_of_vWin` also have mask 31. Bit 1 marks the RH cone. [Mask table](anygeometry-masks.tsv) · [Shore’s target order](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/data/per-theorem.tsv)

Across original Lean source files under `src/`, the text `anyGeometry` occurs in 24 files. In the pruned revision it occurs in 11 files, its constant-True definition is at line 20, and `IsGeoOf` and `HasTrueSurf` each occur in zero files. These are case-sensitive text counts, including definitions. [Per-file occurrences](anygeometry-source.tsv) · [Pruned definition](https://github.com/leanprover-community/riemann-hypothesis/blob/e5ae821a00834f8043e987947f8151cc769bafe2/src/Development/AbelianVarietyTheory/Definitions/AutomorphicMembership/OverIx.lean#L20)

## Direct callers and transitive dependents

29 declarations refer directly to `anyGeometry`. The kernel edge table records 14 distinct referring constants (22 edge rows: 10 type, 12 value), all in the RH cone. The constant edge table covers the kernel closure of the five theorems, and the declaration table covers the whole project in Main’s compiled environment. A constant may reference the predicate in both its type and its value. [Direct kernel edges](anygeometry-direct.tsv) · [Shore’s data schema](https://github.com/james-shore/rh-proof-dependencies/tree/v0.2.1)

Of the 48 distinct declarations that depend on the predicate, 24 lie in the RH cone. The predicate itself is excluded. The distance below is the shortest number of declaration-graph edges from the listed declaration to the predicate. Cone membership uses the union of the theorem masks of the declaration’s non-shared owned project constants. [All 48 dependents](anygeometry-dependents.tsv)

| Distance to predicate | RH-cone declaration | Original source |
| ---: | --- | --- |
| 1 | `GlobalTheory.Fc.S0.Open0ProofU.open_orbit_of_unramified_exponents_alt` | [OpenOrbitOfUnramifiedExponents.lean, line 39](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/OpenOrbitOfUnramifiedExponents.lean#L39) |
| 1 | `GlobalTheory.Fc.S0.StageU.hypotheses_nonempty_of_unramified_exponents_alt` | [HypothesesNonemptyOfUnramifiedExponents.lean, line 41](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/HypothesesNonemptyOfUnramifiedExponents.lean#L41) |
| 1 | `GlobalTheory.Fc.StageOneU.member_bundles_large_unramified_exponents_alt` | [MemberBundlesLargeUnramifiedExponents.lean, line 33](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/MemberBundlesLargeUnramifiedExponents.lean#L33) |
| 1 | `GlobalTheory.Mem.Top.Bl.exists_baseLattice_of_pair_alt` | [ExistsBaseLatticeOfPrime.lean, line 36](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/ExistsBaseLatticeOfPrime.lean#L36) |
| 1 | `GlobalTheory.Mem.Top.Bl.exists_baseLattice_of_prime_alt` | [ExistsBaseLatticeOfPrime.lean, line 57](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/ExistsBaseLatticeOfPrime.lean#L57) |
| 1 | `GlobalTheory.Mem.Top.Bl.parametersOfDependence` | [Prm1.lean, line 20](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/Prm1.lean#L20) |
| 1 | `GlobalTheory.Mem.Top.Closing.divEx_geoCl` | [PublishedInputsImplyConclusion.lean, line 39](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Proofs/IwasawaDecomposition/PublishedInputsImplyConclusion.lean#L39) |
| 1 | `GlobalTheory.Mem.Top.Closing.memberE_closing_alt_alt` | [MemberEClosing.lean, line 17](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/MemberEClosing.lean#L17) |
| 1 | `GlobalTheory.Mem.Top.DivRec.divEx_of_ox` | [TupPinsOfMuIsW.lean, line 211](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Proofs/IwasawaDecomposition/TupPinsOfMuIsW.lean#L211) |
| 1 | `GlobalTheory.Mem.Top.DivRec.divEx_prov` | [TupPinsOfMuIsW.lean, line 204](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Proofs/IwasawaDecomposition/TupPinsOfMuIsW.lean#L204) |
| 1 | `GlobalTheory.T.large_unramified_exponent_bundles_exist_alt` | [MemberBundlesLargeUnramifiedExponents.lean, line 68](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/MemberBundlesLargeUnramifiedExponents.lean#L68) |
| 1 | `GlobalTheory.T.member_exists_baseLattice_alt` | [ExistsBaseLatticeOfPrime.lean, line 79](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/ExistsBaseLatticeOfPrime.lean#L79) |
| 1 | `UpperTheory.GalC.final_of_alt` | [LinkNFam.lean, line 74](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/LinkNFam.lean#L74) |
| 1 | `UpperTheory.Lit.nonempty_hyps_definite_side_of_closed_bound` | [SiegelEisensteinSecondTermHypotheses.lean, line 44](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/SiegelEisensteinSecondTermHypotheses.lean#L44) |
| 2 | `GlobalTheory.NLink.Final.mainTheorem` | [MainTyzTer.lean, line 22](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/MainTyzTer.lean#L22) |
| 2 | `GlobalTheory.T.open0_of_unitary_group_hypotheses` | [OpenOrbitOfUnramifiedExponents.lean, line 74](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/OpenOrbitOfUnramifiedExponents.lean#L74) |
| 2 | `UpperTheory.GalC.final_alt_alt` | [CFinal.lean, line 19](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/CFinal.lean#L19) |
| 2 | `UpperTheory.Lit.every_character_of_theta_integrals_local_matching` | [SiegelEisensteinSecondTermHypotheses.lean, line 69](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/SiegelEisensteinSecondTermHypotheses.lean#L69) |
| 3 | `UpperTheory.LiteratureTheorems.every_character_of_literature_of_vWin` | [EveryCharacterOfLiteratureOfVWin.lean, line 810](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/EveryCharacterOfLiteratureOfVWin.lean#L810) |
| 4 | `UpperTheory.FinalTheorems.everyCharacter_of_row` | [MainConclusion.lean, line 7](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean#L7) |
| 5 | `UpperTheory.FinalTheorems.everyCharacter` | [MainConclusion.lean, line 10](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean#L10) |
| 6 | `allChi` | [MainTheorems.lean, line 7](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Supplements/Kernels/MainTheorems.lean#L7) |
| 7 | `rhOfAll` | [MainTheorems.lean, line 9](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Supplements/Kernels/MainTheorems.lean#L9) |
| 8 | `riemannHypothesis` | [Main.lean, line 4](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Main.lean#L4) |

The spine anchors at ranks 16, 17, 19, 21, 35 and 157 depend on the predicate. This compares each anchor by its full declaration name with the reverse closure above. [Spine anchors and distances](anygeometry-spine.tsv)

In the RH kernel mask, the axioms are `propext`, `Quot.sound` and `Classical.choice`. The checks for `sorryAx`, `Lean.ofReduceBool`, `Lean.trustCompiler`, project axioms and project opaque constants returned zero. This audit reads the published compiled data and the pinned sources. [Axiom rows](anygeometry-axioms.tsv) · [James Shore’s v0.2.1 data](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)

## Credits and reproduction

Jenny Lorraine Nielsen identified the constant-True predicate. Frank Chu asked whether the path from Main runs through it. James Shore supplied the constant and declaration tables. His list of used declarations comes from [Andrew Sutherland’s kernel export](https://math.mit.edu/~drew/grh/). Levent Alpöge, a researcher at Anthropic, supplied the proof, and the Lean community’s upstream repository supplies the pruned revision. This analysis used AI assistance, including an Anthropic model. [Nielsen’s paper](https://philarchive.org/rec/NIEIOT-2) · [Chu’s question](https://dev.to/frankchu/grh-proofs-geometry-is-fun-true-in-24-files-2n2b) · [Shore’s release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1) · [Alpöge’s affiliation](https://alpo.ge/) · [Original proof](https://github.com/leanprover-community/riemann-hypothesis/tree/40e56bab026552e089d7afcfeff08d2defb9c005) · [Pruned source](https://github.com/leanprover-community/riemann-hypothesis/tree/e5ae821a00834f8043e987947f8151cc769bafe2)

Run from the Rosetta checkout with Git, curl, tar and the Python dependencies in `requirements.txt`. The generator verifies both source-tree IDs, the four release SHA-256 values, and the byte hashes of the 20 frozen artifacts before and after analysis. It writes the note and the tables after the numerical checks pass. The content manifest covers the generated Markdown and UTF-8 TSV files. [Generator](../analysis/anygeometry.py) · [Content manifest](anygeometry-content-sha256.json)

```bash
export LC_ALL=C
set -eo pipefail
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p inputs/anygeometry/{original,upstream,shore}
for pin in original:40e56bab026552e089d7afcfeff08d2defb9c005 upstream:e5ae821a00834f8043e987947f8151cc769bafe2; do
  curl -fLsS --retry 3 "https://codeload.github.com/leanprover-community/riemann-hypothesis/tar.gz/${pin#*:}" |
    tar -xz -C "inputs/anygeometry/${pin%:*}" --strip-components=1
done
release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1
for file in constants.csv.gz decls.csv.gz decl_edges.parquet edges.parquet; do
  curl -fLsS --retry 3 "$release/$file" -o "inputs/anygeometry/shore/$file"
done
.venv/bin/python analysis/anygeometry.py inputs/anygeometry/original inputs/anygeometry/upstream inputs/anygeometry/shore --out inputs/anygeometry/replayed
cmp results/anygeometry-content-sha256.json inputs/anygeometry/replayed/anygeometry-content-sha256.json
```
