# Cross-validation of the original-source map

**The compiled RH declaration graph confirms 460 of 462 distinct direct witness edges. The remaining two are false positives of the text trace.** Neither source mention is a direct kernel dependency in either compiled dataset. Both datasets contain all 200 frozen spine anchors, and the declaration graph confirms every edge in 198 of the 200 reading trails. [Per-entry results](comparison-spine.tsv) · [Direct-edge checks](comparison-witness-edges.tsv) · [Alternative compiled trails](comparison-alternative-paths.json)

The original independent results were committed before the comparison inputs were downloaded. A subsequent audit of explicitly global names in our own trace identified three misresolved references. The corrected source-only outputs were frozen in `05f7faa` and then compared afresh with the same four digest-pinned inputs. The subsequent portable ranking freeze changed the module metrics file. The 200 witness chains and the reference inputs match the preceding freeze. [Rounded ranking freeze](https://github.com/dial481/riemann-hypothesis-rosetta/commit/3e5c5447e8ac9d62b8fc2d65e863857b5c2f0b15). [Original independent snapshot](https://github.com/dial481/riemann-hypothesis-rosetta/tree/aca7e1830b22c913bd9658c3f38e82128539beea/results) · [Corrected independent snapshot](https://github.com/dial481/riemann-hypothesis-rosetta/tree/05f7faa030529eccafb8e48ef826960462606422/results) · [Audit and change in membership](review/2026-11-21.md) · [Comparison data and input hashes](comparison.json)

## Scope and identity

The independent source scan begins at the one declaration `riemannHypothesis`. James Shore publishes bit masks for five theorems. His list of used declarations comes from [Andrew Sutherland’s kernel export](https://math.mit.edu/~drew/grh/). We selected bit 1, omitted shared auxiliaries when attributing proof use to a declaration, and joined on the **owning declaration’s file**. A generated constant’s module can differ from its owner’s file. Reconstructing the five sets with that distinction reproduced all five published counts. The Proofs & Reasons download is already restricted to RH and folds generated helpers, fields and constructors into owning declarations. For membership comparisons we match project module plus declaration name, removing Lean’s module-private name prefix. Line numbers provide an additional test on spine entries. [Shore’s schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md) · [Proofs & Reasons graph and schema](https://proofsandreasons.io/rh-graph.html)

| Quantity | Rosetta source scan | Shore RH | Proofs & Reasons RH |
|---|---:|---:|---:|
| Named project declarations reached | 641,100 | 804,891 | 806,982 |
| Project files containing one of those declarations | 134,176 | 146,284 | 146,352 |
| Named declarations shared with Rosetta | — | 638,752 | 638,819 |
| Declarations in Rosetta only, relative to this comparator | — | 2,348 | 2,281 |
| Declarations in the comparator only, relative to Rosetta | — | 166,139 | 168,163 |
| Comparator project files outside Main’s import closure | — | 0 | 0 |

The import census accounts for **all 175,187 project files**. Shore identifies uses of Mathlib constants in **5,081** modules for RH, all inside Rosetta’s **8,312** reachable Mathlib source modules. Imported files can supply tactics, notation, transitive imports, declarations for other targets or declarations simply unused by RH. Module reachability alone cannot decide which reason applies. [Import inventory](inventory.tsv.gz) · [Shore v0.2.1 release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)

Over **99.6%** of our named sites are present in each compiled dataset. The trace recovers **79.4%** of Shore’s RH set and **79.2%** of Proofs & Reasons’ RH set. Of the three-way discrepancies, **2,233** sites appear only in our trace and **166,098** appear in both compiled graphs but are missing from ours. The two compiled sets share **804,802** site identities, with **89** unique to Shore and **2,180** unique to Proofs & Reasons under our join. Possible contributors include auxiliary folding and source ownership. Individual disagreements remain available for investigation. [All discrepant site identities and membership flags](comparison-disagreements.tsv.gz)

| Shore target | Published declarations | Reconstructed from target mask | Shared with our RH-only trace |
|---|---:|---:|---:|
| riemannHypothesis | 804,891 | 804,891 | 638,752 |
| riemannZeta_eq_zero_re | 804,892 | 804,892 | 638,751 |
| LFunction_ne_zero_of_half_lt_re | 804,889 | 804,889 | 638,748 |
| LFunction_eq_zero_re | 804,899 | 804,899 | 638,748 |
| LFunction_eq_zero_re_of_isPrimitive | 804,892 | 804,892 | 638,748 |

The overlap column uses the same independent RH trace in every row. The other four rows show how closely Shore’s five targets overlap with that one trace. [Published per-theorem counts](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/data/per-theorem.tsv)

## Comparison with two source tracers

**On our usual module-plus-name join, Rosetta’s recall / precision is 79.36% / 99.63% against Shore and 79.16% / 99.64% against Proofs & Reasons.** Recall is the fraction of the reference recovered. Precision is the fraction of the tracer’s output present in the reference. These measure agreement about membership of the RH dependency set.

For a like-for-like comparison of the three *outputs*, we reran Yao Xu’s (cadamcat) and jae-63’s published Python scripts on the same original Lean source. Xu’s cone exports declaration names without owning modules. The table therefore uses distinct source-level names for all three tracers, stripping the compiled private-name prefix. Different declarations in different modules can share a name. This join checks fewer identity details than the module-plus-name figures above. Each reference covers RH at all depths. [Counts, intersections and denominators](comparison-peer-traces.json) · [Comparison code](../analysis/compare_peer_traces.py)

| Tracer and starting point | Distinct names | Recall vs Shore | Precision vs Shore | Recall vs Proofs & Reasons | Precision vs Proofs & Reasons |
|---|---:|---:|---:|---:|---:|
| Rosetta · `riemannHypothesis`, full traversal | 639,030 | 79.48% | 99.64% | 79.28% | 99.65% |
| cadamcat · `riemannHypothesis`, full traversal | 697,937 | 85.28% | 97.89% | 85.10% | 97.94% |
| jae-63 · `everyCharacter`, depth ≤12 | 157,117 | 19.41% | 98.96% | 19.37% | 99.03% |

Xu’s tracer recovers about six percentage points more of either complete compiled reference, with about 1.7 percentage points lower precision than Rosetta. Its published cone size of 697,937 matches our rerun. jae-63’s blueprint reports 157,116 declarations at depth ≤12. Our run returned 157,117 including the root. The gap to the *full* RH graph includes both the different root and the depth cutoff. [Xu’s method and published cone size](https://github.com/cadamcat/riemann-hypothesis-exposition/blob/b3e1e2df268c5d81a54594ef405dd4f7d51ce917/article/sections/A-method.tex) · [jae-63’s blueprint and reproduction commands](https://github.com/jae-63/rh-alpoge-blueprint/blob/0434143d80c94d491e2228e234507d38dfcb57d7/BLUEPRINT.md)

**At jae-63’s own root and depth**, a breadth-first traversal of the Proofs & Reasons signature and body edges from `UpperTheory.FinalTheorems.everyCharacter` reaches 185,223 distinct names in at most 12 steps. The overlap is 153,634, giving **82.95% recall and 97.78% precision**. Shore’s per-theorem masks do not encode this interior-root distance. This bounded comparison uses Proofs & Reasons alone.

<details>
<summary>Reproduce the peer comparison</summary>

Run after the independent reproduction and the four pinned reference downloads described in the README. Start at the Rosetta repository root. The two peer scripts write intermediate datasets to the ignored inputs directory.

jae-63’s indexer visits files within each directory in filesystem order, and the tracer uses the first declaration it sees for each name. In the pinned source, 4,046 names appear at multiple locations. The stable sort by module (column 3) makes that choice reproducible across filesystems while preserving source order within each module.

```bash
PY="$(pwd)/.venv/bin/python"
export RH_SRC="$(pwd)/inputs/lean/src"
PEERS="$(pwd)/inputs/peers"
mkdir -p "$PEERS"
git clone https://github.com/cadamcat/riemann-hypothesis-exposition "$PEERS/cadamcat"
git -C "$PEERS/cadamcat" checkout --detach b3e1e2df268c5d81a54594ef405dd4f7d51ce917
git clone https://github.com/jae-63/rh-alpoge-blueprint "$PEERS/jae"
git -C "$PEERS/jae" checkout --detach 0434143d80c94d491e2228e234507d38dfcb57d7
(
  set -e
  cd "$PEERS/cadamcat/tools"
  "$PY" -I index.py "$RH_SRC" out
  "$PY" -I edges.py build
  "$PY" -I edges.py cone riemannHypothesis
)
mkdir -p "$PEERS/jae/out"
"$PY" -I "$PEERS/jae/scripts/index.py" "$RH_SRC" "$PEERS/jae/out"
LC_ALL=C sort -t "$(printf '\t')" -s -k3,3 -o "$PEERS/jae/out/decls.tsv" "$PEERS/jae/out/decls.tsv"
(
  cd "$PEERS/jae/out" && "$PY" -I ../scripts/trace.py UpperTheory.FinalTheorems.everyCharacter 12 t12.json
)
ROSETTA_RESULTS=inputs/reproduced "$PY" analysis/compare_peer_traces.py inputs/comparisons \
  "$PEERS/cadamcat/tools/out/cone_riemannHypothesis.txt" "$PEERS/jae/out/t12.json"
cmp results/comparison-peer-traces.json inputs/reproduced/comparison-peer-traces.json
```

</details>

## Two source mentions excluded by both compiled graphs

| Spine rank | Caller → target | Outgoing edge rows from caller | Distinct constants referencing target | Direct edges, exact / including auxiliaries |
|---:|---|---:|---:|---:|
| 14 | `PositivityTheory.ThKEst.siegelAll_of` → `Formalism.UG.hform` | 327 | 1,630 | 0 / 0 |
| 128 | `GlobalTheory.FunObj.exists_coords` → `Formalism.GradedWeylDivisibility.sSIdxFinite` | 97 | 50 | 0 / 0 |

James Shore’s v0.2.1 kernel edge table contains 2,463 incoming edge rows for `hform` and 51 for `sSIdxFinite`. A caller may occur in both a type edge and a value edge. The distinct-caller column counts each constant once. The family check includes constants assigned to either declaration in the release, including shared auxiliaries, and dotted descendants of either endpoint. This includes `Formalism.UG.hform.eq_1`. No caller-family constant refers directly to a target-family constant in either case. [Kernel edges, v0.2.1](https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1/edges.parquet) · [Ownership and edge schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md) · [Counts, endpoint families and SHA-256](comparison-kernel-edges.json)

At rank 14, line 238 lists `hform` in a simplifier argument. At rank 128, line 78 mentions `sSIdxFinite` when constructing a local instance. Proofs & Reasons also has no direct edge for these pairs. Its compiled RH trails reach the target declarations through `Formalism.MainNotions.S.AutInst` and `GlobalTheory.Branching.finite_nablaSq`, respectively. The frozen spine and its source witnesses retain the original evidence. [Rank 14 source mention](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/WeilBound/ThetaLifts/FrameEstimates/SiegelAll.lean#L238) · [Rank 128 source mention](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Proofs/DivisorProofs/FiniteClPlusAndExistsCoords.lean#L78)

## Bartosz Naskręcki’s atlas

The atlas identifies 107 Lean declaration pins across 64 files, plus two conceptual nodes, in 14 mathematical components. Its model records the same archive hash, original mirror commit and Mathlib pin. We resolved all 107 pins against the original compiled declaration owners by file, source span and exact name or unambiguous qualified-name suffix. All 64 files are in Main’s import closure. The source trace matches 87 pins at the exact line, across 13 of 14 components.

**89 pins are in the kernel closure of `riemannHypothesis`, 17 are in one or more of the four other targets but outside RH, and 1 is outside all five.** That pin is `alternate-rh`, the declaration `UpperTheory.riemannHypothesis_of_everyCharacter`. It has a verified owner and mask zero. For each pin, `shore_five_theorem_mask` is the bitwise union of the theorem masks of its owned, nonshared project constants. A pin may contribute to multiple rows below.

| Mask bit | Kernel target | Pins |
|---:|---|---:|
| 1 | `riemannHypothesis` | 89 |
| 2 | `riemannZeta_eq_zero_re` | 90 |
| 4 | `LFunction_ne_zero_of_half_lt_re` | 87 |
| 8 | `LFunction_eq_zero_re` | 93 |
| 16 | `LFunction_eq_zero_re_of_isPrimitive` | 90 |

On 22 November 2026, the runtime check resolved atlas HEAD to `e9bdf8f4177403b66426f84b0ccbac15a4ad152a`. Its `data/model.json` was byte-identical to the analysis pin `d53b3804`. Both have SHA-256 `8c85bd83b65afa31e330392acd81124397815d6d072a51dca19633936c4af544`. [Model at the observed HEAD](https://github.com/nasqret/riemann-rev/blob/e9bdf8f4177403b66426f84b0ccbac15a4ad152a/data/model.json) · [Frozen atlas model](https://github.com/nasqret/riemann-rev/blob/d53b3804bd013df4cf9af3b4087728148c90c9bd/data/model.json) · [Pin-by-pin comparison](comparison-atlas.tsv)

Two atlas declarations are present in **both** compiled RH sets and absent from our trace. Both have concrete explanations to test in a future resolver:

- `Formalism.FrobeniusOrbits.ThickExists.noRel_image` is called unqualified inside a theorem governed by `open ThickExists in`. The enclosing theorem is in our trace. The resolver handles persistent opens and skips this command-local open. This leaves the atlas’s primes component without a traced pin. [Command-local scope](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/FrobeniusOrbits/FrobeniusOrbitsProofs/ThickExists.lean#L180) · [Call site](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/FrobeniusOrbits/FrobeniusOrbitsProofs/ThickExists.lean#L304)
- `zeta_logderiv_limit` appears as the receiver in `zeta_logderiv_limit.comp`. The source resolver treats the entire dotted spelling as a candidate name and misses the private lemma at line 216. [Private declaration](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/GL3MeanSquares/HookFormulaTorsion/PsiZeroIntegral.lean#L216) · [Dotted call at line 483](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/GL3MeanSquares/HookFormulaTorsion/PsiZeroIntegral.lean#L483)

The atlas labels 85 edges as calls. For **74**, both endpoints are in the Proofs & Reasons RH graph and the direct edge exists. The other **11** have an endpoint outside that RH-only dataset. The comparison table also records support links, analogies and statement dependencies under their own relation types. [Edge-by-edge comparison](comparison-atlas-edges.tsv)

**Reading coverage is a separate limitation.** Ten of the atlas’s 64 files appear in the top 200, covering four of its fourteen components at the file level. Import centrality favors reusable definitions and narrow import bottlenecks. The atlas selects mathematical interfaces across the argument. A reader interested in the prime-sum or reflection steps should use the two maps together. Likewise Rosetta’s **94** project import communities, Proofs & Reasons’ **943** declaration communities, and the atlas’s **four** strata partition different objects. Their counts measure different structures. [Atlas blueprint](https://nasqret.github.io/riemann-rev/book/blueprint.html) · [Proofs & Reasons methodology](https://proofsandreasons.io/rh-graph.html)

## Investigation list

1. Trace the source-only 2,233 sites and the 166,098 missed by the lexical resolver but reported by both compiled sources. The two atlas cases give reproducible fixtures for improving the next independent parser version.
2. Audit the **2,269** names on which the two compiled datasets differ before using either as a complete ground truth. The membership flags preserve both accounts.
3. Review mathematical-area labels for communities dominated by umbrella imports. A centrality rank and a one-line source note are entry points for a mathematician’s review. [Independent community profiles](communities.json)

## Reproduce the edge and atlas checks

Use the repository environment and the README reproduction of the frozen outputs. The comparison runner verifies the release digests, including the 399,119,904-byte edge table (SHA-256 `423a8dfe2150b5a5937679a5822f1477b7d10f241702afc6abd254813203aaae`). The manifest covers the eight generated comparison outputs and hashes gzip payloads after decompression. The live atlas check runs separately so later HEAD changes remain distinguishable from the pinned comparison.

```bash
set -eu
export LC_ALL=C
.venv/bin/python -m pip install -r requirements.txt
ROSETTA_RESULTS=inputs/reproduced .venv/bin/python analysis/compare.py inputs/comparisons --fetch
cmp results/comparison-content-sha256.json inputs/reproduced/comparison-content-sha256.json
.venv/bin/python analysis/check_witness_edges.py inputs/comparisons/shore
.venv/bin/python analysis/check_atlas_head.py --commit e9bdf8f4177403b66426f84b0ccbac15a4ad152a
.venv/bin/python analysis/check_atlas_head.py
```
