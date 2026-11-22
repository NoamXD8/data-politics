"""Data loader : transforme les photos renseignées dans candidats-2027.json en images prêtes à afficher.

Champ "photo" d'une fiche, au choix :
  - lien d'une page Wikimedia Commons : https://commons.wikimedia.org/wiki/File:Nom.jpg
  - ou simplement le nom du fichier :   File:Nom.jpg
  - ou l'adresse directe d'une image (renseigner alors "credit" soi-même)

Pour Commons, on récupère via l'API publique une vignette de 240 px, l'auteur et la licence,
pour afficher le crédit exigé par la licence. Sans connexion, la fiche garde ses initiales.
"""

import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ICI = Path(__file__).parent
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "DataPolitics/0.1 (site electoral etudiant; https://github.com/NoamXD8/data-politics)"}


def titre_commons(photo: str) -> str | None:
    photo = photo.strip()
    if photo.startswith("File:") or photo.startswith("Fichier:"):
        return "File:" + photo.split(":", 1)[1]
    m = re.match(r"https?://commons\.(?:m\.)?wikimedia\.org/wiki/(?:File|Fichier):(.+)", photo)
    return "File:" + urllib.parse.unquote(m[1]).replace("_", " ") if m else None


def texte(valeur: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", valeur or ""))).strip()


def infos_commons(titre: str) -> dict | None:
    params = {"action": "query", "titles": titre, "prop": "imageinfo", "iiprop": "url|extmetadata",
              "iiurlwidth": "240", "format": "json", "formatversion": "2"}
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}", headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        page = json.load(r)["query"]["pages"][0]
    if "imageinfo" not in page:
        return None
    info = page["imageinfo"][0]
    meta = info.get("extmetadata", {})
    auteur = texte(meta.get("Artist", {}).get("value", "")) or "auteur inconnu"
    licence = texte(meta.get("LicenseShortName", {}).get("value", ""))
    return {
        "url": info.get("thumburl") or info["url"],
        "page": info.get("descriptionurl"),
        "credit": f"Photo : {auteur}{f', {licence}' if licence else ''}, via Wikimedia Commons",
    }


def main() -> None:
    fiches = json.loads((ICI / "candidats-2027.json").read_text(encoding="utf-8"))["candidats"]
    photos = {}
    for c in fiches:
        photo = c.get("photo")
        if not photo:
            continue
        titre = titre_commons(photo)
        if not titre:
            photos[c["nom"]] = {"url": photo, "credit": c.get("credit", "")}
            continue
        try:
            infos = infos_commons(titre)
            if infos:
                photos[c["nom"]] = infos
            else:
                print(f"⚠ Photo introuvable sur Commons pour {c['nom']} : {titre}", file=sys.stderr)
        except Exception as e:  # pas de réseau, API indisponible… on garde les initiales
            print(f"⚠ Photo de {c['nom']} non récupérée ({e})", file=sys.stderr)
    json.dump(photos, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
