# Data Politics

Site grand public pour explorer les résultats électoraux français, de la France entière jusqu'à la commune.

- `pipeline/` : Python + DuckDB. Télécharge les résultats officiels (data.gouv.fr) et produit des JSON compacts.
- `site/` : [Observable Framework](https://observablehq.com/framework/). Pages en Markdown + graphiques Observable Plot, site 100 % statique.

## Installation (une seule fois)

Prérequis : Python 3.10+ et Node.js 20+.

```bash
python -m venv politics-env
source politics-env/bin/activate        # Windows : politics-env\Scripts\activate
pip install -r requirements.txt
cd site && npm install && cd ..
```

## Lancer

```bash
python -m pipeline.download      # ~220 Mo, une seule fois
python -m pipeline.build         # produit data/processed/ (affiche un rapport de contrôle)
python -m pipeline.sondages      # sondages 2022 (NSPPolls) : évolution, écarts, précision des instituts
cd site && npm run dev           # http://127.0.0.1:3000
```

`pipeline.build` affiche la liste de **tous** les scrutins présents dans les données source.
Le périmètre (types de scrutins, année minimum, nombre de candidats affichés) se règle dans `pipeline/config.py`.

Si tu relances le pipeline, vide le cache du site : `cd site && npm run clean`.

## Tester sans les vraies données

```bash
python -m tests.make_fixture     # fausses données au schéma exact de data.gouv
python -m tests.run_fixture      # lance le pipeline dessus + contrôles de cohérence
cd site && DATA_DIR=../tests/fixture/processed npm run dev
```

## Mettre en ligne

`cd site && npm run build` produit `site/dist/`, à déposer sur GitHub Pages, Netlify ou Vercel.

## Structure des données produites

Pour chaque territoire et scrutin : `[inscrits, votants, exprimes, blancs, nuls, voix_1, …, voix_n, voix_autres]`,
dans l'ordre de `elections.json[i].candidats`. Voir la docstring de `pipeline/build.py`.

## Tenir à jour les candidatures 2027

Tout est dans `site/src/data/candidats-2027.json`. Champs d'une fiche :

| Champ | Obligatoire | Contenu |
|---|---|---|
| `nom`, `parti`, `famille`, `fonction`, `declaration` | oui | identité ; `famille` = un code de `site/src/components/familles.js` ; date `AAAA-MM-JJ` (ou `AAAA-MM`, `AAAA`) |
| `bio` | non | 2-3 phrases, mandats et fonctions publics uniquement |
| `parcours` | non | `[{"periode": "2017-2020", "fonction": "Premier ministre"}]` |
| `programme` | non | `[{"theme": "Retraites", "proposition": "…", "source": "https://…"}]` |
| `site` | non | site de campagne |
| `photo` | non | photo **libre de droits** : colle simplement le lien de la page Wikimedia Commons (`https://commons.wikimedia.org/wiki/File:…`). L'image, l'auteur et la licence sont récupérés automatiquement à la construction du site (`site/src/data/photos.json.py`) et le crédit s'affiche sous la photo. Pour une autre source, mets l'adresse directe de l'image et renseigne `credit`. |
| `note` | non | statut particulier (candidature sous condition, etc.) |

Les résultats aux présidentielles passées sont calculés automatiquement depuis les données officielles.

## Feuille de route

- [x] Phase 1a : pipeline, accueil national, pages département + fiche commune
- [ ] Phase 1b : carte (contours communes), circonscriptions, données INSEE
- [ ] Phase 2 : page candidat (carrière Wikidata, résultats passés, actus), vote & sociologie
- [ ] Phase 3 : tableau de bord 2027 (parrainages, sondages, soirée électorale)
