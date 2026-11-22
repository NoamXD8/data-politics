---
toc: false
---

```js
import {COULEURS, fmtPct, fmtNombre, participation, resultats, court, scrutinParDefaut} from "../components/elections.js";

const dep = FileAttachment(`../data/departements/${observable.params.dep}.json`).json();
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
const commune = view(Inputs.select(choixCommunes, {
  label: "Commune",
  format: (c) => c.nom,
  value: choixCommunes.find((c) => c.code === depuisUrl) ?? TOUT
}));
```

```js
const election = view(Inputs.select(elections, {label: "Scrutin", format: (e) => e.libelle, value: scrutinParDefaut(elections)}));
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
  subtitle: "Part des suffrages exprimés. Le trait vertical indique le score en France entière.",
  width,
  height: 60 + comparaison.length * 34,
  marginLeft: 140,
  marginRight: 60,
  x: {axis: null, domain: [0, Math.max(0.5, ...comparaison.flatMap((d) => [d.part, d.france ?? 0]))]},
  y: {label: null, domain: comparaison.map((d) => d.candidat)},
  color: {domain: [territoire, "France"], range: [COULEURS.commune, COULEURS.france], legend: true},
  marks: [
    Plot.barX(comparaison, {y: "candidat", x: "part", fill: () => territoire, rx2: 4, insetTop: 6, insetBottom: 6}),
    Plot.tickX(comparaison.filter((d) => d.france != null), {y: "candidat", x: "france", stroke: () => "France", strokeWidth: 3}),
    Plot.text(comparaison, {y: "candidat", x: (d) => Math.max(d.part, d.france ?? 0), text: (d) => fmtPct(d.part), textAnchor: "start", dx: 6, fill: "currentColor"}),
    Plot.tip(comparaison, Plot.pointerY({y: "candidat", x: "part", title: (d) =>
      `${d.candidat}\n${territoire} : ${fmtPct(d.part)} (${fmtNombre(d.voix)} voix)\nFrance : ${fmtPct(d.france)}`})),
    Plot.ruleX([0])
  ]
}) : html``);
```

## La participation au fil des scrutins

```js
const serieParticipation = elections.flatMap((e) => [
  ...(commune.code ? [{scrutin: court(e), qui: commune.nom, p: participation(serieTerritoire[e.id])}] : []),
  {scrutin: court(e), qui: dep.nom, p: participation(dep.total[e.id])},
  {scrutin: court(e), qui: "France", p: participation(france.france[e.id])}
]).filter((d) => d.p != null);
const series = commune.code ? [commune.nom, dep.nom, "France"] : [dep.nom, "France"];
const couleurs = commune.code ? [COULEURS.commune, COULEURS.departement, COULEURS.france] : [COULEURS.departement, COULEURS.france];
display(Plot.plot({
  subtitle: "Votants / inscrits",
  width,
  height: 300,
  marginBottom: 50,
  marginRight: 30,
  x: {label: null, domain: elections.map(court), tickRotate: -30},
  y: {label: null, domain: [0, 1], tickFormat: (d) => fmtPct(d).replace(",0", ""), grid: true},
  color: {domain: series, range: couleurs, legend: true},
  marks: [
    Plot.line(serieParticipation, {x: "scrutin", y: "p", stroke: "qui", strokeWidth: 2}),
    Plot.dot(serieParticipation, {x: "scrutin", y: "p", fill: "qui", r: 4, stroke: "var(--theme-background)", strokeWidth: 2}),
    Plot.tip(serieParticipation, Plot.pointer({x: "scrutin", y: "p", title: (d) => `${d.qui} · ${d.scrutin}\nParticipation : ${fmtPct(d.p)}`}))
  ]
}));
```

## Les communes du département

<p class="explication">${election.libelle}. Clique sur une commune pour l'afficher ci-dessus. Les colonnes sont triables.</p>

```js
const tableCommunes = Object.entries(dep.communes).map(([code, c]) => {
  const vc = c.r[election.id];
  const r = resultats(election, vc).filter((x) => x.candidat !== "Autres");
  return {code, commune: c.nom, inscrits: vc?.[0] ?? null, participation: participation(vc), enTete: r[0]?.candidat ?? "–", score: r[0]?.part ?? null};
}).filter((d) => d.inscrits != null);
display(Inputs.table(tableCommunes, {
  columns: ["commune", "inscrits", "participation", "enTete", "score"],
  header: {commune: "Commune", inscrits: "Inscrits", participation: "Participation", enTete: "En tête", score: "Score"},
  format: {
    commune: (nom, i, data) => html`<a href="?commune=${data[i].code}">${nom}</a>`,
    inscrits: fmtNombre,
    participation: fmtPct,
    score: fmtPct
  },
  sort: "inscrits",
  reverse: true,
  rows: 12,
  layout: "auto"
}));
```
