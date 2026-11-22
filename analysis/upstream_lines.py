"""Count lines lost with removed files and all source edits, by disjoint directory."""
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from common import read_rows, table

FIELDS = ("removed_files", "lines_in_removed_files", "original_lines", "upstream_lines",
          "deleted_lines", "added_lines", "net_lines_removed")


def line_changes(original_root, upstream_root, baseline, out):
    def inventory(directory):
        return {r["path"]: int(r["lines"]) for r in read_rows(directory / "inventory.tsv.gz") if r["category"] == "Novel"}

    old, new = inventory(baseline), inventory(out)
    left, right = original_root.resolve(), upstream_root.resolve()
    diff = subprocess.run(["git", "diff", "--no-index", "--numstat", "-z", "--no-renames", "--text",
                           "--no-textconv", "--no-ext-diff", "--diff-algorithm=myers", "--indent-heuristic",
                           "--", left / "src", right / "src"], stdout=subprocess.PIPE)
    if diff.returncode not in {0, 1}:
        diff.check_returncode()
    records = iter(diff.stdout.decode("utf-8").split("\0"))
    edits = {}
    all_paths = old.keys() | new.keys()
    for header in records:
        if not header:
            break
        added, deleted, name = header.split("\t", 2)
        if name:
            raise ValueError(f"Expected a pair of no-index paths for {name}")
        a, b = next(records), next(records)
        paths = {Path(p).relative_to(side).as_posix() for p,side in ((a,left),(b,right)) if p != "/dev/null"}
        if len(paths) != 1:
            raise ValueError(f"Unexpected path change: {a}, {b}")
        path = paths.pop()
        if path.endswith(".lean"):
            if path in edits or path not in all_paths:
                raise ValueError(f"Unexpected diff record: {path}")
            edits[path] = int(added), int(deleted)
    by_directory = defaultdict(Counter)
    families = defaultdict(Counter)
    for p in sorted(all_paths):
        adds, dels = edits.get(p, (0, 0))
        before, after = old.get(p, 0), new.get(p, 0)
        if before - after != dels - adds:
            raise ValueError(f"Inventory and diff line totals disagree: {p}")
        directory = p.rsplit("/",1)[0]
        family = "/".join(directory.split("/")[:2])
        values = dict(zip(FIELDS, (int(p not in new), before if p not in new else 0, before, after,
                                   dels, adds, before - after), strict=True))
        by_directory[directory].update(values)
        families[family].update(values)
    table(out / "line-changes-by-directory.tsv", ["directory", *FIELDS],
          ((directory, *(v[k] for k in FIELDS)) for directory,v in sorted(by_directory.items())))
    total = Counter()
    for v in families.values():
        total.update(v)
    return families, total
