"""Lance le pipeline sur les fausses données et vérifie quelques invariants.

Usage : python -m tests.run_fixture
"""

import json
from pathlib import Path

from pipeline import build

ICI = Path(__file__).parent
OUT = ICI / "fixture" / "processed"


def main() -> None:
    build.main(raw_dir=ICI / "fixture" / "raw", out_dir=OUT)

    elections = json.loads((OUT / "elections.json").read_text())
    ids = [e["id"] for e in elections]
    assert "2020_muni_t1" not in ids, "les municipales doivent être filtrées"
    assert ids[0] == "2017_pres_t1"

    france = json.loads((OUT / "france.json").read_text())
    for e in elections:
        v = france["france"][e["id"]]
        assert sum(v[5:]) == v[2], f"{e['id']}: somme des voix ≠ exprimés"
        assert v[1] == v[2] + v[3] + v[4], f"{e['id']}: votants ≠ exprimés + blancs + nuls"

    euro = next(e for e in elections if e["type"] == "euro")
    assert euro["candidats"][-1] == "Autres" and len(euro["candidats"]) <= 11

    ain = json.loads((OUT / "departements" / "01.json").read_text())
    assert "01053" in ain["communes"], "les codes commune doivent être au format INSEE"
    corse = json.loads((OUT / "departements" / "2A.json").read_text())
    assert "2A004" in corse["communes"]
    # La somme des communes doit retomber sur le total départemental
    e0 = ids[0]
    assert sum(c["r"][e0][0] for c in ain["communes"].values()) == ain["total"][e0][0]
    legi = next(e for e in elections if e["id"] == "2024_legi_t1")
    fam = dict(zip(legi["candidats"], legi["familles"]))
    assert fam["UG"] == "ug" and fam["RN"] == "rn" and fam["ZZZ"] == "div"
    assert len(legi["noms"]) == len(legi["candidats"])
    print("✓ tous les contrôles passent")


if __name__ == "__main__":
    main()
