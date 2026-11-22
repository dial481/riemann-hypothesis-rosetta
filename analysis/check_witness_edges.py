"""Check direct kernel references between the endpoints of two source witnesses."""
import argparse
import csv
import gzip
import json
import re
from pathlib import Path

import duckdb

from common import digest

EDGES_SHA256 = "423a8dfe2150b5a5937679a5822f1477b7d10f241702afc6abd254813203aaae"
EDGES_BYTES = 399119904
CONSTANTS_SHA256 = "2964f5236046325ac7884906cb9517b0aa582330dd48a07eef291cb579444820"
# Rank, source caller, target, expected outgoing edge rows and distinct incoming constants.
WITNESSES = (
    (14, "PositivityTheory.ThKEst.siegelAll_of", "Formalism.UG.hform", 327, 1630),
    (128, "GlobalTheory.FunObj.exists_coords", "Formalism.GradedWeylDivisibility.sSIdxFinite", 97, 50),
)


def audit(directory):
    parquet = directory / "edges.parquet"
    constants = directory / "constants.csv.gz"
    if parquet.stat().st_size != EDGES_BYTES or digest(parquet) != EDGES_SHA256:
        raise ValueError("The kernel edge table differs from the pinned release")
    if digest(constants) != CONSTANTS_SHA256:
        raise ValueError("The constant ownership table differs from the pinned release")

    names = {name for _, caller, target, _, _ in WITNESSES for name in (caller, target)}
    families = {name: {} for name in names}
    prefix = re.compile(r"^(" + "|".join(re.escape(n) for n in sorted(names)) + r")\.")
    exact = {}
    with gzip.open(constants, "rt") as stream:
        for r in csv.DictReader(stream):
            if r["origin"] != "project":
                continue
            owner, name = r["decl"], r["name"]
            if owner in families:
                families[owner][int(r["id"])] = name
            # Include dotted generated names even if folded to another owner in the release.
            nested = prefix.match(name)
            if nested:
                families[nested[1]][int(r["id"])] = name
            if name in families:
                assert name not in exact and name == owner, name
                exact[name] = int(r["id"])
    assert exact.keys() == names

    # Include shared auxiliaries in the family test as a conservative superset.
    db = duckdb.connect(":memory:")
    results = []
    try:
        for rank, caller, target, _, _ in WITNESSES:
            src_ids, dst_ids = sorted(families[caller]), sorted(families[target])
            src_params = ", ".join("?" for _ in src_ids)
            dst_params = ", ".join("?" for _ in dst_ids)
            edges = db.execute(
                f"SELECT src_id, dst_id FROM read_parquet(?) WHERE src_id IN ({src_params}) OR dst_id IN ({dst_params})",
                [str(parquet), *src_ids, *dst_ids],
            ).fetchall()
            outgoing = [dst for src,dst in edges if src == exact[caller]]
            incoming = [src for src,dst in edges if dst == exact[target]]
            family_incoming = [src for src,dst in edges if dst in families[target]]
            family_hits = [(src,dst) for src,dst in edges if src in families[caller] and dst in families[target]]
            row = {
                "rank": rank, "caller": caller, "target": target,
                "caller_family": sorted(families[caller].values()), "target_family": sorted(families[target].values()),
                "caller_outgoing_edge_rows": len(outgoing), "caller_distinct_targets": len(set(outgoing)),
                "target_incoming_edge_rows": len(incoming), "target_distinct_callers": len(set(incoming)),
                "target_family_incoming_edge_rows": len(family_incoming),
                "target_family_distinct_callers": len(set(family_incoming)),
                "exact_edge_rows": outgoing.count(exact[target]), "family_edge_rows": len(family_hits),
            }
            results.append(row)
    finally:
        db.close()
    return {"edges_bytes": EDGES_BYTES, "edges_sha256": EDGES_SHA256, "constants_sha256": CONSTANTS_SHA256,
            "witnesses": results}


def check_expected(result):
    for row, (_, _, _, outgoing, incoming) in zip(result["witnesses"], WITNESSES, strict=True):
        if (row["caller_outgoing_edge_rows"], row["target_distinct_callers"], row["family_edge_rows"]) != (outgoing, incoming, 0):
            raise ValueError("Kernel comparison differs from the expected counts: " + json.dumps(result["witnesses"]))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("release_dir", type=Path)
    result = audit(cli.parse_args().release_dir)
    print(json.dumps(result, indent=2))
    check_expected(result)
