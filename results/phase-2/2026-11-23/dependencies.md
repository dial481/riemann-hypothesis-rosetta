# Explicit dependencies after the November 23 rebuild

Andrew O’Desky’s *Statements of the Lean RH project* lists 2,399 explicit directed dependencies across its rebuilt theorem and definition pages. Both ends of 2,071 links have November 22 identifiers. Of those, 1,818 have a positive-length path in James Shore’s project declaration graph. [Theorems](https://andrewodesky.com/rh/index.html) · [Definitions](https://andrewodesky.com/rh/definitions.html) · [Kernel data v0.2.1](https://github.com/james-shore/rh-proof-dependencies/tree/v0.2.1)

| Dependency measure | November 22 | November 23 |
| --- | ---: | ---: |
| Explicit directed links | 2,481 | 2,399 |
| Both statements have November 22 identifiers | 2,481 | 2,071 |
| Positive-length path | 1,827 | 1,818 |
| Direct | 628 | 621 |
| Transitive | 1,199 | 1,197 |
| Common named declaration, no path | 2 | 4 |
| No forward path with complete coverage | 151 | 174 |
| Incomplete historical endpoints | 501 | 75 |
| At least one statement lacks a historical mapping | 0 | 328 |
| Reverse path among complete no-forward pairs | 19 | 16 |
| Reverse with exact endpoint names | 17 | 14 |

Joining directed pairs by stable card ID gives 1,965 retained, 434 added and 516 removed. All retained pairs reproduce their previous result. The new pages supply the links. The November 22 snapshot supplies the Lean names. The path check uses the original formalization. A new statement without a historical identifier remains untested. [Per-pair evidence](checked.tsv.gz) · [Historical audit](../odesky-audit.md)

Captured the index at 2026-11-23T14:16:17+00:00 and the definitions at 2026-11-23T14:16:19+00:00. The extraction uses the explicit Depends on field within each card and resolves its href to the printed card address. Used by fields and links embedded in prose are excluded. The counts use distinct directed card pairs. [Snapshot hashes](snapshots.json) · [Card addresses](cards.tsv) · [Directed pairs](depends.tsv)

Replay from the repository root with the pinned Shore release. To verify the HTML extraction, place the two matching pages in an ignored directory and run the comparison below.

```bash
export LC_ALL=C
r=results/phase-2/2026-11-23
.venv/bin/python analysis/catalogue_rebuild.py inputs/audit/decl_edges.parquet --out inputs/rebuilt-audit
cmp "$r/content-sha256.json" inputs/rebuilt-audit/content-sha256.json
.venv/bin/python analysis/statement_index.py inputs/rebuilt-html "$r/snapshots.json" inputs/cards.tsv --depends inputs/depends.tsv
cmp "$r/cards.tsv" inputs/cards.tsv
cmp "$r/depends.tsv" inputs/depends.tsv
```
