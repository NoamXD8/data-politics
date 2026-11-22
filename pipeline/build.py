"""Transforme les résultats par bureau de vote en fichiers JSON compacts pour le site.

Usage : python -m pipeline.build

Entrée  : data/raw/general_results.parquet, data/raw/candidats_results.parquet
Sorties : data/processed/
    elections.json          liste des scrutins retenus + candidats affichés
    departements.json       liste des départements (code, nom)
    france.json             résultats nationaux et par département
    communes.json           index de recherche [[code, nom, code_dep], ...]
    departements/XX.json    résultats par commune d'un département

Format compact des résultats : pour chaque territoire et chaque scrutin, une liste
[inscrits, votants, exprimes, blancs, nuls, voix_cand_1, ..., voix_cand_n, voix_autres]
dans l'ordre de elections[i].candidats.
"""

import json
import re
import sys
from collections import defaultdict

import duckdb

from pipeline.config import (
    ANNEE_MIN,
    LIBELLES_TYPES,
    MAX_CANDIDATS,
    PROCESSED_DIR,
    RAW_DIR,
    SEUIL_NATIONAL_PCT,
    TYPES_RETENUS,
)

RE_ELECTION = re.compile(r"^(\d{4})_([a-z]+)_t(\d)$")
AUTRES = "Autres"


def ecrire_json(chemin, obj) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def connexion(raw_dir=RAW_DIR) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    general = raw_dir / "general_results.parquet"
    candidats = raw_dir / "candidats_results.parquet"
    for f in (general, candidats):
        if not f.exists():
            sys.exit(f"Fichier manquant : {f}\nLance d'abord : python -m pipeline.download")

    # Codes normalisés : département sur 2 caractères, commune au format INSEE 5 caractères.
    # (Si code_commune fait déjà 5 caractères on le garde, sinon on le préfixe par le département.)
    norm = """
        CASE WHEN regexp_matches(code_departement, '^[0-9]$') THEN '0' || code_departement
             ELSE code_departement END AS dep,
        CASE WHEN length(code_commune) = 5 THEN code_commune
             ELSE (CASE WHEN regexp_matches(code_departement, '^[0-9]$') THEN '0' || code_departement
                        ELSE code_departement END) || lpad(code_commune, 3, '0') END AS com
    """
    con.execute(f"CREATE VIEW general AS SELECT *, {norm} FROM read_parquet('{general.as_posix()}')")
    con.execute(f"CREATE VIEW candidats AS SELECT *, {norm} FROM read_parquet('{candidats.as_posix()}')")
    return con


def lister_elections(con) -> list[dict]:
    ids = [r[0] for r in con.execute("SELECT DISTINCT id_election FROM general ORDER BY 1").fetchall()]
    print(f"{len(ids)} scrutins dans les données source :")
    print("  " + ", ".join(ids))
    elections = []
    for i in ids:
        m = RE_ELECTION.match(i or "")
        if not m:
            continue
        annee, typ, tour = int(m[1]), m[2], int(m[3])
        if typ in TYPES_RETENUS and annee >= ANNEE_MIN:
            elections.append({
                "id": i,
                "annee": annee,
                "type": typ,
                "tour": tour,
                "libelle": f"{LIBELLES_TYPES.get(typ, typ)} {annee} — {tour}{'er' if tour == 1 else 'nd'} tour",
            })
    if not elections:
        sys.exit(
            "Aucun scrutin ne correspond au périmètre (TYPES_RETENUS / ANNEE_MIN dans pipeline/config.py).\n"
            "Vérifie les codes de type dans la liste ci-dessus et adapte la config."
        )
    elections.sort(key=lambda e: (e["annee"], e["type"], e["tour"]))
    print(f"→ {len(elections)} scrutins retenus : {', '.join(e['id'] for e in elections)}")
    return elections


def creer_vues_resultats(con, ids: list[str]) -> None:
    liste = ", ".join(f"'{i}'" for i in ids)
    # Libellé affiché : pour les législatives on agrège par nuance (les candidats changent
    # dans chaque circonscription) ; sinon liste (européennes) ou « Prénom NOM » (présidentielle).
    con.execute(f"""
        CREATE TABLE cand AS
        SELECT id_election AS e, dep, com,
               CASE
                 WHEN split_part(id_election, '_', 2) = 'legi'
                   THEN coalesce(nullif(trim(nuance), ''), 'Sans nuance')
                 ELSE coalesce(
                   nullif(trim(libelle_abrege_liste), ''),
                   nullif(trim(liste), ''),
                   nullif(trim(concat_ws(' ', trim(prenom), upper(trim(nom)))), ''),
                   nullif(trim(nuance), ''),
                   'Inconnu')
               END AS label,
               coalesce(voix, 0) AS voix
        FROM candidats
        WHERE id_election IN ({liste})
    """)
    con.execute(f"""
        CREATE TABLE gen AS
        SELECT id_election AS e, dep, com,
               any_value(libelle_departement) AS nom_dep,
               any_value(libelle_commune) AS nom_com,
               sum(coalesce(inscrits, 0)) AS inscrits, sum(coalesce(votants, 0)) AS votants,
               sum(coalesce(exprimes, 0)) AS exprimes, sum(coalesce(blancs, 0)) AS blancs,
               sum(coalesce(nuls, 0)) AS nuls
        FROM general
        WHERE id_election IN ({liste})
        GROUP BY ALL
    """)


def choisir_candidats(con, elections: list[dict]) -> None:
    """Pour chaque scrutin, garde les principaux candidats nationaux ; le reste va dans « Autres »."""
    rows = con.execute("""
        SELECT e, label, sum(voix) AS voix FROM cand GROUP BY ALL ORDER BY e, voix DESC
    """).fetchall()
    exprimes = dict(con.execute("SELECT e, sum(exprimes) FROM gen GROUP BY e").fetchall())
    par_election = defaultdict(list)
    for e, label, voix in rows:
        par_election[e].append((label, voix))
    for el in elections:
        total = exprimes.get(el["id"]) or 1
        gardes = [
            label for label, voix in par_election[el["id"]]
            if 100 * voix / total >= SEUIL_NATIONAL_PCT
        ][:MAX_CANDIDATS]
        el["candidats"] = gardes + [AUTRES]


def vecteurs(rows_gen, rows_cand, elections, cle) -> dict:
    """Construit {territoire: {election: [inscrits, votants, exprimes, blancs, nuls, voix...]}}."""
    index = {el["id"]: {c: i for i, c in enumerate(el["candidats"])} for el in elections}
    out = defaultdict(dict)
    for r in rows_gen:
        e, t = r["e"], r[cle]
        n = len(index[e])
        out[t][e] = [r["inscrits"], r["votants"], r["exprimes"], r["blancs"], r["nuls"]] + [0] * n
    for r in rows_cand:
        e, t = r["e"], r[cle]
        if e not in out.get(t, {}):
            continue  # résultats candidats sans ligne générale : on ignore
        pos = index[e].get(r["label"], index[e][AUTRES])
        out[t][e][5 + pos] += int(r["voix"])
    return out


def fetch_dicts(con, sql):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main(raw_dir=RAW_DIR, out_dir=PROCESSED_DIR) -> None:
    con = connexion(raw_dir)
    elections = lister_elections(con)
    creer_vues_resultats(con, [e["id"] for e in elections])
    choisir_candidats(con, elections)
    ecrire_json(out_dir / "elections.json", elections)

    # Noms : on prend le libellé le plus récent disponible.
    noms_dep = dict(con.execute("""
        SELECT dep, arg_max(nom_dep, e) FROM gen WHERE nom_dep IS NOT NULL GROUP BY dep
    """).fetchall())
    noms_com = con.execute("""
        SELECT com, arg_max(nom_com, e), any_value(dep) FROM gen WHERE nom_com IS NOT NULL GROUP BY com ORDER BY com
    """).fetchall()
    departements = [{"code": d, "nom": noms_dep.get(d) or d} for d in sorted(noms_dep)]
    ecrire_json(out_dir / "departements.json", departements)
    ecrire_json(out_dir / "communes.json", [[c, n, d] for c, n, d in noms_com])

    # Niveau national et départemental
    gen_dep = fetch_dicts(con, """
        SELECT e, dep, sum(inscrits) inscrits, sum(votants) votants, sum(exprimes) exprimes,
               sum(blancs) blancs, sum(nuls) nuls FROM gen GROUP BY ALL
    """)
    cand_dep = fetch_dicts(con, "SELECT e, dep, label, sum(voix) voix FROM cand GROUP BY ALL")
    par_dep = vecteurs(gen_dep, cand_dep, elections, "dep")
    gen_fr = fetch_dicts(con, """
        SELECT e, 'FR' AS t, sum(inscrits) inscrits, sum(votants) votants, sum(exprimes) exprimes,
               sum(blancs) blancs, sum(nuls) nuls FROM gen GROUP BY ALL
    """)
    cand_fr = fetch_dicts(con, "SELECT e, 'FR' AS t, label, sum(voix) voix FROM cand GROUP BY ALL")
    national = vecteurs(gen_fr, cand_fr, elections, "t")["FR"]
    ecrire_json(out_dir / "france.json", {"france": national, "departements": par_dep})

    # Un fichier par département avec ses communes
    gen_com = fetch_dicts(con, "SELECT e, dep, com, inscrits, votants, exprimes, blancs, nuls FROM gen")
    cand_com = fetch_dicts(con, "SELECT e, dep, com, label, sum(voix) voix FROM cand GROUP BY ALL")
    gen_par_dep, cand_par_dep = defaultdict(list), defaultdict(list)
    for r in gen_com:
        gen_par_dep[r["dep"]].append(r)
    for r in cand_com:
        cand_par_dep[r["dep"]].append(r)
    noms_com_dict = {c: n for c, n, _ in noms_com}
    for d in departements:
        code = d["code"]
        communes = vecteurs(gen_par_dep[code], cand_par_dep[code], elections, "com")
        ecrire_json(out_dir / "departements" / f"{code}.json", {
            "code": code,
            "nom": d["nom"],
            "total": par_dep.get(code, {}),
            "communes": {c: {"nom": noms_com_dict.get(c, c), "r": r} for c, r in sorted(communes.items())},
        })

    # Petit rapport de contrôle
    print(f"✓ {len(departements)} départements, {len(noms_com)} communes")
    print(f"  Exemples de codes commune : {[c for c, _, _ in noms_com[:5]]}")
    for el in elections:
        v = national.get(el["id"])
        if v:
            print(f"  {el['id']}: inscrits={v[0]:,} participation={100 * v[1] / max(v[0], 1):.1f}% "
                  f"| {len(el['candidats']) - 1} candidats affichés")
    print(f"→ fichiers écrits dans {out_dir}")


if __name__ == "__main__":
    main()
