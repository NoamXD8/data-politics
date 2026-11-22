"""Croisement vote × INSEE préparé par python -m pipeline.sociologie (renvoie null s'ils n'ont pas encore été générés)."""
import os
import sys
from pathlib import Path

dossier = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[3] / "data" / "processed"))
fichier = dossier / "sociologie.json"
sys.stdout.write(fichier.read_text(encoding="utf-8") if fichier.exists() else "null")
