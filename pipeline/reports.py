"""Estimation des reports de voix entre les deux tours d'une présidentielle.

Usage : python -m pipeline.reports   (après python -m pipeline.build)

Méthode (inférence écologique) : pour chaque commune, on connaît la répartition des inscrits
au 1er tour (chaque candidat, blancs et nuls, abstention) et au 2nd tour (chaque finaliste,
blancs et nuls, abstention). On cherche la matrice de transfert B telle que
    part_2nd_tour(commune) ≈ part_1er_tour(commune) × B
avec, pour chaque électorat du 1er tour, des proportions positives dont la somme fait 100 %.
Résolution par moindres carrés pondérés (poids = inscrits) sous contraintes.
Incertitude : bootstrap sur les départements (on retire / duplique des départements au hasard).

C'est une estimation statistique sur des territoires, pas une mesure des comportements
individuels : elle suppose que les électeurs d'un même candidat se reportent de façon
comparable d'une commune à l'autre.

Sortie : data/processed/reports-<année>.json pour chaque présidentielle à deux tours.
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from pipeline.config import PROCESSED_DIR

N_BOOTSTRAP = 200


def estimer(XtWX: np.ndarray, XtWY: np.ndarray, B0: np.ndarray | None = None) -> np.ndarray:
    """Moindres carrés sous contraintes : B ≥ 0 et chaque ligne de B somme à 1."""
    k, m = XtWY.shape
    B0 = np.full((k, m), 1 / m) if B0 is None else B0
    echelle = np.trace(XtWX) / k  # les sommes pondérées sont énormes : on ramène l'échelle vers 1
    XtWX, XtWY = XtWX / echelle, XtWY / echelle

    def f(b):
        B = b.reshape(k, m)
        return float(np.sum(B * (XtWX @ B)) - 2 * np.sum(B * XtWY))

    def grad(b):
        return (2 * (XtWX @ b.reshape(k, m) - XtWY)).ravel()

    contraintes = [{"type": "eq", "fun": (lambda b, i=i: b.reshape(k, m)[i].sum() - 1),
                    "jac": (lambda b, i=i: np.eye(k)[i].repeat(m).astype(float))} for i in range(k)]
    r = minimize(f, B0.ravel(), jac=grad, bounds=[(0, 1)] * (k * m), constraints=contraintes,
                 method="SLSQP", options={"maxiter": 500, "ftol": 1e-12})
    return np.clip(r.x.reshape(k, m), 0, 1)


def matrices(communes, e1, e2, n1, n2):
    """Construit X (parts du 1er tour) et Y (parts du 2nd tour) sur les inscrits, par département."""
    par_dep = {}
    for dep, liste in communes.items():
        X, Y, w = [], [], []
        for v1, v2 in liste:
            if not v1 or not v2 or v1[0] <= 0 or v2[0] <= 0:
                continue
            x = [*v1[5:5 + n1], v1[3] + v1[4], v1[0] - v1[1]]  # candidats, blancs+nuls, abstention
            y = [*v2[5:5 + n2], v2[3] + v2[4], v2[0] - v2[1]]
            X.append(np.array(x) / v1[0])
            Y.append(np.array(y) / v2[0])
            w.append(v1[0])
        if X:
            X, Y, w = np.array(X), np.array(Y), np.array(w, dtype=float)
            par_dep[dep] = (X.T @ (X * w[:, None]), X.T @ (Y * w[:, None]), len(w), (X * w[:, None]).sum(axis=0))
    return par_dep


def main(processed_dir=PROCESSED_DIR) -> None:
    elections = json.loads((processed_dir / "elections.json").read_text(encoding="utf-8"))
    deps = json.loads((processed_dir / "departements.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(2022)

    for t2 in [e for e in elections if e["type"] == "pres" and e["tour"] == 2]:
        t1 = next((e for e in elections if e["type"] == "pres" and e["annee"] == t2["annee"] and e["tour"] == 1), None)
        if t1 is None:
            continue
        noms1, noms2 = t1.get("noms", t1["candidats"]), t2.get("noms", t2["candidats"])
        n1, n2 = len(noms1), len(noms2)

        communes = {}
        for d in deps:
            data = json.loads((processed_dir / "departements" / f"{d['code']}.json").read_text(encoding="utf-8"))
            communes[d["code"]] = [(c["r"].get(t1["id"]), c["r"].get(t2["id"])) for c in data["communes"].values()]
        par_dep = matrices(communes, t1["id"], t2["id"], n1, n2)

        # On retire les catégories vides (ex. « Autres » à zéro) pour que le problème reste bien posé
        XtWX = sum(m[0] for m in par_dep.values())
        garder = np.where(np.diag(XtWX) > 1e-9)[0]
        garder_y = [j for j in range(n2 + 2) if not (j < n2 and noms2[j] == "Autres")]

        def sel(A, C):
            return A[np.ix_(garder, garder)], C[np.ix_(garder, garder_y)]

        A, C = sel(XtWX, sum(m[1] for m in par_dep.values()))
        B = estimer(A, C)

        codes = list(par_dep)
        tirages = []
        for _ in range(N_BOOTSTRAP):
            echantillon = rng.choice(codes, size=len(codes), replace=True)
            A_b, C_b = sel(sum(par_dep[c][0] for c in echantillon), sum(par_dep[c][1] for c in echantillon))
            tirages.append(estimer(A_b, C_b, B0=B))
        tirages = np.array(tirages)
        bas, haut = np.percentile(tirages, 5, axis=0), np.percentile(tirages, 95, axis=0)

        libelles1 = [*noms1, "Blancs et nuls", "Abstention"]
        familles1 = [*t1["familles"], "blanc", "abstention"]
        libelles2 = [*noms2, "Blancs et nuls", "Abstention"]
        familles2 = [*t2["familles"], "blanc", "abstention"]
        sortie = {
            "t1": t1["id"], "t2": t2["id"], "annee": t2["annee"],
            "origines": [{"nom": libelles1[i], "famille": familles1[i]} for i in garder],
            "destinations": [{"nom": libelles2[j], "famille": familles2[j]} for j in garder_y],
            "matrice": B.round(4).tolist(),
            "bas": bas.round(4).tolist(), "haut": haut.round(4).tolist(),
            "n_communes": int(sum(m[2] for m in par_dep.values())), "n_bootstrap": N_BOOTSTRAP,
            # nombre d'électeurs de chaque catégorie du 1er tour (inscrits des communes retenues)
            "effectifs": sum(m[3] for m in par_dep.values())[garder].round().astype(int).tolist(),
        }
        out = processed_dir / f"reports-{t2['annee']}.json"
        out.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"✓ Reports {t2['annee']} estimés sur {sortie['n_communes']} communes → {out.name}")
        for i, o in enumerate(sortie["origines"]):
            parts = " | ".join(f"{d['nom']} {100 * B[i, j]:.0f} %" for j, d in enumerate(sortie["destinations"]))
            print(f"   {o['nom']:<26} {parts}")


if __name__ == "__main__":
    # Option : dossier des données traitées (par défaut data/processed)
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else PROCESSED_DIR)
