---
toc: false
---

```js
import {graphiqueParticipation} from "../components/participation.js";
import {carteCommunes} from "../components/carte.js";
import {puces, recherche, choixScrutin, choixTour} from "../components/choix.js";
import {couleur, FAMILLES} from "../components/familles.js";
import {COULEURS, fmtPct, fmtNombre, participation, resultats, raccourcir, scrutinParDefaut} from "../components/elections.js";

const dep = FileAttachment(`../data/departements/${observable.params.dep}.json`).json();
const contoursCommunes = FileAttachment(`../data/communes/${observable.params.dep}.json`).json().then((g) => (g.features.length ? g : null));
const elections = FileAttachment("../data/elections.json").json();
const france = FileAttachment("../data/france.json").json();
```

<p class="explication"><a href="../">← Accueil</a></p>

# ${dep.nom} <small>(${dep.code})</small>

```js
// Choix de la commune : « Tout le département » ou une commune, mémorisé dans l'URL (?commune=...)
const TOUT = {code: null, nom: "Tout le département"};
const choixCommunes = [TOUT, ...Object.entries(dep.communes)
  .map(([code, c]) => ({code, nom: c.nom}))
  .sort((a, b) => a.nom.localeCompare(b.nom, "fr"))];
const depuisUrl = new URLSearchParams(location.search).get("commune");
const commune = view(recherche(choixCommunes.slice(1), {
  label: "Commune",
  tous: TOUT,
  format: (c) => c.nom,
  placeholder: "Chercher une commune du département…",
  value: choixCommunes.find((c) => c.code === depuisUrl) ?? TOUT
}));
```

```js
const election = view(choixScrutin(elections, {value: scrutinParDefaut(elections)}));
```

```js
// Garde l'URL à jour pour pouvoir partager le lien d'une commune
{
  const url = new URL(location.href);
  if (commune.code) url.searchParams.set("commune", commune.code);
  else url.searchParams.delete("commune");
  history.replaceState(null, "", url);
}
```

```js
const territoire = commune.code ? commune.nom : dep.nom;
const serieTerritoire = commune.code ? dep.communes[commune.code].r : dep.total;
const v = serieTerritoire[election.id];
const lignes = resultats(election, v);
const national = new Map(resultats(election, france.france[election.id]).map((d) => [d.candidat, d.part]));
```

## ${territoire} · ${election.libelle}

```js
if (!v) display(html`<p class="explication">Pas de résultats pour ce territoire à ce scrutin (par exemple : pas de second tour dans cette circonscription).</p>`);
```

<div class="chiffres">
  <div class="card"><div class="valeur">${fmtPct(participation(v))}</div><div class="legende">participation ici</div></div>
  <div class="card"><div class="valeur">${fmtPct(participation(france.france[election.id]))}</div><div class="legende">participation en France</div></div>
  <div class="card"><div class="valeur">${fmtNombre(v?.[0])}</div><div class="legende">inscrits</div></div>
</div>

```js
const comparaison = lignes.map((d) => ({...d, france: national.get(d.candidat) ?? null}));
display(v ? Plot.plot({
  subtitle: `Part des suffrages exprimés à ${territoire}. Le trait vertical indique le score en France entière.`,
  width,
  height: 50 + comparaison.length * 34,
  marginLeft: 190,
  marginRight: 60,
  x: {axis: null, domain: [0, Math.max(0.5, ...comparaison.flatMap((d) => [d.part, d.france ?? 0]))]},
  y: {label: null, domain: comparaison.map((d) => d.candidat), tickFormat: (d) => raccourcir(d)},
  marks: [
    Plot.barX(comparaison, {y: "candidat", x: "part", fill: (d) => couleur(d.famille, dark), rx2: 4, insetTop: 6, insetBottom: 6}),
    Plot.tickX(comparaison.filter((d) => d.france != null), {y: "candidat", x: "france", stroke: "currentColor", strokeWidth: 2.5}),
    Plot.text(comparaison, {y: "candidat", x: (d) => Math.max(d.part, d.france ?? 0), text: (d) => fmtPct(d.part), textAnchor: "start", dx: 6, fill: "currentColor"}),
    Plot.tip(comparaison, Plot.pointerY({y: "candidat", x: "part", title: (d) =>
      `${d.candidat} · ${FAMILLES[d.famille].nom}\n${territoire} : ${fmtPct(d.part)} (${fmtNombre(d.voix)} voix)\nFrance : ${fmtPct(d.france)}`})),
    Plot.ruleX([0])
  ]
}) : html``);
```

## La carte des communes

```js
const modeCarte = view(puces(["tete", "participation"], {value: "tete", format: (m) => (m === "tete" ? "Candidat en tête" : "Participation")}));
```

```js
display(contoursCommunes
  ? html`<p class="explication">${election.libelle}. ${modeCarte === "tete" ? "Chaque commune prend la couleur du candidat arrivé en tête ; plus la teinte est soutenue, plus son score est élevé." : "Plus le bleu est foncé, plus la participation est forte."} Clique sur une commune pour afficher ses résultats.</p>
    ${carteCommunes({contours: contoursCommunes, communes: dep.communes, election, mode: modeCarte, selection: commune.code, dark, width: Math.min(width, 760)})}`
  : html`<p class="explication">Pas de carte des communes pour ce territoire.</p>`);
```

## La participation au fil des scrutins

<p class="explication">Chaque type d'élection est comparé avec lui-même : on vote toujours beaucoup plus à la présidentielle qu'aux européennes.</p>

```js
const tour = view(choixTour());
```

```js
display(graphiqueParticipation({
  elections, tour, width, selection: election,
  series: [
    ...(commune.code ? [{nom: commune.nom, couleur: COULEURS.commune, valeurs: serieTerritoire}] : []),
    {nom: dep.nom, couleur: COULEURS.departement, valeurs: dep.total},
    {nom: "France", couleur: COULEURS.france, valeurs: france.france}
  ]
}));
```

## Les communes du département

<p class="explication">${election.libelle}. Clique sur une commune pour l'afficher ci-dessus. Les colonnes sont triables.</p>

```js
const tableCommunes = Object.entries(dep.communes).map(([code, c]) => {
  const vc = c.r[election.id];
  const r = resultats(election, vc).filter((x) => x.candidat !== "Autres");
  return {code, commune: c.nom, inscrits: vc?.[0] ?? null, participation: participation(vc), enTete: r[0]?.candidat ?? "–", famille: r[0]?.famille, score: r[0]?.part ?? null};
}).filter((d) => d.inscrits != null);
display(Inputs.table(tableCommunes, {
  columns: ["commune", "inscrits", "participation", "enTete", "score"],
  header: {commune: "Commune", inscrits: "Inscrits", participation: "Participation", enTete: "En tête", score: "Score"},
  format: {
    commune: (nom, i, data) => html`<a href="?commune=${data[i].code}">${nom}</a>`,
    inscrits: fmtNombre,
    participation: fmtPct,
    enTete: (nom, i, data) => data[i].famille ? html`<span style="display:inline-block;width:.7em;height:.7em;border-radius:2px;margin-right:.4em;background:${couleur(data[i].famille, dark)}"></span>${nom}` : nom,
    score: fmtPct
  },
  sort: "inscrits",
  reverse: true,
  rows: 12,
  layout: "auto"
}));
```
