"""Télécharge les fichiers parquet de data.gouv.fr dans data/raw/.

Usage : python -m pipeline.download [--force]
"""

import sys

import requests

from pipeline.config import RAW_DIR, SOURCES


def telecharger(nom: str, url: str, force: bool = False) -> None:
    dest = RAW_DIR / nom
    if dest.exists() and not force:
        print(f"✓ {nom} déjà présent ({dest.stat().st_size / 1e6:.1f} Mo), on passe. (--force pour retélécharger)")
        return
    print(f"↓ {nom} …")
    tmp = dest.with_suffix(".part")
    with requests.get(url, stream=True, timeout=60, allow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        lu = 0
        with open(tmp, "wb") as f:
            for bloc in r.iter_content(chunk_size=1 << 20):
                f.write(bloc)
                lu += len(bloc)
                if total:
                    print(f"\r  {lu / 1e6:6.1f} / {total / 1e6:.1f} Mo", end="", flush=True)
    print()
    tmp.rename(dest)
    print(f"✓ {nom} téléchargé")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    force = "--force" in sys.argv
    for nom, url in SOURCES.items():
        telecharger(nom, url, force)


if __name__ == "__main__":
    main()
