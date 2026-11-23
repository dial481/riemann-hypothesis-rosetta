"""Check the anyGeometry claim against pinned source trees, compiled edges and Rosetta's frozen trace."""

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import duckdb
from check import ARTIFACTS, FREEZE
from common import MATHLIB, PROJECT, digest, put_json, read_rows, table
from inventory import UPSTREAM_PINS

UPSTREAM = UPSTREAM_PINS[0][0]
SRC_TREES = {
    PROJECT: "b41b516b1f7baee4d83ced235ecc71fd43c97695",
    UPSTREAM: "0ba0b4d44fa26b97a376ec10889be6b553237103",
}
SHORE = {
    "constants.csv.gz": "2964f5236046325ac7884906cb9517b0aa582330dd48a07eef291cb579444820",
    "decls.csv.gz": "bdfeae289f2db8b279816439049f26ba69ec993af2bab3b30d53340fe02493b9",
    "decl_edges.parquet": "62a184a781184bc1f3953ed90f5b967a27a2a3517d7b1f7e169ca6cc7d1bbec3",
    "edges.parquet": "423a8dfe2150b5a5937679a5822f1477b7d10f241702afc6abd254813203aaae",
}
RELEASE = "https://github.com/james-shore/rh-proof-dependencies"
PROOF = "https://github.com/leanprover-community/riemann-hypothesis"
BL = "GlobalTheory.Mem.Top.Bl."
ANY = BL + "anyGeometry"
UNUSED = [BL + "geoOf", "GlobalTheory.ShFam.IsGeoOf", "GlobalTheory.ShFam.Pad.HasTrueSurf"]
ROUTE = [
    "riemannHypothesis",
    "rhOfAll",
    "allChi",
    "UpperTheory.FinalTheorems.everyCharacter",
    "UpperTheory.FinalTheorems.everyCharacter_of_row",
    "UpperTheory.LiteratureTheorems.every_character_of_literature_of_vWin",
    "UpperTheory.Lit.every_character_of_theta_integrals_local_matching",
    BL + "parametersOfDependence",
    ANY,
]
USED = [
    ANY,
    BL + "GeoCl",
    "GlobalTheory.Fc.HypsAlt",
    "Formalism.L2.Geo.geoDegenerate",
    "UpperTheory.Top.TopG",
    "UpperTheory.Top.zeroFreeAll_of_topG",
    ROUTE[5],
]
WORDS = ["anyGeometry", "geoOf", "IsGeoOf", "HasTrueSurf"]
OVER = "src/Development/AbelianVarietyTheory/Definitions/AutomorphicMembership/OverIx.lean"
FROZEN = Path("results")


def check(label, observed, expected):
    if observed != expected:
        raise ValueError(f"{label}: observed {observed!r}, expected {expected!r}")


def verify_frozen():
    manifest = json.loads((FROZEN / FREEZE).read_text())
    check("frozen artifact set", set(manifest), set(ARTIFACTS))
    for name, sha in manifest.items():
        check(name, digest(FROZEN / name), sha)


def url(path, line, rev=PROJECT):
    return f"{PROOF}/blob/{rev}/{quote(path)}#L{line}"


def scan_source(root, rev):
    """Reconstruct the Git src tree while counting case-sensitive text occurrences in Lean files."""
    hits = []
    words = [(word, word.encode()) for word in WORDS]

    def object_id(kind, data):
        return hashlib.sha1(kind + b" " + str(len(data)).encode() + b"\0" + data).digest()

    def scan(folder):
        records = []
        for p in folder.iterdir():
            name = os.fsencode(p.name)
            if p.is_symlink():
                mode, key, sha = b"120000", name, object_id(b"blob", os.fsencode(os.readlink(p)))
            elif p.is_dir():
                mode, key, sha = b"40000", name + b"/", scan(p)
            else:
                raw = p.read_bytes()
                mode = b"100755" if p.stat().st_mode & 0o100 else b"100644"
                key, sha = name, object_id(b"blob", raw)
                if p.suffix == ".lean":
                    for word, token in words:
                        if token in raw:
                            lines = [str(i) for i, s in enumerate(raw.split(b"\n"), 1) if token in s]
                            hits.append((rev, word, p.relative_to(root).as_posix(), ",".join(lines)))
            records.append((key, mode + b" " + name + b"\0" + sha))
        return object_id(b"tree", b"".join(data for _, data in sorted(records)))

    check(f"{rev} src tree", scan(root / "src").hex(), SRC_TREES[rev])
    return sorted(hits)


def load_kernel(db, directory):
    for filename, sha in SHORE.items():
        check(filename, digest(directory / filename), sha)
    opts = "all_varchar=true, header=true, delim=',', quote=chr(34), escape=chr(34)"
    db.execute(
        f"""CREATE TEMP TABLE constants AS SELECT id::INTEGER AS id,name,decl,kind,origin,module,
                shared_aux::BOOLEAN AS shared, coalesce(thm_mask::INTEGER,0) AS mask
                FROM read_csv(?,{opts})""",
        [str(directory / "constants.csv.gz")],
    )
    db.execute(
        f"""CREATE TEMP TABLE decls AS SELECT decl,file,start_line::INTEGER AS line,n_constants::INTEGER AS n
                FROM read_csv(?,{opts})""",
        [str(directory / "decls.csv.gz")],
    )
    for name, file in [("edges", "edges.parquet"), ("decl_edges", "decl_edges.parquet")]:
        db.read_parquet(str(directory / file)).create_view(name)


def reverse_paths(db):
    # A typed endpoint prevents collisions between folded declarations and standalone constants.
    target = ("decl", ANY)
    distance, towards = {target: 0}, {}
    frontier = [target]
    while frontier:
        pairs = set()
        for kind in ("decl", "constant"):
            names = [name for k, name in frontier if k == kind]
            if names:
                pairs.update(
                    db.execute(
                        """SELECT DISTINCT src_kind,src,dst_kind,dst FROM decl_edges
                                        WHERE dst_kind=? AND dst IN (SELECT unnest(?))""",
                        [kind, names],
                    ).fetchall()
                )
        frontier = []
        for sk, src, dk, dst in sorted(pairs):
            node, parent = (sk, src), (dk, dst)
            if node not in distance:
                distance[node] = distance[parent] + 1
                towards[node] = parent
                frontier.append(node)
    node = ("decl", "riemannHypothesis")
    path = [node[1]]
    while node != target:
        node = towards[node]
        path.append(node[1])
    return {name: d for (kind, name), d in distance.items() if kind == "decl" and d}, path


def analyze(original, upstream, directory, out):
    verify_frozen()
    hits = scan_source(original, PROJECT) + scan_source(upstream, UPSTREAM)
    mentions = Counter((rev, name) for rev, name, _, _ in hits)
    for rev, name, count in [
        (PROJECT, "anyGeometry", 24),
        (UPSTREAM, "anyGeometry", 11),
        (UPSTREAM, "IsGeoOf", 0),
        (UPSTREAM, "HasTrueSurf", 0),
    ]:
        check(f"{rev} {name} files", mentions[rev, name], count)
    for base, pos in [(original, 19), (upstream, 20)]:
        check(
            "constant-True definition",
            (base / OVER).read_text().splitlines()[pos - 1].strip(),
            "def anyGeometry : GeoP := fun _ _ _ => True",
        )
    geo = (original / OVER).read_text().splitlines()[15:17]
    check(
        "geoOf at line 16 with both conditions",
        geo[0].startswith("def geoOf ") and all(name in geo[1] for name in UNUSED[1:]),
        True,
    )

    with duckdb.connect() as db:
        db.execute("SET threads=3")
        load_kernel(db, directory)
        distance, path = reverse_paths(db)
        check("shortest path", path, ROUTE)
        names = sorted(set(distance) | set(USED + UNUSED + path))
        locations = {
            name: (file, line, n)
            for name, file, line, n in db.execute(
                "SELECT * FROM decls WHERE decl IN (SELECT unnest(?))", [names]
            ).fetchall()
        }
        check("source declarations", set(locations), set(names))
        masks = dict(
            db.execute(
                """SELECT decl,bit_or(mask) FROM constants WHERE NOT shared AND origin='project'
                                AND decl IN (SELECT unnest(?)) GROUP BY decl""",
                [names],
            ).fetchall()
        )
        named = dict(
            db.execute("SELECT name,mask FROM constants WHERE name IN (SELECT unnest(?))", [names]).fetchall()
        )
        masks_table = []
        for name in USED + UNUSED:
            f, line, n = locations[name]
            check(name + " mask", named.get(name, 0), 31 if name in USED else 0)
            incoming, outgoing = db.execute(
                """SELECT count(*) FILTER (WHERE dst=?), count(*) FILTER (WHERE src=?)
                                        FROM edges WHERE dst=? OR src=?""",
                [name] * 4,
            ).fetchone()
            if name in UNUSED:
                check(
                    name + " absence",
                    (n, name in named, masks.get(name, 0), incoming, outgoing),
                    (0, False, 0, 0, 0),
                )
            masks_table.append((name, f, line, n, named.get(name, 0), masks.get(name, 0), incoming, outgoing))
        path_table = []
        for i, src in enumerate(path):
            f, line, _ = locations[src]
            check(
                f"{src} source anchor",
                src.rsplit(".", 1)[-1] in (original / f).read_text().splitlines()[line - 1],
                True,
            )
            dst = path[i + 1] if i + 1 < len(path) else ""
            vias = (
                [
                    r[0]
                    for r in db.execute(
                        "SELECT via FROM edges WHERE src=? AND dst=? ORDER BY via", [src, dst]
                    ).fetchall()
                ]
                if dst
                else []
            )
            if dst:
                check(f"kernel edge {src} -> {dst}", vias, ["value"])
            path_table.append((i, src, f, line, dst, ",".join(vias), url(f, line)))
        constants = db.execute(
            """SELECT c.name,c.mask,e.via FROM edges e JOIN constants c ON c.id=e.src_id
                               WHERE e.dst=? ORDER BY c.name,e.via""",
            [ANY],
        ).fetchall()
        check(
            "raw edge name/id join",
            len(constants),
            db.execute("SELECT count(*) FROM edges WHERE dst=?", [ANY]).fetchone()[0],
        )
        check("edge kinds", Counter(v for _, _, v in constants), {"type": 10, "value": 12})
        check(
            "direct kernel callers",
            (len({n for n, _, _ in constants}), len({n for n, m, _ in constants if m & 1})),
            (14, 14),
        )
        dependents = sorted((distance[n], n, masks.get(n, 0), *locations[n][:2]) for n in distance)
        rh = [row for row in dependents if row[2] & 1]
        check(
            "direct declarations / total / in RH",
            (sum(d == 1 for d in distance.values()), len(dependents), len(rh)),
            (29, 48, 24),
        )
        axioms = db.execute("""SELECT name,kind,origin,mask FROM constants WHERE (mask & 1)=1 AND
                           (kind='axiom' OR (origin='project' AND kind='opaque') OR name IN
                           ('sorryAx','Lean.ofReduceBool','Lean.trustCompiler')) ORDER BY name""").fetchall()
        check(
            "RH axioms and trust checks",
            [(n, k, o) for n, k, o, _ in axioms],
            [(n, "axiom", "core") for n in ("Classical.choice", "Quot.sound", "propext")],
        )
        check(
            "final statement",
            db.execute("SELECT origin,module FROM constants WHERE name='RiemannHypothesis'").fetchall(),
            [("mathlib", "Mathlib.NumberTheory.LSeries.RiemannZeta")],
        )
        check(
            "RH signature in Main",
            (original / locations[path[0]][0]).read_text().splitlines()[locations[path[0]][1] - 1],
            "theorem riemannHypothesis : RiemannHypothesis := rhOfAll",
        )

    traced = {r["name"]: r for r in read_rows(FROZEN / "rh-trace.tsv.gz") if r["name"] in [ANY, *UNUSED]}
    check("trace reach and depth", {n: int(r["depth"]) for n, r in traced.items()}, {ANY: 8})
    trace_rows = [
        (n, int(n in traced), traced[n]["depth"] if n in traced else "", *locations[n][:2])
        for n in [ANY, *UNUSED]
    ]
    spine = [
        (int(r["rank"]), r["anchor"], r["path"], r["line"], distance[r["anchor"]])
        for r in read_rows(FROZEN / "spine.tsv")
        if r["anchor"] in distance
    ]
    check("spine ranks", [r[0] for r in spine], [16, 17, 19, 21, 35, 157])
    files = {
        "source": (["commit", "identifier", "file", "mention_lines"], hits),
        "masks": (
            [
                "declaration",
                "file",
                "line",
                "owned_constants",
                "named_constant_mask",
                "declaration_mask",
                "incoming_edge_rows",
                "outgoing_edge_rows",
            ],
            masks_table,
        ),
        "path": (
            ["step", "declaration", "file", "line", "next_declaration", "kernel_via", "source_url"],
            path_table,
        ),
        "direct": (["referring_constant", "five_target_mask", "via"], constants),
        "dependents": (
            ["distance_to_anyGeometry", "declaration", "five_target_mask", "file", "line"],
            dependents,
        ),
        "axioms": (["constant", "kind", "origin", "five_target_mask"], axioms),
        "trace": (["declaration", "trace_reached", "source_depth", "file", "line"], trace_rows),
        "spine": (["spine_rank", "anchor", "file", "line", "distance_to_anyGeometry"], spine),
    }
    for stem, (header, rows) in files.items():
        table(out / f"anygeometry-{stem}.tsv", header, rows)
    write_note(out, path_table, rh)
    put_json(out / "anygeometry-content-sha256.json", {f.name: digest(f) for f in sorted(out.iterdir())})
    verify_frozen()


def write_note(out, path, rh):
    mathfile = "Mathlib/NumberTheory/LSeries/RiemannZeta.lean"
    s = f"""# Where `anyGeometry` occurs in the checked RH proof

The constant-True predicate `GlobalTheory.Mem.Top.Bl.anyGeometry` is eight dependency edges from `riemannHypothesis` on a kernel-checked path. Beside it, `geoOf` requires a positive integer satisfying `IsGeoOf` and a `HasTrueSurf` witness. None of the five theorems uses this predicate. [Original definitions]({url(OVER, 16)}) · [Checked path](anygeometry-path.tsv)

The final statement is Mathlib’s `RiemannHypothesis` and its proof uses the standard three axioms, so the predicate choice does not bear on whether this theorem is proved. The checked route does not use the geometric conditions suggested by these names. These tables do not locate the argument’s mathematical content. [Main theorem]({url("src/Main.lean", 4)}) · [Mathlib statement](https://github.com/leanprover-community/mathlib4/blob/{MATHLIB}/{mathfile}#L185) · [Axioms](anygeometry-axioms.tsv)

## The eight edges

Each row gives the declaration’s starting line. Each arrow to the following row has a `value` edge between those exact constant names in Shore’s kernel edge table. Searching backwards from the predicate, one edge per layer, establishes that the path is shortest. The search retains the declaration graph’s distinct declaration and constant endpoint kinds. [Edge-by-edge data](anygeometry-path.tsv)

| Distance from RH | Declaration | Original source |
| ---: | --- | --- |
"""
    for step, name, file, line, _, _, link in path:
        s += f"| {step} | `{name}` | [{Path(file).name}, line {line}]({link}) |\n"
    s += f"""
## Reach and source occurrences

In the original tree, `geoOf` starts at line 16 and `anyGeometry` at line 19 of `OverIx.lean`. Rosetta’s source trace reaches `anyGeometry` at depth 8. It misses `GlobalTheory.Mem.Top.Bl.geoOf`, `GlobalTheory.ShFam.IsGeoOf` and `GlobalTheory.ShFam.Pad.HasTrueSurf`. Shore records zero owned kernel constants and zero incident constant edges for each of these three declarations. [Trace lookup](anygeometry-trace.tsv) · [Masks and incident edges](anygeometry-masks.tsv)

The mask for `anyGeometry` is 31, the sum of the five target bits. The named constants `GlobalTheory.Mem.Top.Bl.GeoCl`, `GlobalTheory.Fc.HypsAlt`, `Formalism.L2.Geo.geoDegenerate`, `UpperTheory.Top.TopG`, `UpperTheory.Top.zeroFreeAll_of_topG` and `UpperTheory.LiteratureTheorems.every_character_of_literature_of_vWin` also have mask 31. Bit 1 marks the RH cone. [Mask table](anygeometry-masks.tsv) · [Shore’s target order]({RELEASE}/blob/v0.2.1/data/per-theorem.tsv)

Across original Lean source files under `src/`, the text `anyGeometry` occurs in 24 files. In the pruned revision it occurs in 11 files, its constant-True definition is at line 20, and `IsGeoOf` and `HasTrueSurf` each occur in zero files. These are case-sensitive text counts, including definitions. [Per-file occurrences](anygeometry-source.tsv) · [Pruned definition]({url(OVER, 20, UPSTREAM)})

## Direct callers and transitive dependents

29 declarations refer directly to `anyGeometry`. The kernel edge table records 14 distinct referring constants (22 edge rows: 10 type, 12 value), all in the RH cone. The constant edge table covers the kernel closure of the five theorems, and the declaration table covers the whole project in Main’s compiled environment. A constant may reference the predicate in both its type and its value. [Direct kernel edges](anygeometry-direct.tsv) · [Shore’s data schema]({RELEASE}/tree/v0.2.1)

Of the 48 distinct declarations that depend on the predicate, 24 lie in the RH cone. The predicate itself is excluded. The distance below is the shortest number of declaration-graph edges from the listed declaration to the predicate. Cone membership uses the union of the theorem masks of the declaration’s non-shared owned project constants. [All 48 dependents](anygeometry-dependents.tsv)

| Distance to predicate | RH-cone declaration | Original source |
| ---: | --- | --- |
"""
    for dist, name, _, file, line in rh:
        s += f"| {dist} | `{name}` | [{Path(file).name}, line {line}]({url(file, line)}) |\n"
    s += f"""
The spine anchors at ranks 16, 17, 19, 21, 35 and 157 depend on the predicate. This compares each anchor by its full declaration name with the reverse closure above. [Spine anchors and distances](anygeometry-spine.tsv)

In the RH kernel mask, the axioms are `propext`, `Quot.sound` and `Classical.choice`. The checks for `sorryAx`, `Lean.ofReduceBool`, `Lean.trustCompiler`, project axioms and project opaque constants returned zero. This audit reads the published compiled data and the pinned sources. [Axiom rows](anygeometry-axioms.tsv) · [James Shore’s v0.2.1 data]({RELEASE}/releases/tag/v0.2.1)

## Credits and reproduction

Jenny Lorraine Nielsen identified the constant-True predicate. Frank Chu asked whether the path from Main runs through it. James Shore supplied the kernel and declaration data. Levent Alpöge, a researcher at Anthropic, supplied the proof, and the Lean community’s upstream repository supplies the pruned revision. This analysis used AI assistance, including an Anthropic model. [Nielsen’s paper](https://philarchive.org/rec/NIEIOT-2) · [Chu’s question](https://dev.to/frankchu/grh-proofs-geometry-is-fun-true-in-24-files-2n2b) · [Shore’s release]({RELEASE}/releases/tag/v0.2.1) · [Alpöge’s affiliation](https://alpo.ge/) · [Original proof]({PROOF}/tree/{PROJECT}) · [Pruned source]({PROOF}/tree/{UPSTREAM})

Run from the Rosetta checkout with Git, curl, tar and the Python dependencies in `requirements.txt`. The generator verifies both source-tree IDs, the four release SHA-256 values, and the byte hashes of the 20 frozen artifacts before and after analysis. It writes the note and the tables after the numerical checks pass. The content manifest covers the generated Markdown and UTF-8 TSV files. [Generator](../analysis/anygeometry.py) · [Content manifest](anygeometry-content-sha256.json)

```bash
export LC_ALL=C
set -eo pipefail
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p inputs/anygeometry/{{original,upstream,shore}}
for pin in original:{PROJECT} upstream:{UPSTREAM}; do
  curl -fLsS --retry 3 "https://codeload.github.com/leanprover-community/riemann-hypothesis/tar.gz/${{pin#*:}}" |
    tar -xz -C "inputs/anygeometry/${{pin%:*}}" --strip-components=1
done
release={RELEASE}/releases/download/v0.2.1
for file in constants.csv.gz decls.csv.gz decl_edges.parquet edges.parquet; do
  curl -fLsS --retry 3 "$release/$file" -o "inputs/anygeometry/shore/$file"
done
.venv/bin/python analysis/anygeometry.py inputs/anygeometry/original inputs/anygeometry/upstream inputs/anygeometry/shore --out inputs/anygeometry/replayed
cmp results/anygeometry-content-sha256.json inputs/anygeometry/replayed/anygeometry-content-sha256.json
```
"""
    (out / "anygeometry.md").write_text(s, encoding="utf-8")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "upstream", "shore"):
        cli.add_argument(name, type=Path)
    cli.add_argument("--out", type=Path, default=FROZEN)
    a = cli.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.out) as tmp:
        stage = Path(tmp)
        analyze(a.original, a.upstream, a.shore, stage)
        for artifact in sorted(stage.iterdir(), key=lambda p: (p.name.endswith(".json"), p.name)):
            artifact.replace(a.out / artifact.name)


if __name__ == "__main__":
    main()
