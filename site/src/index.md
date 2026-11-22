---
title: Accueil
toc: false
---

```js
import {COULEURS, fmtPct, fmtNombre, participation, resultats, court, scrutinParDefaut, normaliser} from "./components/elections.js";

const elections = FileAttachment("data/elections.json").json();
const france = FileAttachment("data/france.json").json();
const communes = FileAttachment("data/communes.json").json();
const departements = FileAttachment("data/departements.json").json();
```

# Les élections en France, en données

<p class="explication">Tous les résultats officiels depuis 2012, de la France entière jusqu'à ta commune. Les données viennent du Ministère de l'Intérieur, publiées sur data.gouv.fr.</p>

## Trouve ta commune

```js
const requete = view(Inputs.text({placeholder: "Ex. : Lyon, Bourg-en-Bresse, 69123…", autocomplete: "off"}));
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
const election = view(Inputs.select(elections, {label: "Scrutin", format: (e) => e.libelle, value: scrutinParDefaut(elections)}));
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
  marginLeft: 140,
  marginRight: 60,
  x: {axis: null, domain: [0, Math.max(0.5, ...lignes.map((d) => d.part))]},
  y: {label: null, domain: lignes.map((d) => d.candidat)},
  marks: [
    Plot.barX(lignes, {y: "candidat", x: "part", fill: COULEURS.commune, rx2: 4, insetTop: 4, insetBottom: 4,
      tip: {format: {x: false, y: false}, channels: {Score: (d) => fmtPct(d.part), Voix: (d) => fmtNombre(d.voix)}}}),
    Plot.text(lignes, {y: "candidat", x: "part", text: (d) => fmtPct(d.part), textAnchor: "start", dx: 6, fill: "currentColor"}),
    Plot.ruleX([0])
  ]
}));
```

## La participation au fil des scrutins

```js
const serie = elections.map((e) => ({scrutin: court(e), participation: participation(france.france[e.id]), selection: e.id === election.id}));
display(Plot.plot({
  subtitle: "Votants / inscrits, France entière",
  width,
  height: 280,
  marginBottom: 50,
  x: {label: null, domain: serie.map((d) => d.scrutin), tickRotate: -30},
  y: {label: null, domain: [0, 1], tickFormat: (d) => fmtPct(d).replace(",0", ""), grid: true},
  marks: [
    Plot.line(serie, {x: "scrutin", y: "participation", stroke: COULEURS.france, strokeWidth: 2}),
    Plot.dot(serie, {x: "scrutin", y: "participation", fill: COULEURS.france, r: (d) => (d.selection ? 6 : 4), tip: {format: {y: false}, channels: {Participation: (d) => fmtPct(d.participation)}}}),
    Plot.text(serie.filter((d) => d.selection), {x: "scrutin", y: "participation", text: (d) => fmtPct(d.participation), dy: -14, fill: "currentColor"})
  ]
}));
```

## Par département

<p class="explication">Clique sur un département pour voir le détail de ses communes. Les colonnes sont triables.</p>

```js
const tableDep = departements.map((d) => {
  const vd = france.departements[d.code]?.[election.id];
  const r = resultats(election, vd).filter((x) => x.candidat !== "Autres");
  return {code: d.code, departement: d.nom, participation: participation(vd), enTete: r[0]?.candidat ?? "–", score: r[0]?.part ?? null};
});
display(Inputs.table(tableDep, {
  columns: ["code", "departement", "participation", "enTete", "score"],
  header: {code: "N°", departement: "Département", participation: "Participation", enTete: "En tête", score: "Score"},
  format: {
    departement: (nom, i, data) => html`<a href="./departement/${data[i].code}">${nom}</a>`,
    participation: fmtPct,
    score: fmtPct
  },
  rows: 12,
  layout: "auto"
}));
```
