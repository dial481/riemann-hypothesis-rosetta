# Dependency checks for the rebuilt statement site

**133 retained links have no recorded path between the tested declarations in either of the two compiled declaration graphs.** Original source imports or declaration order rule out 79 of those links. For 14, both graphs have a path in the opposite direction. Of the 1,965 retained links in Andrew O’Desky’s *Statements of the Lean RH project*, 1,746 have a forward path in James Shore’s graph and 86 are unsettled. These results describe the listed Lean declarations. A statement can have a mathematical motivation outside those declarations. [Owner table](owner-no-path.tsv) · [Every directed link](checked.tsv.gz)

| Measure | Reproduced | Expected | Difference |
| --- | ---: | ---: | ---: |
| Retained directed links | 1,965 | 1,965 | 0 |
| Forward path in Shore | 1,746 | 1,746 | 0 |
| ↳ Path in Proofs & Reasons | 1,742 | 1,742 | 0 |
| ↳ Not testable in Proofs & Reasons | 4 | 4 | 0 |
| ↳ Contradicted in Proofs & Reasons | 0 | 0 | 0 |
| No recorded path between the tested declarations in either graph | 133 | 133 | 0 |
| ↳ Ruled out by source imports or line order | 79 | 79 | 0 |
| ↳ Opposite path in both graphs | 14 | 14 | 0 |
| Unsettled | 86 | 86 | 0 |
| ↳ Unmatched printed name | 77 | 77 | 0 |
| ↳ Same declaration | 3 | 3 | 0 |
| ↳ No Shore path and second graph not testable | 5 | 5 | 0 |
| ↳ Graphs disagree | 1 | 1 | 0 |
| Links with a path in either graph forbidden by source | 0 | 0 | 0 |

Indented rows describe subsets. Source exclusions and opposite paths can overlap. The expected figures are the reviewer’s counts. The per-link table identifies the citing page A and the linked page B. Its classification is based on the declarations printed on those pages.

## How a link is tested

A → B means A lists B in its “Depends on” field. Of the 2,399 links in the November 23 snapshot, 1,965 also occur on November 22. The 434 additions have empty evidence fields. Of these, 106 connect two older card IDs and 328 have an unmapped endpoint. A surviving statement can inherit links from one it absorbed. The November 22 snapshot contained 2,481 links, of which 516 disappeared. The theorem index was captured at 2026-11-23T14:16:17+00:00 and the definitions page at 2026-11-23T14:16:19+00:00. The Lean name mapping is from 2026-11-22T17:15:18Z. [Andrew O’Desky’s statement index](https://andrewodesky.com/rh/index.html) · [Snapshot hashes](snapshots.json) · [Historical citation audit](../odesky-audit.md)

The replay intersects the complete directed edge lists by the two card IDs, preserving direction. The SHA-256 of the [November 22 list](depends-2026-11-22.tsv) is `2ae4ce99a2c6af542c281e9a4dac2471d6c861936cdfa20b6d79922fe308a0d2`. The SHA-256 of the [November 23 14:16 UTC list](depends.tsv) is `34348795270fba02e0b753cf1de9316c5eb03a748ce227b180c95a63f5900c81`. The owner table takes display numbers, titles and addresses from a later capture at 2026-11-23T17:42:43+00:00 for theorems and 2026-11-23T17:42:44+00:00 for definitions. Its printed-name columns come from November 22. [Display citations](display-cards.tsv) · [Display snapshot hashes](display-snapshots.json)

1. Resolve each printed name exactly. Map an identified structure field to its owning declaration. When a field is absent from Shore’s constants table, match its qualified name and enclosing structure header in the pinned source to the parent’s file and header range in the compiled declaration table. Search all pairs of owners for a positive-length forward path, preferring a direct witness. A common owner is recorded separately from a path. For a negative conclusion every printed name must resolve, the two sets of owners must be disjoint and every owner must be present in the second graph. The historical audit preserves the earlier single-graph counts. [James Shore’s v0.2.1 declaration graph](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)
2. Search the signature and body edges in the RH graph from Proofs & Reasons, led by Simon DeDeo. Match both file and exact owner name. A found path supplies a witness even when another endpoint is absent. If there is no witness and an endpoint is missing, the result is *not testable*. This graph covers the RH cone. Its output can therefore confirm fewer paths than the whole-project graph. [Proofs & Reasons](https://proofsandreasons.io/rh-graph.html) · [Pinned declaration graph](https://photos.proofsandreasons.io/alp-graph/rh/alp-declaration-graph-used-by-rh.json.gz)
3. Read the import headers of all 175,187 original project source files. Check each file’s SHA-256 and imports against the frozen inventory and follow the transitive imports. In a shared file, a later declaration rules out a forward reference when both declarations are outside mutual blocks. If either declaration is in a mutual block, line order is inconclusive. A source exclusion requires every A–B combination to fail. An available import or earlier line permits a dependency without establishing one. The evidence table records the number of owner pairs under each source test. Every positive owner pair in both directions was checked against its own files and lines. [Levent Alpöge’s original source](https://github.com/leanprover-community/riemann-hypothesis/tree/40e56bab026552e089d7afcfeff08d2defb9c005)

## Cases where the second graph changes what can be reported

The table below identifies Shore paths that the second graph cannot test and the pairs removed from the earlier exact-name list of 139. Each row also appears in the full evidence table. The owner table contains the pairs with two negative results.

| A | Listed B | Shore | Proofs & Reasons | Missing owner or forward witness in Proofs & Reasons |
| --- | --- | --- | --- | --- |
| [divisibility](https://andrewodesky.com/rh/s/divisibility.html) | [dwork-integrality](https://andrewodesky.com/rh/lean/Formalism.MainNotions.FormalGroupSystem.Pf.sx_dwork/) | no path | not testable | `Formalism.InvariantFactorPaths.G7.FrameJetExcessBound` |
| [divisibility](https://andrewodesky.com/rh/s/divisibility.html) | [hasse-jet-identity](https://andrewodesky.com/rh/lean/Formalism.InvariantFactorPaths.G7.Top.e_one_identity/) | no path | not testable | `Formalism.InvariantFactorPaths.G7.FrameJetExcessBound` |
| [divisibility](https://andrewodesky.com/rh/s/divisibility.html) | [minor-derivative-cap](https://andrewodesky.com/rh/lean/Formalism.InvariantFactorPaths.G7.Top.hitsCapPos/) | no path | not testable | `Formalism.InvariantFactorPaths.G7.FrameJetExcessBound` |
| [family-point-kernel-bases](https://andrewodesky.com/rh/s/family-point-kernel-bases.html) | [family-point-kernel-ideals](https://andrewodesky.com/rh/s/family-point-kernel-ideals.html) | no path | path | `Formalism.L2.Ker.Base → Formalism.MainNotions.TaylorLogMetric.IsCurveIdeal` |
| [main](https://andrewodesky.com/rh/lean/riemannHypothesis/) | [z1-primitive-zero-reflection](https://andrewodesky.com/rh/lean/Claim.prim_reflect/) | transitive | not testable | `Claim.prim_reflect, LFunction_eq_zero_re, LFunction_ne_zero_of_half_lt_re` |
| [selmer-vanishing](https://andrewodesky.com/rh/lean/UpperTheory.V.Z.Kato.WeilSphericalRecords.katoTwoW_of_printsH/) | [u4-frobenius-determines-semisimple](https://andrewodesky.com/rh/s/u4-frobenius-determines-semisimple.html) | no path | not testable | `UpperTheory.V.Af.isoOfFrob` |
| [u2-cyclic-spectral-lifting](https://andrewodesky.com/rh/lean/UpperTheory.ConvolutionTheory.T.coreLift/) | [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/u3-csd-local-global-compatibility.html) | no path | not testable | `UpperTheory.V.Af.compatCsd` |
| [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/u3-csd-local-global-compatibility.html) | [u2-spherical-hecke-commutativity](https://andrewodesky.com/rh/lean/Formalism.UG.Final.HeckeCommGL/) | transitive | not testable | `UpperTheory.V.Af.compatCsd` |
| [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/u3-csd-local-global-compatibility.html) | [u4-frobenius-determines-semisimple](https://andrewodesky.com/rh/s/u4-frobenius-determines-semisimple.html) | transitive | not testable | `UpperTheory.V.Af.compatCsd, UpperTheory.V.Af.isoOfFrob` |
| [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/u3-csd-local-global-compatibility.html) | [v3-spherical-satake-existence](https://andrewodesky.com/rh/lean/GlobalTheory.SatakeExists.main/) | transitive | not testable | `UpperTheory.V.Af.compatCsd` |

For `family-point-kernel-bases` → `family-point-kernel-ideals`, Proofs & Reasons folds the shared helper `Formalism.MainNotions.GL3Theta.cube2._proof_2` into `cube2`. That supplies an edge from `Formalism.MainNotions.GL3Theta.IsTwoTorsionPointUnkilled` to `Formalism.MainNotions.GL3Theta.cube2`. Removing that single folded edge eliminates every forward path between the owners of the two pages in Proofs & Reasons. Shore records a value edge from each declaration to the shared helper and no path from the former declaration to the latter. The source at lines 198–200 defines a predicate about membership in a subgroup and makes no call to `cube2`, defined at line 124. The link remains unsettled. [Predicate source](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/SharpRestriction/GlobalSchurBounds/GL3Theta.lean#L198-L200) · [cube2 source](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/SharpRestriction/GlobalSchurBounds/GL3Theta.lean#L124-L127)

**Name-resolution footnote.** Allowing the bare `FrameLA1` to stand for `Formalism.HN.FrameLA1` moved 5 links into the earlier single-graph no-path list. Exact naming leaves them unsettled. [`slope-inequality`](https://andrewodesky.com/rh/lean/Formalism.HN.theoremF/) → [`image-slope`](https://andrewodesky.com/rh/lean/Formalism.HN.slope_inequality_mean/) · [`slope-inequality`](https://andrewodesky.com/rh/lean/Formalism.HN.theoremF/) → [`q11-hn-slopes`](https://andrewodesky.com/rh/lean/Formalism.HN.polygon_slopes_characterization/) · [`slope-inequality`](https://andrewodesky.com/rh/lean/Formalism.HN.theoremF/) → [`q11-hn-threshold`](https://andrewodesky.com/rh/lean/Formalism.HN.frameB_hnStep/) · [`slope-inequality`](https://andrewodesky.com/rh/lean/Formalism.HN.theoremF/) → [`q11-lattice-realizations`](https://andrewodesky.com/rh/lean/Formalism.HN.place_lattice_structure/) · [`slope-inequality`](https://andrewodesky.com/rh/lean/Formalism.HN.theoremF/) → [`q11-layer-cake`](https://andrewodesky.com/rh/lean/Formalism.CorankShareLayerCake.FR.layer_cake_formula/)

## Replay

Run from the checkout root with the original source directory in `PROOF` and the November 22 citation and dependency outputs in place. The script checks both compiled input digests and the hashes of both complete edge lists before taking their intersection. It reads back the owner table, checks both printed-name columns, and independently traverses both graphs to verify the opposite-path witnesses and their direct-edge flags. The content manifest hashes decompressed table bytes.

```bash
export LC_ALL=C
r=results/phase-2/2026-11-23
mkdir -p inputs/audit
release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1
curl -fL --retry 3 "$release/decl_edges.parquet" -o inputs/audit/decl_edges.parquet
curl -fL --retry 3 https://photos.proofsandreasons.io/alp-graph/rh/alp-declaration-graph-used-by-rh.json.gz -o inputs/audit/pr-graph.json.gz
.venv/bin/python analysis/catalogue_rebuild.py inputs/audit/decl_edges.parquet inputs/audit/pr-graph.json.gz "$PROOF" --out inputs/rebuilt-audit --verify-owner "$r/owner-no-path.tsv"
cmp "$r/content-sha256.json" inputs/rebuilt-audit/content-sha256.json
```

For extraction from the saved HTML, use the November 22 index, graph and two disambiguating pages under `inputs/audit/html/`, the 14:16 index and definitions under `inputs/rebuilt-html/`, and the 17:42 captures under `inputs/display-html/`. The historical reports record the input hashes. Run in the same shell.

```bash
.venv/bin/python analysis/catalogue_edge_lists.py inputs/audit/html inputs/rebuilt-html inputs/reproduced-pairs
cmp "$r/depends-2026-11-22.tsv" inputs/reproduced-pairs/depends-2026-11-22.tsv
cmp "$r/depends.tsv" inputs/reproduced-pairs/depends.tsv
.venv/bin/python analysis/statement_index.py inputs/rebuilt-html "$r/snapshots.json" inputs/cards.tsv
cmp "$r/cards.tsv" inputs/cards.tsv
.venv/bin/python analysis/statement_index.py inputs/display-html "$r/display-snapshots.json" inputs/display-cards.tsv
cmp "$r/display-cards.tsv" inputs/display-cards.tsv
```
