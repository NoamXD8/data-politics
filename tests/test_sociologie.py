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


def main():
    rng = np.random.default_rng(1)
    large = faux_insee(communes(), rng)
    long = large.melt(id_vars="CODGEO", var_name="INDICATEUR", value_name="OBS_VALUE").rename(columns={"CODGEO": "GEO"})
    long["GEO_OBJECT"] = "COM"
    long["OBS_VALUE"] = long["OBS_VALUE"].astype(str)
    for nom, df, ext in [("large", large, "csv"), ("long", long, "parquet")]:
        dossier = ICI / "fixture" / "raw" / "insee"
        shutil.rmtree(dossier, ignore_errors=True)
        dossier.mkdir(parents=True)
        (df.to_csv(dossier / "base.csv", index=False, sep=",") if ext == "csv" else df.to_parquet(dossier / "base.parquet"))
        sociologie.DOSSIER_INSEE = dossier
        sociologie.main(PROCESSED)
        out = json.loads((PROCESSED / "sociologie.json").read_text())
        bloc = out["elections"]["2022_pres_t1"]
        assert set(out["indicateurs"]) == {"med", "tp60", "chom", "densite", "pop", "rsec"}, out["indicateurs"].keys()
        tr = bloc["indicateurs"]["med"]
        assert sum(t["communes"] for t in tr) == bloc["communes"]
        assert all(abs(sum(t["scores"].values()) - 1) < 0.02 for t in tr), "scores d'une tranche ≈ 100 %"
        print(f"✓ format {nom} : {bloc['communes']} communes, {len(tr)} tranches")
    shutil.rmtree(ICI / "fixture" / "raw" / "insee")


if __name__ == "__main__":
    main()
