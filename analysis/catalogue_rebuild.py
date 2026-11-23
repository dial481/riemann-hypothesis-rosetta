"""Compare retained directed links under exact and unique-suffix name resolution."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from catalogue_closure import check_links
from common import content_digest, put_json, read_rows, table
from odesky_coverage import from_index, INDEX, OUT, UTC

PIN = OUT / "2026-11-23"
CITES = "odesky-audit-citations.tsv.gz"
OLD = "odesky-audit-dependencies.tsv.gz"
EVIDENCE = (
    "result",
    "witness_caller",
    "witness_dependency",
    "opposite_path",
    "opposite_witness_caller",
    "opposite_witness_dependency",
    "shared_graph_owners",
)


def evidence(row):
    return dict(zip(EVIDENCE, [*row[9:15], row[16]], strict=True))


def results_count(rows):
    counts = Counter(r["result"] for r in rows)
    counts["positive path"] = counts["direct"] + counts["transitive"]
    counts["opposite path"] = sum(bool(r["opposite_path"]) for r in rows)
    return counts


def run(edge_file, dest):
    dest.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((OUT / "odesky-audit-content-sha256.json").read_text())
    for name in (CITES, OLD):
        if content_digest(OUT / name) != manifest[name]:
            raise ValueError(f"Historical evidence digest differs for {name}")
    original, _ = from_index(OUT / INDEX)
    entries = {Path(url).stem: info for url, info in original.items()}
    owners = {mode: defaultdict(dict) for mode in ("exact", "suffix")}
    for row in read_rows(OUT / CITES):
        key = Path(row["entry_url"]).stem
        if row["graph_owner"]:
            owners["suffix"][key][row["cited_name"]] = row["graph_owner"]
            if row["spelling"] == "exact name":
                owners["exact"][key][row["cited_name"]] = row["graph_owner"]
    prior = {
        (Path(r["entry_url"]).stem, Path(r["dependency_url"]).stem): r
        for r in read_rows(OUT / OLD)
        if r["explicit_depends_on"] == "1"
    }
    cards = {r["card_id"]: r for r in read_rows(PIN / "cards.tsv")}
    current = {
        (r["card_id"], r["depends_on_card_id"]) for r in read_rows(PIN / "depends.tsv")
    }
    retained = current & prior.keys()
    # The new edges never enter the graph query, even when both card IDs survived.
    exact = {
        r[:2]: evidence(r)
        for r in check_links(
            edge_file, entries, dict.fromkeys(prior, (1, 0)), owners["exact"]
        )
    }
    suffix = {p: {k: r[k] for k in EVIDENCE} for p, r in prior.items()}
    modes = {"exact": exact, "suffix": suffix}
    fields = (
        "card_id",
        "dependency_card_id",
        "entry_url",
        "dependency_url",
        "cohort",
        *(mode + "_" + k for mode in modes for k in EVIDENCE),
    )
    checked = []
    for a, b in sorted(current):
        pair = (a, b)
        values = [
            m[pair][k] if pair in retained else ""
            for m in modes.values()
            for k in EVIDENCE
        ]
        checked.append(
            (
                a,
                b,
                cards[a]["url"],
                cards[b]["url"],
                "retained" if pair in retained else "added since November 22",
                *values,
            )
        )
    table(dest / "checked.tsv.gz", fields, checked)

    captures = json.loads((PIN / "snapshots.json").read_text())

    def page(key):
        card = cards[key]
        timestamp = captures[
            "definitions.html" if card["kind"] == "definition" else "index.html"
        ]["utc"]
        tested = json.dumps(owners["suffix"][key], ensure_ascii=False, sort_keys=True)
        return (
            card["number"] or "unnumbered",
            card["title"],
            card["url"],
            timestamp,
            " | ".join(entries[key][0]),
            tested,
            " | ".join(sorted(set(owners["exact"][key].values()))),
        )

    side = (
        "number",
        "title",
        "url",
        "snapshot_utc",
        "printed_lean_names",
        "printed_name_to_tested_owner_unique_suffix",
        "tested_owners_exact",
    )
    fields = (
        "lean_mapping_snapshot_utc",
        *("A_" + k for k in side),
        *("B_" + k for k in side),
        "exact_result",
        "unique_suffix_result",
        "opposite_witness_caller",
        "opposite_caller_page_B",
        "opposite_witness_dependency",
        "opposite_dependency_page_A",
        "opposite_path_kind",
        "opposite_edge_direct",
    )
    owner_rows = []
    for a, b in sorted(retained):
        pair = (a, b)
        if not any(m[pair]["result"] == "no path" for m in modes.values()):
            continue
        rev = next((m[pair] for m in modes.values() if m[pair]["opposite_path"]), {})
        caller = rev.get("opposite_witness_caller", "")
        callee = rev.get("opposite_witness_dependency", "")
        if rev:
            a_owners, b_owners = (
                set(owners["suffix"][a].values()),
                set(owners["suffix"][b].values()),
            )
            assert caller in b_owners - a_owners and callee in a_owners - b_owners
        kind = rev.get("opposite_path", "")
        owner_rows.append(
            (
                UTC,
                *page(a),
                *page(b),
                exact[pair]["result"],
                suffix[pair]["result"],
                caller,
                cards[b]["url"] if rev else "",
                callee,
                cards[a]["url"] if rev else "",
                kind,
                ("yes" if kind == "direct" else "no") if rev else "n/a",
            )
        )
    table(dest / "owner-no-path.tsv", fields, owner_rows)
    counts = {
        mode: [results_count([m[p] for p in group]) for group in (prior, retained)]
        for mode, m in modes.items()
    }
    changed = [
        p
        for p in retained
        if suffix[p]["result"] == "no path" and exact[p]["result"] != "no path"
    ]
    frame_changes = sum(
        any(owners["suffix"][k].get("FrameLA1") == "Formalism.HN.FrameLA1" for k in p)
        for p in changed
    )
    added = current - prior.keys()
    both = sum(a in entries and b in entries for a, b in added)
    text = [
        "# Dependency checks for the rebuilt statement site",
        "",
        f"Of {len(current):,} explicit directed links in Andrew O’Desky’s *Statements of the Lean RH project* on November 23, {len(retained):,} also occur on November 22. On those retained links, {counts['exact'][1]['no path']} have no forward path under exact naming, and {counts['suffix'][1]['no path']} under unique-suffix resolution. The owner table gives the statements, tested names and reverse witnesses. [Owner table](owner-no-path.tsv) · [Per-link evidence](checked.tsv.gz)",
        "",
        "| Dependency measure | Nov 22 exact | Nov 22 unique suffix | Retained Nov 23 exact | Retained Nov 23 unique suffix |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, k in (
        ("Positive-length forward path", "positive path"),
        ("Direct", "direct"),
        ("Transitive", "transitive"),
        ("Common graph owner, no forward path", "common declaration"),
        ("No forward path, disjoint and fully resolved owners", "no path"),
        ("Incomplete endpoints, no forward path", "incomplete endpoint coverage"),
        ("Opposite path among the no-path pairs", "opposite path"),
    ):
        vals = [counts[mode][i][k] for i in (0, 1) for mode in modes]
        text.append("| " + label + " | " + " | ".join(f"{n:,}" for n in vals) + " |")
    text += [
        "",
        f"The November 22 denominator is {len(prior):,}. The rebuilt site has {len(added):,} added links and omits {len(prior.keys() - current)} old links. The added cohort includes {both} pairs with two historical card IDs and {len(added) - both} with an unmapped endpoint. A surviving page can absorb links from merged statements, so its earlier names cannot establish the new link’s mathematical endpoints. Every added link has a cohort label and empty path fields.",
        "",
        "Exact resolution accepts the printed Lean spelling. For a source-qualified reading of a bare name, unique-suffix resolution also accepts a single matching qualified declaration across the statement’s cited source files. Both use the same compiled structure owner for an identified projection. The per-link table records shared owners even where a separate positive-length forward witness exists. Such pairs contribute to the positive-path row. Without a forward witness, two pages with a shared graph owner are classified as common. A negative result requires every name to resolve to an owner and disjoint owner sets. Opposite witnesses run from a B owner to an A owner. Direct means a single directed edge in Shore’s graph. [James Shore’s declaration data v0.2.1](https://github.com/james-shore/rh-proof-dependencies/tree/v0.2.1)",
        "",
        f"{len(changed)} retained pairs move from incomplete under exact naming to no path under unique-suffix resolution. In {frame_changes} of these, the published bare name is `FrameLA1` and the unique qualified match is `Formalism.HN.FrameLA1`. The owner table shows both classifications and the names available under each rule.",
        "",
        "The family-arithmetic-data pair shares `Formalism.MainNotions.FamP`. The family-point-moduli pair shares `Formalism.L2.Pj.LawsM`. Folding projections identifies those shared owners on both dates. The FamP-to-FamCore witness belongs within a page, so it does not enter the opposite-path count.",
        "",
        f"The current theorem index was captured at {captures['index.html']['utc']} and the definition page at {captures['definitions.html']['utc']}. The Lean identifiers come from {UTC}. Definitions have no printed number. [Snapshots](snapshots.json) · [Cards](cards.tsv) · [Directed pairs](depends.tsv) · [Historical audit](../odesky-audit.md)",
        "",
        "Replay from the checkout root with the pinned Shore release and the November 22 audit outputs.",
        "",
        "\x60\x60\x60bash",
        "export LC_ALL=C",
        "r=results/phase-2/2026-11-23",
        ".venv/bin/python analysis/catalogue_rebuild.py inputs/audit/decl_edges.parquet --out inputs/rebuilt-audit",
        'cmp "$r/content-sha256.json" inputs/rebuilt-audit/content-sha256.json',
        '.venv/bin/python analysis/statement_index.py inputs/rebuilt-html "$r/snapshots.json" inputs/cards.tsv --depends inputs/depends.tsv',
        'cmp "$r/cards.tsv" inputs/cards.tsv',
        'cmp "$r/depends.tsv" inputs/depends.tsv',
        "\x60\x60\x60",
        "",
    ]
    (dest / "dependencies.md").write_text("\n".join(text))
    put_json(
        dest / "content-sha256.json",
        {
            k: content_digest(
                (PIN if k in ("cards.tsv", "depends.tsv", "snapshots.json") else dest)
                / k
            )
            for k in (
                "cards.tsv",
                "checked.tsv.gz",
                "dependencies.md",
                "depends.tsv",
                "owner-no-path.tsv",
                "snapshots.json",
            )
        },
    )


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("edges", type=Path)
    cli.add_argument("--out", type=Path, default=PIN)
    args = cli.parse_args()
    run(args.edges, args.out)
