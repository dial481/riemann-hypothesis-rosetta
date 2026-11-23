"""Join the rebuilt catalogue's explicit dependency pairs to the dated citation evidence."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from catalogue_closure import check_links
from common import content_digest, put_json, read_rows, table
from odesky_coverage import from_index, INDEX, OUT

PIN = OUT / "2026-11-23"
CITES = "odesky-audit-citations.tsv.gz"
OLD = "odesky-audit-dependencies.tsv.gz"


def run(edge_file, dest):
    dest.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((OUT / "odesky-audit-content-sha256.json").read_text())
    for name in (CITES, OLD):
        if content_digest(OUT / name) != manifest[name]:
            raise ValueError(f"Historical evidence digest differs for {name}")
    original, _ = from_index(OUT / INDEX)
    old_key = {url: Path(url).stem for url in original}
    entries = {old_key[url]: values for url,values in original.items()}
    owners, identities = defaultdict(dict), defaultdict(set)
    for row in read_rows(OUT / CITES):
        if row["graph_owner"]:
            key = old_key[row["entry_url"]]
            owners[key][row["cited_name"]] = row["graph_owner"]
            identities[key].add(row["qualified_name"])
    cards = {r["card_id"]:r for r in read_rows(PIN / "cards.tsv")}
    pairs = {(r["card_id"],r["depends_on_card_id"]) for r in read_rows(PIN / "depends.tsv")}
    prior = {(old_key[r["entry_url"]],old_key[r["dependency_url"]]):r for r in read_rows(OUT / OLD)
             if r["explicit_depends_on"]=="1"}
    mapped = {p:(1,0) for p in pairs if all(k in entries for k in p)}
    # Recompute every testable current pair, including the ones that survived the rebuild.
    checked = {r[:2]:r for r in check_links(edge_file, entries, mapped, owners, identities)}
    fields = ("card_id","dependency_card_id","entry_url","dependency_url","nov22_pair","mapped_endpoints","result",
              "witness_caller","witness_dependency","reverse_path","reverse_witness_caller","reverse_witness_dependency",
              "exact_reverse","shared_named_declarations")
    records = []
    for a,b in sorted(pairs):
        row = checked.get((a,b))
        evidence = (row[9],*row[10:15],int(bool(row[15])),row[16]) if row else ("no November 22 mapping","","","","","",0,"")
        records.append((a,b,cards[a]["url"],cards[b]["url"],int((a,b) in prior),int(a in entries)+int(b in entries),*evidence))
        if row and (a,b) in prior:
            then = prior[a,b]
            if (row[9],row[10],row[11],row[12]) != tuple(then[k] for k in ("result","witness_caller","witness_dependency","opposite_path")):
                raise ValueError(f"Kernel result differs on surviving pair {a}, {b}")
    table(dest/"checked.tsv.gz", fields, records)
    before=Counter(r["result"] for r in prior.values())
    after=Counter(r[6] for r in records)
    def fmt(n): return f"{n:,}"
    rows = [("Explicit directed links",len(prior),len(pairs)),
            ("Both statements have November 22 identifiers",len(prior),len(mapped)),
            ("Positive-length path",before["direct"]+before["transitive"],after["direct"]+after["transitive"])]
    rows += [(s,before[k],after[k]) for s,k in [("Direct","direct"),("Transitive","transitive"),("Common named declaration, no path","common declaration"),
             ("No forward path with complete coverage","no path"),("Incomplete historical endpoints","incomplete endpoint coverage"),
             ("At least one statement lacks a historical mapping","no November 22 mapping")]]
    rows += [("Reverse path among complete no-forward pairs",sum(bool(r["opposite_path"]) for r in prior.values()),sum(bool(r[9]) for r in records)),
             ("Reverse with exact endpoint names",sum(r["opposite_with_exact_names"]=="1" for r in prior.values()),sum(r[12] for r in records))]
    capture=json.loads((PIN/"snapshots.json").read_text())
    text=["# Explicit dependencies after the November 23 rebuild","",
          f"Andrew O’Desky’s *Statements of the Lean RH project* lists {fmt(len(pairs))} explicit directed dependencies across its rebuilt theorem and definition pages. Both ends of {fmt(len(mapped))} links have November 22 identifiers. Of those, {fmt(after['direct']+after['transitive'])} have a positive-length path in James Shore’s project declaration graph. [Theorems](https://andrewodesky.com/rh/index.html) · [Definitions](https://andrewodesky.com/rh/definitions.html) · [Kernel data v0.2.1](https://github.com/james-shore/rh-proof-dependencies/tree/v0.2.1)",
          "", "| Dependency measure | November 22 | November 23 |","| --- | ---: | ---: |"]
    text += [f"| {label} | {fmt(a)} | {fmt(b)} |" for label,a,b in rows]
    text += ["",f"Joining directed pairs by stable card ID gives {fmt(len(pairs & prior.keys()))} retained, {fmt(len(pairs-prior.keys()))} added and {fmt(len(prior.keys()-pairs))} removed. All retained pairs reproduce their previous result. The new pages supply the links. The November 22 snapshot supplies the Lean names. The path check uses the original formalization. A new statement without a historical identifier remains untested. [Per-pair evidence](checked.tsv.gz) · [Historical audit](../odesky-audit.md)",
             "",f"Captured the index at {capture['index.html']['utc']} and the definitions at {capture['definitions.html']['utc']}. The extraction uses the explicit Depends on field within each card and resolves its href to the printed card address. Used by fields and links embedded in prose are excluded. The counts use distinct directed card pairs. [Snapshot hashes](snapshots.json) · [Card addresses](cards.tsv) · [Directed pairs](depends.tsv)","",
             "Replay from the repository root with the pinned Shore release. To verify the HTML extraction, place the two matching pages in an ignored directory and run the comparison below.","","\x60\x60\x60bash",
             "export LC_ALL=C","r=results/phase-2/2026-11-23",
             ".venv/bin/python analysis/catalogue_rebuild.py inputs/audit/decl_edges.parquet --out inputs/rebuilt-audit",
             "cmp \"$r/content-sha256.json\" inputs/rebuilt-audit/content-sha256.json",
             ".venv/bin/python analysis/statement_index.py inputs/rebuilt-html \"$r/snapshots.json\" inputs/cards.tsv --depends inputs/depends.tsv",
             "cmp \"$r/cards.tsv\" inputs/cards.tsv","cmp \"$r/depends.tsv\" inputs/depends.tsv","\x60\x60\x60",""]
    (dest/"dependencies.md").write_text("\n".join(text))
    put_json(dest/"content-sha256.json", {k:content_digest((PIN if k in ("cards.tsv","depends.tsv","snapshots.json") else dest)/k)
        for k in ("cards.tsv","checked.tsv.gz","dependencies.md","depends.tsv","snapshots.json")})


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("edges",type=Path)
    cli.add_argument("--out",type=Path,default=PIN)
    a=cli.parse_args()
    run(a.edges,a.out)
