"""Join a digest-pinned HTML catalogue's identifier fields to the frozen spine."""
import argparse
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from common import NAME_RE, digest, put_json, read_rows, table

URL = "https://andrewodesky.com/rh/index.html"
UTC = "2026-11-22T17:15:18Z"
HTML_SHA = "2c57f0ee0c8d291a1595ab46e1a6a4c732c10b14ca15b46cd4f0431b20e8879e"
OWNER_SHA = "bdfeae289f2db8b279816439049f26ba69ec993af2bab3b30d53340fe02493b9"
SPINE = Path("results/spine.tsv")
SPINE_SHA = "36505f7c81ffd347bee1a0cc0a95646eeff63f9c6fe14c8cab31fe712e94d4de"
OUT = Path("results/phase-2")
INDEX = "odesky-index.tsv.gz"
OWNER_TABLE = "odesky-spine-owners.tsv"
ENTRY_TABLE = "odesky-entries.tsv"
ANCHOR_TABLE = "odesky-anchors.tsv"
REPORT = "odesky-coverage.md"
MANIFEST = "odesky-sha256.json"
FILE = re.compile(r"(?:\.\./\.lake/packages/mathlib/)?[\w/'-][\w./'-]*\.lean(?::[1-9][0-9]*)?")
SLUG = re.compile(r"[A-Za-z0-9_-]+")


class Catalogue(HTMLParser):
    """Read identifiers and source paths inside article definition lists."""
    def __init__(self):
        super().__init__()
        self.entries = {}
        self.slug = None
        self.field = self.capture = ""
        self.in_list = self.in_value = self.in_heading = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article":
            slug = attrs["id"]
            if self.slug or not SLUG.fullmatch(slug) or slug in self.entries:
                raise ValueError(f"Invalid or repeated catalogue entry: {slug}")
            self.slug = slug
            self.entries[slug] = {}
        elif self.slug:
            if tag == "h3":
                self.in_heading = True
            elif self.in_heading and tag == "a":
                href = attrs["href"]
                assert href == f"s/{self.slug}.html"
                self.entries[self.slug]["url"] = urljoin(URL, href)
            elif tag == "dl":
                self.in_list = True
            elif self.in_list and tag == "dd":
                self.in_value = True
            elif self.in_list and (tag == "dt" or (tag == "code" and self.in_value and self.field in {"Lean", "File"})):
                self.capture, self.buffer = tag, []

    def handle_data(self, data):
        if self.capture:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if self.capture and tag == self.capture:
            value = "".join(self.buffer).strip()
            if tag == "dt":
                self.field = value
            else:
                record = self.entries[self.slug]
                if self.field in record:
                    raise ValueError(f"Repeated metadata field in {self.slug}")
                record[self.field] = value
            self.capture = ""
        if tag == "dd":
            self.in_value = False
        elif tag == "dl":
            self.in_list = False
        elif tag == "h3":
            self.in_heading = False
        elif tag == "article":
            self.slug, self.field = None, ""


def validate(url, names, refs):
    base = urljoin(URL, "s/")
    if not url.startswith(base) or not url.endswith(".html") or not SLUG.fullmatch(url[len(base):-5]):
        raise ValueError(f"Unexpected entry URL: {url}")
    if not names or not all(NAME_RE.fullmatch(n) for n in names):
        raise ValueError(f"Non-identifier in the Lean field of {url}")
    if not refs or not all(FILE.fullmatch(p) and ".." not in p.removeprefix("../.lake/packages/mathlib/") for p in refs):
        raise ValueError(f"Invalid source field in {url}")
    return tuple(sorted(set(names))), tuple(sorted(set(refs)))


def from_html(path):
    if digest(path) != HTML_SHA:
        raise ValueError("The HTML differs from the recorded snapshot. Use the frozen identifier index for replay.")
    parser = Catalogue()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    result = {}
    for entry in parser.entries.values():
        assert set(entry) == {"url", "Lean", "File"}
        url = entry["url"]
        result[url] = validate(url, [n.strip() for n in entry["Lean"].split(",")],
                               [p.strip() for p in re.split("[;,]",entry["File"])])
    return result


def from_index(path):
    expected = json.loads((OUT / MANIFEST).read_text())[INDEX]
    if digest(path) != expected:
        raise ValueError("Identifier index checksum mismatch")
    result = {}
    for r in read_rows(path):
        url = r["entry_url"]
        if url in result:
            raise ValueError(f"Repeated catalogue entry: {url}")
        result[url] = validate(url, r["lean_names"].split("|"), r["cited_files"].split("|"))
    return result


def spine_owners(data, wanted, paths):
    if digest(data) != OWNER_SHA:
        raise ValueError("Declaration owner table checksum mismatch")
    owners = {}
    with gzip.open(data, "rt", newline="") as stream:
        for row in csv.DictReader(stream):
            name, path = row["decl"], row["file"]
            if name in wanted and path in paths and row["origin"] == "project":
                if name in owners:
                    raise ValueError(f"Ambiguous compiled owner: {name}")
                owners[name] = path
    return owners


def project_paths(refs):
    return {"src/" + p.partition(":")[0] for p in refs if not p.startswith("../.lake/")}


def join(spine, entries, owners):
    by_name = {s["anchor"]:int(s["rank"]) for s in spine}
    by_file = {s["path"]:int(s["rank"]) for s in spine}
    assert len(by_name) == len(by_file) == 200
    name_hits, file_hits, reverse = defaultdict(set), defaultdict(set), {}
    for url, (names, refs) in sorted(entries.items()):
        a = {by_name[n] for n in names if n in by_name}
        f = {by_file[p] for p in project_paths(refs) if p in by_file}
        o = {by_file[owners[n]] for n in names if n in owners}
        assert a <= o, (url,a-o)
        reverse[url] = (a,f,o)
        for i in a:
            name_hits[i].add(url)
        for i in f:
            file_hits[i].add(url)
    return name_hits, file_hits, reverse


def packed(values):
    return "|".join(str(v) for v in sorted(values))


def report(spine, entries, names, files, reverse):
    kinds = Counter(s["kind"] for s in spine)
    groups = {"Theorems": {int(s["rank"]) for s in spine if s["kind"]=="theorem"},
              "Definitions and structures": {int(s["rank"]) for s in spine if s["kind"]!="theorem"}}
    groups["All anchors"] = set.union(*groups.values())
    assert kinds=={"theorem":106, "def":57, "structure":28, "abbrev":8, "class":1}
    lines = ["# Statement catalogue coverage of the original spine", "",
             f"Snapshot of {len(entries):,} distinct catalogue entries retrieved **{UTC}**. "
             f"HTML SHA-256: `{HTML_SHA}`. [Catalogue index]({URL}) · [Frozen identifier index]({INDEX})", "",
             "## Coverage of the 200 spine anchors", "",
             "| Anchor kind | Anchors | Name cited | File cited | Name and file in one entry | File without name | Name without file | Neither |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for group, ranks in groups.items():
        n = {i for i in ranks if names[i]}
        f = {i for i in ranks if files[i]}
        same = {i for i in ranks if names[i] & files[i]}
        lines.append(f"| {group} | {len(ranks)} | {len(n)} | {len(f)} | {len(same)} | {len(f-n)} | {len(n-f)} | {len(ranks-(n|f))} |")
    lines += ["", f"The second row comprises {kinds['def']} definitions, {kinds['structure']} structures, "
              f"{kinds['abbrev']} abbreviations and {kinds['class']} class. "
              "A declaration match requires the exact qualified Lean identifier. A file match requires a listed project path "
              "equal to the frozen spine path after adding the source root and removing the catalogue's line pointer. "
              "An entry can list multiple declarations and multiple paths. We compare those fields independently and make no positional pairing. "
              "A line number can change with the source revision. Partial names, prose mentions, and subject resemblance do not establish a match.", "",
              "## Reverse coverage of the catalogue", "",
              "| Spine group | Entries naming an anchor | Entries citing a spine file | Entries naming any declaration owned by a spine file | Either file or owner |",
              "|---|---:|---:|---:|---:|"]
    for group, ranks in groups.items():
        n,f,o = [{url for url,hit in reverse.items() if hit[i] & ranks} for i in range(3)]
        lines.append(f"| {group} | {len(n)} | {len(f)} | {len(o)} | {len(f|o)} |")
    f_urls = {u for u,(_,f,_) in reverse.items() if f}
    o_urls = {u for u,(_,_,o) in reverse.items() if o}
    lines += ["", f"Of {len(entries):,} entries, **{len(f_urls)}** cite a spine file in their File field. "
              f"Looking up the listed Lean names in the original compiled declaration table gives **{len(o_urls)}** entries "
              f"with a declaration owned by a spine module. The two sets share {len(o_urls&f_urls)} entries. Each entry counts once per group. "
              f"[Entry-by-entry joins]({ENTRY_TABLE}) · [Matched names and owner paths]({OWNER_TABLE}) · "
              "[Pinned owner-table release](https://github.com/james-shore/rh-proof-dependencies/releases/tag/v0.2.1)", "",
              "## Spine entries for review", "",
              f"The table gives the original file and line for every anchor. The two link columns show catalogue entries with an exact name "
              f"or file citation. A dash means the corresponding lookup found no entry. [Machine-readable matches and unmatched entries]({ANCHOR_TABLE})", "",
              "| Rank | Kind | Lean anchor | Original file and line | Name citation | File citation |", "|---:|---|---|---|---|---|"]
    def links(urls):
        return " ".join(f"[{i}]({url})" for i,url in enumerate(sorted(urls),1)) or "—"
    for s in spine:
        i = int(s["rank"])
        lines.append(f"| {i} | {s['kind']} | `{s['anchor']}` | [{s['path']}#L{s['line']}]({s['source_url']}) "
                     f"| {links(names[i])} | {links(files[i])} |")
    lines += ["", "## Reproduce", "",
              "From the repository root, the frozen identifier index reproduces the joins even after the live catalogue changes. "
              "The raw HTML snapshot is stored locally under `inputs/odesky/`. "
              "The extraction reads the Lean and File fields and the permanent entry link from each article. "
              "The committed index preserves the validated identifiers and file citations. "
              "The manifest records SHA-256 for the report and all four tables.", "",
              "```bash","set -eu","export LC_ALL=C","mkdir -p inputs/kernel inputs/odesky",
              "curl -fsSL --retry 3 https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1/decls.csv.gz -o inputs/kernel/decls.csv.gz",
              f"echo '{OWNER_SHA}  inputs/kernel/decls.csv.gz' | sha256sum -c -",
              "python3 analysis/odesky_coverage.py --index results/phase-2/odesky-index.tsv.gz --owners inputs/kernel/decls.csv.gz --out inputs/replayed-coverage",
              "cmp results/phase-2/odesky-sha256.json inputs/replayed-coverage/odesky-sha256.json","```", "",
              "To re-extract the metadata with the captured HTML, run the following commands. "
              "To attempt a fresh retrieval without overwriting the snapshot, "
              f"run `curl -fsSL --retry 3 {URL} -o inputs/odesky/live-index.html` and pass "
              "`--html inputs/odesky/live-index.html` instead. The extractor checks the pinned digest.", "",
              "```bash", "set -eu", "export LC_ALL=C", f"echo '{HTML_SHA}  inputs/odesky/index.html' | sha256sum -c -",
              "python3 analysis/odesky_coverage.py --html inputs/odesky/index.html --owners inputs/kernel/decls.csv.gz --out inputs/reextracted-coverage",
              "cmp results/phase-2/odesky-sha256.json inputs/reextracted-coverage/odesky-sha256.json","```", ""]
    return "\n".join(lines)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--html", type=Path)
    mode.add_argument("--index", type=Path)
    cli.add_argument("--owners", type=Path, required=True)
    cli.add_argument("--out", type=Path, default=OUT)
    args = cli.parse_args()
    entries = from_html(args.html) if args.html else from_index(args.index)
    if digest(SPINE) != SPINE_SHA:
        raise ValueError("Spine checksum mismatch")
    spine = list(read_rows(SPINE))
    wanted = {n for ns,_ in entries.values() for n in ns}
    owners = spine_owners(args.owners, wanted, {s["path"] for s in spine})
    name_hits, file_hits, reverse = join(spine, entries, owners)
    dest = args.out
    dest.mkdir(parents=True,exist_ok=True)
    table(dest/INDEX, ["entry_url","lean_names","cited_files"],
          ((url,packed(ns),packed(refs)) for url,(ns,refs) in sorted(entries.items())))
    table(dest/OWNER_TABLE, ["declaration","original_spine_path"],sorted(owners.items()))
    table(dest/ENTRY_TABLE, ["entry_url","anchor_ranks_named","spine_ranks_by_cited_file","spine_ranks_by_declaration_owner"],
          ((url,packed(a),packed(f),packed(o)) for url,(a,f,o) in sorted(reverse.items())))
    table(dest/ANCHOR_TABLE, ["rank","kind","anchor","original_path","original_line","name_entry_urls","file_entry_urls"],
          ((s["rank"],s["kind"],s["anchor"],s["path"],s["line"],packed(name_hits[int(s["rank"])]),packed(file_hits[int(s["rank"])])) for s in spine))
    (dest/REPORT).write_text(report(spine, entries, name_hits, file_hits, reverse), encoding="utf-8")
    put_json(dest/MANIFEST,{name:digest(dest/name) for name in sorted((INDEX,OWNER_TABLE,ENTRY_TABLE,ANCHOR_TABLE,REPORT))})


if __name__ == "__main__":
    main()
