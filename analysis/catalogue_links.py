"""Extract entry identifiers and distinguish promised dependencies from reverse links."""
import re
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin

from common import digest
from odesky_coverage import HTML_SHA, SLUG, URL

GRAPH_SHA = "354e43be13ce0eb0075fdc2c0ea11fb6843f9407c41e5be00918c9ed2b25865e"
PAGE_HASHES = {
    "galois-representations": "4a707d2ea0a23e255e246d35f482f1de93b28b4347957e1a09505079923bc9b8",
    "cohomological-bound": "9c0b7a34a97093673c55c5df8d89a07749ff3c3c9703c6d9f3dca4315f78cde4",
}


class Relations(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slugs = set()
        self.relations = {"Depends on": set(), "Used by": set()}
        self.slug = self.field = None
        self.in_term = self.in_value = False

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "article":
            self.slug = attr["id"]
            if not SLUG.fullmatch(self.slug) or self.slug in self.slugs:
                raise ValueError("Invalid article identifier")
            self.slugs.add(self.slug)
        elif self.slug and tag == "dt":
            self.in_term, self.field = True, ""
        elif self.slug and tag == "dd":
            self.in_value = True
        elif tag == "a" and self.in_value and self.field in self.relations:
            link = attr["href"]
            if not link.startswith("#") or not SLUG.fullmatch(link[1:]):
                raise ValueError(f"Unexpected dependency link {link}")
            pair = (self.slug, link[1:])
            self.relations[self.field].add(pair if self.field == "Depends on" else pair[::-1])

    def handle_endtag(self, tag):
        if tag == "dt":
            self.in_term = False
        elif tag == "dd":
            self.in_value = False
        elif tag == "article":
            self.slug = self.field = None

    def handle_data(self, data):
        if self.in_term:
            self.field += data


def entry_url(slug):
    return urljoin(URL, f"s/{slug}.html")


def catalogue_links(index, graph, pages, entries):
    if digest(index) != HTML_SHA or digest(graph) != GRAPH_SHA:
        raise ValueError("Catalogue index or graph checksum mismatch")
    parser = Relations()
    parser.feed(index.read_text())
    parser.close()
    outgoing, reverse = parser.relations.values()
    if {entry_url(s) for s in parser.slugs} != entries.keys() or not outgoing <= reverse:
        raise ValueError("Index inventory or reciprocal dependency fields disagree")
    for slug, expected in PAGE_HASHES.items():
        page = pages / (slug + ".html")
        if digest(page) != expected:
            raise ValueError(f"Entry checksum mismatch for {slug}")
        body = re.search(r'<h2>Depends on</h2>\s*<ul class="rel">(.*?)</ul>', page.read_text(), re.S)
        if body is None:
            raise ValueError(f"Dependency section missing for {slug}")
        page_deps = set(re.findall(r'<a href="([\w-]+)\.html">', body[1]))
        if page_deps != {b for a,b in outgoing if a == slug}:
            raise ValueError(f"Entry and index disagree for {slug}")

    # Within-field edges expose both endpoints. Cross-field arcs end at portals.
    svg = graph.read_text()
    fields = {}
    for area, drawing in re.findall(r'<svg[^>]+data-view="([a-z]+)"[^>]*>(.*?)</svg>', svg, re.S):
        for slug in re.findall(r'<g class="node [^"]+" data-id="([\w-]+)">', drawing):
            if slug in fields:
                raise ValueError(f"Repeated graph node {slug}")
            fields[slug] = area
    same_field = set(re.findall(r'<path class="e" data-a="([\w-]+)" data-b="([\w-]+)"', svg))
    totals = {(a,b): int(n) for a,b,n in re.findall(
        r'<path class="fl" data-a="([a-z]+)" data-b="([a-z]+)"[^>]*><title>(\d+) dependencies:', svg)}
    if fields.keys() != parser.slugs:
        raise ValueError("Graph nodes differ from index entries")
    within = {(a,b) for a,b in reverse if fields[a] == fields[b]}
    across = Counter((fields[a],fields[b]) for a,b in reverse if fields[a] != fields[b])
    if within != same_field or across != totals:
        raise ValueError("Reverse index links differ from the graph by endpoints or field totals")
    return {(entry_url(a),entry_url(b)): (int((a,b) in outgoing), int((a,b) in same_field))
            for a,b in sorted(reverse)}
