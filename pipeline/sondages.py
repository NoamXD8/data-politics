"""Sondages des présidentielles : évolution, écart avec les résultats, précision des instituts.

Usage : python -m pipeline.sondages   (après python -m pipeline.build ; --force pour retélécharger)

Sources (téléchargées dans data/raw) :
- 2022 : NSPPolls (https://github.com/nsppolls/nsppolls), licence MIT, 1er et 2nd tours.
- 2017 : Léopold Mebazaa (https://github.com/lemeb/presidentielle), licence MIT, pour le 1er tour ;
  Wikipédia pour le 2nd tour.
- 2012 : Wikipédia, 1er et 2nd tours.
  Les tableaux Wikipédia (CC BY-SA 4.0) sont extraits une fois pour toutes dans data/sondages/*.csv
  (versionnés) : la mise en page de Wikipédia change trop souvent pour un téléchargement automatique.
- 2027 : « 2027 et moi » (https://github.com/2027etmoi/2027etmoi), Licence Ouverte 2.0, 1er tour,
  chaque sondage vérifié sur sa notice à la Commission des sondages.
Les résultats officiels viennent de data/processed (pipeline.build).

Sortie : data/processed/sondages.json  ({"annees": [...], "2027": {...}, "2022": {...}, "2017": {...}})
"""

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from pipeline.config import PROCESSED_DIR, RAW_DIR

URL = "https://raw.githubusercontent.com/nsppolls/nsppolls/master/presidentielle.csv"
FICHIER = RAW_DIR / "nsppolls-presidentielle.csv"
URL_2017 = "https://raw.githubusercontent.com/lemeb/presidentielle/master/data/sondages_17.csv"
FICHIER_2017 = RAW_DIR / "sondages-2017-lemeb.csv"
URL_2027 = "https://raw.githubusercontent.com/2027etmoi/2027etmoi/main/data/"
DOSSIER_2027 = RAW_DIR / "2027etmoi"
WIKI = Path(__file__).resolve().parent.parent / "data" / "sondages"
WIKI_URL = "https://fr.wikipedia.org/wiki/Liste_de_sondages_sur_l%27%C3%A9lection_pr%C3%A9sidentielle_fran%C3%A7aise_de_{}"
INSTITUTS = {"Ispos": "Ipsos", "Cevipof Ipsos-Sopra Steria": "Cevipof Ipsos Sopra Steria",
             "Kantar Sofres - OnePoint": "Kantar Sofres-OnePoint"}  # coquilles et graphies variables de la source
DEBUT = "2021-09-01"  # un scénario par sondage : celui des candidats réellement présents
# Interdiction de publication la veille et le jour du vote : derniers sondages publiables
DERNIER_T1, DERNIER_T2 = "2022-04-08", "2022-04-22"


def cle(nom: str) -> str:
    """« Éric ZEMMOUR » et « Eric Zemmour » → « eric-zemmour »."""
    s = unicodedata.normalize("NFD", nom)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def telecharger_fichier(url, fichier, force=False):
    if force or not fichier.exists():
        print(f"↓ {url}")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_bytes(r.content)
    return fichier


def telecharger(force=False) -> pd.DataFrame:
    return pd.read_csv(telecharger_fichier(URL, FICHIER, force))


def resultats(processed_dir, election_id) -> dict:
    """Résultats officiels (% des exprimés) par candidat, depuis la sortie de pipeline.build."""
    elections = json.loads((processed_dir / "elections.json").read_text(encoding="utf-8"))
    france = json.loads((processed_dir / "france.json").read_text(encoding="utf-8"))["france"]
    el = next((e for e in elections if e["id"] == election_id), None)
    if el is None or election_id not in france:
        raise LookupError(f"{election_id} absent des données : lance d'abord python -m pipeline.build")
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




def sondages(d: pd.DataFrame) -> list:
    """Un objet par sondage : institut, fin du terrain, échantillon, scores par candidat."""
    return [{"id": str(sid), "institut": g["nom_institut"].iloc[0], "fin": g["fin_enquete"].iloc[0],
             "echantillon": int(g["echantillon"].fillna(0).iloc[0]), "rolling": bool(g["rolling"].iloc[0]),
             "scores": {r.cle: round(float(r.intentions), 2) for r in g.itertuples()}}
            for sid, g in d.sort_values("fin_enquete").groupby("id", sort=False)]


def tour_avec_resultats(d: pd.DataFrame, res: dict, dernier: str, vote: str, h: float = 8.0, finale: bool = True,
                        classement_depuis: str | None = None) -> dict:
    """Bloc d'un tour déjà joué : sondages, tendances, précision des instituts, moyenne finale.

    classement_depuis : pour le 2nd tour, seuls les instituts ayant sondé après le 1er tour sont classés
    (un duel testé des semaines avant ne se compare pas au résultat)."""
    recents = d if classement_depuis is None else d[d["fin_enquete"] >= classement_depuis]
    dernier_id = recents.sort_values("fin_enquete").groupby("nom_institut")["id"].last()
    derniers = d[d["id"].isin(dernier_id)]
    bloc = {"candidats": res, "sondages": sondages(d), "dernier_jour": dernier, "vote": vote,
            "tendances": {k: tendance(g, dernier, h) for k, g in d.groupby("cle")},
            "instituts": precision(derniers, res)}
    if finale:
        bloc["moyenne_finale"] = {k: round(v, 2) for k, v in derniers.groupby("cle")["intentions"].mean().items()}
    return bloc


# ---------------------------------------------------------------- 2022 (NSPPolls)

def annee_2022(processed_dir, force=False) -> dict:
    df = telecharger(force)
    df["cle"] = df["candidat"].map(cle)
    res1, res2 = resultats(processed_dir, "2022_pres_t1"), resultats(processed_dir, "2022_pres_t2")

    # 1er tour : un scénario par sondage, candidats du 1er tour seulement
    t1 = df[(df["tour"] == "Premier tour") & (df["fin_enquete"] >= DEBUT) & (df["fin_enquete"] <= DERNIER_T1)]
    t1 = un_scenario_par_sondage(t1, set(res1))
    t1 = t1[t1["cle"].isin(res1)]

    # 2nd tour : duel des deux finalistes
    t2 = df[(df["tour"] == "Deuxième tour") & (df["fin_enquete"] >= DEBUT) & (df["fin_enquete"] <= DERNIER_T2)]
    t2 = t2[t2.groupby("id")["cle"].transform(lambda s: set(s) == set(res2))]

    return {
        "annee": 2022, "statut": "termine",
        "source": {"nom": "NSPPolls", "url": "https://github.com/nsppolls/nsppolls", "licence": "MIT",
                   "reference": "https://fr.wikipedia.org/wiki/Liste_de_sondages_sur_l%27%C3%A9lection_pr%C3%A9sidentielle_fran%C3%A7aise_de_2022"},
        "methode": "Pour un même sondage testant plusieurs hypothèses de candidatures, on garde celle qui correspond aux candidats réellement présents.",
        "t1": tour_avec_resultats(t1, res1, DERNIER_T1, "2022-04-10"),
        "t2": {**tour_avec_resultats(t2, res2, DERNIER_T2, "2022-04-24", finale=False, classement_depuis="2022-04-10"), "debut_graphique": "2022-02-01"},
    }


# ---------------------------------------------------------------- Tableaux extraits de Wikipédia

def wikipedia(nom_fichier: str, res: dict, dernier: str) -> pd.DataFrame:
    """CSV large (fin;institut;echantillon;candidat…) → format long, une ligne par sondage et candidat."""
    large = pd.read_csv(WIKI / nom_fichier, sep=";").drop_duplicates().reset_index(drop=True)
    large["id"] = large["institut"] + " " + large["fin"] + " #" + large.index.astype(str)
    long = large.melt(id_vars=["id", "fin", "institut", "echantillon"], var_name="candidat", value_name="intentions").dropna(subset=["intentions"])
    long["cle"] = long["candidat"].map(cle)
    inconnus = set(long["cle"]) - set(res)
    if inconnus:
        raise LookupError(f"{nom_fichier} : candidats absents des résultats officiels {sorted(inconnus)}")
    long = long.rename(columns={"institut": "nom_institut", "fin": "fin_enquete"})
    long["nom_institut"] = long["nom_institut"].replace(INSTITUTS)
    long["echantillon"] = long["echantillon"].fillna(0)
    long["rolling"] = False
    return long[long["fin_enquete"] <= dernier]


def source_wikipedia(annee) -> dict:
    return {"nom": "Wikipédia", "url": WIKI_URL.format(annee), "licence": "CC BY-SA 4.0"}


# ---------------------------------------------------------------- 2012 (Wikipédia)

def annee_2012(processed_dir) -> dict:
    res1, res2 = resultats(processed_dir, "2012_pres_t1"), resultats(processed_dir, "2012_pres_t2")
    t1 = wikipedia("wikipedia-2012-t1.csv", res1, "2012-04-20")
    t2 = wikipedia("wikipedia-2012-t2.csv", res2, "2012-05-04")
    return {
        "annee": 2012, "statut": "termine", "source": source_wikipedia(2012),
        "methode": "Sondages de janvier 2012 au 1er tour, et d'intentions de vote en duel Hollande–Sarkozy depuis janvier 2011. La taille des échantillons n'est pas indiquée par la source. « < 0,5 % » est compté 0,25 %.",
        "t1": tour_avec_resultats(t1, res1, "2012-04-20", "2012-04-22"),
        "t2": {**tour_avec_resultats(t2, res2, "2012-05-04", "2012-05-06", h=10, finale=False, classement_depuis="2012-04-22"), "debut_graphique": "2012-01-01"},
    }


# ---------------------------------------------------------------- 2017 (lemeb/presidentielle + Wikipédia)

COLONNES_2017 = {"Arthaud": "arthaud", "Poutou": "poutou", "Melenchon": "melenchon", "Hamon": "hamon", "Macron": "macron",
                 "Fillon": "fillon", "DupontAignan": "dupont-aignan", "Asselineau": "asselineau", "LePen": "le-pen",
                 "Cheminade": "cheminade", "Lassalle": "lassalle"}  # Jadot et Bayrou se sont retirés avant le vote


def annee_2017(processed_dir, force=False) -> dict:
    brut = pd.read_csv(telecharger_fichier(URL_2017, FICHIER_2017, force)).drop_duplicates()
    res1 = resultats(processed_dir, "2017_pres_t1")
    # Colonne « LePen » → clé officielle « marine-le-pen »
    vers_cle = {col: next((k for k in res1 if k == nom or k.endswith("-" + nom)), None) for col, nom in COLONNES_2017.items()}
    vers_cle = {c: k for c, k in vers_cle.items() if k}
    brut["id"] = brut["Institut"] + " " + brut["DateFin"]
    long = brut.melt(id_vars=["id", "Institut", "DateFin", "N"], value_vars=list(vers_cle), var_name="col", value_name="intentions").dropna()
    # Un même sondage peut apparaître en plusieurs hypothèses : moyenne par candidat
    long = long.groupby(["id", "Institut", "DateFin", "col"], as_index=False).agg(intentions=("intentions", "mean"), N=("N", "max"))
    long = long.rename(columns={"Institut": "nom_institut", "DateFin": "fin_enquete", "N": "echantillon"})
    long["cle"] = long["col"].map(vers_cle)
    long["rolling"] = False
    long = long[long["fin_enquete"] <= "2017-04-21"]
    res2 = resultats(processed_dir, "2017_pres_t2")
    t2 = wikipedia("wikipedia-2017-t2.csv", res2, "2017-05-05")
    return {
        "annee": 2017, "statut": "termine",
        "source": {"nom": "Léopold Mebazaa", "url": "https://github.com/lemeb/presidentielle", "licence": "MIT",
                   "reference": "https://fr.wikipedia.org/wiki/Liste_de_sondages_sur_l%27%C3%A9lection_pr%C3%A9sidentielle_fran%C3%A7aise_de_2017"},
        "methode": "1er tour : sondages publiés de décembre 2016 au vote ; quand un même sondage figure plusieurs fois, on fait la moyenne. 2nd tour : duels Macron–Le Pen relevés sur Wikipédia, avant et après le 1er tour.",
        "source_t2": source_wikipedia(2017),
        "t1": tour_avec_resultats(long, res1, "2017-04-21", "2017-04-23", h=10),
        "t2": {**tour_avec_resultats(t2, res2, "2017-05-05", "2017-05-07", h=10, finale=False, classement_depuis="2017-04-23"), "debut_graphique": "2017-02-01"},
    }


# ---------------------------------------------------------------- 2027 (2027 et moi)

# Personnalités testées dans les sondages mais absentes de notre liste de candidats 2027
HORS_LISTE_2027 = {"hollande": ("François Hollande", "ps"), "faure": ("Olivier Faure", "ps"), "guedj": ("Jérôme Guedj", "ps"),
                   "royal": ("Ségolène Royal", "ps"), "maurel": ("Emmanuel Maurel", "dvg"), "ruffin": ("François Ruffin", "dvg"),
                   "le-maire": ("Bruno Le Maire", "ens"), "lagarde": ("Christine Lagarde", "ens"), "bonnal": ("Sébastien Bonnal", "div")}
LISTE_2027 = Path(__file__).resolve().parent.parent / "site" / "src" / "data" / "candidats-2027.json"


def nom_majuscules(nom: str) -> str:
    """« Marine Le Pen » → « Marine LE PEN » (même écriture que les résultats officiels)."""
    prenom, _, reste = nom.partition(" ")
    particule = ""
    for p in ("de ", "d'"):
        if reste.startswith(p):
            particule, reste = p, reste[len(p):]
    return f"{prenom} {particule}{reste.upper()}"


def annee_2027(force=False) -> dict:
    brut = json.loads(telecharger_fichier(URL_2027 + "sondages.json", DOSSIER_2027 / "sondages.json", force).read_text(encoding="utf-8"))
    fiches = json.loads(telecharger_fichier(URL_2027 + "candidats.json", DOSSIER_2027 / "candidats.json", force).read_text(encoding="utf-8"))
    noms = {c["id"]: c["nom"] for c in fiches["candidats"]} | {k: v for k, v in brut.get("noms_hors_liste", {}).items()}
    familles = {cle(c["nom"]): c["famille"] for c in json.loads(LISTE_2027.read_text(encoding="utf-8"))["candidats"]}

    lignes = []
    for i, p in enumerate(brut["sondages"]):
        # Plusieurs hypothèses de candidatures par sondage : moyenne de chaque personnalité sur celles où elle figure
        scores = pd.DataFrame([h["scores"] for h in p["hypotheses"]]).mean()
        for k, v in scores.items():
            lignes.append({"id": f"{p['institut']} {p['terrain_fin']} {i}", "nom_institut": p["institut"], "fin_enquete": p["terrain_fin"],
                           "echantillon": p.get("echantillon") or 1000, "rolling": False, "cle": k, "intentions": float(v),
                           "source": p["source"]["url"]})
    d = pd.DataFrame(lignes)
    candidats = {}
    for k in d["cle"].unique():
        nom = noms.get(k) or HORS_LISTE_2027.get(k, (k.title(), "div"))[0]
        famille = familles.get(cle(nom)) or HORS_LISTE_2027.get(k, (None, "div"))[1]
        candidats[k] = {"nom": nom_majuscules(nom), "famille": famille, "pct": None, "nb_sondages": int((d["cle"] == k).sum())}
    fin = d["fin_enquete"].max()
    blocs = sondages(d)
    sources = d.drop_duplicates("id").set_index("id")["source"].to_dict()
    for b in blocs:
        b["source"] = sources[b["id"]]
    return {
        "annee": 2027, "statut": "en_cours",
        "source": {"nom": "2027 et moi", "url": "https://github.com/2027etmoi/2027etmoi", "licence": "Licence Ouverte 2.0",
                   "mise_a_jour": brut.get("mise_a_jour")},
        "methode": "Chaque sondage teste plusieurs hypothèses de candidatures : on prend la moyenne de chaque personnalité sur les hypothèses où elle figure.",
        "t1": {"candidats": candidats, "sondages": blocs, "dernier_jour": fin, "vote": "2027-04-18",
               "tendances": {k: tendance(g, fin, 14.0) for k, g in d.groupby("cle") if len(g) >= 3},
               "instituts": []},
    }


def main(processed_dir=PROCESSED_DIR, force=False) -> None:
    sortie = {"annees": [], "genere_le": date.today().isoformat()}
    for annee, fabrique in (("2027", lambda: annee_2027(force)), ("2022", lambda: annee_2022(processed_dir, force)),
                            ("2017", lambda: annee_2017(processed_dir, force)), ("2012", lambda: annee_2012(processed_dir))):
        try:
            bloc = fabrique()
        except (LookupError, requests.RequestException, FileNotFoundError) as e:
            print(f"✗ {annee} ignorée : {e}")
            continue
        sortie[annee] = bloc
        sortie["annees"].append(annee)
        t1, t2 = bloc["t1"], bloc.get("t2")
        print(f"✓ {annee} : {len(t1['sondages'])} sondages de 1er tour" + (f", {len(t2['sondages'])} de 2nd tour" if t2 else ""))
        for i in t1["instituts"][:3]:
            print(f"   {i['institut']:<22} {i['fin']}  erreur moyenne {i['erreur_moyenne']:.2f} pt")
    out = processed_dir / "sondages.json"
    out.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    ancien = processed_dir / "sondages-2022.json"
    if ancien.exists():
        ancien.unlink()
    print(f"→ {out}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
