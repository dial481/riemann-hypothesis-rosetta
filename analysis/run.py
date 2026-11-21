"""Rebuild only the independent artifacts from the two pinned source trees."""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("proof", type=Path)
    cli.add_argument("mathlib", type=Path)
    cli.add_argument("--out", type=Path, default=Path("results"))
    args = cli.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONHASHSEED": "0", "OPENBLAS_NUM_THREADS": "1", "ROSETTA_RESULTS": str(args.out.resolve())}
    for script, params in [("inventory", [args.proof,args.mathlib]), ("structure", []), ("overview", []),
                           ("trace", [args.proof]), ("spine", [args.proof]), ("report", []),
                           ("check", [args.proof, "--mathlib", args.mathlib, "--freeze"])]:
        print(f"Running {script}", flush=True)
        subprocess.run([sys.executable, f"analysis/{script}.py", *params], env=env, check=True)


if __name__ == "__main__":
    main()
