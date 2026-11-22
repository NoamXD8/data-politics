"""Vote et sociologie : scores des candidats selon le profil des communes (données INSEE).

Usage :
  python -m pipeline.sociologie   (après python -m pipeline.build)
  Le fichier INSEE (comparateur.parquet) est téléchargé automatiquement dans data/raw/insee/.
  En cas d'échec, le télécharger sur https://www.insee.fr/fr/statistiques/2521169 et le placer
  dans ce dossier (parquet, csv ou zip tel quel).

Le lecteur accepte l'ancien format « large » (une colonne par indicateur : P21_POP, MED21…)
et le format « long » (une ligne par indicateur et par territoire). Il retrouve les indicateurs
d'après leurs codes INSEE ; s'il n'y arrive pas, il affiche les codes disponibles.

Méthode : on range les communes en 10 tranches selon un indicateur (revenu médian, par exemple),
chaque tranche regroupant environ 10 % des inscrits, puis on calcule le score de chaque candidat
dans chaque tranche (voix / exprimés). Ce sont des comparaisons entre territoires : une commune
aisée qui vote davantage pour X ne signifie pas que les électeurs aisés votent X.

Sortie : data/processed/sociologie.json
"""

import json
import re
import sys
import zipfile
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from pipeline.config import PROCESSED_DIR, RAW_DIR

DOSSIER_INSEE = RAW_DIR / "insee"
URL_INSEE = "https://www.insee.fr/fr/statistiques/fichier/2521169/comparateur.parquet"
ELECTIONS = ["2022_pres_t1", "2022_pres_t2", "2017_pres_t1", "2017_pres_t2"]

# Indicateur → motifs des codes INSEE : ancien format (P21_POP, MED21…) puis nouveau format (juillet 2026)
CODES = {
    "pop": [r"^P\d{2}_POP$", r"^POP$"],
    "superf": [r"^SUPERF$", r"^SUP$"],
    "med": [r"^MED\d{2}$", r"^MED_SL$"],
    "tp60": [r"^TP60\d{2}$", r"^PR_MD60$"],
    "chom": [r"^P\d{2}_CHOM1564$"],
    "act": [r"^P\d{2}_ACT1564$"],
    "log": [r"^P\d{2}_LOG$", r"^DWELLINGS$"],
    "rsec": [r"^P\d{2}_RSECOCC$", r"^DWELLINGS_OCS_DW_SEC_DW_OCC$"],
    "vac": [r"^P\d{2}_LOGVAC$", r"^DWELLINGS_OCS_DW_VAC$"],
    "rp": [r"^P\d{2}_RP$", r"^DWELLINGS_OCS_DW_MAIN$"],
    "proprio": [r"^P\d{2}_RP_PROP$", r"^DWELLINGS_OCS_DW_MAIN_TSH_100$"],
}
TOUS_LES_MOTIFS = [m for motifs in CODES.values() for m in motifs]
INDICATEURS = {
    "med": {"libelle": "Niveau de vie médian", "unite": "€ par an et par unité de consommation", "format": "euros"},
    "tp60": {"libelle": "Taux de pauvreté", "unite": "% de la population", "format": "pct100"},
    "chom": {"libelle": "Taux de chômage", "unite": "% des actifs de 15 à 64 ans", "format": "pct"},
    "densite": {"libelle": "Densité de population", "unite": "habitants par km²", "format": "nombre"},
    "pop": {"libelle": "Taille de la commune", "unite": "habitants", "format": "nombre"},
    "rsec": {"libelle": "Résidences secondaires", "unite": "% des logements", "format": "pct"},
    "proprio": {"libelle": "Part de propriétaires", "unite": "% des résidences principales", "format": "pct"},
    "vac": {"libelle": "Logements vacants", "unite": "% des logements", "format": "pct"},
}


def trouver_fichier() -> Path:
    fichiers = sorted([*DOSSIER_INSEE.glob("*.parquet"), *DOSSIER_INSEE.glob("*.csv"), *DOSSIER_INSEE.glob("*.zip")])
    if not fichiers:
        try:
            import requests
            print("↓ base du comparateur de territoires (INSEE) …")
            r = requests.get(URL_INSEE, timeout=120)
            r.raise_for_status()
            DOSSIER_INSEE.mkdir(parents=True, exist_ok=True)
            (DOSSIER_INSEE / "comparateur.parquet").write_bytes(r.content)
            return DOSSIER_INSEE / "comparateur.parquet"
        except Exception as e:  # pas de réseau, adresse changée…
            print(f"⚠ téléchargement impossible ({e})")
        sys.exit(f"Aucun fichier INSEE dans {DOSSIER_INSEE}.\n"
                 "Télécharge la « Base du comparateur de territoires » sur https://www.insee.fr/fr/statistiques/2521169 "
                 "et place le fichier (parquet, csv ou zip) dans ce dossier.")
    f = fichiers[0]
    if f.suffix == ".zip":
        with zipfile.ZipFile(f) as z:
            membres = [m for m in z.namelist() if m.lower().endswith((".csv", ".parquet")) and "meta" not in m.lower()]
            if not membres:
                sys.exit(f"Le zip {f.name} ne contient ni CSV ni Parquet.")
            cible = DOSSIER_INSEE / Path(membres[0]).name
            if not cible.exists():
                with z.open(membres[0]) as src, open(cible, "wb") as dst:
                    dst.write(src.read())
            return cible
    return f


def lire(f: Path) -> pd.DataFrame:
    con = duckdb.connect()
    if f.suffix == ".parquet":
        return con.execute(f"SELECT * FROM read_parquet('{f.as_posix()}')").df()
    return con.execute(f"SELECT * FROM read_csv('{f.as_posix()}', all_varchar=true, header=true)").df()


def nombre(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False).str.replace(" ", "", regex=False), errors="coerce")


def en_format_large(df: pd.DataFrame) -> pd.DataFrame:
    """Renvoie un tableau commune × codes d'indicateurs, quel que soit le format d'origine."""
    cols = {c.upper(): c for c in df.columns}
    # Format long : une colonne de valeurs + une colonne de codes d'indicateurs
    valeur = next((cols[c] for c in ("OBS_VALUE", "VALEUR", "VALUE") if c in cols), None)
    if valeur:
        if "GEO_OBJECT" in cols:
            df = df[df[cols["GEO_OBJECT"]].astype(str).str.upper().isin(["COM", "COMMUNE"])]
        geo = next(cols[c] for c in ("GEO", "CODGEO", "CODE_GEO", "COM") if c in cols)
        candidates = [c for c in df.columns if c not in (valeur, geo) and not pd.api.types.is_numeric_dtype(df[c])]
        def score(c):
            vals = df[c].dropna().astype(str).unique()[:5000]
            return sum(any(re.match(m, v.upper()) for m in TOUS_LES_MOTIFS) for v in vals)
        code = max(candidates, key=score)
        if score(code) == 0:
            raise ValueError("codes d'indicateurs introuvables", candidates)
        # S'il y a plusieurs millésimes, on garde le plus récent pour chaque indicateur
        if "TIME_PERIOD" in cols:
            df = df.sort_values(cols["TIME_PERIOD"]).drop_duplicates([geo, code], keep="last")
        large = df.pivot_table(index=geo, columns=code, values=valeur, aggfunc="first")
        large.columns = [str(c).upper() for c in large.columns]
        large.index = large.index.astype(str)
        return large.apply(nombre)
    geo = next(cols[c] for c in ("CODGEO", "GEO", "CODE_GEO", "COM") if c in cols)
    large = df.set_index(geo)
    large.index = large.index.astype(str)
    large.columns = [str(c).upper() for c in large.columns]
    return large.apply(nombre)


def indicateurs(large: pd.DataFrame) -> pd.DataFrame:
    choisis = {}
    for nom, motifs in CODES.items():
        trouves = sorted(c for c in large.columns if any(re.match(m, c) for m in motifs))
        if trouves:
            choisis[nom] = trouves[-1]  # millésime le plus récent
    manquants = [n for n in ("pop", "med") if n not in choisis]
    if manquants:
        exemples = ", ".join(sorted(large.columns)[:80])
        sys.exit(f"Indicateurs INSEE introuvables ({', '.join(manquants)}). Codes disponibles : {exemples}\n"
                 "Copie ce message pour adapter pipeline/sociologie.py (dictionnaire CODES).")
    print("  Indicateurs INSEE utilisés : " + ", ".join(f"{k}={v}" for k, v in choisis.items()))
    out = pd.DataFrame({k: large[v] for k, v in choisis.items()})
    if "superf" in out:
        out["densite"] = out["pop"] / out["superf"].where(out["superf"] > 0)
    if {"chom", "act"} <= set(out):
        out["chom"] = 100 * out["chom"] / out["act"].where(out["act"] > 0)
    if {"rsec", "log"} <= set(out):
        out["rsec"] = 100 * out["rsec"] / out["log"].where(out["log"] > 0)
    if {"vac", "log"} <= set(out):
        out["vac"] = 100 * out["vac"] / out["log"].where(out["log"] > 0)
    if {"proprio", "rp"} <= set(out):
        out["proprio"] = 100 * out["proprio"] / out["rp"].where(out["rp"] > 0)
    if "act" not in out:
        out = out.drop(columns=["chom"], errors="ignore")
    return out[[k for k in INDICATEURS if k in out]]


def communes_resultats(processed_dir: Path, election: dict) -> pd.DataFrame:
    lignes = []
    for f in sorted((processed_dir / "departements").glob("*.json")):
        for code, c in json.loads(f.read_text(encoding="utf-8"))["communes"].items():
            v = c["r"].get(election["id"])
            if v and v[2] > 0:
                lignes.append([code, *v])
    noms = election.get("noms", election["candidats"])
    return pd.DataFrame(lignes, columns=["code", "inscrits", "votants", "exprimes", "blancs", "nuls", *noms]).set_index("code")


def tranches(x: pd.Series, poids: pd.Series, n=10) -> pd.Series:
    """Tranches regroupant chacune environ 1/n des inscrits."""
    ordre = x.sort_values()
    cumul = poids.loc[ordre.index].cumsum() / poids.sum()
    return pd.Series(np.minimum((cumul * n).apply(np.ceil).astype(int), n), index=ordre.index).reindex(x.index)


def main(processed_dir=PROCESSED_DIR) -> None:
    f = trouver_fichier()
    print(f"Lecture de {f.name} …")
    insee = indicateurs(en_format_large(lire(f)))
    elections = {e["id"]: e for e in json.loads((processed_dir / "elections.json").read_text(encoding="utf-8"))}
    sortie = {"indicateurs": {k: v for k, v in INDICATEURS.items() if k in insee}, "elections": {}}
    for eid in [e for e in ELECTIONS if e in elections]:
        el = elections[eid]
        res = communes_resultats(processed_dir, el).join(insee, how="inner")
        noms = [n for n in el.get("noms", el["candidats"]) if n != "Autres"]
        fam = dict(zip(el.get("noms", el["candidats"]), el["familles"]))
        bloc = {"libelle": el["libelle"], "candidats": [{"nom": n, "famille": fam[n]} for n in noms],
                "communes": int(len(res)), "indicateurs": {}}
        for ind in sortie["indicateurs"]:
            d = res.dropna(subset=[ind])
            d = d[d["inscrits"] > 0]
            t = tranches(d[ind], d["inscrits"])
            g = d.groupby(t)
            somme = g[["inscrits", "votants", "exprimes", *noms]].sum()
            bloc["indicateurs"][ind] = [{
                "tranche": int(k),
                "min": float(g[ind].min()[k]), "max": float(g[ind].max()[k]),
                "mediane": float(d.loc[t == k, ind].median()),
                "communes": int(g.size()[k]),
                "participation": round(float(somme.loc[k, "votants"] / somme.loc[k, "inscrits"]), 4),
                "scores": {n: round(float(somme.loc[k, n] / somme.loc[k, "exprimes"]), 4) for n in noms},
            } for k in somme.index]
            # Corrélation pondérée commune par commune, pour signaler les liens les plus nets
            bloc.setdefault("correlations", {})[ind] = {
                n: round(float(pd.Series(d[n] / d["exprimes"]).corr(d[ind] if ind not in ("pop", "densite") else np.log10(d[ind].clip(lower=1)))), 3)
                for n in noms}
        sortie["elections"][eid] = bloc
        print(f"✓ {eid} : {bloc['communes']} communes croisées avec l'INSEE")
    out = processed_dir / "sociologie.json"
    out.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"→ {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else PROCESSED_DIR)
