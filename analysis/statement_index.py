"""Extract card identifiers, public addresses and explicit dependencies, excluding statement text."""
import argparse
import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

BASE = "https://andrewodesky.com/rh/"


class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = {}
        self.edges = set()
        self.card = self.field = self.capture = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "theorem-card" in attrs.get("class", "").split():
            key, kind = attrs["id"], attrs["data-kind"]
            if self.card or not re.fullmatch(r"[\w-]+", key) or key in self.cards:
                raise ValueError(f"Ambiguous card {key}")
            self.card = key
            self.cards[key] = [kind, None]
        if self.card:
            if tag in ("h3", "dt", "dd"):
                self.capture = tag
                if tag == "dt":
                    self.field = ""
            if tag == "a" and (self.capture == "h3" or (self.capture == "dd" and self.field == "Depends on")):
                url = urljoin(BASE, attrs["href"])
                if not url.startswith(BASE + "s/") or urlsplit(url).fragment:
                    raise ValueError(f"Unexpected statement address {url}")
                if self.capture == "h3":
                    if self.cards[self.card][1]:
                        raise ValueError(f"Multiple headings for {self.card}")
                    self.cards[self.card][1] = url
                else:
                    self.edges.add((self.card, url))

    def handle_data(self, text):
        if self.card and self.capture == "dt":
            self.field += text

    def handle_endtag(self, tag):
        if self.card and tag == self.capture:
            self.capture = None
        if self.card and tag == "article":
            if not self.cards[self.card][1]:
                raise ValueError(f"Missing address for {self.card}")
            self.card = self.field = self.capture = None


def extract(directory, metadata):
    parser = Cards()
    for name in ("index.html", "definitions.html"):
        data = (directory / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != metadata[name]["sha256"]:
            raise ValueError(f"Snapshot hash differs for {name}")
        parser.feed(data.decode())
        if parser.card:
            raise ValueError(f"Unclosed card in {name}")
    parser.close()
    by_url = {url: key for key, (_, url) in parser.cards.items()}
    if len(by_url) != len(parser.cards):
        raise ValueError("Two cards share an address")
    relations = sorted((src, by_url[url]) for src, url in parser.edges)
    return sorted((key, *v) for key,v in parser.cards.items()), relations


def tsv(path, columns, rows):
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("html", type=Path)
    cli.add_argument("metadata", type=Path)
    cli.add_argument("cards", type=Path)
    cli.add_argument("--depends", type=Path)
    a = cli.parse_args()
    cards, relations = extract(a.html, json.loads(a.metadata.read_text()))
    tsv(a.cards, ["card_id", "kind", "url"], cards)
    if a.depends:
        tsv(a.depends, ["card_id", "depends_on_card_id"], relations)
