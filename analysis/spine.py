"""Fuse hub and cut rankings, then attach source witnesses and reader notes."""
import argparse
from collections import Counter
from pathlib import Path

from common import PROJECT, RESULTS, read_rows, table

SOURCE = f"https://github.com/leanprover-community/riemann-hypothesis/blob/{PROJECT}/"


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("proof", type=Path)
    cli.add_argument("--preview", type=Path, help="Write a temporary source-reading worksheet instead of publication files")
    args = cli.parse_args()
    metrics = {r["module"]: r for r in read_rows(RESULTS / "metrics.tsv.gz") if r["import_rank"]}
    inventory = {r["module"]: r for r in read_rows(RESULTS / "inventory.tsv.gz") if r["category"] == "Novel"}
    cutlist = sorted((m for m, r in metrics.items() if m != "Main" and int(r["disconnected_novel"])),
                     key=lambda m: (-int(metrics[m]["disconnected_novel"]), m))
    cut_rank = {m: i for i, m in enumerate(cutlist, 1)}

    counts, anchor, best = Counter(), {}, {}
    witnesses = {}
    for r in read_rows(RESULTS / "rh-trace.tsv.gz"):
        m, n = r["module"], int(r["line"])
        counts[m] += 1
        key = (int(r["depth"]), r["kind"] not in ("theorem", "lemma"), n)
        if m not in best or key < best[m]:
            best[m], anchor[m] = key, r
        witnesses[m, n] = (r["caller_module"], int(r["caller_decl_line"]), int(r["use_line"]), r["token"], r["name"])
    def score(m):
        return 1 / (50 + int(metrics[m]["import_rank"])) + (1 / (50 + cut_rank[m]) if m in cut_rank else 0)
    selected = sorted(anchor, key=lambda m: (-score(m), m))[:200]
    if len(selected) != 200:
        raise ValueError("Insufficient distinct source-traced modules")
    if args.preview:
        with args.preview.open("w") as out:
            for i, m in enumerate(selected, 1):
                a = anchor[m]
                lines = (args.proof / inventory[m]["path"]).read_text().splitlines()
                j = int(a["line"]) - 1
                snippet = " ".join(s.strip() for s in lines[j:j+6]).split(" := by")[0][:600]
                print(f"{i}\t{m}\t{a['name']}\t{snippet}", file=out)
        return
    notes = {r["module"]: r for r in read_rows("analysis/reader-notes.tsv")}
    if set(selected) != notes.keys():
        raise ValueError("Reader annotations do not match the independently selected modules")
    rows, chains = [], {}
    markdown = ["# A reading spine of 200 modules", "",
                "Read down the table for a balance of widely imported foundations and modules that guard large branches. "
                "Each source link opens the selected declaration in the original archive. The two numbers in the impact "
                "column are direct project dependents and other project modules disconnected by removal. The evidence "
                "column links to the literal reference in its caller and gives the number of explicit source steps from RH. "
                "The complete line-by-line chains are in [spine-witnesses.json.gz](spine-witnesses.json.gz).", "",
                "| Priority | Import rank | File and starting line | Dependents / cut | RH source evidence | What to read here |",
                "|---:|---:|---|---:|---|---|"]
    for priority, m in enumerate(selected, 1):
        a, mr, note = anchor[m], metrics[m], notes[m]
        path, line = inventory[m]["path"], int(a["line"])
        if a["name"] != note["anchor"]:
            raise ValueError(f"Anchor mismatch in {m}")
        url = SOURCE + path + f"#L{line}"
        callerpath = inventory[a["caller_module"]]["path"]
        callerurl = SOURCE + callerpath + "#L" + a["use_line"]
        rows.append((priority, m, path, line, a["name"], a["kind"], mr["import_rank"], cut_rank.get(m, ""),
                     score(m), mr["novel_dependents"], mr["disconnected_novel"], mr["community"], counts[m],
                     a["depth"], a["caller"], callerpath, a["use_line"], a["token"], note["description"], url))
        markdown.append(f"| {priority} | {mr['import_rank']} | [{path}:{line}]({url}) | {mr['novel_dependents']} / "
                        f"{mr['disconnected_novel']} | [{a['token'] or a['name']}]({callerurl}) · {a['depth']} steps | {note['description']} |")
        chain, node = [], (m, line)
        while True:
            caller, start, use_line, token, name = witnesses[node]
            chain.append({"module": node[0], "path": inventory[node[0]]["path"], "line": node[1], "name": name,
                          "caller_use_line": use_line if token else None, "token_in_caller": token})
            if (caller, start) == node:
                break
            node = (caller, start)
        chains[m] = chain[::-1]
    header = ["rank", "module", "path", "line", "anchor", "kind", "import_rank", "cut_rank", "reading_score",
              "novel_dependents", "disconnected_novel", "community", "traced_declarations", "rh_steps", "caller",
              "caller_path", "use_line", "token", "description", "source_url"]
    table(RESULTS / "spine.tsv", header, rows)
    from common import gzout, json
    with gzout(RESULTS / "spine-witnesses.json.gz") as out:
        json.dump(chains, out, ensure_ascii=False, separators=(",", ":"))
    (RESULTS / "SPINE.md").write_text("\n".join(markdown) + "\n")


if __name__ == "__main__":
    main()
