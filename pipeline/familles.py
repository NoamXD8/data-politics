"""Rattachement des candidats, listes et nuances à des familles politiques.

Choix éditorial documenté sur la page Méthodologie du site. Les couleurs de chaque famille
sont définies côté site (site/src/components/familles.js) ; ici on ne fait que classer.

- Présidentielles : par nom de candidat.
- Européennes : par mots-clés dans le nom de la liste.
- Législatives : par code de nuance du Ministère de l'Intérieur (ils changent selon les années).

Tout libellé non reconnu tombe dans "div" (Divers et autres) et est signalé par le pipeline.
"""

import re
import unicodedata

# Codes de familles (même ordre que la palette validée, de gauche à droite)
FAMILLES = [
    "exg", "pcf", "lfi", "ug", "ps", "dvg",
    "eco", "ens", "mdm", "udi", "dvc",
    "lr", "dvd", "souv", "rn", "uxd", "rec",
    "reg", "div",
]

# Législatives : codes de nuance → famille (+ libellé lisible pour le grand public)
NUANCES = {
    "EXG": ("exg", "Extrême gauche"), "DXG": ("exg", "Extrême gauche"),
    "COM": ("pcf", "Parti communiste"),
    "FG": ("lfi", "Front de gauche"), "FI": ("lfi", "La France insoumise"),
    "NUP": ("ug", "NUPES"), "UG": ("ug", "Nouveau Front populaire"),
    "SOC": ("ps", "Parti socialiste"),
    "RDG": ("dvg", "Radicaux de gauche"), "DVG": ("dvg", "Divers gauche"),
    "VEC": ("eco", "Les Écologistes"), "ECO": ("eco", "Écologistes"),
    "REM": ("ens", "La République en marche"), "ENS": ("ens", "Ensemble"),
    "HOR": ("ens", "Horizons"),
    "MDM": ("mdm", "MoDem"), "CEN": ("mdm", "Le Centre pour la France"),
    "UDI": ("udi", "UDI"), "NCE": ("udi", "Nouveau Centre"), "ALLI": ("udi", "Alliance centriste"),
    "PRV": ("udi", "Parti radical"),
    "DVC": ("dvc", "Divers centre"),
    "UMP": ("lr", "UMP"), "LR": ("lr", "Les Républicains"),
    "DVD": ("dvd", "Divers droite"),
    "DLF": ("souv", "Debout la France"), "DSV": ("souv", "Divers souverainistes"),
    "FN": ("rn", "Front national"), "RN": ("rn", "Rassemblement national"),
    "UXD": ("uxd", "Alliés du RN (Ciotti)"),
    "REC": ("rec", "Reconquête"),
    "EXD": ("div", "Extrême droite (autres)"), "DXD": ("div", "Extrême droite (autres)"),
    "REG": ("reg", "Régionalistes"),
    "DIV": ("div", "Divers"), "AUT": ("div", "Autres"),
}

# Présidentielles : nom de famille → famille
CANDIDATS = {
    "MACRON": "ens", "LE PEN": "rn", "MELENCHON": "lfi", "ZEMMOUR": "rec",
    "PECRESSE": "lr", "FILLON": "lr", "SARKOZY": "lr",
    "JADOT": "eco", "JOLY": "eco",
    "HOLLANDE": "ps", "HAMON": "ps", "HIDALGO": "ps",
    "ROUSSEL": "pcf", "DUPONT-AIGNAN": "souv", "DUPONT AIGNAN": "souv",
    "ARTHAUD": "exg", "POUTOU": "exg", "BAYROU": "mdm",
    "LASSALLE": "div", "ASSELINEAU": "div", "CHEMINADE": "div",
}

# Européennes : mots-clés (testés dans l'ordre) → famille
LISTES = [
    (r"RECONQUETE", "rec"),
    (r"RASSEMBLEMENT NATIONAL|FRONT NATIONAL|BLEU MARINE|PRENEZ LE POUVOIR|LA FRANCE REVIENT|BARDELLA", "rn"),
    (r"INSOUMIS|FRONT DE GAUCHE", "lfi"),
    (r"COMMUNISTE|\bPCF\b|GAUCHE UNIE|EUROPE DES GENS", "pcf"),
    (r"LUTTE OUVRIERE|\bNPA\b|CAMP DES TRAVAILLEURS|MONDE DES TRAVAILLEURS", "exg"),
    (r"PARTI SOCIALISTE|\bPS\b|PLACE PUBLIQUE|REVEILLER L.?EUROPE|ENVIE D.?EUROPE|CHOISIR NOTRE EUROPE", "ps"),
    (r"ECOLOG|\bEELV\b|LES VERTS", "eco"),
    (r"RENAISSANCE|BESOIN D.?EUROPE|ENSEMBLE|EN MARCHE|\bLREM\b", "ens"),
    (r"\bUDI\b|MODEM|LES EUROPEENS", "udi"),
    (r"LES REPUBLICAINS|\bUMP\b|UNION POUR UN MOUVEMENT POPULAIRE|UNION DE LA DROITE|LA DROITE POUR", "lr"),
    (r"DEBOUT LA FRANCE|\bDLF\b", "souv"),
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip().upper()


def classer(type_election: str, label: str) -> tuple[str, str, bool]:
    """Renvoie (famille, libellé affiché, reconnu)."""
    if label == "Autres":
        return "div", "Autres", True
    n = _norm(label)
    if type_election == "legi":
        if n in NUANCES:
            fam, nom = NUANCES[n]
            return fam, f"{nom} ({n})", True
        return "div", label, False
    if type_election == "pres":
        for nom, fam in CANDIDATS.items():
            if nom in n:
                return fam, label, True
        return "div", label, False
    for motif, fam in LISTES:
        if re.search(motif, n):
            return fam, label, True
    return "div", label, False
