from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path

PROJECT = "40e56bab026552e089d7afcfeff08d2defb9c005"
MATHLIB = "0df444a360eaa60ab8c11dca51a86af692955474"
PAGERANK_PLACES = 14
SCORE_PLACES = 12
RESULTS = Path(os.environ.get("ROSETTA_RESULTS", "results"))
SEG = r"(?:«[^»\n]+»|[^\W\d][\w'₀-₉]*)"
NAME = rf"{SEG}(?:\.{SEG})*"
NAME_RE = re.compile(NAME)
SPACE = re.compile(r"\s+|--[^\n]*")
COMMENT = re.compile(r"/-|-/")


def imports(source):
    """Read only the module header. Comments can nest or separate tokens."""
    pos = 0
    expecting = False
    dependencies = []
    while pos < len(source):
        gap = SPACE.match(source, pos)
        if gap:
            pos = gap.end()
            continue
        if source.startswith("/-", pos):
            depth = 1
            for delim in COMMENT.finditer(source, pos + 2):
                depth += 1 if delim[0] == "/-" else -1
                if not depth:
                    pos = delim.end()
                    break
            else:
                raise ValueError("unterminated header comment")
            continue
        match = NAME_RE.match(source, pos)
        if not match:
            break
        token = match[0]
        pos = match.end()
        if expecting and token != "all":
            dependencies.append(token.replace("«", "").replace("»", ""))
            expecting = False
        elif token == "import":
            expecting = True
        elif token not in {"module", "prelude", "public", "private", "meta", "all"}:
            break
    if expecting:
        raise ValueError("incomplete import")
    return dependencies


@contextmanager
def gzout(path):
    with Path(path).open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=6) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf8", newline="") as out:
                yield out


def put_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def table(path, fields, rows):
    with (gzout(path) if str(path).endswith(".gz") else Path(path).open("w", newline="")) as out:
        wr = csv.writer(out, delimiter="\t", lineterminator="\n")
        wr.writerow(fields)
        wr.writerows(rows)


def read_rows(path):
    with (gzip.open(path, "rt") if str(path).endswith(".gz") else open(path)) as src:
        yield from csv.DictReader(src, delimiter="\t")


def archive_data():
    with gzip.open(RESULTS / "imports.json.gz", "rt") as src:
        adjacency = json.load(src)
    records = {r["module"]: r for r in read_rows(RESULTS / "inventory.tsv.gz")}
    return adjacency, records


def digest(path):
    with open(path, "rb") as src:
        return hashlib.file_digest(src, "sha256").hexdigest()



def content_digest(path):
    """Hash a generated artifact's payload independently of its gzip encoding."""
    if Path(path).suffix != ".gz":
        return digest(path)
    with gzip.open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
