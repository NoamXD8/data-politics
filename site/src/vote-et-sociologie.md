---
title: Vote et sociologie
toc: false
---

```js
import {couleur} from "./components/familles.js";

const socio = FileAttachment("data/sociologie.json").json();
```

# Vote et sociologie

<div class="note" label="Comparer des territoires, pas des personnes">On compare ici des <strong>communes</strong>, pas des électeurs. Si un candidat fait de meilleurs scores dans les communes les plus aisées, cela ne veut pas dire que les électeurs aisés ont voté pour lui : dans ces communes vivent aussi des personnes modestes. Une relation entre deux chiffres n'est pas non plus une explication.</div>

```js
if (!socio) display(html`<div class="note">Les données INSEE ne sont pas encore croisées : télécharge la base du comparateur de territoires (voir le README), puis lance <code>python -m pipeline.sociologie</code>.</div>`);
```

```js
const ids = Object.keys(socio.elections);
const eid = view(Inputs.select(ids, {label: "Scrutin", format: (i) => socio.elections[i].libelle, value: ids[0]}));
```

```js
const ind = view(Inputs.select(Object.keys(socio.indicateurs), {label: "Indicateur", format: (k) => socio.indicateurs[k].libelle, value: "med"}));
```

```js
const bloc = socio.elections[eid];
const info = socio.indicateurs[ind];
const tranchesInd = bloc.indicateurs[ind];
const parScore = [...bloc.candidats].sort((a, b) =>
  tranchesInd.reduce((s, t) => s + t.scores[b.nom], 0) - tranchesInd.reduce((s, t) => s + t.scores[a.nom], 0));
const choisis = view(Inputs.checkbox(parScore.map((c) => c.nom), {label: "Candidats", value: parScore.slice(0, 5).map((c) => c.nom)}));
```

```js
const fmt = {
  euros: (x) => `${Math.round(x / 100) * 100 >= 1000 ? (Math.round(x / 100) * 100).toLocaleString("fr-FR") : Math.round(x)} €`,
  pct: (x) => `${x.toLocaleString("fr-FR", {maximumFractionDigits: 1})} %`,
  pct100: (x) => `${x.toLocaleString("fr-FR", {maximumFractionDigits: 1})} %`,
  nombre: (x) => (x >= 1000 ? `${Math.round(x / 100) / 10} k` : Math.round(x).toLocaleString("fr-FR"))
}[info.format];
const etiquette = (t) => fmt(t.mediane);
const familles = new Map(bloc.candidats.map((c) => [c.nom, c.famille]));
const points = tranchesInd.flatMap((t) => choisis.map((nom) => ({tranche: t.tranche, nom, score: t.scores[nom], t})));
```

## Score des candidats selon « ${info.libelle.toLowerCase()} »

<p class="explication">Les ${bloc.communes.toLocaleString("fr-FR")} communes sont rangées en 10 groupes, du plus faible au plus fort ${info.libelle.toLowerCase()} (${info.unite}). Chaque groupe rassemble environ 10 % des inscrits. L'axe horizontal indique la valeur médiane de chaque groupe.</p>

```js
display(Plot.plot({
  width,
  height: 420,
  marginRight: 140,
  x: {label: `${info.libelle} (médiane du groupe) →`, domain: tranchesInd.map((t) => t.tranche), tickFormat: (k) => etiquette(tranchesInd.find((t) => t.tranche === k))},
  y: {label: null, grid: true, tickFormat: (d) => `${Math.round(d * 100)} %`},
  color: {domain: choisis, range: choisis.map((n) => couleur(familles.get(n), dark))},
  marks: [
    Plot.line(points, {x: "tranche", y: "score", stroke: "nom", strokeWidth: 2.2}),
    Plot.dot(points, {x: "tranche", y: "score", fill: "nom", r: 3.5}),
    Plot.text(points.filter((d) => d.tranche === tranchesInd.at(-1).tranche), {x: "tranche", y: "score", text: "nom", dx: 8, textAnchor: "start", fill: "nom", fontWeight: 600}),
    Plot.tip(points, Plot.pointer({x: "tranche", y: "score", title: (d) =>
      `${d.nom} : ${(d.score * 100).toLocaleString("fr-FR", {maximumFractionDigits: 1})} %\nCommunes où ${info.libelle.toLowerCase()} va de ${fmt(d.t.min)} à ${fmt(d.t.max)} (${d.t.communes.toLocaleString("fr-FR")} communes)`}))
  ]
}));
```

```js
const liens = Object.entries(bloc.correlations[ind]).map(([nom, r]) => ({nom, r})).filter((d) => Number.isFinite(d.r)).sort((a, b) => Math.abs(b.r) - Math.abs(a.r));
const force = (r) => (Math.abs(r) >= 0.5 ? "nette" : Math.abs(r) >= 0.3 ? "modérée" : "faible");
display(html`<p class="explication">Relations les plus marquées, commune par commune (coefficient de corrélation, de −1 à +1) :
  ${liens.slice(0, 3).map((d, i) => html`${i ? " · " : ""}<strong>${d.nom}</strong> ${d.r > 0 ? "plus haut" : "plus bas"} quand ${info.libelle.toLowerCase()} augmente (r = ${d.r.toLocaleString("fr-FR")}, relation ${force(d.r)})`)}.</p>`);
```

## Participation

```js
display(Plot.plot({
  width,
  height: 260,
  subtitle: "Votants / inscrits, par groupe de communes",
  x: {label: `${info.libelle} (médiane du groupe) →`, domain: tranchesInd.map((t) => t.tranche), tickFormat: (k) => etiquette(tranchesInd.find((t) => t.tranche === k))},
  y: {label: null, grid: true, tickFormat: (d) => `${Math.round(d * 100)} %`},
  marks: [
    Plot.line(tranchesInd, {x: "tranche", y: "participation", stroke: "var(--series-1)", strokeWidth: 2.2}),
    Plot.dot(tranchesInd, {x: "tranche", y: "participation", fill: "var(--series-1)", r: 4}),
    Plot.text(tranchesInd, {x: "tranche", y: "participation", text: (t) => `${(t.participation * 100).toLocaleString("fr-FR", {maximumFractionDigits: 1})} %`, dy: -12, fill: "currentColor"})
  ]
}));
```

<p class="explication">Sources : résultats officiels (Ministère de l'Intérieur) ; indicateurs communaux de l'INSEE (base du comparateur de territoires). Les communes nouvelles ou fusionnées dont le code a changé entre les deux sources ne sont pas comptées.</p>
