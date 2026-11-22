"""Vérifie que l'estimation des reports retrouve une matrice de transfert connue.

On fabrique des communes avec des résultats de 1er tour aléatoires, on applique une
matrice de transfert « vraie » (plus un peu de bruit), puis on vérifie que le modèle
la retrouve. Usage : python -m tests.test_reports
"""

import numpy as np

from pipeline.reports import estimer, matrices

VRAIE = np.array([  # lignes : A, B, C, blancs+nuls, abstention ; colonnes : X, Y, blancs+nuls, abstention
    [0.85, 0.05, 0.05, 0.05],
    [0.10, 0.80, 0.03, 0.07],
    [0.40, 0.15, 0.15, 0.30],
    [0.10, 0.05, 0.60, 0.25],
    [0.03, 0.04, 0.01, 0.92],
])


def main() -> None:
    rng = np.random.default_rng(0)
    communes = {}
    for d in range(60):
        liste = []
        for _ in range(150):
            inscrits = int(rng.integers(200, 5000))
            parts = rng.dirichlet([4, 3, 3, 0.4, 2.5])
            t1 = (parts * inscrits).round().astype(int)
            t2 = (parts @ VRAIE * inscrits * rng.normal(1, 0.03, 4)).clip(0).round().astype(int)
            v1 = [inscrits, inscrits - t1[4], t1[:3].sum(), t1[3], 0, *t1[:3]]
            v2 = [int(t2.sum()), int(t2[:3].sum()), int(t2[:2].sum()), int(t2[2]), 0, *t2[:2]]
            liste.append((v1, v2))
        communes[str(d)] = liste
    par_dep = matrices(communes, "t1", "t2", 3, 2)
    B = estimer(sum(m[0] for m in par_dep.values()), sum(m[1] for m in par_dep.values()))
    erreur = np.abs(B - VRAIE).max()
    print(np.round(B, 3))
    print(f"erreur maximale : {100 * erreur:.1f} points")
    assert np.allclose(B.sum(axis=1), 1, atol=1e-6), "chaque ligne doit sommer à 100 %"
    assert erreur < 0.05, "la matrice estimée doit être proche de la vraie"
    print("✓ la méthode retrouve les reports connus")


if __name__ == "__main__":
    main()
