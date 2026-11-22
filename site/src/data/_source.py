"""Partagé par les data loaders : où trouver les fichiers produits par le pipeline."""
import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("DATA_DIR", RACINE / "data" / "processed"))


def emettre(nom: str) -> None:
    chemin = DATA_DIR / nom
    if not chemin.exists():
        sys.exit(f"{chemin} introuvable : lance d'abord `python -m pipeline.build` à la racine du projet.")
    sys.stdout.write(chemin.read_text(encoding="utf-8"))
