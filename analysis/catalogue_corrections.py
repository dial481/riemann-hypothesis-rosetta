"""Recount explicit Depends on links from the author's chunked card catalogue."""
import argparse
import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from statement_index import BASE, Cards, tsv

AGENT = "Rosetta catalogue comparison"
PAGES = ("index.html", "definitions.html")


class Chunks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = {}

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == "article" and "data-chunk" in fields:
            chunk = fields["data-chunk"]
            if not re.fullmatch(r"cards/[A-Za-z0-9-]+\.html", chunk) or fields["id"] in self.cards:
                raise ValueError("Unexpected chunk or duplicate card")
            self.cards[fields["id"]] = chunk


def capture(cache):
    cache.mkdir(parents=True, exist_ok=True)
    robots = RobotFileParser()
    robots_url = "https://andrewodesky.com/robots.txt"
    try:
        with urlopen(Request(robots_url, headers={"User-Agent": AGENT}), timeout=30) as response:
            robots.parse(response.read().decode().splitlines())
    except HTTPError as exc:
        if exc.code != 404:
            raise
        robots.parse([])
    meta = {}
    def fetch(name):
        url = BASE + name
        if not robots.can_fetch(AGENT, url):
            raise ValueError(f"robots.txt disallows {url}")
        time.sleep(max(1, robots.crawl_delay(AGENT) or 0))
        with urlopen(Request(url, headers={"User-Agent": AGENT}), timeout=45) as response:
            data = response.read()
        path = cache/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        meta[name] = {"url":url, "utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "sha256":hashlib.sha256(data).hexdigest()}
        return data.decode()

    chunks = Chunks()
    for name in PAGES:
        chunks.feed(fetch(name))
    for name in sorted(set(chunks.cards.values())):
        fetch(name)
    (cache/"capture.json").write_text(json.dumps(meta, indent=2, sort_keys=True)+"\n")


def extract(cache):
    meta = json.loads((cache/"capture.json").read_text())
    def read(name):
        data = (cache/name).read_bytes()
        if hashlib.sha256(data).hexdigest() != meta[name]["sha256"]:
            raise ValueError(f"Source hash mismatch for {name}")
        return data.decode()
    listing = Chunks()
    parser = Cards()
    for name in PAGES:
        html = read(name)
        listing.feed(html)
        parser.feed(html)
    loaded = set()
    for name in sorted(set(listing.cards.values())):
        chunk = Cards()
        chunk.feed(read(name))
        if any(parser.cards.get(key) != card for key, card in chunk.cards.items()):
            raise ValueError(f"Chunk and index headings differ for {name}")
        loaded.update(k for k in chunk.cards if listing.cards.get(k) == name)
        parser.edges.update(chunk.edges)
    if loaded != listing.cards.keys():
        raise ValueError("Missing lazy card in its advertised chunk")
    by_url = {v[1]:k for k,v in parser.cards.items()}
    if len(by_url) != len(parser.cards):
        raise ValueError("Duplicate canonical card address")
    return sorted((a,by_url[url]) for a,url in parser.edges)


def compare(pairs, owner, dest):
    with owner.open() as stream:
        historic = {(r["A_card_id"],r["B_card_id"]) for r in csv.DictReader(stream,delimiter="\t")}
    current = set(pairs)
    dest.mkdir(parents=True, exist_ok=True)
    tsv(dest/"depends.tsv",["card_id","depends_on_card_id"],sorted(current))
    tsv(dest/"historical-link-status.tsv",["card_id","depends_on_card_id","listed"],[(a,b,"yes" if (a,b) in current else "no") for a,b in sorted(historic)])
    print(len(current), "current links;", len(historic & current), "still listed;",len(historic-current),"removed")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cache",type=Path)
    cli.add_argument("dest",type=Path)
    mode=cli.add_mutually_exclusive_group()
    mode.add_argument("--capture",action="store_true")
    mode.add_argument("--pairs", action="store_true", help="Read the committed depends.tsv from the input directory")
    cli.add_argument("--owner",type=Path,default=Path("results/phase-2/2026-11-23/owner-no-path.tsv"))
    args=cli.parse_args()
    if args.capture:
        capture(args.cache)
    if args.pairs:
        with (args.cache/"depends.tsv").open() as stream:
            pairs = [(r["card_id"],r["depends_on_card_id"]) for r in csv.DictReader(stream,delimiter="\t")]
        if pairs != sorted(set(pairs)):
            raise ValueError("Expected sorted, distinct links")
    else:
        pairs = extract(args.cache)
    compare(pairs,args.owner,args.dest)
