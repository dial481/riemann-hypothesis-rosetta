# Dependency checks for the rebuilt statement site

Of 2,399 explicit directed links in Andrew O’Desky’s *Statements of the Lean RH project* on November 23, 1,965 also occur on November 22. On those retained links, 139 have no forward path under exact naming, and 144 under unique-suffix resolution. The owner table gives the statements, tested names and reverse witnesses. [Owner table](owner-no-path.tsv) · [Per-link evidence](checked.tsv.gz)

| Dependency measure | Nov 22 exact | Nov 22 unique suffix | Retained Nov 23 exact | Retained Nov 23 unique suffix |
| --- | ---: | ---: | ---: | ---: |
| Positive-length forward path | 1,825 | 1,827 | 1,746 | 1,748 |
| Direct | 627 | 628 | 588 | 589 |
| Transitive | 1,198 | 1,199 | 1,158 | 1,159 |
| Common graph owner, no forward path | 3 | 4 | 3 | 4 |
| No forward path, disjoint and fully resolved owners | 144 | 149 | 139 | 144 |
| Incomplete endpoints, no forward path | 509 | 501 | 77 | 69 |
| Opposite path among the no-path pairs | 18 | 18 | 14 | 14 |

The November 22 denominator is 2,481. The rebuilt site has 434 added links and omits 516 old links. The added cohort includes 106 pairs with two historical card IDs and 328 with an unmapped endpoint. A surviving page can absorb links from merged statements, so its earlier names cannot establish the new link’s mathematical endpoints. Every added link has a cohort label and empty path fields.

Exact resolution accepts the printed Lean spelling. For a source-qualified reading of a bare name, unique-suffix resolution also accepts a single matching qualified declaration across the statement’s cited source files. Both use the same compiled structure owner for an identified projection. The per-link table records shared owners even where a separate positive-length forward witness exists. Such pairs contribute to the positive-path row. Without a forward witness, two pages with a shared graph owner are classified as common. A negative result requires every name to resolve to an owner and disjoint owner sets. Opposite witnesses run from a B owner to an A owner. Direct means a single directed edge in Shore’s graph. [James Shore’s declaration data v0.2.1](https://github.com/james-shore/rh-proof-dependencies/tree/v0.2.1)

5 retained pairs move from incomplete under exact naming to no path under unique-suffix resolution. In 5 of these, the published bare name is `FrameLA1` and the unique qualified match is `Formalism.HN.FrameLA1`. The owner table shows both classifications and the names available under each rule.

The family-arithmetic-data pair shares `Formalism.MainNotions.FamP`. The family-point-moduli pair shares `Formalism.L2.Pj.LawsM`. Folding projections identifies those shared owners on both dates. The FamP-to-FamCore witness belongs within a page, so it does not enter the opposite-path count.

The current theorem index was captured at 2026-11-23T14:16:17+00:00 and the definition page at 2026-11-23T14:16:19+00:00. The Lean identifiers come from 2026-11-22T17:15:18Z. Definitions have no printed number. [Snapshots](snapshots.json) · [Cards](cards.tsv) · [Directed pairs](depends.tsv) · [Historical audit](../odesky-audit.md)

Replay from the checkout root with the pinned Shore release and the November 22 audit outputs.

```bash
export LC_ALL=C
r=results/phase-2/2026-11-23
.venv/bin/python analysis/catalogue_rebuild.py inputs/audit/decl_edges.parquet --out inputs/rebuilt-audit
cmp "$r/content-sha256.json" inputs/rebuilt-audit/content-sha256.json
.venv/bin/python analysis/statement_index.py inputs/rebuilt-html "$r/snapshots.json" inputs/cards.tsv --depends inputs/depends.tsv
cmp "$r/cards.tsv" inputs/cards.tsv
cmp "$r/depends.tsv" inputs/depends.tsv
```
