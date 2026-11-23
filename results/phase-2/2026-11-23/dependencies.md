# Dependency checks for the rebuilt statement site

**133 retained links have no dependency between their exact declaration owners in either compiled graph.** Original source imports or declaration order rule out 79 of those links. For 14, both graphs have a path in the opposite direction. Of the 1,965 retained links in Andrew O’Desky’s *Statements of the Lean RH project*, 1,746 have a forward path in James Shore’s graph and 86 are unsettled. These results describe the listed Lean declarations. A statement can have a mathematical motivation outside those declarations. [Owner table](owner-no-path.tsv) · [Every directed link](checked.tsv.gz)

| Measure | Reproduced | Expected | Difference |
| --- | ---: | ---: | ---: |
| Retained directed links | 1,965 | 1,965 | 0 |
| Forward path in Shore | 1,746 | 1,746 | 0 |
| ↳ Path in Proofs & Reasons | 1,742 | 1,742 | 0 |
| ↳ Not testable in Proofs & Reasons | 4 | 4 | 0 |
| ↳ Contradicted in Proofs & Reasons | 0 | 0 | 0 |
| No dependency between tested owners in either graph | 133 | 133 | 0 |
| ↳ Ruled out by source imports or line order | 79 | 79 | 0 |
| ↳ Opposite path in both graphs | 14 | 14 | 0 |
| Unsettled | 86 | 86 | 0 |
| ↳ Unmatched printed name | 77 | 77 | 0 |
| ↳ Same declaration | 3 | 3 | 0 |
| ↳ No Shore path and second graph not testable | 5 | 5 | 0 |
| ↳ Graphs disagree | 1 | 1 | 0 |
| Links with a path in either graph forbidden by source | 0 | 0 | 0 |

Indented rows describe subsets. Source exclusions and opposite paths can overlap. The expected figures are the reviewer’s counts. The per-link table identifies A and B and records each result separately.

## How a link is tested

A → B means A lists B in its “Depends on” field. Of the 2,399 links in the November 23 snapshot, 1,965 also occur on November 22. The 434 additions have empty evidence fields. Of these, 106 connect two older card IDs and 328 have an unmapped endpoint. A surviving statement can inherit links from one it absorbed. The November 22 snapshot contained 2,481 links, of which 516 disappeared. The theorem index was captured at 2026-11-23T14:16:17+00:00 and the definitions page at 2026-11-23T14:16:19+00:00. The Lean name mapping is from 2026-11-22T17:15:18Z. [Andrew O’Desky’s statement index](https://andrewodesky.com/rh/index.html) · [Snapshot hashes](snapshots.json) · [Historical citation audit](../odesky-audit.md)

1. Resolve each printed name exactly. Map an identified structure field to its owning declaration. Search all pairs of owners for a positive-length forward path, preferring a direct witness. A common owner is recorded separately from a path. For a negative conclusion every printed name must resolve, the two sets of owners must be disjoint and every owner must be present in the second graph. The historical audit preserves the earlier single-graph counts. [James Shore’s v0.2.1 declaration graph](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)
2. Search the signature and body edges in the RH graph from Proofs & Reasons, led by Simon DeDeo. Match both file and exact owner name. A found path supplies a witness even when another endpoint is absent. If there is no witness and an endpoint is missing, the result is *not testable*. This graph covers the RH cone. Its output can therefore confirm fewer paths than the whole-project graph. [Proofs & Reasons](https://proofsandreasons.io/rh-graph.html) · [Pinned declaration graph](https://photos.proofsandreasons.io/alp-graph/rh/alp-declaration-graph-used-by-rh.json.gz)
3. Read the import headers of all 175,187 original project source files. Check each file’s SHA-256 and imports against the frozen inventory and follow the transitive imports. In a shared file, compare the owners’ declaration-start lines. A source exclusion requires every A–B combination to fail. An available import or earlier line permits a dependency without establishing one. The evidence table records the number of owner pairs under each source test. Every positive owner pair in both directions was checked against its own files and lines. [Levent Alpöge’s original source](https://github.com/leanprover-community/riemann-hypothesis/tree/40e56bab026552e089d7afcfeff08d2defb9c005)

## Cases where the second graph changes what can be reported

The table below identifies Shore paths that the second graph cannot test and the pairs removed from the earlier exact-name list of 139. Each row also appears in the full evidence table. The owner table contains the pairs with two negative results.

| A | Listed B | Shore | Proofs & Reasons | Missing owner or forward witness in Proofs & Reasons |
| --- | --- | --- | --- | --- |
| [divisibility](https://andrewodesky.com/rh/s/padic/5+/1753/) | [dwork-integrality](https://andrewodesky.com/rh/s/padic/5+/0107/) | no path | not testable | `Formalism.InvariantFactorPaths.G7.FrameJetExcessBound` |
| [divisibility](https://andrewodesky.com/rh/s/padic/5+/1753/) | [hasse-jet-identity](https://andrewodesky.com/rh/s/alg/5+/0116/) | no path | not testable | `Formalism.InvariantFactorPaths.G7.FrameJetExcessBound` |
| [divisibility](https://andrewodesky.com/rh/s/padic/5+/1753/) | [minor-derivative-cap](https://andrewodesky.com/rh/s/alg/5+/0135/) | no path | not testable | `Formalism.InvariantFactorPaths.G7.FrameJetExcessBound` |
| [family-point-kernel-bases](https://andrewodesky.com/rh/s/family-point-kernel-bases.html) | [family-point-kernel-ideals](https://andrewodesky.com/rh/s/family-point-kernel-ideals.html) | no path | path | `Formalism.L2.Ker.Base → Formalism.MainNotions.TaylorLogMetric.IsCurveIdeal` |
| [main](https://andrewodesky.com/rh/s/ant/1/0001/) | [z1-primitive-zero-reflection](https://andrewodesky.com/rh/s/ant/5+/1738/) | transitive | not testable | `Claim.prim_reflect, LFunction_eq_zero_re, LFunction_ne_zero_of_half_lt_re` |
| [selmer-vanishing](https://andrewodesky.com/rh/s/gc/5+/1118/) | [u4-frobenius-determines-semisimple](https://andrewodesky.com/rh/s/agr/5+/1253/) | no path | not testable | `UpperTheory.V.Af.isoOfFrob` |
| [u2-cyclic-spectral-lifting](https://andrewodesky.com/rh/s/agr/5+/1165/) | [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/agr/5+/1205/) | no path | not testable | `UpperTheory.V.Af.compatCsd` |
| [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/agr/5+/1205/) | [u2-spherical-hecke-commutativity](https://andrewodesky.com/rh/s/rep/5+/1194/) | transitive | not testable | `UpperTheory.V.Af.compatCsd` |
| [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/agr/5+/1205/) | [u4-frobenius-determines-semisimple](https://andrewodesky.com/rh/s/agr/5+/1253/) | transitive | not testable | `UpperTheory.V.Af.compatCsd, UpperTheory.V.Af.isoOfFrob` |
| [u3-csd-local-global-compatibility](https://andrewodesky.com/rh/s/agr/5+/1205/) | [v3-spherical-satake-existence](https://andrewodesky.com/rh/s/rep/5+/1447/) | transitive | not testable | `UpperTheory.V.Af.compatCsd` |

For `family-point-kernel-bases` → `family-point-kernel-ideals`, Proofs & Reasons folds the shared helper `Formalism.MainNotions.GL3Theta.cube2._proof_2` into `cube2`. That supplies an edge from `Formalism.MainNotions.GL3Theta.IsTwoTorsionPointUnkilled` to `Formalism.MainNotions.GL3Theta.cube2`. Removing that single folded edge eliminates every forward path between the owners of the two pages in Proofs & Reasons. Shore records a value edge from each declaration to the shared helper and no path from the former declaration to the latter. The source at lines 198–200 defines a predicate about membership in a subgroup and makes no call to `cube2`, defined at line 124. The link remains unsettled. [Predicate source](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/SharpRestriction/GlobalSchurBounds/GL3Theta.lean#L198-L200) · [cube2 source](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/SharpRestriction/GlobalSchurBounds/GL3Theta.lean#L124-L127)

**Name-resolution footnote.** Allowing the bare `FrameLA1` to stand for `Formalism.HN.FrameLA1` moved 5 links into the earlier single-graph no-path list. Exact naming leaves them unsettled. [`slope-inequality`](https://andrewodesky.com/rh/s/arak/5+/1120/) → [`image-slope`](https://andrewodesky.com/rh/s/arak/5+/0119/) · [`slope-inequality`](https://andrewodesky.com/rh/s/arak/5+/1120/) → [`q11-hn-slopes`](https://andrewodesky.com/rh/s/arak/5+/0147/) · [`slope-inequality`](https://andrewodesky.com/rh/s/arak/5+/1120/) → [`q11-hn-threshold`](https://andrewodesky.com/rh/s/arak/5+/0148/) · [`slope-inequality`](https://andrewodesky.com/rh/s/arak/5+/1120/) → [`q11-lattice-realizations`](https://andrewodesky.com/rh/s/arak/5+/0149/) · [`slope-inequality`](https://andrewodesky.com/rh/s/arak/5+/1120/) → [`q11-layer-cake`](https://andrewodesky.com/rh/s/alg/5+/0150/)

## Replay

Run from the checkout root with the original source directory in `PROOF` and the November 22 citation and dependency outputs in place. The script checks both compiled input digests. The content manifest hashes decompressed table bytes.

```bash
export LC_ALL=C
r=results/phase-2/2026-11-23
mkdir -p inputs/audit
release=https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1
curl -fL --retry 3 "$release/decl_edges.parquet" -o inputs/audit/decl_edges.parquet
curl -fL --retry 3 https://photos.proofsandreasons.io/alp-graph/rh/alp-declaration-graph-used-by-rh.json.gz -o inputs/audit/pr-graph.json.gz
.venv/bin/python analysis/catalogue_rebuild.py inputs/audit/decl_edges.parquet inputs/audit/pr-graph.json.gz "$PROOF" --out inputs/rebuilt-audit
cmp "$r/content-sha256.json" inputs/rebuilt-audit/content-sha256.json
```

To re-extract the statement pairs, place the two HTML captures in `inputs/rebuilt-html/` as `index.html` and `definitions.html`. The extractor verifies their recorded hashes. Run in the same shell.

```bash
.venv/bin/python analysis/statement_index.py inputs/rebuilt-html "$r/snapshots.json" inputs/cards.tsv --depends inputs/depends.tsv
cmp "$r/cards.tsv" inputs/cards.tsv
cmp "$r/depends.tsv" inputs/depends.tsv
```
