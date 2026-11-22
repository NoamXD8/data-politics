import argparse, sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from _source import emettre

args = argparse.ArgumentParser()
args.add_argument("--dep", required=True)
emettre(f"departements/{args.parse_args().dep}.json")
