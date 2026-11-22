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

from catalogue_modules import LINK_TABLE, MODULE_TABLE, load_modules, write_module_join
from common import NAME_RE, content_digest, digest, put_json, read_rows, table

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
MATCH_TABLE = "odesky-spine-matches.tsv"
FILE = re.compile(r"(?:\.\./\.lake/packages/mathlib/)?[\w/'-][\w./'-]*\.lean(?::[1-9][0-9]*)?")
SLUG = re.compile(r"[A-Za-z0-9_-]+")
# Section permalinks in document order at the captured snapshot.
SECTIONS = {
    "g-result": "The result", "g-analytic": "Analytic reduction", "g-count": "Fields and the prime count",
    "g-theta": "Theta maps and divisibility", "g-slope": "Slope inequality", "g-geometry": "Geometric estimate",
    "g-cohomology": "Cohomological input", "g-automorphic": "Automorphic and Galois input",
}


class Catalogue(HTMLParser):
    """Read identifiers and source paths inside article definition lists."""
    def __init__(self):
        super().__init__()
        self.entries = {}
        self.sections = {}
        self.section = None
        self.slug = None
        self.field = self.capture = ""
        self.in_list = self.in_value = self.in_heading = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section":
            anchor = attrs["id"]
            if self.section is not None or not re.fullmatch("g-[a-z]+", anchor):
                raise ValueError(f"Unexpected catalogue section: {anchor}")
            self.section = URL + "#" + anchor
        if self.section and tag == "h2":
            self.capture, self.buffer = tag, []
        if tag == "article":
            if self.section is None:
                raise ValueError("Catalogue article outside a section")
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
                url = urljoin(URL, href)
                self.entries[self.slug]["url"] = url
                self.sections[url] = self.section
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
            if tag == "h2":
                if SECTIONS[self.section.rsplit("#",1)[1]] != value:
                    raise ValueError(f"Unexpected heading for {self.section}")
            elif tag == "dt":
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
        elif tag == "section":
            self.section = None


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
    if list(dict.fromkeys(u.split("#")[-1] for u in parser.sections.values())) != list(SECTIONS):
        raise ValueError("Catalogue sections differ from the snapshot order")
    return result, parser.sections


def from_index(path):
    expected = json.loads((OUT / MANIFEST).read_text())[INDEX]
    if content_digest(path) != expected:
        raise ValueError("Identifier index checksum mismatch")
    result = {}
    sections = {}
    for r in read_rows(path):
        url = r["entry_url"]
        if url in result:
            raise ValueError(f"Repeated catalogue entry: {url}")
        result[url] = validate(url, r["lean_names"].split("|"), r["cited_files"].split("|"))
        section = r["section_url"]
        if not section.startswith(URL+"#") or not re.fullmatch("g-[a-z]+", section[len(URL)+1:]):
            raise ValueError(f"Invalid section link: {section}")
        sections[url] = section
    return result, sections


def project_owners(data, wanted, paths):
    if digest(data) != OWNER_SHA:
        raise ValueError("Declaration owner table checksum mismatch")
    owners = {}
    used_names = set()
    with gzip.open(data, "rt", newline="") as stream:
        for row in csv.DictReader(stream):
            name, path = row["decl"], row["file"]
            if name in wanted and path in paths and row["origin"] == "project":
                if name in owners:
                    raise ValueError(f"Ambiguous compiled owner: {name}")
                owners[name] = path
                if row["in_cone"] == "true":
                    used_names.add(name)
    return owners, used_names


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
        o = {by_file[owners[n]] for n in names if n in owners and owners[n] in by_file}
        assert a <= o, (url,a-o)
        reverse[url] = (a,f,o)
        for i in a:
            name_hits[i].add(url)
        for i in f:
            file_hits[i].add(url)
    return name_hits, file_hits, reverse


def packed(values):
    return "|".join(str(v) for v in sorted(values))


def section_label(url):
    return SECTIONS[url.rsplit("#",1)[1]]


def report(spine, entries, names, files, reverse, sections, entry_counts, module_count, owner_count):
    kinds = Counter(s["kind"] for s in spine)
    groups = {"Theorems": {int(s["rank"]) for s in spine if s["kind"]=="theorem"},
              "Definitions and structures": {int(s["rank"]) for s in spine if s["kind"]!="theorem"}}
    groups["All anchors"] = set.union(*groups.values())
    assert kinds=={"theorem":106, "def":57, "structure":28, "abbrev":8, "class":1}
    matched_anchors = sum(bool(names[int(s["rank"])] or files[int(s["rank"])]) for s in spine)
    touched = sum(bool(f or o) for _,f,o in reverse.values())
    matched = sum(bool(n) for n in entry_counts.values())
    external = [u for u,n in entry_counts.items() if not n]
    lines = ["# Statement catalogue coverage of the original proof", "",
             f"**{matched_anchors} of {len(spine)} spine anchors** have a catalogue match by name or cited file. In the reverse direction, "
             f"**{touched} of {len(entries):,} catalogue entries ({touched/len(entries):.1%})** cite a spine file or name a declaration owned by one.", "",
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
              "Spine rank measures the role of a file in the import graph. A catalogue entry describes a mathematical statement. "
              "An unmatched anchor can be a definition or a wrapper. An absent citation alone supplies no reading priority.", "",
              "## Across all original project modules", "",
              f"Joining the full 175,187-file inventory places **{matched:,} of {len(entries):,} entries** in **{module_count:,} distinct project modules**. "
              f"The remaining {len(external)} entries cite Mathlib. Their rows carry empty project metrics. "
              "Each entry–file row identifies its catalogue section and whether the file was cited, owns an exactly named declaration, or both. "
              "Multi-file entries keep every match and its own metrics. "
              f"Of {len({n for ns,_ in entries.values() for n in ns}):,} distinct listed identifiers, {owner_count:,} have an exact original project owner. "
              "The entry table records the remaining names, including library names and unqualified spellings.", "",
              "Import rank is the original structural ranking (1 is highest). The cut counts other project files that lose every import path from Main "
              "when the module is removed, excluding the module itself. Kernel use is measured on the original proof: RH, another target, or unused "
              "by all five. The five-target mask is preserved. The two declaration-name columns separately identify which exactly matched declarations "
              "occur in any of the five kernel cones. File-level use alone cannot establish use of a named declaration. "
              f"[Every entry and its module metrics]({LINK_TABLE}) · [All original modules, including zero matches]({MODULE_TABLE})", "",
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
              "## Where the matches occur in the argument", "",
              "| Catalogue section | All entries | Entries touching a spine file | Entries matched to any project file |",
              "|---|---:|---:|---:|"]
    for anchor in SECTIONS:
        section = URL + "#" + anchor
        urls = {url for url,sec in sections.items() if sec == section}
        lines.append(f"| [{section_label(section)}]({section}) | {len(urls)} | "
                     f"{sum(bool(reverse[u][1] or reverse[u][2]) for u in urls)} | {sum(bool(entry_counts[u]) for u in urls)} |")
    lines += ["", "## Spine entries for review", "",
              "Each citation link identifies the entry's section. The match table also includes entries naming a different declaration in a spine module. "
              f"A dash means the corresponding lookup found no entry. [All matches with sections]({MATCH_TABLE}) · "
              f"[All anchors, including unmatched entries]({ANCHOR_TABLE})", "",
              "| Rank | Kind | Lean anchor | Original file and line | Name citation | File citation |", "|---:|---|---|---|---|---|"]
    def links(urls):
        return " ".join(f"[{section_label(sections[url])} {i}]({url})" for i,url in enumerate(sorted(urls),1)) or "—"
    for s in spine:
        i = int(s["rank"])
        lines.append(f"| {i} | {s['kind']} | `{s['anchor']}` | [{s['path']}#L{s['line']}]({s['source_url']}) "
                     f"| {links(names[i])} | {links(files[i])} |")
    lines += ["", "## Reproduce", "",
              "From the repository root, the frozen identifier index reproduces the joins even after the live catalogue changes. "
              "The raw HTML snapshot is stored locally under `inputs/odesky/`. "
              "The extraction reads the Lean and File fields, the entry link and its enclosing section link. "
              "The committed index preserves the validated identifiers and file citations. "
              "The manifest hashes decompressed contents for gzip artifacts and file contents for text. Run from the stacked checkout with the original metrics and upstream kernel file mask in place.", "",
              "```bash","set -eu","export LC_ALL=C","mkdir -p inputs/kernel inputs/odesky",
              "curl -fsSL --retry 3 https://github.com/james-shore/rh-proof-dependencies/releases/download/v0.2.1/decls.csv.gz -o inputs/kernel/decls.csv.gz",
              f"echo '{OWNER_SHA}  inputs/kernel/decls.csv.gz' | sha256sum -c -",
              ".venv/bin/python analysis/odesky_coverage.py --index results/phase-2/odesky-index.tsv.gz --owners inputs/kernel/decls.csv.gz --out inputs/replayed-coverage",
              "cmp results/phase-2/odesky-sha256.json inputs/replayed-coverage/odesky-sha256.json","```", "",
              "To re-extract the metadata with the captured HTML, run the following commands. "
              "To attempt a fresh retrieval without overwriting the snapshot, "
              f"run `curl -fsSL --retry 3 {URL} -o inputs/odesky/live-index.html` and pass "
              "`--html inputs/odesky/live-index.html` instead. The extractor checks the pinned digest.", "",
              "```bash", "set -eu", "export LC_ALL=C", f"echo '{HTML_SHA}  inputs/odesky/index.html' | sha256sum -c -",
              ".venv/bin/python analysis/odesky_coverage.py --html inputs/odesky/index.html --owners inputs/kernel/decls.csv.gz --out inputs/reextracted-coverage",
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
    entries, sections = from_html(args.html) if args.html else from_index(args.index)
    if digest(SPINE) != SPINE_SHA:
        raise ValueError("Spine checksum mismatch")
    spine = list(read_rows(SPINE))
    wanted = {n for ns,_ in entries.values() for n in ns}
    modules = load_modules()
    owners, used_names = project_owners(args.owners, wanted, modules)
    name_hits, file_hits, reverse = join(spine, entries, owners)
    dest = args.out
    dest.mkdir(parents=True,exist_ok=True)
    entry_counts, module_count = write_module_join(dest, entries, sections, owners, used_names, modules)
    table(dest/INDEX, ["entry_url","lean_names","cited_files","section_url"],
          ((url,packed(ns),packed(refs),sections[url]) for url,(ns,refs) in sorted(entries.items())))
    spine_paths = {s["path"] for s in spine}
    table(dest/OWNER_TABLE, ["declaration","original_spine_path"], sorted((n,p) for n,p in owners.items() if p in spine_paths))
    table(dest/MATCH_TABLE, ["rank","entry_url","section_url","anchor_named","spine_file_cited","named_declaration_owned"],
          ((i,url,sections[url],int(i in a),int(i in f),int(i in o))
           for url,(a,f,o) in sorted(reverse.items()) for i in sorted(a|f|o)))
    table(dest/ENTRY_TABLE, ["entry_url","anchor_ranks_named","spine_ranks_by_cited_file","spine_ranks_by_declaration_owner","section_url","project_modules_matched","names_without_exact_project_owner"],
          ((url,packed(a),packed(f),packed(o),sections[url],entry_counts[url],packed(set(entries[url][0])-owners.keys()))
           for url,(a,f,o) in sorted(reverse.items())))
    table(dest/ANCHOR_TABLE, ["rank","kind","anchor","original_path","original_line","name_entry_urls","file_entry_urls"],
          ((s["rank"],s["kind"],s["anchor"],s["path"],s["line"],packed(name_hits[int(s["rank"])]),packed(file_hits[int(s["rank"])])) for s in spine))
    (dest/REPORT).write_text(report(spine, entries, name_hits, file_hits, reverse, sections, entry_counts, module_count, len(owners)), encoding="utf-8")
    put_json(dest/MANIFEST,{name:content_digest(dest/name) for name in sorted((INDEX,OWNER_TABLE,ENTRY_TABLE,ANCHOR_TABLE,REPORT,MODULE_TABLE,LINK_TABLE,MATCH_TABLE))})


if __name__ == "__main__":
    main()
