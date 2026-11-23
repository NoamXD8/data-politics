"""Sondages de la présidentielle 2022 : évolution, écart avec les résultats, précision des instituts.

Usage : python -m pipeline.sondages   (après python -m pipeline.build)

Source des sondages : NSPPolls (https://github.com/nsppolls/nsppolls), licence MIT,
compilation des sondages publiés (notices de la Commission des sondages).
Les résultats officiels viennent de data/processed (pipeline.build).

Sortie : data/processed/sondages-2022.json
"""

import json
import re
import sys
import unicodedata
from datetime import date

import numpy as np
import pandas as pd
import requests

from pipeline.config import PROCESSED_DIR, RAW_DIR

URL = "https://raw.githubusercontent.com/nsppolls/nsppolls/master/presidentielle.csv"
FICHIER = RAW_DIR / "nsppolls-presidentielle.csv"
ELECTION_T1, ELECTION_T2 = "2022_pres_t1", "2022_pres_t2"
DEBUT = "2021-09-01"  # un scénario par sondage : celui des candidats réellement présents
# Interdiction de publication la veille et le jour du vote : derniers sondages publiables
DERNIER_T1, DERNIER_T2 = "2022-04-08", "2022-04-22"


def cle(nom: str) -> str:
    """« Éric ZEMMOUR » et « Eric Zemmour » → « eric-zemmour »."""
    s = unicodedata.normalize("NFD", nom)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def telecharger(force=False) -> pd.DataFrame:
    if force or not FICHIER.exists():
        print("↓ sondages NSPPolls …")
        r = requests.get(URL, timeout=60)
        r.raise_for_status()
        FICHIER.parent.mkdir(parents=True, exist_ok=True)
        FICHIER.write_bytes(r.content)
    return pd.read_csv(FICHIER)


def resultats(processed_dir, election_id) -> dict:
    """Résultats officiels (% des exprimés) par candidat, depuis la sortie de pipeline.build."""
    elections = json.loads((processed_dir / "elections.json").read_text(encoding="utf-8"))
    france = json.loads((processed_dir / "france.json").read_text(encoding="utf-8"))["france"]
    el = next((e for e in elections if e["id"] == election_id), None)
    if el is None or election_id not in france:
        sys.exit(f"{election_id} absent des données : lance d'abord python -m pipeline.build")
    v = france[election_id]
    noms = el.get("noms", el["candidats"])
    return {cle(n): {"nom": n, "famille": f, "pct": round(100 * v[5 + i] / v[2], 2)}
            for i, (n, f) in enumerate(zip(noms, el["familles"])) if n != "Autres"}


def un_scenario_par_sondage(df: pd.DataFrame, candidats: set) -> pd.DataFrame:
    """Un même sondage peut tester plusieurs hypothèses : on garde celle qui contient
    le plus de candidats réellement présents au 1er tour."""
    df = df.assign(hyp=df["hypothese"].fillna(""), present=df["cle"].isin(candidats))
    score = df.groupby(["id", "hyp"])["present"].sum().reset_index()
    meilleure = score.sort_values(["id", "present", "hyp"], ascending=[True, False, True]).drop_duplicates("id")
    return df.merge(meilleure[["id", "hyp"]], on=["id", "hyp"])


def precision(derniers: pd.DataFrame, res: dict) -> list:
    """Erreur de chaque institut sur son dernier sondage publiable."""
    lignes = []
    for (institut, sid), g in derniers.groupby(["nom_institut", "id"]):
        ecarts = {r.cle: r.intentions - res[r.cle]["pct"] for r in g.itertuples() if r.cle in res}
        if len(ecarts) < len(res) * 0.8:
            continue
        pire = max(ecarts, key=lambda k: abs(ecarts[k]))
        lignes.append({
            "institut": institut, "id": sid, "fin": g["fin_enquete"].iloc[0], "echantillon": int(g["echantillon"].iloc[0]),
            "erreur_moyenne": round(sum(abs(e) for e in ecarts.values()) / len(ecarts), 2),
            "pire": {"nom": res[pire]["nom"], "ecart": round(ecarts[pire], 2)},
            "ecarts": {k: round(e, 2) for k, e in ecarts.items()},
        })
    return sorted(lignes, key=lambda x: x["erreur_moyenne"])


def tendance(d: pd.DataFrame, fin: str, h: float = 8.0) -> list:
    """Moyenne lissée des sondages, jour par jour : régression locale linéaire (noyau gaussien de
    largeur h jours, pondéré par la racine de l'échantillon), qui suit les tendances jusqu'au
    dernier jour sans être tirée vers le passé, avec une bande d'incertitude à 95 %."""
    t = (pd.to_datetime(d["fin_enquete"]) - pd.Timestamp("2000-01-01")).dt.days.to_numpy(float)
    y = d["intentions"].to_numpy(float)
    n = (d["echantillon"].fillna(1000).clip(lower=300).to_numpy(float) / 1000) ** 0.5
    jours = np.arange(t.min(), (pd.Timestamp(fin) - pd.Timestamp("2000-01-01")).days + 1)
    sortie = []
    for j in jours:
        noyau = np.exp(-0.5 * ((j - t) / h) ** 2)
        w = noyau * n
        if noyau.sum() < 1.5:  # trop peu de sondages autour de cette date
            continue
        x = t - j
        X = np.column_stack([np.ones_like(x), x])
        XtW = X.T * w
        try:
            a, b = np.linalg.solve(XtW @ X + np.diag([1e-9, 1e-3]), XtW @ y)
        except np.linalg.LinAlgError:
            a, b = (w * y).sum() / w.sum(), 0.0
        m = a
        n_eff = w.sum() ** 2 / (w ** 2).sum()
        se = np.sqrt(max((w * (y - (a + b * x)) ** 2).sum() / w.sum(), 0.25) / n_eff)
        sortie.append({"date": (pd.Timestamp("2000-01-01") + pd.Timedelta(days=int(j))).date().isoformat(),
                       "moy": round(m, 2), "bas": round(m - 1.96 * se, 2), "haut": round(m + 1.96 * se, 2)})
    return sortie


def main(processed_dir=PROCESSED_DIR, force=False) -> None:
    df = telecharger(force)
    df["cle"] = df["candidat"].map(cle)
    res1, res2 = resultats(processed_dir, ELECTION_T1), resultats(processed_dir, ELECTION_T2)

    # 1er tour : un scénario par sondage, depuis janvier 2022, candidats du 1er tour seulement
    t1 = df[(df["tour"] == "Premier tour") & (df["fin_enquete"] >= DEBUT) & (df["fin_enquete"] <= DERNIER_T1)]
    t1 = un_scenario_par_sondage(t1, set(res1))
    t1 = t1[t1["cle"].isin(res1)]

    # Dernier sondage publiable de chaque institut
    dernier_id = t1.sort_values("fin_enquete").groupby("nom_institut")["id"].last()
    derniers = t1[t1["id"].isin(dernier_id)]
    instituts = precision(derniers, res1)
    moyenne = derniers.groupby("cle")["intentions"].mean()

    # 2nd tour : duel Macron - Le Pen
    finalistes = set(res2)
    t2 = df[(df["tour"] == "Deuxième tour") & (df["fin_enquete"] >= DEBUT) & (df["fin_enquete"] <= DERNIER_T2)]
    t2 = t2[t2.groupby("id")["cle"].transform(lambda s: set(s) == finalistes)]
    t2_dernier_id = t2.sort_values("fin_enquete").groupby("nom_institut")["id"].last()
    instituts_t2 = precision(t2[t2["id"].isin(t2_dernier_id)], res2)

    def sondages(d):
        return [{"id": sid, "institut": g["nom_institut"].iloc[0], "fin": g["fin_enquete"].iloc[0],
                 "echantillon": int(g["echantillon"].iloc[0]), "rolling": bool(g["rolling"].iloc[0]),
                 "scores": {r.cle: float(r.intentions) for r in g.itertuples()}}
                for sid, g in d.sort_values("fin_enquete").groupby("id", sort=False)]

    sortie = {
        "source": {"nom": "NSPPolls", "url": "https://github.com/nsppolls/nsppolls", "licence": "MIT",
                   "reference": "https://fr.wikipedia.org/wiki/Liste_de_sondages_sur_l%27%C3%A9lection_pr%C3%A9sidentielle_fran%C3%A7aise_de_2022"},
        "genere_le": date.today().isoformat(),
        "t1": {"candidats": res1, "sondages": sondages(t1), "dernier_jour": DERNIER_T1, "vote": "2022-04-10",
               "tendances": {k: tendance(g, DERNIER_T1) for k, g in t1.groupby("cle")},
               "instituts": instituts,
               "moyenne_finale": {k: round(v, 2) for k, v in moyenne.items()}},
        "t2": {"candidats": res2, "sondages": sondages(t2), "dernier_jour": DERNIER_T2, "vote": "2022-04-24",
               "tendances": {k: tendance(g, DERNIER_T2) for k, g in t2.groupby("cle")},
               "instituts": instituts_t2},
    }
    out = processed_dir / "sondages-2022.json"
    out.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"✓ {len(sortie['t1']['sondages'])} sondages de 1er tour, {len(sortie['t2']['sondages'])} de 2nd tour depuis {DEBUT}")
    print("  Précision des instituts (1er tour, dernier sondage publiable, erreur moyenne en points) :")
    for i in instituts:
        print(f"   {i['institut']:<20} {i['fin']}  {i['erreur_moyenne']:.2f} pt  (plus gros écart : {i['pire']['nom']} {i['pire']['ecart']:+.1f})")
    print(f"→ {out}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
