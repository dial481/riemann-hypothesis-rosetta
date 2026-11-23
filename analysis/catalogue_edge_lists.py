"""Extract the two complete explicit Depends-on lists from the dated statement snapshots."""
import argparse
import json
from pathlib import Path

from catalogue_links import catalogue_links
from common import digest, table
from odesky_coverage import INDEX, OUT, from_index
from statement_index import extract

COLUMNS = ("card_id", "depends_on_card_id")
NOV22 = "depends-2026-11-22.tsv"
NOV23 = "depends.tsv"
PIN = OUT / "2026-11-23"


def extract_lists(early, late, dest):
    entries, _ = from_index(OUT / INDEX)
    links = catalogue_links(early / "index.html", early / "graph.html", early / "s", entries)
    old = sorted((Path(a).stem, Path(b).stem) for (a,b),(explicit,_) in links.items() if explicit)
    _, current = extract(late, json.loads((PIN / "snapshots.json").read_text()))
    dest.mkdir(parents=True, exist_ok=True)
    for filename, pairs in ((NOV22, old), (NOV23, current)):
        table(dest / filename, COLUMNS, pairs)
        print(filename, len(pairs), digest(dest / filename))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("nov22", type=Path)
    cli.add_argument("nov23", type=Path)
    cli.add_argument("dest", type=Path)
    args = cli.parse_args()
    extract_lists(args.nov22, args.nov23, args.dest)
