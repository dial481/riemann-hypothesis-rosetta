"""Join catalogue citations and declaration owners to the complete original module inventory."""
import json
from collections import Counter, defaultdict
from pathlib import Path

from common import content_digest, read_rows, table

MODULE_TABLE = "odesky-module-metrics.tsv.gz"
LINK_TABLE = "odesky-entry-modules.tsv.gz"
METRIC_FIELDS = ("module", "original_path", "import_rank", "cut_other_project_modules", "kernel_target_mask", "kernel_use")
FROZEN = Path("results")
USAGE = "upstream/e5ae821a/kernel-file-usage.tsv.gz"


def load_modules():
    baseline = json.loads((FROZEN / "independent-content-sha256.json").read_text())
    upstream = json.loads((FROZEN / USAGE).with_name("sha256.json").read_text())
    for name, expected in (("inventory.tsv.gz", baseline["inventory.tsv.gz"]),
                           ("metrics.tsv.gz", baseline["metrics.tsv.gz"]), (USAGE, upstream[USAGE])):
        if content_digest(FROZEN / name) != expected:
            raise ValueError(f"Module input payload changed: {name}")
    path_for = {r["module"]:r["path"] for r in read_rows(FROZEN / "inventory.tsv.gz") if r["category"] == "Novel"}
    masks = {r["original_path"]:int(r["target_mask"]) for r in read_rows(FROZEN / USAGE)}
    if set(path_for.values()) != masks.keys() or len(masks) != 175187:
        raise ValueError("Project inventories disagree")
    modules = {}
    for r in read_rows(FROZEN / "metrics.tsv.gz"):
        name = r["module"]
        if name not in path_for:
            continue
        path = path_for[name]
        mask = masks[path]
        use = "RH" if mask & 1 else "other target" if mask else "unused"
        modules[path] = (name, path, int(r["import_rank"]), int(r["disconnected_novel"]), mask, use)
    if len(modules) != len(masks) or {m[2] for m in modules.values()} != set(range(1,len(masks)+1)):
        raise ValueError("Incomplete import ranks")
    return modules


def write_module_join(dest, entries, sections, owners, used_names, modules):
    cited_counts, owner_counts, total_counts = Counter(), Counter(), Counter()
    entry_counts = {}
    rows = []
    for url, (names, refs) in sorted(entries.items()):
        citations = defaultdict(list)
        declarations = defaultdict(list)
        for ref in refs:
            path = ref.partition(":")[0]
            key = path if path.startswith("../") else "src/" + path
            citations[key].append(ref)
        for name in names:
            if name in owners:
                declarations[owners[name]].append(name)
        paths = sorted(citations.keys() | declarations.keys())
        project = set(paths) & modules.keys()
        entry_counts[url] = len(project)
        for path in paths:
            match = modules.get(path)
            if match:
                total_counts[path] += 1
                cited_counts[path] += bool(citations[path])
                owner_counts[path] += bool(declarations[path])
            cited = "|".join(sorted(citations[path]))
            owned = set(declarations[path])
            relation = "file and owner" if cited and owned else "file" if cited else "owner"
            scope = "original project" if match else "external Mathlib" if path.startswith("../.lake/packages/mathlib/") else "outside original project"
            rows.append((url, sections[url], scope, relation, *(match or ("", path, "", "", "", "")),
                         cited, "|".join(sorted(owned)), "|".join(sorted(owned & used_names)),
                         "|".join(sorted(owned - used_names))))
    table(dest / LINK_TABLE, ("entry_url", "section_url", "scope", "match", *METRIC_FIELDS, "catalogue_file_citations",
                              "owned_names", "owned_names_used_by_any_target", "owned_names_unused_by_all_targets"), rows)
    table(dest / MODULE_TABLE, (*METRIC_FIELDS,"entries_citing_file","entries_naming_owned_declaration","distinct_entries"),
          ((*module, cited_counts[p], owner_counts[p], total_counts[p]) for p,module in sorted(modules.items())))
    return entry_counts, len(total_counts)
