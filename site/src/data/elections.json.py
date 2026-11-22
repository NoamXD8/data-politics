import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _source import emettre

emettre("elections.json")
