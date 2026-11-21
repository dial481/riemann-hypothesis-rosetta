"""Fingerprint the unpacked trees, then scan their source independently."""
import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

from common import MATHLIB, PROJECT, RESULTS, gzout, imports, json, put_json, table


def git_tree(root):
    # Private index captures the actual files on disk, even for a dirty checkout.
    with tempfile.TemporaryDirectory() as temp:
        git = ["git", "--git-dir=" + temp, "--work-tree=" + str(root),
               "-c", "core.autocrlf=false", "-c", "core.filemode=true"]
        subprocess.run(["git", "init", "-q", "--bare", temp], check=True)
        subprocess.run(git + ["add", "-f", "--", "."], cwd=root, check=True)
        return subprocess.check_output(git + ["write-tree"], cwd=root, text=True).strip()


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("proof", type=Path)
    cli.add_argument("mathlib", type=Path)
    args = cli.parse_args()
    RESULTS.mkdir(exist_ok=True)
    adj, inventory, provenance = {}, [], {}
    for category, base, commit, tree in [
        ("Novel", args.proof, PROJECT, "e517b335d21898fd2506ad538a1e1775c0aaa4e4"),
        ("Mathlib", args.mathlib, MATHLIB, "f18edc0401eb2459e5241329743eb8626fdff148")
    ]:
        base = base.resolve()
        actual = git_tree(base)
        if actual != tree:
            raise ValueError(f"{category} tree {actual}, expected {tree}")
        provenance[category] = {"commit": commit, "git_tree": actual}
        root = base / "src" if category == "Novel" else base
        for file in sorted(root.rglob("*.lean")):
            module = ".".join(file.relative_to(root).with_suffix("").parts)
            if module in adj:
                raise ValueError(f"module name collision: {module}")
            data = file.read_bytes()
            deps = imports(data.decode("utf8"))
            adj[module] = sorted(set(deps))
            lines = data.count(b"\n") + bool(data and not data.endswith(b"\n"))
            inventory.append((module, category, file.relative_to(base).as_posix(), lines,
                              len(data), len(deps), hashlib.sha256(data).hexdigest()))
    source_modules = set(adj)
    for mod in {d for deps in adj.values() for d in deps} - source_modules:
        adj[mod] = []
    # A placeholder has no local file and no asserted outgoing dependencies.
    with gzout(RESULTS / "imports.json.gz") as out:
        out.write("{\n")
        for i, mod in enumerate(sorted(adj)):
            if i:
                out.write(",\n")
            out.write(json.dumps(mod) + ":" + json.dumps(adj[mod], separators=(",", ":")))
        out.write("\n}\n")
    table(RESULTS / "inventory.tsv.gz",
          ["module", "category", "path", "lines", "bytes", "import_commands", "sha256"], inventory)
    put_json(RESULTS / "provenance.json", provenance)


if __name__ == "__main__":
    main()
