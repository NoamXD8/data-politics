"""Teste le lecteur INSEE sur les deux formats (large et long) avec de fausses données.
Usage : python -m tests.test_sociologie"""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import sociologie

ICI = Path(__file__).parent
PROCESSED = ICI / "fixture" / "processed"


def communes():
    codes = []
    for f in (PROCESSED / "departements").glob("*.json"):
        codes += list(json.loads(f.read_text())["communes"])
    return codes


def faux_insee(codes, rng):
    return pd.DataFrame({
        "CODGEO": codes, "P22_POP": rng.integers(100, 200000, len(codes)), "SUPERF": rng.uniform(1, 80, len(codes)).round(2),
        "MED22": rng.integers(17000, 32000, len(codes)), "TP6022": rng.uniform(5, 30, len(codes)).round(1),
        "P22_CHOM1564": rng.integers(10, 900, len(codes)), "P22_ACT1564": rng.integers(1000, 9000, len(codes)),
        "P22_RSECOCC": rng.integers(0, 500, len(codes)), "P22_LOG": rng.integers(600, 9000, len(codes)),
    })


def faux_insee_2026(codes, rng):
    """Copie de la structure de la base INSEE publiée en juillet 2026 (format long)."""
    mesures = {"POP": ("DS_RP_SERIE_HISTORIQUE", lambda: rng.integers(100, 200000)), "SUP": ("DS_RP_SERIE_HISTORIQUE", lambda: rng.uniform(1, 80)),
               "MED_SL": ("DS_FILOSOFI_CC", lambda: rng.integers(17000, 32000)), "PR_MD60": ("DS_FILOSOFI_CC", lambda: rng.uniform(5, 30)),
               "DWELLINGS": ("DS_RP_LOGEMENT_PRINC", lambda: rng.integers(800, 9000)), "DWELLINGS_OCS_DW_MAIN": ("DS_RP_LOGEMENT_PRINC", lambda: rng.integers(500, 700)),
               "DWELLINGS_OCS_DW_MAIN_TSH_100": ("DS_RP_LOGEMENT_PRINC", lambda: rng.integers(100, 500)),
               "DWELLINGS_OCS_DW_SEC_DW_OCC": ("DS_RP_LOGEMENT_PRINC", lambda: rng.integers(0, 300)), "DWELLINGS_OCS_DW_VAC": ("DS_RP_LOGEMENT_PRINC", lambda: rng.integers(0, 100)),
               "LVB": ("DS_ETAT_CIVIL_NAIS_COMMUNES", lambda: rng.integers(0, 50))}
    lignes = []
    for code in codes:
        for m, (ds, val) in mesures.items():
            for annee in ("2017", "2023"):  # plusieurs millésimes : le plus récent doit être retenu
                lignes.append({"GEO_REF": "2026", "GEO_OBJECT": "COM", "GEO_OBJECT_LABEL": "Commune", "GEO": code, "GEO_LABEL": code,
                               "TIME_PERIOD": annee, "DS": ds, "TAB_MEASURE": m, "TAB_MEASURE_LABEL": m, "OBS_VALUE": float(val()),
                               "OBS_STATUS": "A", "UNIT_MEASURE": None, "CONF_STATUS": None})
        lignes.append({**lignes[-1], "GEO_OBJECT": "DEP", "GEO": code[:2]})  # autre niveau à ignorer
    return pd.DataFrame(lignes)


def main():
    rng = np.random.default_rng(1)
    large = faux_insee(communes(), rng)
    long = large.melt(id_vars="CODGEO", var_name="INDICATEUR", value_name="OBS_VALUE").rename(columns={"CODGEO": "GEO"})
    long["GEO_OBJECT"] = "COM"
    long["OBS_VALUE"] = long["OBS_VALUE"].astype(str)
    nouveau = faux_insee_2026(communes(), rng)
    attendus = {"large": {"med", "tp60", "chom", "densite", "pop", "rsec"}, "long": {"med", "tp60", "chom", "densite", "pop", "rsec"},
                "insee-2026": {"med", "tp60", "densite", "pop", "rsec", "proprio", "vac"}}
    for nom, df, ext in [("large", large, "csv"), ("long", long, "parquet"), ("insee-2026", nouveau, "parquet")]:
        dossier = ICI / "fixture" / "raw" / "insee"
        shutil.rmtree(dossier, ignore_errors=True)
        dossier.mkdir(parents=True)
        (df.to_csv(dossier / "base.csv", index=False, sep=",") if ext == "csv" else df.to_parquet(dossier / "base.parquet"))
        sociologie.DOSSIER_INSEE = dossier
        sociologie.main(PROCESSED)
        out = json.loads((PROCESSED / "sociologie.json").read_text())
        bloc = out["elections"]["2022_pres_t1"]
        assert set(out["indicateurs"]) == attendus[nom], out["indicateurs"].keys()
        tr = bloc["indicateurs"]["med"]
        assert sum(t["communes"] for t in tr) == bloc["communes"]
        assert all(abs(sum(t["scores"].values()) - 1) < 0.02 for t in tr), "scores d'une tranche ≈ 100 %"
        print(f"✓ format {nom} : {bloc['communes']} communes, {len(tr)} tranches")
    shutil.rmtree(ICI / "fixture" / "raw" / "insee")


if __name__ == "__main__":
    main()
