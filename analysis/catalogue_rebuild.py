"""Audit retained statement links using two compiled declaration graphs and original Lean imports."""
import argparse
import json
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

from catalogue_closure import classify_links, path_witnesses, project_graph
from catalogue_crosscheck import CUBE, THETA_FILE, UNKILLED, rh_graph, source_paths, verify_fold
from catalogue_dependency_note import write_note
from catalogue_owner_check import NO_RECORDED, verify_owner_table
from catalogue_edge_lists import NOV22, NOV23
from common import content_digest, put_json, read_rows, table
from odesky_coverage import from_index, INDEX, OUT, UTC

PIN = OUT / "2026-11-23"
CITES = "odesky-audit-citations.tsv.gz"
OLD = "odesky-audit-dependencies.tsv.gz"
PATH = {"direct", "transitive"}
PERMITS = {"file order permits", "transitive imports permit"}
SHORE = ("result", "witness_caller", "witness_dependency", "opposite_path", "opposite_witness_caller",
         "opposite_witness_dependency", "shared_graph_owners")
RH = ("pr_result", "pr_path_kind", "pr_witness_caller", "pr_witness_dependency", "pr_missing_owners",
      "unmatched_printed_names", "pr_opposite_path", "pr_opposite_witness_caller", "pr_opposite_witness_dependency")
SOURCE = ("source_result", "source_tests")


def witness(hit):
    if not hit:
        return "", "", ""
    distance, caller, dependency = hit[0]
    return ("direct" if distance == 0 else "transitive"), caller, dependency


def classify(shore, pr):
    if shore in PATH:
        return "graphs disagree" if pr == "no path" else "path"
    if shore == "common declaration":
        return "same declaration"
    if shore == "incomplete endpoint coverage":
        return "unmatched name"
    if shore != "no path":
        raise ValueError(f"Unknown Shore result {shore}")
    return {"no path": NO_RECORDED, "path": "graphs disagree", "not testable": "second graph not testable"}[pr]


def run(edge_file, pr_file, proof, dest, verify_owner=None):
    dest.mkdir(parents=True, exist_ok=True)
    if verify_owner is not None and verify_owner.resolve() == (dest / "owner-no-path.tsv").resolve():
        raise ValueError("Use a separate output directory when verifying a previous owner table")
    # The stable dated inputs are separate from the regenerated derived tables.
    pinned = json.loads((PIN / "content-sha256.json").read_text())
    inputs = ("cards.tsv", NOV22, NOV23, "snapshots.json", "display-cards.tsv", "display-snapshots.json")
    for name in inputs:
        if content_digest(PIN / name) != pinned[name]:
            raise ValueError(f"Dated statement snapshot differs for {name}")
    manifest = json.loads((OUT / "odesky-audit-content-sha256.json").read_text())
    for name in (CITES, OLD):
        if content_digest(OUT / name) != manifest[name]:
            raise ValueError(f"Historical evidence digest differs for {name}")
    original, _ = from_index(OUT / INDEX)
    entries = {Path(url).stem: info for url, info in original.items()}
    prior = {(Path(r["entry_url"]).stem, Path(r["dependency_url"]).stem): r
             for r in read_rows(OUT / OLD) if r["explicit_depends_on"] == "1"}
    cards = {r["card_id"]: r for r in read_rows(PIN / "cards.tsv")}
    display = {r["card_id"]: r for r in read_rows(PIN / "display-cards.tsv")}
    def directed_pairs(name):
        pairs = [(r["card_id"], r["depends_on_card_id"]) for r in read_rows(PIN / name)]
        if len(pairs) != len(set(pairs)):
            raise ValueError(f"Duplicate directed link in {name}")
        return set(pairs)
    earlier, current = directed_pairs(NOV22), directed_pairs(NOV23)
    if earlier != prior.keys():
        raise ValueError("November 22 edge list differs from the historical explicit links")
    retained = sorted(earlier & current)

    mappings = defaultdict(dict)
    sites = {UNKILLED: (THETA_FILE, 198), CUBE: (THETA_FILE, 124)}
    frame_cards = set()
    for r in read_rows(OUT / CITES):
        key = Path(r["entry_url"]).stem
        if r["cited_name"] == "FrameLA1" and r["spelling"] == "unique source suffix" and r["graph_owner"] == "Formalism.HN.FrameLA1":
            frame_cards.add(key)
        if r["spelling"] == "exact name" and r["graph_owner"]:
            owner = r["graph_owner"]
            site = r["compiled_owner"], int(r["owner_start_line"])
            if sites.setdefault(owner, site) != site:
                raise ValueError(f"Multiple source sites for {owner}")
            mappings[key][r["cited_name"]] = owner

    shore_graph, shore_ids = project_graph(edge_file, sites)
    shore_paths = path_witnesses(shore_graph, shore_ids)
    shore = {r[:2]: dict(zip(SHORE, [*r[9:15], r[16]], strict=True))
             for r in classify_links(entries, dict.fromkeys(retained, (1, 0)), mappings, shore_paths)}
    graph, pr_ids = rh_graph(pr_file, sites)
    pr_paths = path_witnesses(graph, pr_ids)
    source_test, file_count = source_paths(proof, sites)
    verify_fold(edge_file, graph, pr_ids, mappings, shore_paths, proof)

    fields = ("card_id", "dependency_card_id", "entry_url", "dependency_url", "cohort",
              *("exact_" + k for k in SHORE), *RH, *SOURCE, "classification")
    rows = []
    details = {}
    for a, b in sorted(current):
        pair = (a, b)
        row = dict(zip(fields[:4], (a, b, cards[a]["url"], cards[b]["url"])))
        if pair not in shore:
            row["cohort"] = "added since November 22"
        else:
            row["cohort"] = "retained"
            s = shore[pair]
            row.update(("exact_" + k, v) for k, v in s.items())
            left, right = (set(mappings[k].values()) for k in pair)
            unmatched = sorted({n for key in pair for n in entries[key][0] if n not in mappings[key]})
            absent = sorted((left | right) - pr_ids.keys())
            pk, pc, pd = witness(pr_paths(left, right))
            rk, rc, rd = witness(pr_paths(right, left))
            pr = "path" if pk else "not testable" if absent or unmatched else "no path"
            row.update(zip(RH, (pr, pk, pc, pd, " | ".join(absent), " | ".join(unmatched), rk, rc, rd), strict=True))
            tests = Counter(source_test(x, y) for x, y in product(left, right))
            if PERMITS & tests.keys():
                source = "permitted"
            elif unmatched or not tests or "order inconclusive (mutual block)" in tests:
                source = "not testable"
            else:
                source = "ruled out"
            for caller_set, target_set in ((left, right), (right, left)):
                hits = shore_paths(caller_set, target_set) + pr_paths(caller_set, target_set)
                for _, caller, target in hits:
                    if source_test(caller, target) in {"later in same file", "no transitive import"}:
                        raise ValueError(f"Source forbids {caller} → {target} for {pair}")
            row.update(source_result=source, source_tests=json.dumps(tests, sort_keys=True), classification=classify(s["result"], pr))
            details[pair] = row
        rows.append([row.get(k, "") for k in fields])
    table(dest / "checked.tsv.gz", fields, rows)

    captures = json.loads((PIN / "snapshots.json").read_text())
    display_captures = json.loads((PIN / "display-snapshots.json").read_text())
    def page(k):
        card = display[k]
        snapshot = "definitions.html" if card["kind"] == "definition" else "index.html"
        return (k, card["number"] or "unnumbered", card["title"], card["url"], display_captures[snapshot]["utc"],
                " | ".join(entries[k][0]), json.dumps(mappings[k], ensure_ascii=False, sort_keys=True),
                " | ".join(f"{n} @ {sites[n][0]}:{sites[n][1]}" for n in sorted(set(mappings[k].values()))))

    side = ("card_id", "number", "title", "url", "snapshot_utc", "printed_lean_names", "exact_name_to_tested_owner", "owner_locations")
    reverse_fields = ("B_caller", "A_dependency", "kind", "edge_direct")
    fields = ("lean_mapping_snapshot_utc", *("A_" + k for k in side), *("B_" + k for k in side),
              "evidence", *SOURCE, *(g + "_opposite_" + k for g in ("shore", "pr") for k in reverse_fields))
    owner_rows = []
    for (a, b), r in details.items():
        if r["classification"] != NO_RECORDED:
            continue
        src = r["source_result"]
        reason = "Both compiled declaration graphs have no recorded path between the tested declarations. "
        reason += {"ruled out": "Source rules out every owner pair.",
                   "permitted": "Source permits at least one owner pair.",
                   "not testable": "Source order or imports are inconclusive."}[src]
        if r["exact_opposite_path"] and r["pr_opposite_path"]:
            reason += " Both graphs have an opposite path from B to A."
        reverse = []
        for prefix in ("exact_", "pr_"):
            kind = r[prefix + "opposite_path"]
            reverse.extend((r[prefix + "opposite_witness_caller"], r[prefix + "opposite_witness_dependency"],
                            kind, ("yes" if kind == "direct" else "no") if kind else "n/a"))
        owner_rows.append((UTC, *page(a), *page(b), reason, src, r["source_tests"], *reverse))
    table(dest / "owner-no-path.tsv", fields, owner_rows)
    graphs = {"shore": (shore_graph, shore_ids), "pr": (graph, pr_ids)}
    expected_pairs = {p for p,r in details.items() if r["classification"] == NO_RECORDED}
    for target in dict.fromkeys(p for p in (dest / "owner-no-path.tsv", verify_owner) if p is not None):
        verify_owner_table(target, expected_pairs, entries, mappings, display, graphs)
    write_note(dest, details, prior, current, entries, display, captures, frame_cards, file_count, display_captures, pinned)
    put_json(dest / "content-sha256.json", {k: content_digest(folder / k) for folder, names in (
        (PIN, inputs),
        (dest, ("checked.tsv.gz", "dependencies.md", "owner-no-path.tsv"))) for k in names})


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("edges", type=Path)
    cli.add_argument("pr_graph", type=Path)
    cli.add_argument("proof", type=Path, help="Original pinned checkout containing src/")
    cli.add_argument("--out", type=Path, default=PIN)
    cli.add_argument("--verify-owner", type=Path, help="Also verify a previously exported owner table")
    args = cli.parse_args()
    run(args.edges, args.pr_graph, args.proof, args.out, args.verify_owner)
