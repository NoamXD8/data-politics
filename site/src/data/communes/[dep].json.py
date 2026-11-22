"""Contours simplifiés des communes d'un département (site/geo/communes/XX.json).

Source : IGN Admin Express via france-geojson (Licence Ouverte), simplifiés à 6 %.
Renvoie une collection vide pour les territoires sans contour (outre-mer, étranger).
"""
import argparse
import sys
from pathlib import Path

dep = argparse.ArgumentParser()
dep.add_argument("--dep", required=True)
fichier = Path(__file__).resolve().parents[3] / "geo" / "communes" / f"{dep.parse_args().dep}.json"
sys.stdout.write(fichier.read_text(encoding="utf-8") if fichier.exists() else '{"type":"FeatureCollection","features":[]}')
