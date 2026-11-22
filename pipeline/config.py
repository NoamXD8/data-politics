"""Configuration du pipeline de données électorales."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Jeu de données « Données des élections agrégées » (data.gouv.fr)
# https://www.data.gouv.fr/datasets/donnees-des-elections-agregees
# Identifiants de ressources tirés du code source data.gouv :
# github.com/datagouv/datagouvfr_data_pipelines (data_processing/elections/aggregation)
SOURCES = {
    "general_results.parquet": "https://www.data.gouv.fr/api/1/datasets/r/ff16d511-10c0-405e-9b35-511723948fce",
    "candidats_results.parquet": "https://www.data.gouv.fr/api/1/datasets/r/4d3b35f6-0b22-4415-a24c-419a676312e2",
}

# Périmètre de la phase 1 : on garde les scrutins nationaux depuis 2012.
# id_election a la forme "2022_pres_t1" (année, type, tour).
TYPES_RETENUS = ["pres", "legi", "euro"]
ANNEE_MIN = 2012

LIBELLES_TYPES = {
    "pres": "Présidentielle",
    "legi": "Législatives",
    "euro": "Européennes",
    "muni": "Municipales",
    "regi": "Régionales",
    "dpmt": "Départementales",
    "cant": "Cantonales",
}

# Nombre maximum de candidats / listes / nuances affichés par scrutin.
# Les autres sont regroupés dans « Autres » (utile pour les européennes : 38 listes en 2024).
MAX_CANDIDATS = 10
# Un candidat est gardé s'il fait au moins ce score national (en % des exprimés)...
SEUIL_NATIONAL_PCT = 1.0
