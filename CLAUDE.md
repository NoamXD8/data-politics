# Conventions du projet

## Sélecteurs (règle pour toutes les pages)

Tout choix proposé à l'utilisateur (scrutin, tour, candidats, indicateur, commune…)
passe par `site/src/components/choix.js`, en pastilles. Pas d'`Inputs.select`,
`Inputs.radio`, `Inputs.checkbox` ni `Inputs.text` dans les pages.

- `puces(options, {value, multiple, format, detail, couleur, groupe, raccourcis, label})` — choix simple ou multiple
- `recherche(options, {value, format, placeholder, tous, label})` — liste longue (communes…)
- `champ({placeholder, label})` — saisie libre
- `choixScrutin(elections)` / `choixTour()` — raccourcis courants

Toujours appeler `view(...)` dans sa propre cellule (sinon « circular definition »).
Styles : bloc « Sélecteurs en pastilles » de `site/src/style.css`.
