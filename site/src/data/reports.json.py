"""Reports de voix estimés par python -m pipeline.reports, regroupés par année ({} s'ils n'existent pas)."""
import json
import os
import sys
from pathlib import Path

dossier = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[3] / "data" / "processed"))
sortie = {f.stem.split("-")[1]: json.loads(f.read_text(encoding="utf-8")) for f in sorted(dossier.glob("reports-*.json"))}
json.dump(sortie, sys.stdout, ensure_ascii=False)
