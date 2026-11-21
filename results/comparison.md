# Cross-validation of the original-source map

**Both compiled RH datasets contain all 200 independently chosen starting declarations, at their cited source locations.** The Proofs & Reasons graph also contains every direct step in **198 of the 200** source trails. In the two exceptions the starting declaration is used by RH, and the particular route from our source scan includes one direct edge absent from that graph. [Per-entry results](comparison-spine.tsv) · [Direct-edge checks](comparison-witness-edges.tsv) · [Alternative compiled trails](comparison-alternative-paths.json)

The source scan, graph partitions, ranking, annotations and witness paths were completed and committed in `aca7e1830b22c913bd9658c3f38e82128539beea` before these comparison inputs were downloaded. The comparison verifies every frozen checksum before and after it runs. The comparisons below leave the independent ranking intact. [Frozen hashes](independent-sha256.json) · [Comparison data and input hashes](comparison.json)

## Scope and identity

The independent source scan begins at the one declaration `riemannHypothesis`. Shore publishes bit masks for five theorems. We selected bit 1, omitted shared auxiliaries when attributing proof use to a declaration, and joined on the **owning declaration’s file**. A generated constant’s module can differ from its owner’s file. Reconstructing the five sets with that distinction reproduced all five published counts. The Proofs & Reasons download is already restricted to RH and folds generated helpers, fields and constructors into owning declarations. For membership comparisons we match project module plus declaration name, removing Lean’s module-private name prefix. Line numbers provide an additional test on spine entries. [Shore’s schema](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/docs/dataset.md) · [Proofs & Reasons graph and schema](https://proofsandreasons.io/rh-graph.html)

| Quantity | Rosetta source scan | Shore RH | Proofs & Reasons RH |
|---|---:|---:|---:|
| Named project declarations reached | 641,100 | 804,891 | 806,982 |
| Project files containing one of those declarations | 134,176 | 146,284 | 146,352 |
| Named declarations shared with Rosetta | — | 638,751 | 638,818 |
| Declarations in Rosetta only, relative to this comparator | — | 2,349 | 2,282 |
| Declarations in the comparator only, relative to Rosetta | — | 166,140 | 168,164 |
| Comparator project files outside Main’s import closure | — | 0 | 0 |

The import census accounts for **all 175,187 project files**. Shore identifies uses of Mathlib constants in **5,081** modules for RH, all inside Rosetta’s **8,312** reachable Mathlib source modules. Imported files can supply tactics, notation, transitive imports, declarations for other targets or declarations simply unused by RH. Module reachability alone cannot decide which reason applies. [Import inventory](inventory.tsv.gz) · [Shore v0.2.1 release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)

Over **99.6%** of our named sites are present in each compiled dataset. The trace recovers **79.4%** of Shore’s RH set and **79.2%** of Proofs & Reasons’ RH set. Of the three-way discrepancies, **2,234** sites appear only in our trace and **166,099** appear in both compiled graphs but are missing from ours. The two compiled sets share **804,802** site identities, with **89** unique to Shore and **2,180** unique to Proofs & Reasons under our join. Possible contributors include auxiliary folding and source ownership. Individual disagreements remain available for investigation. [All discrepant site identities and membership flags](comparison-disagreements.tsv.gz)

| Shore target | Published declarations | Reconstructed from target mask | Shared with our RH-only trace |
|---|---:|---:|---:|
| riemannHypothesis | 804,891 | 804,891 | 638,751 |
| riemannZeta_eq_zero_re | 804,892 | 804,892 | 638,750 |
| LFunction_ne_zero_of_half_lt_re | 804,889 | 804,889 | 638,747 |
| LFunction_eq_zero_re | 804,899 | 804,899 | 638,747 |
| LFunction_eq_zero_re_of_isPrimitive | 804,892 | 804,892 | 638,747 |

The overlap column uses the same independent RH trace in every row. The other four rows show how closely Shore’s five targets overlap with that one trace. [Published per-theorem counts](https://github.com/james-shore/rh-proof-dependencies/blob/v0.2.1/data/per-theorem.tsv)

## The two disputed spine edges

| Reading priority | Source mention | Result of checking the compiled graph |
|---:|---|---|
| 14 · Formalism.SatakeDualWeyl.Statement | `siegelAll_of` lists `Formalism.UG.hform` in a `simp only` call at line 238. | Both declarations are present. The compiled graph has no direct edge between them. An alternative shortest RH trail has 10 edges and reaches `hform` through `Formalism.MainNotions.S.AutInst`. |
| 128 · Formalism.GradedWeylDivisibility.FinalD | `exists_coords` invokes `sSIdxFinite` to construct a local finiteness instance at line 78. | Both endpoints are present. The compiled graph has no direct edge between them. An alternative shortest RH trail has 11 edges and reaches `sSIdxFinite` through `GlobalTheory.Branching.finite_nablaSq`. |

These are literal references in the submitted source. Simplification or local-instance elaboration can represent the resulting term differently. The exact reason for each missing direct edge requires inspection of the elaborated term. The external trails are stored separately from our independent witnesses. [Rank 14 source mention](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/WeilBound/ThetaLifts/FrameEstimates/SiegelAll.lean#L238) · [Rank 128 source mention](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Development/AbelianVarietyTheory/Proofs/DivisorProofs/FiniteClPlusAndExistsCoords.lean#L78)

## Naskręcki’s atlas

The atlas identifies 107 Lean declaration pins across 64 files, plus two conceptual nodes, in 14 mathematical components. Its model records the same archive hash, original mirror commit and Mathlib pin. We matched its abbreviated local names by exact module and line plus a unique qualified-name suffix. All **64** files are in Main’s closure. **87 of 107** declaration pins match our RH trace at the exact source line, spanning **13 of 14** components. Of the remaining 20, **18** also fall outside both compiled RH selections. The atlas covers five exports, so a separate endpoint such as `critAll` has a place in that map. [Frozen atlas model](https://github.com/nasqret/riemann-rev/blob/d53b3804bd013df4cf9af3b4087728148c90c9bd/data/model.json) · [Pin-by-pin comparison](comparison-atlas.tsv)

Two atlas declarations are present in **both** compiled RH sets and absent from our trace. Both have concrete explanations to test in a future resolver:

- `Formalism.FrobeniusOrbits.ThickExists.noRel_image` is called unqualified inside a theorem governed by `open ThickExists in`. The enclosing theorem is in our trace. The resolver handles persistent opens and skips this command-local open. This leaves the atlas’s primes component without a traced pin. [Command-local scope](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/FrobeniusOrbits/FrobeniusOrbitsProofs/ThickExists.lean#L180) · [Call site](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/FrobeniusOrbits/FrobeniusOrbitsProofs/ThickExists.lean#L304)
- `zeta_logderiv_limit` appears as the receiver in `zeta_logderiv_limit.comp`. The source resolver treats the entire dotted spelling as a candidate name and misses the private lemma at line 216. [Private declaration](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/GL3MeanSquares/HookFormulaTorsion/PsiZeroIntegral.lean#L216) · [Dotted call at line 483](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/GL3MeanSquares/HookFormulaTorsion/PsiZeroIntegral.lean#L483)

The atlas labels 85 edges as calls. For **74**, both endpoints are in the Proofs & Reasons RH graph and the direct edge exists. The other **11** have an endpoint outside that RH-only dataset. The comparison table also records support links, analogies and statement dependencies under their own relation types. [Edge-by-edge comparison](comparison-atlas-edges.tsv)

**Reading coverage is a separate limitation.** Ten of the atlas’s 64 files appear in the top 200, covering four of its fourteen components at the file level. Import centrality favors reusable definitions and narrow import bottlenecks. The atlas selects mathematical interfaces across the argument. A reader interested in the prime-sum or reflection steps should use the two maps together. Likewise Rosetta’s **94** project import communities, Proofs & Reasons’ **943** declaration communities, and the atlas’s **four** strata partition different objects. Their counts measure different structures. [Atlas blueprint](https://nasqret.github.io/riemann-rev/book/blueprint.html) · [Proofs & Reasons methodology](https://proofsandreasons.io/rh-graph.html)

## Investigation list

1. Inspect term-level ownership of the two disputed direct edges above. Both target anchors already have independently published compiled RH paths.
2. Trace the source-only 2,234 sites and the 166,099 missed by the lexical resolver but reported by both compiled sources. The two atlas cases give reproducible fixtures for improving the next independent parser version.
3. Audit the **2,269** names on which the two compiled datasets differ before using either as a complete ground truth. The membership flags preserve both accounts.
4. Review mathematical-area labels for communities dominated by umbrella imports. A centrality rank and a one-line source note are entry points for a mathematician’s review. [Independent community profiles](communities.json)
