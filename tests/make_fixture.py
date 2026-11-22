"""Génère de FAUSSES données au schéma exact de data.gouv, pour tester le pipeline et le site
sans télécharger les 220 Mo de données réelles.

Usage : python -m tests.make_fixture   puis   python -m tests.run_fixture
Les noms de candidats sont inventés (« Candidat A », …) : rien de réel ici.
"""

import random
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "fixture" / "raw"

COMMUNES = {
    ("01", "Ain"): [("053", "Bourg-en-Bresse"), ("004", "Ambérieu-en-Bugey"), ("283", "Oyonnax")],
    ("75", "Paris"): [("056", "Paris")],
    ("2A", "Corse-du-Sud"): [("004", "Ajaccio"), ("247", "Porto-Vecchio")],
}
ELECTIONS = {
    "2017_pres_t1": ["Candidat A", "Candidat B", "Candidat C", "Candidat D", "Candidat E"],
    "2022_pres_t1": ["Candidat A", "Candidat B", "Candidat F", "Candidat G", "Candidat H", "Candidat I"],
    "2022_pres_t2": ["Candidat A", "Candidat B"],
    "2024_euro_t1": [f"Liste {c}" for c in "ABCDEFGHIJKLMNOP"],  # beaucoup de listes → test « Autres »
    "2024_legi_t1": ["NUA", "NUB", "NUC", "NUD"],
    "2020_muni_t1": ["Liste X"],  # hors périmètre → doit être filtrée
}


def main() -> None:
    random.seed(42)
    gen, cand = [], []
    for (dep, nom_dep), communes in COMMUNES.items():
        for code_com, nom_com in communes:
            nb_bv = 12 if nom_com == "Paris" else random.randint(2, 5)
            for bv in range(1, nb_bv + 1):
                for e, noms in ELECTIONS.items():
                    inscrits = random.randint(600, 1400)
                    votants = int(inscrits * random.uniform(0.45, 0.8))
                    blancs, nuls = int(votants * 0.02), int(votants * 0.01)
                    exprimes = votants - blancs - nuls
                    poids = [random.random() ** (1 + i * 0.4) for i in range(len(noms))]
                    s = sum(poids)
                    voix = [int(exprimes * p / s) for p in poids]
                    voix[0] += exprimes - sum(voix)
                    id_brut = f"{dep}{code_com}_{bv:04d}"
                    gen.append({
                        "id_election": e, "id_brut_miom": id_brut,
                        "code_departement": dep, "libelle_departement": nom_dep,
                        "code_canton": "", "libelle_canton": "",
                        "code_commune": code_com, "libelle_commune": nom_com,
                        "code_circonscription": f"{dep}01", "libelle_circonscription": "1ère circonscription",
                        "code_bv": f"{bv:04d}", "inscrits": inscrits, "abstentions": inscrits - votants,
                        "votants": votants, "blancs": blancs, "nuls": nuls, "exprimes": exprimes,
                    })
                    typ = e.split("_")[1]
                    for i, (n, v) in enumerate(zip(noms, voix), start=1):
                        cand.append({
                            "id_election": e, "id_brut_miom": id_brut, "code_departement": dep,
                            "code_commune": code_com, "code_bv": f"{bv:04d}", "no_panneau": i, "voix": v,
                            "nuance": n if typ == "legi" else "",
                            "sexe": "", "nom": n.split()[-1] if typ == "pres" else "",
                            "prenom": n.split()[0] if typ == "pres" else "",
                            "liste": "", "libelle_abrege_liste": n if typ in ("euro", "muni") else "",
                            "libelle_etendu_liste": "", "nom_tete_liste": "", "binome": "",
                        })
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(gen).to_parquet(OUT / "general_results.parquet", index=False)
    pd.DataFrame(cand).to_parquet(OUT / "candidats_results.parquet", index=False)
    print(f"✓ fixture écrite dans {OUT} ({len(gen)} lignes générales, {len(cand)} lignes candidats)")


if __name__ == "__main__":
    main()
