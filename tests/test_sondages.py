"""Contrôles des tableaux de sondages extraits de Wikipédia (data/sondages/*.csv)."""

from pathlib import Path

import pandas as pd
import pytest

DOSSIER = Path(__file__).resolve().parent.parent / "data" / "sondages"
# nombre de lignes et somme de toutes les intentions, relevés au moment de l'extraction
ATTENDU = {"wikipedia-2012-t1.csv": (73, 7211.5), "wikipedia-2012-t2.csv": (115, 11500.0),
           "wikipedia-2017-t2.csv": (94, 9400.0)}


@pytest.mark.parametrize("fichier", sorted(ATTENDU))
def test_extraction_intacte(fichier):
    d = pd.read_csv(DOSSIER / fichier, sep=";")
    assert list(d.columns[:3]) == ["fin", "institut", "echantillon"]
    assert (len(d), d.iloc[:, 3:].sum().sum()) == ATTENDU[fichier]


@pytest.mark.parametrize("fichier", sorted(ATTENDU))
def test_valeurs_plausibles(fichier):
    d = pd.read_csv(DOSSIER / fichier, sep=";")
    assert pd.to_datetime(d["fin"], format="%Y-%m-%d").notna().all()
    scores = d.iloc[:, 3:]
    assert ((scores >= 0) & (scores <= 100) | scores.isna()).all().all()
    # chaque sondage totalise environ 100 % (arrondis des instituts, « < 0,5 % » compté 0,25) (moins pour le 1er tour quand de petits candidats manquent)
    total = scores.sum(axis=1)
    assert total.between(85, 102).all(), d[~total.between(85, 102)]
