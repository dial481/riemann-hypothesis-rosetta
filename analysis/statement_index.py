"""Extract card identifiers, public addresses and explicit dependencies, excluding statement text."""

import argparse
import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

BASE = "https://andrewodesky.com/rh/"


def address_name(url):
    """Parse a canonical theorem address without altering Lean spelling."""
    parsed = urlsplit(url)
    if not url.startswith(BASE) or parsed.fragment or parsed.query:
        raise ValueError(f"Unexpected statement address {url}")
    path = url[len(BASE):]
    if path.startswith("s/") and len(path) > 2:
        return ""
    match = re.fullmatch(r"lean/([^/]+)/", path)
    if not match:
        raise ValueError(f"Unexpected statement address {url}")
    name = unquote(match[1], errors="strict")
    if "/" in name or any(ord(c) < 32 for c in name):
        raise ValueError(f"Invalid declaration segment in {url}")
    return name


class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = {}
        self.edges = set()
        self.card = self.field = self.capture = None
        self.number_open = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "theorem-card" in attrs.get("class", "").split():
            key, kind = attrs["id"], attrs["data-kind"]
            if self.card or not re.fullmatch(r"[\w-]+", key) or key in self.cards:
                raise ValueError(f"Ambiguous card {key}")
            self.card = key
            self.cards[key] = [kind, None, "", ""]
        if self.card:
            if tag == "span" and "theorem-number" in attrs.get("class", "").split():
                self.number_open = True
            if tag in ("h3", "dt", "dd"):
                self.capture = tag
                if tag == "dt":
                    self.field = ""
            if tag == "a" and (
                self.capture == "h3"
                or (self.capture == "dd" and self.field == "Depends on")
            ):
                url = urljoin(BASE, attrs["href"])
                name = address_name(url)
                if name:
                    url = BASE + "lean/" + quote(name, safe="'") + "/"
                if self.capture == "h3":
                    if self.cards[self.card][1]:
                        raise ValueError(f"Multiple headings for {self.card}")
                    self.cards[self.card][1] = url
                else:
                    self.edges.add((self.card, url))

    def handle_data(self, text):
        if self.card and self.number_open:
            self.cards[self.card][2] += text
        if self.card and self.capture == "h3":
            self.cards[self.card][3] += text
        if self.card and self.capture == "dt":
            self.field += text

    def handle_endtag(self, tag):
        if tag == "span":
            self.number_open = False
        if self.card and tag == self.capture:
            self.capture = None
        if self.card and tag == "article":
            if not self.cards[self.card][1]:
                raise ValueError(f"Missing address for {self.card}")
            row = self.cards[self.card]
            row[2:] = [" ".join(value.split()) for value in row[2:]]
            if not row[3] or (row[0] == "theorem" and not row[2]):
                raise ValueError(
                    f"Missing statement heading or theorem number for {self.card}"
                )
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
    by_url = {url: key for key, (_, url, _, _) in parser.cards.items()}
    if len(by_url) != len(parser.cards):
        raise ValueError("Two cards share an address")
    relations = sorted((src, by_url[url]) for src, url in parser.edges)
    return sorted((key, *v) for key, v in parser.cards.items()), relations


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
    tsv(a.cards, ["card_id", "kind", "url", "number", "title"], cards)
    if a.depends:
        tsv(a.depends, ["card_id", "depends_on_card_id"], relations)
