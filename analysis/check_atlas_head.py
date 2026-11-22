"""Compare the atlas model at a resolved Git commit with the analysis pin."""
import argparse
import hashlib
import json
import re
import subprocess
from urllib.request import Request, urlopen

REPO = "https://github.com/nasqret/riemann-rev.git"
PIN = "d53b3804bd013df4cf9af3b4087728148c90c9bd"
MODEL_SHA256 = "8c85bd83b65afa31e330392acd81124397815d6d072a51dca19633936c4af544"


def model_url(commit):
    return f"https://raw.githubusercontent.com/nasqret/riemann-rev/{commit}/data/model.json"


def compare_model(commit=None):
    if commit is None:
        line = subprocess.check_output(["git", "ls-remote", "--exit-code", REPO, "HEAD"], text=True)
        commit, ref = line.strip().split()
        assert ref == "HEAD"
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full Git commit")
    with urlopen(Request(model_url(commit), headers={"User-Agent": "Rosetta-model-check"}), timeout=30) as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"pinned_commit": PIN, "pinned_sha256": MODEL_SHA256, "checked_commit": commit,
            "checked_sha256": actual, "matches_pinned": actual == MODEL_SHA256}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--commit", help="Replay a recorded observation. Defaults to the current remote HEAD.")
    print(json.dumps(compare_model(cli.parse_args().commit), indent=2))
