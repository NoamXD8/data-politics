---
title: Accueil
toc: false
---

```js
import {graphiqueParticipation} from "./components/participation.js";
import {carteDepartements} from "./components/carte.js";
import {champ, choixScrutin, choixTour} from "./components/choix.js";
import {couleur, FAMILLES} from "./components/familles.js";
import {COULEURS, fmtPct, fmtNombre, participation, resultats, raccourcir, scrutinParDefaut, normaliser, slug} from "./components/elections.js";

const elections = FileAttachment("data/elections.json").json();
const france = FileAttachment("data/france.json").json();
const communes = FileAttachment("data/communes.json").json();
const departements = FileAttachment("data/departements.json").json();
const contours = FileAttachment("data/departements-contours.geojson").json();
```

# Les élections en France, en données

<p class="explication">Tous les résultats officiels depuis 2012, de la France entière jusqu'à ta commune. Les données viennent du Ministère de l'Intérieur, publiées sur data.gouv.fr.</p>

## Trouve ta commune

```js
const requete = view(champ({placeholder: "Ex. : Lyon, Bourg-en-Bresse, 69123…"}));
```

```js
const index = communes.map(([code, nom, dep]) => ({code, nom, dep, cle: normaliser(`${nom} ${code}`)}));
```

```js
const q = normaliser(requete.trim());
const trouves = q.length < 2 ? [] : index.filter((d) => d.cle.includes(q))
  .sort((a, b) => (normaliser(a.nom).startsWith(q) ? 0 : 1) - (normaliser(b.nom).startsWith(q) ? 0 : 1) || a.nom.localeCompare(b.nom, "fr"))
  .slice(0, 8);
const nomsDep = new Map(departements.map((d) => [d.code, d.nom]));
if (q.length >= 2) display(trouves.length === 0 ? html`<p class="explication">Aucune commune trouvée.</p>` : html`<ul class="resultats-recherche">${trouves.map((d) => html`<li><a href="./departement/${d.dep}?commune=${d.code}">${d.nom}</a> <small>${nomsDep.get(d.dep) ?? d.dep} · ${d.code}</small></li>`)}</ul>`);
```

## Résultats nationaux

```js
const election = view(choixScrutin(elections, {value: scrutinParDefaut(elections)}));
```

```js
const v = france.france[election.id];
const lignes = resultats(election, v);
```

<div class="chiffres">
  <div class="card"><div class="valeur">${fmtPct(participation(v))}</div><div class="legende">participation (votants / inscrits)</div></div>
  <div class="card"><div class="valeur">${fmtNombre(v?.[0])}</div><div class="legende">inscrits</div></div>
  <div class="card"><div class="valeur">${fmtPct(v ? (v[3] + v[4]) / v[1] : null)}</div><div class="legende">votes blancs et nuls (parmi les votants)</div></div>
</div>

```js
display(Plot.plot({
  title: election.libelle,
  subtitle: "Part des suffrages exprimés (hors blancs et nuls), France entière",
  width,
  height: 40 + lignes.length * 34,
  marginLeft: 190,
  marginRight: 60,
  x: {axis: null, domain: [0, Math.max(0.5, ...lignes.map((d) => d.part))]},
  y: {label: null, domain: lignes.map((d) => d.candidat), tickFormat: (d) => raccourcir(d)},
  marks: [
    Plot.barX(lignes, {y: "candidat", x: "part", fill: (d) => couleur(d.famille, dark), rx2: 4, insetTop: 4, insetBottom: 4,
      tip: {format: {x: false, y: false, fill: false}, channels: {Nom: "candidat", Famille: (d) => FAMILLES[d.famille].nom, Score: (d) => fmtPct(d.part), Voix: (d) => fmtNombre(d.voix)}}}),
    Plot.text(lignes, {y: "candidat", x: "part", text: (d) => fmtPct(d.part), textAnchor: "start", dx: 6, fill: "currentColor"}),
    Plot.ruleX([0])
  ]
}));
```

## Les candidat·es de ${derniere.annee}

<p class="explication">Une page par candidat·e, construite sur le même modèle pour tous : scores, carte, évolution.</p>

```js
const derniere = elections.filter((e) => e.type === "pres" && e.tour === 1).at(-1);
const scoresDerniere = new Map(resultats(derniere, france.france[derniere.id]).map((d) => [d.candidat, d.part]));
display(html`<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.5rem">${derniere.noms.map((n, i) => [n, derniere.familles[i]]).filter(([n]) => n !== "Autres").map(([n, f]) =>
  html`<a href="./candidat/${slug(n)}" style="display:flex;align-items:center;gap:.6em;padding:.5rem .7rem;border:1px solid var(--theme-foreground-faintest);border-radius:8px;text-decoration:none;color:inherit">
    <span style="width:.9em;height:2.2em;border-radius:3px;flex:none;background:${couleur(f, dark)}"></span>
    <span><strong style="font-weight:600">${n}</strong><br><small style="color:var(--theme-foreground-muted)">${FAMILLES[f].nom} · ${fmtPct(scoresDerniere.get(n))}</small></span></a>`)}</div>`);
```

## La carte

<p class="explication">${election.libelle} : chaque département prend la couleur du candidat arrivé en tête. Plus la teinte est soutenue, plus son score est élevé. Clique sur un département pour voir le détail de ses communes.</p>

```js
display(carteDepartements({contours, departements, parDep: france.departements, election, width: Math.min(width, 760), dark}));
```

## La participation au fil des scrutins

<p class="explication">Chaque type d'élection est comparé avec lui-même : on vote toujours beaucoup plus à la présidentielle qu'aux européennes.</p>

```js
const tour = view(choixTour());
```

```js
display(graphiqueParticipation({
  elections, tour, width, selection: election,
  series: [{nom: "France", couleur: COULEURS.france, valeurs: france.france}]
}));
```

## Par département

<p class="explication">Clique sur un département pour voir le détail de ses communes. Les colonnes sont triables.</p>

```js
const pastille = (nom, famille) => famille ? html`<span style="display:inline-block;width:.7em;height:.7em;border-radius:2px;margin-right:.4em;background:${couleur(famille, dark)}"></span>${nom}` : nom;
const tableDep = departements.map((d) => {
  const vd = france.departements[d.code]?.[election.id];
  const r = resultats(election, vd).filter((x) => x.candidat !== "Autres");
  return {code: d.code, departement: d.nom, participation: participation(vd), enTete: r[0]?.candidat ?? "–", famille: r[0]?.famille, score: r[0]?.part ?? null};
});
display(Inputs.table(tableDep, {
  columns: ["code", "departement", "participation", "enTete", "score"],
  header: {code: "N°", departement: "Département", participation: "Participation", enTete: "En tête", score: "Score"},
  format: {
    departement: (nom, i, data) => html`<a href="./departement/${data[i].code}">${nom}</a>`,
    participation: fmtPct,
    enTete: (nom, i, data) => pastille(nom, data[i].famille),
    score: fmtPct
  },
  rows: 12,
  layout: "auto"
}));
```
